from datetime import datetime, timezone
import json
from unittest.mock import Mock, patch

import pytest
import requests

from src.weather.dashboard_weather import DashboardWeather, parse_forecasts


def response_data():
    return {"daily": {"time": ["2026-09-18"], "weather_code": [71],
                      "temperature_2m_max": [None], "temperature_2m_min": [-2.5],
                      "precipitation_probability_max": [None]}}


def test_missing_measurements_remain_unknown():
    forecast = parse_forecasts(response_data())[0]
    assert forecast.high is None and forecast.rain is None
    assert forecast.low == -2.5 and forecast.code == 71


def test_mismatched_arrays_are_rejected():
    data = response_data()
    data["daily"]["weather_code"] = []
    with pytest.raises(ValueError):
        parse_forecasts(data)


def test_network_failure_preserves_cached_dates_and_marks_error(tmp_path):
    client = DashboardWeather({}, tmp_path, start_worker=False)
    response = Mock()
    response.json.return_value = response_data()
    with patch("src.weather.dashboard_weather.requests.get", return_value=response):
        assert client.refresh()
    before = client.snapshot()
    with patch("src.weather.dashboard_weather.requests.get", side_effect=requests.Timeout("offline")):
        assert not client.refresh()
    after = client.snapshot()
    assert after.forecasts == before.forecasts
    assert after.updated == before.updated
    assert after.error and after.revision > before.revision
    restored = DashboardWeather({}, tmp_path, start_worker=False).snapshot()
    assert restored.forecasts == before.forecasts


def test_cache_from_another_location_is_not_reused(tmp_path):
    client = DashboardWeather({}, tmp_path, start_worker=False)
    client.cache_file.parent.mkdir()
    client.cache_file.write_text(json.dumps({
        "location": {"latitude": 1, "longitude": 2, "timezone": "Asia/Tokyo"},
        "updated": datetime.now(timezone.utc).isoformat(), "response": response_data()}))
    assert not DashboardWeather({}, tmp_path, start_worker=False).snapshot().forecasts
