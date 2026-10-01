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


def forecast(category="rain", day=DAY, retrieved_at="2026-09-18T06:00:00+00:00",
             high=19.5, low=12.0, probability=80):
    return {"category": category, "forecast_date": day.isoformat(), "retrieved_at": retrieved_at,
            "high_c": high, "low_c": low, "precipitation_probability": probability}


def write_weather_cache(root, updated="2026-09-18T06:00:00+00:00", days=None):
    root.joinpath("cache").mkdir(parents=True, exist_ok=True)
    days = days or [DAY.isoformat()]
    payload = {"location": {"latitude": 35.681236, "longitude": 139.767125,
                            "timezone": "Asia/Tokyo"},
               "updated": updated,
               "response": {"daily": {"time": days,
                                      "weather_code": [61] * len(days),
                                      "temperature_2m_max": [19.5] * len(days),
                                      "temperature_2m_min": [12.0] * len(days),
                                      "precipitation_probability_max": [80] * len(days)}}}
    root.joinpath("cache/field_notes_weather.json").write_text(json.dumps(payload))


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


def test_server_accepts_bounded_forecast_and_event_context():
    context = {"forecast": forecast(), "theme": "Autumn tea", "holiday": "none",
               "event": {"name": "Coffee Day", "visual_hint": "A steaming cup on a table."}}
    clean = server.clean_context(context, DAY)
    assert clean["forecast"]["category"] == "rain"
    assert clean["forecast"]["high_c"] == 19.5
    assert clean["event"]["name"] == "Coffee Day"


@pytest.mark.parametrize("context", [
    {"forecast": []},
    {"forecast": {"category": "hail"}},
    {"forecast": {**forecast(), "forecast_date": "2026-09-19"}},
    {"forecast": {**forecast(), "retrieved_at": "2026-09-18T06:00:00"}},
    {"forecast": {**forecast(), "low_c": 25}},
    {"forecast": {**forecast(), "precipitation_probability": 101}},
    {"forecast": {"category": "unknown", "high_c": 19.5}},
    {"event": {"name": "Coffee Day", "visual_hint": "x" * 301}},
    {"event": {"name": "bad\nname", "visual_hint": "A cup."}},
    {"unexpected": "field"},
])
def test_server_rejects_malformed_or_unbounded_forecast_and_event_context(context):
    with pytest.raises(ValueError):
        server.clean_context(context, DAY)


def test_curated_events_are_sent_only_on_matching_dates(tmp_path):
    ordinary = client.context_for_date(tmp_path, {}, DAY)
    coffee_day = client.context_for_date(tmp_path, {}, date(2026, 10, 1))
    assert ordinary["event"] is None
    assert coffee_day["event"]["name"] == "Coffee Day"
    assert "coffee beans" in coffee_day["event"]["visual_hint"]


@pytest.mark.parametrize("event_day,event_name", [
    (date(2026, 1, 7), "Nanakusa no Sekku (Seven Herbs Festival)"),
    (date(2026, 1, 11), "Kagami Biraki (Mirror Opening)"),
    (date(2026, 1, 15), "Little New Year"),
    (date(2026, 3, 3), "Hinamatsuri (Doll Festival)"),
    (date(2026, 5, 5), "Tango no Sekku (Boys' Festival)"),
    (date(2026, 7, 7), "Tanabata (Star Festival)"),
    (date(2026, 9, 9), "Choyo no Sekku (Chrysanthemum Festival)"),
    (date(2026, 10, 1), "Coffee Day"),
    (date(2026, 12, 31), "New Year's Eve"),
])
def test_verified_catalog_events_have_matching_dates(tmp_path, event_day, event_name):
    context = client.context_for_date(tmp_path, {}, event_day)
    assert context["event"]["name"] == event_name


def test_configured_observance_overrides_recurring_and_exact_date(tmp_path):
    settings = {"daily_art": {"observances": {
        "10-01": {"name": "House Coffee Day", "visual_hint": "A favorite family mug."},
        "10-02": {"name": "Annual Local Day", "visual_hint": "A blue ribbon."},
        "2026-10-02": {"name": "One-off Local Day", "visual_hint": "A paper lantern."},
    }}}
    first = client.context_for_date(tmp_path, settings, date(2026, 10, 1))
    second = client.context_for_date(tmp_path, settings, date(2026, 10, 2))
    assert first["event"]["name"] == "House Coffee Day"
    assert second["event"]["name"] == "One-off Local Day"


@pytest.mark.parametrize("key", ["2026-2-01", "02-30", "../secret", "2026-02-29"])
def test_configured_observances_reject_invalid_date_keys(tmp_path, key):
    settings = {"daily_art": {"observances": {key: {"name": "Event", "visual_hint": "Hint"}}}}
    with pytest.raises(ValueError):
        client.context_for_date(tmp_path, settings, DAY)


@pytest.mark.parametrize("event", ["", {"name": "Event", "unexpected": "field"},
                                    {"name": "x" * 121}, {"name": "Event", "visual_hint": "x" * 301}])
def test_configured_observances_reject_invalid_values(tmp_path, event):
    settings = {"daily_art": {"observances": {"10-01": event}}}
    with pytest.raises(ValueError):
        client.context_for_date(tmp_path, settings, date(2026, 10, 1))


@pytest.mark.parametrize("observances", [
    [], None,
    {**{f"01-{day:02d}": {"name": "Event", "visual_hint": "Hint"}
       for day in range(1, 32)},
     **{f"02-{day:02d}": {"name": "Event", "visual_hint": "Hint"}
        for day in range(1, 35)}},
])
def test_configured_observance_mapping_is_bounded_and_typed(tmp_path, observances):
    settings = {"daily_art": {"observances": observances}}
    with pytest.raises(ValueError):
        client.context_for_date(tmp_path, settings, DAY)


def test_weather_context_contains_fresh_target_date_forecast(tmp_path):
    write_weather_cache(tmp_path)
    now = datetime(2026, 9, 18, 6, 30, tzinfo=timezone.utc)
    context = client.context_for_date(tmp_path, {}, DAY, now)
    assert context["forecast"] == forecast()


@pytest.mark.parametrize("case", ["stale", "location", "missing_target", "corrupt"])
def test_invalid_weather_cache_becomes_unknown_without_numbers(tmp_path, case):
    now = datetime(2026, 9, 18, 9 if case == "stale" else 6,
                   0 if case == "stale" else 30, tzinfo=timezone.utc)
    if case == "stale":
        write_weather_cache(tmp_path, updated="2026-09-18T06:00:00+00:00")
    elif case == "location":
        write_weather_cache(tmp_path)
    elif case == "missing_target":
        write_weather_cache(tmp_path, days=["2026-09-19"])
    else:
        tmp_path.joinpath("cache").mkdir(parents=True, exist_ok=True)
        tmp_path.joinpath("cache/field_notes_weather.json").write_text("{")
    settings = {"weather": {"location": {"lat": 40.0, "lon": 140.0}}} if case == "location" else {}
    result = client.context_for_date(tmp_path, settings, DAY, now)["forecast"]
    assert result == {"category": "unknown", "forecast_date": None, "retrieved_at": None,
                      "high_c": None, "low_c": None, "precipitation_probability": None}


def test_prompt_prioritizes_theme_and_uses_forecast_snapshot_and_event_details():
    context = server.clean_context({"forecast": forecast(), "theme": "Autumn tea by a window",
                                   "holiday": "Autumn Holiday",
                                   "event": {"name": "Coffee Day", "visual_hint": "A steaming cup."}}, DAY)
    prompt = server.build_prompt(DAY, context)
    assert prompt.index("Primary theme") < prompt.index("Confirmed date event")
    assert prompt.index("Confirmed date event") < prompt.index("Japanese public holiday")
    assert prompt.index("Japanese public holiday") < prompt.index("Season in Japan")
    assert prompt.index("Season in Japan") < prompt.index("Generation-time forecast")
    assert "Coffee Day" in prompt and "A steaming cup." in prompt
    assert "Forecast for 2026-09-18, retrieved at 2026-09-18T06:00:00+00:00" in prompt
    assert "high 19.5 degrees C" in prompt and "precipitation probability 80%" in prompt
    assert "If rain is forecast, shelter the fox" in prompt.replace("\n", " ")


def test_prompt_does_not_invent_weather_or_named_events_when_unknown():
    prompt = server.build_prompt(DAY, server.clean_context({}))
    assert "No fresh forecast for the requested date is available" in prompt
    assert "Do not infer or describe weather conditions" in prompt
    assert "No verified daily observance was supplied" in prompt


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
    assert context == {"forecast": {"category": "unknown", "forecast_date": None, "retrieved_at": None,
                                     "high_c": None, "low_c": None, "precipitation_probability": None},
                       "theme": "Autumn picnic", "event": None, "holiday": ""}


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
