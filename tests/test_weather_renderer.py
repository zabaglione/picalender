"""
WeatherRendererのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pygame
import time
from datetime import datetime

# モジュールが存在しない場合のダミークラス
try:
    from src.ui.weather_renderer import WeatherRenderer
    from src.ui.renderable import Renderable
except ImportError:
    WeatherRenderer = None
    Renderable = None


class TestWeatherRenderer(unittest.TestCase):
    """WeatherRendererのテスト"""
    
    def setUp(self):
        """テストの初期設定"""
        pygame.init()
        
        # モックアセットマネージャー
        self.mock_asset_manager = MagicMock()
        self.mock_font = MagicMock()
        self.mock_font.get_height.return_value = 20
        self.mock_font.size.return_value = (100, 20)
        self.mock_font.render.return_value = pygame.Surface((100, 20))
        self.mock_asset_manager.get_font.return_value = self.mock_font
        
        # 天気アイコンのモック
        self.mock_icon = pygame.Surface((64, 64))
        self.mock_asset_manager.get_image.return_value = self.mock_icon
        
        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = self._mock_config_get
        
        # モックプロバイダー
        self.mock_provider = MagicMock()
        self.mock_provider.fetch.return_value = self._get_mock_weather_data()
        
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'weather.position.x': 24,
            'weather.position.y': 320,
            'weather.panel.width': 420,
            'weather.panel.height': 260,
            'weather.panel.bg_color': (0, 0, 0, 180),
            'weather.panel.corner_radius': 10,
            'weather.font.size': 22,
            'weather.font.size_large': 36,
            'weather.font.color': (255, 255, 255),
            'weather.update_interval': 1800,  # 30分
            'weather.show_location': True,
            'weather.animation.enabled': False
        }
        return config_values.get(key, default)
    
    def _get_mock_weather_data(self):
        """モック天気データ"""
        return {
            "updated": int(time.time()),
            "location": {"lat": 35.681236, "lon": 139.767125},
            "current": {
                "temperature": 22,
                "icon": "sunny",
                "humidity": 65,
                "wind_speed": 3.5
            },
            "forecasts": [
                {
                    "date": "2024-01-15",
                    "icon": "sunny",
                    "tmin": 8,
                    "tmax": 18,
                    "pop": 10
                },
                {
                    "date": "2024-01-16",
                    "icon": "cloudy",
                    "tmin": 10,
                    "tmax": 20,
                    "pop": 30
                },
                {
                    "date": "2024-01-17",
                    "icon": "rain",
                    "tmin": 12,
                    "tmax": 17,
                    "pop": 80
                }
            ]
        }
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_inheritance(self):
        """Renderableインターフェースを実装していることを確認"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        self.assertIsInstance(renderer, Renderable)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 初期状態の確認
        self.assertIsNotNone(renderer)
        self.assertTrue(renderer.visible)
        self.assertTrue(renderer.is_dirty())
        
        # 位置とサイズの確認
        bounds = renderer.get_bounds()
        self.assertEqual(bounds, (24, 320, 420, 260))
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_render_with_data(self):
        """天気データがある場合の描画テスト"""
        screen = pygame.Surface((1024, 600))
        
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 描画実行
        renderer.render(screen)
        
        # 描画されたことを確認
        self.assertFalse(renderer.is_dirty())
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_render_without_data(self):
        """天気データがない場合の描画テスト"""
        screen = pygame.Surface((1024, 600))
        
        # データなしのプロバイダー
        self.mock_provider.fetch.return_value = None
        
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 描画実行（エラーにならないこと）
        renderer.render(screen)
        
        # "取得中..." または "データなし" が表示されるはず
        self.assertFalse(renderer.is_dirty())
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_update_interval(self):
        """更新間隔のテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 初回更新
        renderer.update(0.1)
        self.mock_provider.fetch.assert_called()
        fetch_count = self.mock_provider.fetch.call_count
        
        # 短時間での更新（データ取得されない）
        renderer.update(10)  # 10秒
        self.assertEqual(self.mock_provider.fetch.call_count, fetch_count)
        
        # 更新間隔を超えた更新
        renderer.update(1800)  # 30分
        self.assertGreater(self.mock_provider.fetch.call_count, fetch_count)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_async_update(self):
        """非同期更新のテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 非同期更新を開始
        if hasattr(renderer, 'update_async'):
            future = renderer.update_async()
            self.assertIsNotNone(future)
            
            # 結果を待機
            result = future.result(timeout=5)
            self.assertIsNotNone(result)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_visibility_control(self):
        """表示/非表示制御のテスト"""
        screen = pygame.Surface((1024, 600))
        
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # 非表示にする
        renderer.set_visible(False)
        self.assertFalse(renderer.visible)
        
        # 非表示時は描画されない
        renderer.render(screen)
        # 実際の描画内容をテストするのは難しいが、エラーが出ないことを確認
        
        # 表示に戻す
        renderer.set_visible(True)
        self.assertTrue(renderer.visible)
        self.assertTrue(renderer.is_dirty())
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_icon_loading(self):
        """天気アイコンの読み込みテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # アイコンが読み込まれることを確認
        if hasattr(renderer, 'get_weather_icon'):
            icon = renderer.get_weather_icon('sunny')
            self.assertIsNotNone(icon)
            
            # キャッシュされることを確認
            icon2 = renderer.get_weather_icon('sunny')
            self.assertEqual(icon, icon2)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_panel_background(self):
        """パネル背景の描画テスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'create_panel_surface'):
            panel = renderer.create_panel_surface()
            self.assertIsNotNone(panel)
            self.assertEqual(panel.get_size(), (420, 260))
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_temperature_formatting(self):
        """温度表示のフォーマットテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'format_temperature'):
            # 整数
            self.assertEqual(renderer.format_temperature(20), "20°C")
            
            # 小数
            self.assertEqual(renderer.format_temperature(20.5), "21°C")
            self.assertEqual(renderer.format_temperature(20.4), "20°C")
            
            # 負の値
            self.assertEqual(renderer.format_temperature(-5), "-5°C")
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_date_formatting(self):
        """日付表示のフォーマットテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'format_forecast_date'):
            # MM/DD形式
            formatted = renderer.format_forecast_date("2024-01-15")
            self.assertIn("01", formatted)
            self.assertIn("15", formatted)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_error_display(self):
        """エラー表示のテスト"""
        screen = pygame.Surface((1024, 600))
        
        # プロバイダーがエラーを返す
        self.mock_provider.fetch.side_effect = Exception("API Error")
        
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # エラーでも描画が続行されること
        renderer.render(screen)
        self.assertFalse(renderer.is_dirty())
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_forecast_layout(self):
        """予報レイアウトのテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'calculate_forecast_positions'):
            # 3日分の予報の位置を計算
            positions = renderer.calculate_forecast_positions()
            self.assertEqual(len(positions), 3)
            
            # 横並びで配置されること
            for i in range(1, len(positions)):
                self.assertGreater(positions[i][0], positions[i-1][0])
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_wind_speed_formatting(self):
        """風速表示のフォーマットテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'format_wind_speed'):
            self.assertEqual(renderer.format_wind_speed(3.5), "3.5 m/s")
            self.assertEqual(renderer.format_wind_speed(10), "10.0 m/s")
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_humidity_formatting(self):
        """湿度表示のフォーマットテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'format_humidity'):
            self.assertEqual(renderer.format_humidity(65), "65%")
            self.assertEqual(renderer.format_humidity(100), "100%")
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_location_display(self):
        """位置情報表示のテスト"""
        # 位置情報表示を有効にする
        self.mock_config.get.side_effect = lambda k, d=None: {
            'weather.show_location': True
        }.get(k, self._mock_config_get(k, d))
        
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        if hasattr(renderer, 'format_location'):
            location = renderer.format_location(35.681236, 139.767125)
            self.assertIn("35.68", location)
            self.assertIn("139.77", location)
    
    @unittest.skipIf(WeatherRenderer is None, "WeatherRenderer not implemented yet")
    def test_memory_cleanup(self):
        """メモリクリーンアップのテスト"""
        renderer = WeatherRenderer(
            self.mock_asset_manager,
            self.mock_config,
            self.mock_provider
        )
        
        # いくつかの操作を実行
        renderer.update(1)
        screen = pygame.Surface((1024, 600))
        renderer.render(screen)
        
        # クリーンアップ
        if hasattr(renderer, 'cleanup'):
            renderer.cleanup()
            # エラーが発生しないことを確認


if __name__ == '__main__':
    unittest.main()