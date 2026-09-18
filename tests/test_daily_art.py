from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image
import pytest

from scripts import serve_daily_art as server
from scripts import sync_daily_art as client


DAY = date(2026, 9, 18)


def png(path, color="red"):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (160, 90), color).save(path)
    return path


def manifest(path, day=DAY):
    return dict(server.read_png(path), date=day.isoformat(), cached=True)


@pytest.mark.parametrize("value", ["../../etc/passwd", "2026-9-18", "2026-09-31", "2026-09-18;id", "20260918"])
def test_reject_unsafe_or_noncanonical_dates(value):
    with pytest.raises(ValueError):
        server.valid_date(value)


def test_server_generates_once_and_preserves_other_dates(tmp_path):
    calls = []

    def generate(job, prompt, config):
        calls.append(prompt)
        png(job / "source.png")

    first = server.ensure(tmp_path, DAY, server.clean_context({}), {}, generate)
    second = server.ensure(tmp_path, DAY, server.clean_context({"weather": "rain"}), {}, generate)
    server.ensure(tmp_path, date(2026, 9, 19), server.clean_context({}), {}, generate)
    assert not first["cached"] and second["cached"]
    assert len(calls) == 2
    assert first["sha256"] == second["sha256"]
    assert len(list((tmp_path / "cache").glob("*/source.png"))) == 2
    assert "built-in image_gen" in calls[0]


def test_generation_lock_prevents_duplicate_job(tmp_path):
    job = tmp_path / "cache" / DAY.isoformat()
    job.mkdir(parents=True)
    with (job / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="already running"):
            server.ensure(tmp_path, DAY, {}, {}, lambda *_: pytest.fail("Duplicate generation"))


def test_failure_cooldown_and_daily_attempt_limit(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(server.time, "time", lambda: 5000)

    def fail(*args):
        calls.append(1)
        raise RuntimeError("Test failure")

    with pytest.raises(RuntimeError, match="Test failure"):
        server.ensure(tmp_path, DAY, {}, {}, fail)
    with pytest.raises(RuntimeError, match="cooldown"):
        server.ensure(tmp_path, DAY, {}, {}, fail)
    monkeypatch.setattr(server.time, "time", lambda: 7000)
    with pytest.raises(RuntimeError, match="Test failure"):
        server.ensure(tmp_path, DAY, {}, {}, fail)
    monkeypatch.setattr(server.time, "time", lambda: 9000)
    with pytest.raises(RuntimeError, match="limit"):
        server.ensure(tmp_path, DAY, {}, {}, fail)
    assert len(calls) == 2


def test_server_rejects_corrupt_cache_without_spending_more(tmp_path):
    source = png(tmp_path / "cache" / DAY.isoformat() / "source.png")
    data = bytearray(source.read_bytes())
    data[45] ^= 1
    source.write_bytes(data)
    with pytest.raises(ValueError):
        server.ensure(tmp_path, DAY, {}, {}, lambda *_: pytest.fail("Unexpected generation"))


@pytest.mark.parametrize("context", [{"weather": "command"}, {"weather": {}}, {"theme": "bad\ntext"}, {"theme": "x" * 501}])
def test_context_is_bounded_data(context):
    with pytest.raises(ValueError):
        server.clean_context(context)


@pytest.mark.parametrize("instant,expected", [("2026-09-19T04:59:59+09:00", DAY),
                                               ("2026-09-19T05:00:00+09:00", date(2026, 9, 19)),
                                               ("2026-01-01T01:00:00+09:00", date(2025, 12, 31))])
def test_japan_date_cutover(instant, expected):
    assert client.target_date(datetime.fromisoformat(instant), 5) == expected


def test_new_image_replaces_previous_and_keeps_only_one(tmp_path):
    directory = tmp_path / "cache"
    directory.mkdir()
    downloaded = png(tmp_path / "download.png")
    client.install_download(directory, downloaded, manifest(downloaded), DAY)
    png(downloaded, "blue")
    tomorrow = date(2026, 9, 19)
    client.install_download(directory, downloaded, manifest(downloaded, tomorrow), tomorrow)
    assert client.already_current(directory, tomorrow)
    assert not client.already_current(directory, DAY)
    assert sorted(p.name for p in directory.iterdir()) == ["current.json", "current.png"]
    with Image.open(directory / "current.png") as image:
        assert image.size == (800, 450)
        assert image.getpixel((100, 100)) == (0, 0, 255)


@pytest.mark.parametrize("damage", ["checksum", "date", "size", "pixels"])
def test_bad_download_leaves_previous_image_intact(tmp_path, damage):
    old = png(tmp_path / "current.png", "green").read_bytes()
    downloaded = png(tmp_path / "download.png")
    info = manifest(downloaded)
    if damage == "checksum":
        info["sha256"] = "0" * 64
    elif damage == "date":
        info["date"] = "2026-09-19"
    elif damage == "size":
        info["bytes"] += 1
    else:
        downloaded.write_bytes(b"broken image data" * 20)
        info["bytes"] = downloaded.stat().st_size
        info["sha256"] = hashlib.sha256(downloaded.read_bytes()).hexdigest()
    with pytest.raises((ValueError, OSError)):
        client.install_download(tmp_path, downloaded, info, DAY)
    assert (tmp_path / "current.png").read_bytes() == old
    assert not (tmp_path / "current.png.tmp").exists()


def test_ssh_uses_host_key_checks_and_quotes_remote_path():
    config = {"ssh_host": "owner@server.local", "remote_script": "art folder/serve.py"}
    command = client.ssh_command(config, "ensure", DAY)
    assert "StrictHostKeyChecking=yes" in command
    assert "BatchMode=yes" in command
    assert command[-1] == "python3 'art folder/serve.py' ensure --date 2026-09-18"
    with pytest.raises(ValueError):
        client.ssh_command({"ssh_host": "-oProxyCommand=invalid"}, "ensure", DAY)


def test_current_image_avoids_ssh_and_generation(tmp_path, monkeypatch):
    directory = tmp_path / "cache/daily_art"
    directory.mkdir(parents=True)
    downloaded = png(tmp_path / "download.png")
    client.install_download(directory, downloaded, manifest(downloaded), DAY)
    monkeypatch.setattr(client.subprocess, "run", lambda *a, **k: pytest.fail("Unexpected SSH"))
    assert not client.sync(tmp_path, {"daily_art": {"enabled": True}}, datetime(2026, 9, 18, 12, tzinfo=timezone.utc))


def test_ssh_failure_preserves_previous_image(tmp_path, monkeypatch):
    directory = tmp_path / "cache/daily_art"
    old = png(directory / "current.png").read_bytes()

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(255, "ssh", stderr="Connection refused")

    monkeypatch.setattr(client.subprocess, "run", fail)
    settings = {"daily_art": {"enabled": True, "ssh_host": "owner@server.local"}}
    with pytest.raises(subprocess.CalledProcessError):
        client.sync(tmp_path, settings, datetime(2026, 9, 18, 12, tzinfo=timezone.utc))
    assert (directory / "current.png").read_bytes() == old


def test_missing_weather_cache_keeps_calendar_theme(tmp_path):
    context = client.context_for_date(tmp_path, {"daily_art": {"themes": {"2026-09-18": "Autumn picnic"}}}, DAY)
    assert context == {"weather": "unknown", "theme": "Autumn picnic", "holiday": ""}


def test_renderer_reloads_without_restart_and_keeps_valid_image_on_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from src.renderers.field_notes_renderer import FieldNotesRenderer
    pygame.init()
    try:
        screen = pygame.display.set_mode((1024, 600))
        renderer = FieldNotesRenderer({"daily_art": {"enabled": True}}, start_worker=False)
        renderer.root = tmp_path
        now = datetime(2026, 9, 18, 12, tzinfo=timezone.utc)
        source = png(tmp_path / "cache/daily_art/current.png", "red")
        renderer.render(screen, now)
        assert screen.get_at((100, 400))[:3] == (255, 0, 0)
        png(source, "blue")
        renderer._artwork_next_check = 0
        renderer.render(screen, now)
        assert screen.get_at((100, 400))[:3] == (0, 0, 255)
        source.write_bytes(b"broken")
        renderer._artwork_next_check = 0
        renderer.render(screen, now)
        assert screen.get_at((100, 400))[:3] == (0, 0, 255)
        renderer.cleanup()
    finally:
        pygame.quit()
