"""
OpenWeatherMapプロバイダーのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import json
import time
from datetime import datetime, timedelta

# モジュールが存在しない場合のダミークラス
try:
    from src.providers.weather_openweathermap import OpenWeatherMapProvider
    from src.providers.weather_base import WeatherProvider
except ImportError:
    OpenWeatherMapProvider = None
    WeatherProvider = None


class TestOpenWeatherMapProvider(unittest.TestCase):
    """OpenWeatherMapプロバイダーのテスト"""
    
    def setUp(self):
        """テストの初期設定"""
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = self._mock_config_get
        
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'weather.provider': 'openweathermap',
            'weather.openweathermap.api_key': 'test_api_key_12345',
            'weather.openweathermap.units': 'metric',
            'weather.openweathermap.lang': 'ja',
            'weather.location.lat': 35.681236,
            'weather.location.lon': 139.767125,
            'weather.cache_dir': './cache_test',
            'weather.cache_duration': 1800,
            'weather.timeout': 10
        }
        return config_values.get(key, default)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_inheritance(self):
        """WeatherProviderを継承していることを確認"""
        provider = OpenWeatherMapProvider(self.mock_config)
        self.assertIsInstance(provider, WeatherProvider)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # APIキーが設定されている
        self.assertEqual(provider.api_key, 'test_api_key_12345')
        
        # 単位系が設定されている
        self.assertEqual(provider.units, 'metric')
        
        # 言語が設定されている
        self.assertEqual(provider.lang, 'ja')
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_api_url_construction(self):
        """API URLの構築テスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # API 2.5のURL（無料版）
        expected_base = "https://api.openweathermap.org/data/2.5"
        
        if hasattr(provider, 'get_api_url'):
            url = provider.get_api_url()
            self.assertIn(expected_base, url)
            self.assertIn('lat=35.681236', url)
            self.assertIn('lon=139.767125', url)
            self.assertIn('appid=test_api_key_12345', url)
            self.assertIn('units=metric', url)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    @patch('requests.get')
    def test_fetch_from_api_success(self, mock_get):
        """API取得成功のテスト"""
        # Current Weather APIのレスポンス
        current_response = MagicMock()
        current_response.status_code = 200
        current_response.json.return_value = {
            "main": {
                "temp": 10.5,
                "humidity": 65
            },
            "wind": {
                "speed": 3.5
            },
            "weather": [
                {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}
            ]
        }
        
        # Forecast APIのレスポンス
        forecast_response = MagicMock()
        forecast_response.status_code = 200
        forecast_response.json.return_value = {
            "list": [
                {
                    "dt": 1642233600,
                    "main": {"temp": 5.2},
                    "weather": [{"id": 800}],
                    "pop": 0.1
                },
                {
                    "dt": 1642244400,
                    "main": {"temp": 15.8},
                    "weather": [{"id": 800}],
                    "pop": 0.1
                },
                {
                    "dt": 1642320000,
                    "main": {"temp": 7.1},
                    "weather": [{"id": 802}],
                    "pop": 0.3
                },
                {
                    "dt": 1642330800,
                    "main": {"temp": 17.3},
                    "weather": [{"id": 802}],
                    "pop": 0.3
                },
                {
                    "dt": 1642406400,
                    "main": {"temp": 8.5},
                    "weather": [{"id": 500}],
                    "pop": 0.8
                },
                {
                    "dt": 1642417200,
                    "main": {"temp": 14.2},
                    "weather": [{"id": 500}],
                    "pop": 0.8
                }
            ]
        }
        
        # 2回のAPI呼び出しを設定
        mock_get.side_effect = [current_response, forecast_response]
        
        provider = OpenWeatherMapProvider(self.mock_config)
        result = provider._fetch_from_api()
        
        self.assertIsNotNone(result)
        self.assertIn('current', result)
        self.assertIn('daily', result)
        self.assertEqual(len(result['daily']), 3)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_parse_response(self):
        """レスポンス解析のテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # OpenWeatherMapレスポンス
        raw_response = {
            "current": {
                "dt": 1642234567,
                "temp": 10.5,
                "humidity": 65,
                "wind_speed": 3.5,
                "weather": [
                    {"id": 801, "main": "Clouds", "description": "few clouds"}
                ]
            },
            "daily": [
                {
                    "dt": 1642233600,
                    "temp": {"min": 5.2, "max": 15.8},
                    "weather": [{"id": 800, "main": "Clear"}],
                    "pop": 0.1
                },
                {
                    "dt": 1642320000,
                    "temp": {"min": 7.1, "max": 17.3},
                    "weather": [{"id": 802, "main": "Clouds"}],
                    "pop": 0.3
                },
                {
                    "dt": 1642406400,
                    "temp": {"min": 8.5, "max": 14.2},
                    "weather": [{"id": 500, "main": "Rain"}],
                    "pop": 0.8
                }
            ]
        }
        
        parsed = provider._parse_response(raw_response)
        
        # 標準フォーマットの確認
        self.assertIn('updated', parsed)
        self.assertIn('current', parsed)
        self.assertIn('forecasts', parsed)
        
        # 現在の天気
        self.assertEqual(parsed['current']['temperature'], 10.5)
        self.assertEqual(parsed['current']['humidity'], 65)
        self.assertEqual(parsed['current']['wind_speed'], 3.5)
        
        # 予報
        self.assertEqual(len(parsed['forecasts']), 3)
        self.assertEqual(parsed['forecasts'][0]['tmin'], 5.2)
        self.assertEqual(parsed['forecasts'][0]['tmax'], 15.8)
        self.assertEqual(parsed['forecasts'][0]['pop'], 10)  # 0.1 -> 10%
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_map_icon(self):
        """天気アイコンマッピングのテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # OpenWeatherMap天気コードのマッピング
        test_cases = [
            (200, 'thunder'),    # Thunderstorm
            (300, 'rain'),       # Drizzle
            (500, 'rain'),       # Rain
            (600, 'snow'),       # Snow
            (741, 'fog'),        # Fog
            (800, 'sunny'),      # Clear
            (801, 'partly_cloudy'), # Few clouds
            (803, 'cloudy'),     # Broken clouds
            (804, 'cloudy'),     # Overcast clouds
        ]
        
        for weather_id, expected_icon in test_cases:
            result = provider._map_icon(weather_id)
            self.assertEqual(result, expected_icon, 
                           f"Weather ID {weather_id} should map to {expected_icon}")
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """APIエラーハンドリングのテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # 401 Unauthorized (APIキーエラー)
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_get.return_value = mock_response
        
        result = provider._fetch_from_api()
        self.assertIsNone(result)
        
        # 429 Too Many Requests (レート制限)
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_get.return_value = mock_response
        
        result = provider._fetch_from_api()
        self.assertIsNone(result)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """ネットワークエラーハンドリングのテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        provider.clear_cache()
        
        # ネットワークエラー
        mock_get.side_effect = Exception("Connection error")
        
        result = provider._fetch_from_api()
        self.assertIsNone(result)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_date_formatting(self):
        """日付フォーマットのテスト"""
        provider = OpenWeatherMapProvider(self.mock_config)
        
        # Unixタイムスタンプから日付文字列への変換
        timestamp = 1642233600  # 2022-01-15 00:00:00 UTC
        
        if hasattr(provider, 'format_date'):
            formatted = provider.format_date(timestamp)
            # YYYY-MM-DD形式
            self.assertRegex(formatted, r'\d{4}-\d{2}-\d{2}')
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    def test_missing_api_key(self):
        """APIキーが設定されていない場合のテスト"""
        # APIキーなしの設定
        mock_config = MagicMock()
        mock_config.get.return_value = None
        
        with self.assertRaises(ValueError):
            OpenWeatherMapProvider(mock_config)
    
    @unittest.skipIf(OpenWeatherMapProvider is None, "OpenWeatherMapProvider not implemented yet")
    @patch('requests.get')
    def test_full_fetch_integration(self, mock_get):
        """完全な取得フローのテスト"""
        # Current Weather APIレスポンス
        current_response = MagicMock()
        current_response.status_code = 200
        current_response.json.return_value = {
            "main": {
                "temp": 22.5,
                "humidity": 60
            },
            "wind": {
                "speed": 5.0
            },
            "weather": [{"id": 801, "main": "Clouds"}]
        }
        
        # Forecast APIレスポンス
        forecast_response = MagicMock()
        forecast_response.status_code = 200
        dt = int(time.time())
        forecast_response.json.return_value = {
            "list": [
                {
                    "dt": dt + i * 3600,
                    "main": {"temp": 18 + i},
                    "weather": [{"id": 800}],
                    "pop": 0.0
                }
                for i in range(24)  # 3日分のデータ
            ]
        }
        
        # 2回のAPI呼び出しを設定
        mock_get.side_effect = [current_response, forecast_response]
        
        provider = OpenWeatherMapProvider(self.mock_config)
        result = provider.fetch()
        
        # 標準フォーマットの確認
        self.assertIsNotNone(result)
        self.assertTrue(provider.validate_response(result))
        self.assertEqual(result['current']['temperature'], 22.5)
        self.assertEqual(len(result['forecasts']), 3)


if __name__ == '__main__':
    unittest.main()