"""Small, thread-safe Open-Meteo client with a location-bound offline cache."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import logging
import math
from pathlib import Path
import threading

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Forecast:
    date: date
    code: int | None
    high: float | None
    low: float | None
    rain: float | None


@dataclass(frozen=True)
class WeatherSnapshot:
    forecasts: tuple[Forecast, ...] = ()
    updated: datetime | None = None
    error: bool = False
    revision: int = 0


def _number(value):
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def parse_forecasts(data: dict) -> tuple[Forecast, ...]:
    daily = data["daily"]
    names = ("time", "weather_code", "temperature_2m_max", "temperature_2m_min",
             "precipitation_probability_max")
    length = len(daily["time"])
    if not length or any(len(daily[name]) != length for name in names):
        raise ValueError("Incomplete forecast arrays")
    result = []
    for i, day in enumerate(daily["time"]):
        code = _number(daily["weather_code"][i])
        rain = _number(daily["precipitation_probability_max"][i])
        result.append(Forecast(date.fromisoformat(day), int(code) if code is not None else None,
                               _number(daily["temperature_2m_max"][i]),
                               _number(daily["temperature_2m_min"][i]),
                               min(100, max(0, rain)) if rain is not None else None))
    return tuple(result)


class DashboardWeather:
    def __init__(self, settings: dict, root: Path, start_worker: bool = True):
        config = settings.get("weather", {})
        location = config.get("location", {})
        self.location = {"latitude": location.get("lat", 35.681236),
                         "longitude": location.get("lon", 139.767125),
                         "timezone": config.get("timezone", "Asia/Tokyo")}
        self.interval = max(60, int(config.get("refresh_sec", 1800)))
        self.cache_file = root / "cache" / "field_notes_weather.json"
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._snapshot = WeatherSnapshot()
        self._load_cache()
        self._thread = None
        if start_worker:
            self._thread = threading.Thread(target=self._worker, name="weather", daemon=True)
            self._thread.start()

    def snapshot(self) -> WeatherSnapshot:
        with self._lock:
            return self._snapshot

    def _load_cache(self):
        try:
            cached = json.loads(self.cache_file.read_text())
            if cached["location"] != self.location:
                return
            updated = datetime.fromisoformat(cached["updated"])
            if updated.tzinfo is None:
                return
            self._snapshot = WeatherSnapshot(parse_forecasts(cached["response"]), updated)
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def refresh(self):
        try:
            params = dict(self.location, daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                          forecast_days=3)
            response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            forecasts = parse_forecasts(data)
            updated = datetime.now(timezone.utc)
            with self._lock:
                self._snapshot = WeatherSnapshot(forecasts, updated, False, self._snapshot.revision + 1)
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.cache_file.with_suffix(".tmp")
                temporary.write_text(json.dumps({"location": self.location,
                                                "updated": updated.isoformat(), "response": data}))
                temporary.replace(self.cache_file)
            except OSError as exc:
                LOGGER.warning("Weather cache write failed: %s", exc)
            LOGGER.info("Weather refreshed: %d days", len(forecasts))
            return True
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            with self._lock:
                old = self._snapshot
                self._snapshot = WeatherSnapshot(old.forecasts, old.updated, True, old.revision + 1)
            LOGGER.warning("Weather refresh failed: %s", exc)
            return False

    def _worker(self):
        while not self._stop.is_set():
            # Monotonic Event waits avoid busy retries when the network is down.
            success = self.refresh()
            self._stop.wait(self.interval if success else 60)

    def cleanup(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.2)
