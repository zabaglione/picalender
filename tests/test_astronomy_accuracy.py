"""Independent published ephemerides, civil-day boundaries, and lunar geometry."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from src.utils.moon_phase import (JST, calculate_moon_age, get_moon_info,
                                  get_next_moon_phases)
from src.utils.lunisolar import lunar_date, LunarDate
from src.utils.rokuyou import calculate_rokuyou
from src.utils.sky_events import clock_time, rise_set_times
from src.renderers.moon_disk import is_illuminated

REFERENCE = json.loads((Path(__file__).parent / "fixtures/naoj_moon_phases_2026.json").read_text())
EVENTS = get_next_moon_phases(date(2026, 1, 1), 365)


def test_complete_year_of_quarter_events():
    assert len(EVENTS) == len(REFERENCE["events"]) == 50


@pytest.mark.parametrize("index", range(50))
def test_against_naoj_published_event(index):
    expected, actual = REFERENCE["events"][index], EVENTS[index]
    assert actual["phase"] == expected["phase"]
    # NAOJ rounds to one minute; the engine has finite ephemeris accuracy.
    assert abs((actual["time"] - datetime.fromisoformat(expected["jst"])).total_seconds()) < 120


def test_timezone_aware_equivalence_and_naive_jst_contract():
    jst = datetime(2026, 9, 18, 20, 0, tzinfo=JST)
    assert calculate_moon_age(jst) == calculate_moon_age(jst.astimezone(timezone.utc))
    assert calculate_moon_age(jst) == calculate_moon_age(jst.replace(tzinfo=None))
    assert calculate_moon_age(date(2026, 9, 18)) == calculate_moon_age(jst.replace(hour=12))


def test_new_moon_resets_at_conjunction_not_midnight():
    event = next(event for event in EVENTS if event["phase"] == "new" and event["date"].month == 9)
    moment = event["time"]
    assert calculate_moon_age(moment - timedelta(seconds=2)) > 29
    assert 0 <= calculate_moon_age(moment + timedelta(seconds=2)) < 0.0001
    assert calculate_moon_age(moment + timedelta(days=2)) == pytest.approx(2, abs=1e-6)


def test_month_age_is_not_capped_at_mean_lunation():
    new_moons = [event for event in EVENTS if event["phase"] == "new"]
    long_month = next(b for a, b in zip(new_moons, new_moons[1:])
                      if (b["time"] - a["time"]).total_seconds() / 86400 > 29.6)
    assert calculate_moon_age(long_month["time"] - timedelta(minutes=1)) > 29.53


def test_current_date_and_real_time_progression():
    now = datetime(2026, 9, 18, 20, 0, tzinfo=JST)
    info = get_moon_info(now)
    assert info["age"] == 7.3
    assert 0.45 < info["illumination_fraction"] < 0.49
    assert calculate_moon_age(now + timedelta(hours=6)) - info["age_days"] == pytest.approx(0.25)


@pytest.mark.parametrize("day, phase, english, japanese", [
    (25, "waxing_gibbous", "Waxing gibbous", "満ちていく月"),
    (26, "waxing_gibbous", "Waxing gibbous", "満ちていく月"),
    (27, "full", "Full moon", "満月"),
    (28, "waning_gibbous", "Waning gibbous", "欠けていく月"),
])
def test_full_moon_label_follows_jst_event_date(day, phase, english, japanese):
    info = get_moon_info(datetime(2026, 9, day, 12, tzinfo=JST))
    assert (info["phase"], info["phase_name"], info["phase_name_ja"]) == (
        phase, english, japanese)


def test_full_moon_date_label_on_both_sides_of_event():
    event = next(event for event in EVENTS if event["phase"] == "full"
                 and event["date"] == date(2026, 9, 27))["time"]
    assert get_moon_info(event - timedelta(hours=1))["phase"] == "full"
    assert get_moon_info(event + timedelta(hours=1))["phase"] == "full"
    assert get_moon_info(event - timedelta(hours=3))["phase"] == "waxing_gibbous"


def test_tokyo_rise_set_times_against_naoj_daily_calendar():
    # https://eco.mtk.nao.ac.jp/cgi-bin/koyomi/sunmoon.cgi/25
    # Published for Tokyo on 2026-09-25; the configured point is Tokyo Station.
    sky = rise_set_times(date(2026, 9, 25), 35.681236, 139.767125)
    for value, published in zip((sky.sunrise, sky.sunset, sky.moonrise, sky.moonset),
                                ("05:31", "17:34", "16:43", "03:40")):
        assert value is not None and value.date() == date(2026, 9, 25)
        hour, minute = map(int, published.split(":"))
        expected = value.replace(hour=hour, minute=minute, second=0, microsecond=0)
        assert abs((value - expected).total_seconds()) < 180
    assert clock_time(sky.sunrise) == "05:31"


def test_polar_day_does_not_invent_rise_or_set_times():
    sky = rise_set_times(date(2026, 6, 21), 69.6492, 18.9553, "Europe/Oslo")
    assert sky.sunrise is None and sky.sunset is None
    assert clock_time(sky.sunrise) == "--:--"


@pytest.mark.parametrize("fraction", [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1])
@pytest.mark.parametrize("waxing", [True, False])
def test_moon_disc_lit_area_matches_illumination(fraction, waxing):
    points = [(x / 80, y / 80) for x in range(-80, 81) for y in range(-80, 81)
              if x * x + y * y < 80 * 80]
    bright = sum(is_illuminated(x, y, fraction, waxing) for x, y in points)
    assert bright / len(points) == pytest.approx(fraction, abs=0.012)


def test_quarter_moons_light_opposite_sides():
    assert is_illuminated(0.5, 0, 0.5, True)
    assert not is_illuminated(-0.5, 0, 0.5, True)
    assert is_illuminated(-0.5, 0, 0.5, False)
    assert not is_illuminated(0.5, 0, 0.5, False)


# NAOJ's 2014/1984 calendar tables and 2033 proposal 1:
# https://eco.mtk.nao.ac.jp/koyomi/topics/html/topics2014.html
@pytest.mark.parametrize("day, expected", [
    (date(2014, 1, 31), LunarDate(2014, 1, 1)),
    (date(2014, 9, 24), LunarDate(2014, 9, 1)),
    (date(2014, 10, 24), LunarDate(2014, 9, 1, True)),
    (date(2014, 11, 22), LunarDate(2014, 10, 1)),
    (date(2014, 12, 22), LunarDate(2014, 11, 1)),
    (date(1984, 11, 23), LunarDate(1984, 10, 1, True)),
    (date(1984, 12, 22), LunarDate(1984, 11, 1)),
    (date(1985, 1, 21), LunarDate(1984, 12, 1)),
    (date(1985, 2, 20), LunarDate(1985, 1, 1)),
    (date(2033, 8, 25), LunarDate(2033, 8, 1)),
    (date(2033, 9, 23), LunarDate(2033, 9, 1)),
    (date(2033, 11, 22), LunarDate(2033, 11, 1)),
    (date(2033, 12, 22), LunarDate(2033, 11, 1, True)),
    (date(2034, 1, 20), LunarDate(2033, 12, 1)),
    (date(2034, 2, 19), LunarDate(2034, 1, 1)),
    (date(2034, 3, 20), LunarDate(2034, 2, 1)),
    (date(2025, 7, 25), LunarDate(2025, 6, 1, True)),
    (date(2026, 9, 18), LunarDate(2026, 8, 8)),
])
def test_lunisolar_dates_against_reference(day, expected):
    assert lunar_date(day) == expected


def test_lunar_day_changes_at_jst_midnight_even_before_new_moon():
    # 2026-09-11's conjunction is 12:27 JST, but the lunar date is day 1 all day.
    assert lunar_date(date(2026, 9, 11)) == LunarDate(2026, 8, 1)
    assert 28 < calculate_moon_age(datetime(2026, 9, 11, 0, 1, tzinfo=JST)) < 30


def test_rokuyou_resets_at_lunar_month_boundary():
    # Month 8 day 1 is Tomobiki, not the next item in an endless six-day cycle.
    assert calculate_rokuyou(date(2026, 9, 11)) == 1
    assert calculate_rokuyou(date(2026, 9, 18)) == 2
    assert calculate_rokuyou(date(2026, 10, 11)) == 2
    assert calculate_rokuyou(date(2025, 7, 25)) == 5
