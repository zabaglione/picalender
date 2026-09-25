"""Offline lunar ephemeris. Dates mean noon JST; aware datetimes mean an instant.

Moon age is elapsed UT days since the actual conjunction, not a fixed-period
remainder. Phase and illumination are independent astronomical quantities.
"""
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo
import astronomy

JST = ZoneInfo("Asia/Tokyo")
UTC = timezone.utc
MOON_PHASES = {
    "new": "New moon", "waxing_crescent": "Waxing crescent",
    "first_quarter": "First quarter", "waxing_gibbous": "Waxing gibbous",
    "full": "Full moon", "waning_gibbous": "Waning gibbous",
    "last_quarter": "Last quarter", "waning_crescent": "Waning crescent",
}
MOON_PHASES_JA = {
    "new": "新月", "waxing_crescent": "満ちていく細い月",
    "first_quarter": "上弦の月", "waxing_gibbous": "満ちていく月",
    "full": "満月", "waning_gibbous": "欠けていく月",
    "last_quarter": "下弦の月", "waning_crescent": "欠けていく細い月",
}
MOON_ASCII = dict(zip(MOON_PHASES, (".", ")", "D", "O>", "O", "<O", "C", "(")))
QUARTER_PHASES = ("new", "first_quarter", "full", "last_quarter")


def as_utc(value: date | datetime) -> datetime:
    """Interpret a naive datetime as JST, never implicitly as machine time."""
    if isinstance(value, datetime):
        return (value.replace(tzinfo=JST) if value.tzinfo is None else value).astimezone(UTC)
    if isinstance(value, date):
        return datetime.combine(value, time(12), JST).astimezone(UTC)
    raise TypeError("Expected a date or datetime")


def astronomy_time(value: datetime) -> astronomy.Time:
    value = as_utc(value)
    return astronomy.Time.Make(value.year, value.month, value.day, value.hour,
                               value.minute, value.second + value.microsecond / 1e6)


def utc_datetime(value: astronomy.Time) -> datetime:
    # Astronomy Engine returns a naive datetime whose documented scale is UTC.
    return value.Utc().replace(tzinfo=UTC)


@lru_cache(maxsize=64)
def _lunation_at_midnight(day: date) -> tuple[astronomy.Time, astronomy.Time]:
    start = astronomy_time(datetime.combine(day, time(), UTC))
    previous = astronomy.SearchMoonPhase(0, start, -32)
    if previous is None:
        raise ValueError("Previous new moon not found")
    following = astronomy.SearchMoonPhase(0, previous.AddDays(1), 32)
    if following is None:
        raise ValueError("Next new moon not found")
    return previous, following


def _lunation(instant: datetime) -> tuple[astronomy.Time, astronomy.Time]:
    previous, following = _lunation_at_midnight(instant.date())
    if instant >= utc_datetime(following):
        previous = following
        following = astronomy.SearchMoonPhase(0, previous.AddDays(1), 32)
        if following is None:
            raise ValueError("Next new moon not found")
    return previous, following


def calculate_moon_age(target_date: date | datetime) -> float:
    instant = as_utc(target_date)
    previous, _ = _lunation(instant)
    return (instant - utc_datetime(previous)).total_seconds() / 86400


def _calendar_phase(instant: datetime, longitude: float) -> str:
    """Name primary phases on their JST event date; name other days by geometry."""
    start = astronomy_time(instant - timedelta(days=1))
    event = astronomy.SearchMoonQuarter(start)
    if utc_datetime(event.time).astimezone(JST).date() == instant.astimezone(JST).date():
        return QUARTER_PHASES[event.quarter]
    return ("waxing_crescent", "waxing_gibbous", "waning_gibbous",
            "waning_crescent")[int(longitude // 90) % 4]


def get_moon_info(target_date: date | datetime) -> dict:
    instant = as_utc(target_date)
    t = astronomy_time(instant)
    previous, following = _lunation(instant)
    age = (instant - utc_datetime(previous)).total_seconds() / 86400
    longitude = astronomy.MoonPhase(t)
    fraction = astronomy.Illumination(astronomy.Body.Moon, t).phase_fraction
    # Primary names refer to the local calendar date of the actual event.
    phase = _calendar_phase(instant, longitude)
    return {
        "age": round(age, 1), "age_days": age,
        "phase": phase, "phase_name": MOON_PHASES[phase],
        "phase_name_ja": MOON_PHASES_JA[phase],
        "ascii": MOON_ASCII[phase],
        "emoji": MOON_ASCII[phase],  # Compatibility alias; no emoji font needed.
        "illumination": round(fraction * 100, 1),
        "illumination_fraction": fraction,
        "phase_angle": longitude, "waxing": longitude < 180,
        "previous_new_moon": utc_datetime(previous),
        "next_new_moon": utc_datetime(following),
    }


def get_moon_phase(target_date: date | datetime) -> str:
    return get_moon_info(target_date)["phase"]


def get_moon_display(target_date: date | datetime, format_type: str = "text") -> str:
    info = get_moon_info(target_date)
    if format_type in ("ascii", "emoji"):
        return info["ascii"]
    if format_type == "full":
        return f"{info['phase_name']} / age {info['age']:.1f} days"
    return info["phase_name"]


def get_next_moon_phases(start_date: date | datetime, days: int = 30) -> list[dict]:
    """Actual new/quarter/full events, including time, within [start, end)."""
    if days < 0:
        raise ValueError("days must be nonnegative")
    instant = (datetime.combine(start_date, time(), JST).astimezone(UTC)
               if not isinstance(start_date, datetime) else as_utc(start_date))
    end = instant + timedelta(days=days)
    quarter = astronomy.SearchMoonQuarter(astronomy_time(instant))
    result = []
    phases = ("new", "first_quarter", "full", "last_quarter")
    while utc_datetime(quarter.time) < end:
        event_time = utc_datetime(quarter.time)
        phase = phases[quarter.quarter]
        result.append({"date": event_time.astimezone(JST).date(),
                       "time": event_time, "phase": phase, "name": MOON_PHASES[phase]})
        quarter = astronomy.NextMoonQuarter(quarter)
    return result
