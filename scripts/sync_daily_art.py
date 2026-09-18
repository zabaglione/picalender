#!/usr/bin/env python3
"""Ask a private SSH server for today's artwork; retain only the latest PNG."""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import logging
from pathlib import Path
import re
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

import holidays
from PIL import Image, ImageOps
import yaml

LOGGER = logging.getLogger("daily_art")
ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 20 * 1024 * 1024


def target_date(now, refresh_hour):
    if not 0 <= refresh_hour <= 23:
        raise ValueError("Refresh hour must be between 0 and 23")
    return (now - timedelta(hours=refresh_hour)).date()


def ssh_command(config, action, day):
    host = config["ssh_host"]
    if not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@:-]*", host):
        raise ValueError("Invalid SSH host")
    script = config.get("remote_script", "picalender-artwork/serve_daily_art.py")
    if not isinstance(script, str) or not script or script.startswith("~"):
        raise ValueError("Remote script must be an absolute or home-relative path")
    command = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "UpdateHostKeys=no", "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=30",
               "-o", "ServerAliveCountMax=3"]
    if config.get("identity_file"):
        command += ["-i", str(Path(config["identity_file"]).expanduser()), "-o", "IdentitiesOnly=yes"]
    command += [host, shlex.join(["python3", script, action, "--date", day.isoformat()])]
    return command


def weather_category(code):
    if code in (0, 1):
        return "clear"
    if code in (2, 3):
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "thunder"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    return "unknown"


def context_for_date(root, settings, day):
    config = settings.get("daily_art", {})
    context = {"weather": "unknown", "theme": config.get("themes", {}).get(day.isoformat(), "")}
    calendar_config = settings.get("calendar", {})
    context["holiday"] = str(holidays.country_holidays(calendar_config.get("holidays_country", "JP"),
                                                       years=day.year, language="en_US").get(day, ""))
    try:
        cached = json.loads((root / "cache/field_notes_weather.json").read_text())
        weather_config = settings.get("weather", {})
        location = weather_config.get("location", {})
        expected = {"latitude": location.get("lat", 35.681236),
                    "longitude": location.get("lon", 139.767125),
                    "timezone": weather_config.get("timezone", "Asia/Tokyo")}
        updated = datetime.fromisoformat(cached["updated"])
        if cached["location"] == expected and updated.tzinfo is not None and \
                0 <= (datetime.now(timezone.utc) - updated).total_seconds() < 7200:
            daily = cached["response"]["daily"]
            index = daily["time"].index(day.isoformat())
            context["weather"] = weather_category(daily["weather_code"][index])
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        pass
    return context


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def already_current(directory, day):
    try:
        state = json.loads((directory / "current.json").read_text())
        image = directory / "current.png"
        return state["date"] == day.isoformat() and image.stat().st_size <= MAX_BYTES and \
            digest(image) == state["sha256"]
    except (OSError, ValueError, KeyError, TypeError):
        return False


def install_download(directory, downloaded, manifest, day):
    """Validate before replacing the displayed image; keep the old one on errors."""
    if manifest.get("date") != day.isoformat():
        raise ValueError("Server returned a different date")
    if not 45 <= downloaded.stat().st_size <= MAX_BYTES or downloaded.stat().st_size != manifest["bytes"]:
        raise ValueError("Downloaded image size mismatch")
    if digest(downloaded) != manifest["sha256"]:
        raise ValueError("Downloaded image checksum mismatch")
    temporary = directory / "current.png.tmp"
    metadata_tmp = directory / "current.json.tmp"
    try:
        with Image.open(downloaded) as artwork:
            width, height = artwork.size
            if artwork.format != "PNG" or (width, height) != (manifest["width"], manifest["height"]):
                raise ValueError("Unexpected image format or dimensions")
            if not (64 <= width <= 4096 and 64 <= height <= 4096 and width * height <= 12000000):
                raise ValueError("Image dimensions outside supported bounds")
            artwork.load()
            # Store a small display copy on the Pi; the server retains the original.
            ImageOps.fit(artwork.convert("RGB"), (800, 450), method=Image.Resampling.LANCZOS).save(temporary, format="PNG")
        state = {"date": day.isoformat(), "sha256": digest(temporary), "source_sha256": manifest["sha256"],
                 "updated": datetime.now(timezone.utc).isoformat()}
        metadata_tmp.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(directory / "current.png")
        metadata_tmp.replace(directory / "current.json")
    finally:
        temporary.unlink(missing_ok=True)
        metadata_tmp.unlink(missing_ok=True)


def sync(root, settings, now=None):
    config = settings.get("daily_art", {})
    if not config.get("enabled", False):
        LOGGER.info("Daily artwork is disabled")
        return False
    zone = ZoneInfo(settings.get("weather", {}).get("timezone", "Asia/Tokyo"))
    now = now.astimezone(zone) if now is not None else datetime.now(zone)
    day = target_date(now, int(config.get("refresh_hour", 5)))
    directory = root / "cache/daily_art"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".sync.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            LOGGER.info("An artwork sync is already running")
            return False
        if already_current(directory, day):
            LOGGER.info("Artwork is current: %s", day)
            return False
        result = subprocess.run(ssh_command(config, "ensure", day), input=json.dumps(context_for_date(root, settings, day)),
                                text=True, capture_output=True, check=True, timeout=1000)
        manifest = json.loads(result.stdout)
        if manifest.get("date") != day.isoformat() or not 45 <= manifest["bytes"] <= MAX_BYTES:
            raise ValueError("Invalid server image manifest")
        downloaded = directory / ".download.png"
        try:
            with downloaded.open("wb") as output:
                subprocess.run(ssh_command(config, "fetch", day), stdout=output, stderr=subprocess.PIPE,
                               check=True, timeout=90)
            install_download(directory, downloaded, manifest, day)
        finally:
            downloaded.unlink(missing_ok=True)
        LOGGER.info("Artwork updated: %s (server cache hit: %s)", day, manifest["cached"])
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, default=ROOT / "settings.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        settings = yaml.safe_load(args.settings.read_text()) or {}
        sync(ROOT, settings)
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        LOGGER.error("Artwork SSH command failed: %s", (error or "no diagnostic").strip()[-1000:])
        return 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        LOGGER.error("Artwork update failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
