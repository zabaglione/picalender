"""Japanese lunisolar dates from JST new-moon days and principal solar terms.

Month 11 contains the winter solstice. In a 13-month solstice cycle, the first
following month without a principal term repeats the previous month number.
This explicitly chooses the leap-11 convention for the ambiguous year 2033.
Modern old-calendar dates are a convention, not an official Japanese calendar.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
import astronomy
from .moon_phase import JST, astronomy_time, utc_datetime


@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    leap: bool = False


def _local_day(t: astronomy.Time) -> date:
    return utc_datetime(t).astimezone(JST).date()


def _month_eleven(year: int) -> astronomy.Time:
    solstice_day = _local_day(astronomy.Seasons(year).dec_solstice)
    # A conjunction later on the same local date still starts that calendar day.
    end_of_day = datetime.combine(solstice_day + timedelta(days=1), time(), JST)
    moon = astronomy.SearchMoonPhase(0, astronomy_time(end_of_day - timedelta(seconds=1)), -32)
    if moon is None:
        raise ValueError("Winter month boundary not found")
    return moon


@lru_cache(maxsize=12)
def _year_months(year: int) -> tuple:
    first, end = _month_eleven(year), _month_eleven(year + 1)
    moons = [first]
    while _local_day(moons[-1]) < _local_day(end):
        following = astronomy.SearchMoonPhase(0, moons[-1].AddDays(1), 32)
        if following is None:
            raise ValueError("Lunar month boundary not found")
        moons.append(following)
    starts = [_local_day(moon) for moon in moons]
    count = len(starts) - 1
    if count not in (12, 13):
        raise ValueError("Invalid lunisolar year length")
    leap_index = None
    if count == 13:
        begin = astronomy_time(datetime.combine(starts[0], time(), JST))
        terms = set()
        for angle in range(0, 360, 30):
            term = astronomy.SearchSunLongitude(angle, begin, 400)
            while term is not None and _local_day(term) < starts[-1]:
                terms.add(_local_day(term))
                term = astronomy.SearchSunLongitude(angle, term.AddDays(1), 400)
        leap_index = next((i for i in range(1, count)
                           if not any(starts[i] <= term < starts[i + 1] for term in terms)), None)
        if leap_index is None:
            raise ValueError("Leap month not found")
    months = []
    lunar_year, month = year, 11
    for index in range(count):
        leap = index == leap_index
        if index and not leap:
            month = month % 12 + 1
            if month == 1:
                lunar_year += 1
        months.append((starts[index], starts[index + 1], lunar_year, month, leap))
    return tuple(months)


@lru_cache(maxsize=400)
def lunar_date(day: date) -> LunarDate:
    for year in (day.year - 1, day.year):
        for start, end, lunar_year, month, leap in _year_months(year):
            if start <= day < end:
                return LunarDate(lunar_year, month, (day - start).days + 1, leap)
    raise ValueError("Date outside the computed lunisolar calendar")
