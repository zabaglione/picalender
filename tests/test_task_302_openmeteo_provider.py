#!/usr/bin/env python3
"""
TASK-302: Open-Meteoプロバイダ実装 - テストコード（Red Phase）

OpenMeteoProviderクラスのテストスイート。
Priority 1の15個のテストケースを実装。
"""

import json
import time
import unittest
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any

# まだ実装されていないがテスト対象のクラス
try:
    from src.weather.providers.openmeteo import OpenMeteoProvider
except ImportError:
    # Red Phaseではクラスが存在しないのでダミー定義
    class OpenMeteoProvider:
        BASE_URL = "https://api.open-meteo.com/v1/forecast"
        
        def __init__(self, settings):
            pass
        
        def fetch(self):
            return {}
        
        def _build_request_params(self):
            return {}
        
        def _parse_openmeteo_response(self, data):
            return {}
        
        def _map_wmo_code_to_icon(self, code):
            return "cloudy"

from src.weather.providers.base import WeatherProvider
from src.weather.providers.exceptions import (
    WeatherProviderError, NetworkError, APIError, DataFormatError
)


class TestOpenMeteoProvider(unittest.TestCase):
    """Open-Meteoプロバイダのテストケース"""
    
    def setUp(self):
        """各テストの前処理"""
        self.test_settings = {
            'weather': {
                'location': {
                    'latitude': 35.681236,
                    'longitude': 139.767125
                },
                'timeout': 10
            }
        }
        
        # モックOpen-Meteoレスポンス
        self.mock_openmeteo_response = {
            "latitude": 35.6812,
            "longitude": 139.7671,
            "timezone": "Asia/Tokyo",
            "timezone_abbreviation": "JST",
            "elevation": 35.0,
            "daily": {
                "time": ["2025-01-11", "2025-01-12", "2025-01-13"],
                "temperature_2m_max": [12.5, 8.3, 7.1],
                "temperature_2m_min": [5.2, 3.1, 4.0],
                "weathercode": [1, 3, 61],
                "precipitation_probability_max": [30, 60, 90]
            }
        }
    
    # =================================================================
    # Test Category 1: 基本機能テスト
    # =================================================================
    
    def test_openmeteo_provider_initialization(self):
        """Test Case 1.1: OpenMeteoProvider初期化"""
        # OpenMeteoProviderが正しく初期化されることを確認
        provider = OpenMeteoProvider(self.test_settings)
        
        # 基底クラスを継承していることを確認
        self.assertIsInstance(provider, WeatherProvider)
        
        # BASE_URLが定義されていることを確認
        self.assertEqual(provider.BASE_URL, "https://api.open-meteo.com/v1/forecast")
    
    def test_fetch_method_implementation(self):
        """Test Case 1.2: fetch()メソッド実装確認"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # fetch()メソッドが存在し呼び出し可能であることを確認
        self.assertTrue(hasattr(provider, 'fetch'))
        self.assertTrue(callable(getattr(provider, 'fetch')))
        
        # 戻り値が辞書型であることを確認（モック環境）
        with patch.object(provider, '_make_request') as mock_request:
            mock_request.return_value = self.mock_openmeteo_response
            result = provider.fetch()
            self.assertIsInstance(result, dict)
    
    # =================================================================
    # Test Category 2: APIリクエスト構築テスト
    # =================================================================
    
    def test_request_params_building(self):
        """Test Case 2.1: リクエストパラメータ構築"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # _build_request_params()メソッドの確認
        params = provider._build_request_params()
        
        # 必須パラメータの存在確認
        self.assertIn('latitude', params)
        self.assertIn('longitude', params)
        self.assertIn('daily', params)
        self.assertIn('timezone', params)
        self.assertIn('forecast_days', params)
        
        # dailyパラメータの内容確認
        expected_daily = [
            'temperature_2m_max',
            'temperature_2m_min', 
            'weathercode',
            'precipitation_probability_max'
        ]
        self.assertEqual(params['daily'], expected_daily)
        
        # その他パラメータの値確認
        self.assertEqual(params['timezone'], 'Asia/Tokyo')
        self.assertEqual(params['forecast_days'], 3)
    
    # =================================================================
    # Test Category 3: レスポンス変換テスト
    # =================================================================
    
    def test_normal_response_conversion(self):
        """Test Case 3.1: 正常レスポンス変換"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # Open-Meteo形式から標準形式への変換
        result = provider._parse_openmeteo_response(self.mock_openmeteo_response)
        
        # 標準形式の構造確認
        self.assertIn('updated', result)
        self.assertIn('location', result)
        self.assertIn('forecasts', result)
        
        # updatedフィールドが現在時刻付近であることを確認
        self.assertIsInstance(result['updated'], (int, float))
        current_time = time.time()
        self.assertLess(abs(result['updated'] - current_time), 10)
        
        # locationフィールドの確認
        self.assertIn('latitude', result['location'])
        self.assertIn('longitude', result['location'])
        self.assertEqual(result['location']['latitude'], 35.681236)
        self.assertEqual(result['location']['longitude'], 139.767125)
        
        # forecastsが3日分あることを確認
        self.assertEqual(len(result['forecasts']), 3)
    
    def test_daily_data_conversion(self):
        """Test Case 3.2: 日次データ変換"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # 変換実行
        result = provider._parse_openmeteo_response(self.mock_openmeteo_response)
        forecasts = result['forecasts']
        
        # 各日の予報データを確認
        for i, forecast in enumerate(forecasts):
            # 必須フィールドの存在確認
            self.assertIn('date', forecast)
            self.assertIn('icon', forecast)
            self.assertIn('temperature', forecast)
            self.assertIn('precipitation_probability', forecast)
            
            # 日付形式の確認（YYYY-MM-DD）
            expected_date = self.mock_openmeteo_response['daily']['time'][i]
            self.assertEqual(forecast['date'], expected_date)
            
            # 温度データの確認
            self.assertIn('min', forecast['temperature'])
            self.assertIn('max', forecast['temperature'])
            self.assertIsInstance(forecast['temperature']['min'], (int, float))
            self.assertIsInstance(forecast['temperature']['max'], (int, float))
            
            # 降水確率の確認
            self.assertIsInstance(forecast['precipitation_probability'], (int, float))
            self.assertGreaterEqual(forecast['precipitation_probability'], 0)
            self.assertLessEqual(forecast['precipitation_probability'], 100)
    
    # =================================================================
    # Test Category 4: WMOコードマッピングテスト
    # =================================================================
    
    def test_sunny_code_mapping(self):
        """Test Case 4.1: 晴れコードマッピング"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # WMOコード0, 1が"sunny"にマッピングされることを確認
        self.assertEqual(provider._map_wmo_code_to_icon(0), "sunny")
        self.assertEqual(provider._map_wmo_code_to_icon(1), "sunny")
    
    def test_cloudy_code_mapping(self):
        """Test Case 4.2: 曇りコードマッピング"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # WMOコード2, 3が"cloudy"にマッピングされることを確認
        self.assertEqual(provider._map_wmo_code_to_icon(2), "cloudy")
        self.assertEqual(provider._map_wmo_code_to_icon(3), "cloudy")
    
    def test_rain_code_mapping(self):
        """Test Case 4.3: 雨コードマッピング"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # 雨関連コードが"rain"にマッピングされることを確認
        rain_codes = [51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82]
        for code in rain_codes:
            self.assertEqual(provider._map_wmo_code_to_icon(code), "rain",
                           f"Code {code} should map to 'rain'")
        
        # 雪コードも"rain"として扱う
        snow_codes = [71, 73, 75, 77, 85, 86]
        for code in snow_codes:
            self.assertEqual(provider._map_wmo_code_to_icon(code), "rain",
                           f"Snow code {code} should map to 'rain'")
    
    def test_thunder_code_mapping(self):
        """Test Case 4.4: 雷コードマッピング"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # WMOコード95, 96, 99が"thunder"にマッピングされることを確認
        self.assertEqual(provider._map_wmo_code_to_icon(95), "thunder")
        self.assertEqual(provider._map_wmo_code_to_icon(96), "thunder")
        self.assertEqual(provider._map_wmo_code_to_icon(99), "thunder")
    
    def test_fog_code_mapping(self):
        """Test Case 4.5: 霧コードマッピング"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # WMOコード45, 48が"fog"にマッピングされることを確認
        self.assertEqual(provider._map_wmo_code_to_icon(45), "fog")
        self.assertEqual(provider._map_wmo_code_to_icon(48), "fog")
    
    # =================================================================
    # Test Category 5: データ取得フローテスト
    # =================================================================
    
    @patch('src.weather.providers.base.requests.Session.get')
    def test_complete_fetch_flow(self, mock_get):
        """Test Case 5.1: 完全fetch()フロー"""
        # モックレスポンス設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_openmeteo_response
        mock_get.return_value = mock_response
        
        # fetch()実行
        provider = OpenMeteoProvider(self.test_settings)
        result = provider.fetch()
        
        # APIリクエストが正しく行われたか確認
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # URLの確認
        self.assertEqual(call_args[0][0], provider.BASE_URL)
        
        # パラメータの確認
        params = call_args[1]['params']
        self.assertEqual(params['latitude'], 35.681236)
        self.assertEqual(params['longitude'], 139.767125)
        
        # 標準形式のデータが返されることを確認
        self.assertIn('updated', result)
        self.assertIn('forecasts', result)
        self.assertEqual(len(result['forecasts']), 3)
        
        # 各予報データの確認
        for forecast in result['forecasts']:
            self.assertIn('date', forecast)
            self.assertIn('icon', forecast)
            self.assertIn('temperature', forecast)
            self.assertIn('precipitation_probability', forecast)
    
    # =================================================================
    # Test Category 6: エラーハンドリングテスト
    # =================================================================
    
    @patch('src.weather.providers.base.requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """Test Case 6.1: ネットワークエラー処理"""
        # requests.ConnectionErrorを使用
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        provider = OpenMeteoProvider(self.test_settings)
        
        # NetworkError例外が発生することを確認
        with self.assertRaises(NetworkError) as context:
            provider.fetch()
        
        self.assertIn("Connection error", str(context.exception))
    
    def test_invalid_response_handling(self):
        """Test Case 6.3: 不正レスポンス処理"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # 必須フィールド欠如データ
        invalid_response = {
            "latitude": 35.6812,
            "longitude": 139.7671,
            # daily フィールドなし
        }
        
        # DataFormatError例外が発生することを確認
        with self.assertRaises(DataFormatError) as context:
            provider._parse_openmeteo_response(invalid_response)
        
        self.assertIn("Missing required field", str(context.exception))
    
    # =================================================================
    # Test Category 7: 統合テスト
    # =================================================================
    
    def test_base_class_integration(self):
        """Test Case 7.1: 基底クラス機能統合"""
        provider = OpenMeteoProvider(self.test_settings)
        
        # 設定管理機能の確認
        self.assertEqual(provider.location['latitude'], 35.681236)
        self.assertEqual(provider.location['longitude'], 139.767125)
        
        # HTTPクライアント初期化確認
        self.assertIsNotNone(provider.session)
        self.assertEqual(provider.timeout, 10)
        
        # cleanup()メソッドの動作確認
        provider.cleanup()
        # cleanup後もエラーが発生しないことを確認
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()