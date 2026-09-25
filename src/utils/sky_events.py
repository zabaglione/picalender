"""Offline rise and set times for the configured location and civil date."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

import astronomy

from .moon_phase import astronomy_time, utc_datetime


@dataclass(frozen=True)
class SkyTimes:
    sunrise: datetime | None
    sunset: datetime | None
    moonrise: datetime | None
    moonset: datetime | None


@lru_cache(maxsize=64)
def rise_set_times(day: date, latitude: float, longitude: float,
                   timezone_name: str = "Asia/Tokyo") -> SkyTimes:
    """Return events within the requested local date, or None when no event occurs."""
    zone = ZoneInfo(timezone_name)
    start = datetime.combine(day, time(), zone).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time(), zone).astimezone(timezone.utc)
    limit_days = (end - start).total_seconds() / 86400
    observer = astronomy.Observer(latitude, longitude)
    start_time = astronomy_time(start)

    def event(body, direction):
        result = astronomy.SearchRiseSet(body, observer, direction, start_time, limit_days)
        if result is None:
            return None
        local = utc_datetime(result).astimezone(zone)
        return local if local.date() == day else None

    return SkyTimes(
        event(astronomy.Body.Sun, astronomy.Direction.Rise),
        event(astronomy.Body.Sun, astronomy.Direction.Set),
        event(astronomy.Body.Moon, astronomy.Direction.Rise),
        event(astronomy.Body.Moon, astronomy.Direction.Set),
    )


def clock_time(value: datetime | None) -> str:
    """Display an event to the nearest minute without inventing missing events."""
    return (value + timedelta(seconds=30)).strftime("%H:%M") if value else "--:--"
