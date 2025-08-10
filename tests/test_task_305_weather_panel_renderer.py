#!/usr/bin/env python3
"""
TASK-305: 天気パネルレンダラー実装 - テストコード

WeatherPanelRendererクラスのテストスイート。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import pygame
from datetime import datetime

# テスト対象のクラス
from src.renderers.weather_panel_renderer import WeatherPanelRenderer


class TestWeatherPanelRenderer(unittest.TestCase):
    """天気パネルレンダラーのテストケース"""
    
    def setUp(self):
        """各テストの前処理"""
        # pygame初期化（モック）
        pygame.init()
        
        # モックアセットマネージャー
        self.mock_asset_manager = Mock()
        
        # モックフォント
        self.mock_font = Mock()
        self.mock_font.render.return_value = Mock(
            get_size=Mock(return_value=(100, 20)),
            get_width=Mock(return_value=100),
            get_height=Mock(return_value=20),
            get_rect=Mock(return_value=pygame.Rect(0, 0, 100, 20))
        )
        
        self.mock_small_font = Mock()
        self.mock_small_font.render.return_value = Mock(
            get_size=Mock(return_value=(80, 16)),
            get_width=Mock(return_value=80),
            get_height=Mock(return_value=16),
            get_rect=Mock(return_value=pygame.Rect(0, 0, 80, 16))
        )
        
        self.mock_asset_manager.get_font.side_effect = lambda name, size: (
            self.mock_font if size == 22 else self.mock_small_font
        )
        
        # テスト設定
        self.test_settings = {
            'ui': {
                'margins': {'x': 24, 'y': 16},
                'weather_font_px': 22
            },
            'weather': {
                'panel': {
                    'width': 420,
                    'height': 280,
                    'radius': 15,
                    'color': (30, 30, 40, 200)
                }
            }
        }
        
        # テスト用天気データ
        self.test_weather_data = {
            'updated': 1705123200,
            'forecasts': [
                {
                    'date': '2025-01-11',
                    'icon': 'sunny',
                    'temperature': {'min': 5, 'max': 13},
                    'precipitation_probability': 10
                },
                {
                    'date': '2025-01-12',
                    'icon': 'cloudy',
                    'temperature': {'min': 7, 'max': 15},
                    'precipitation_probability': 30
                },
                {
                    'date': '2025-01-13',
                    'icon': 'rain',
                    'temperature': {'min': 8, 'max': 12},
                    'precipitation_probability': 80
                }
            ]
        }
    
    def tearDown(self):
        """各テスト後の後処理"""
        pygame.quit()
    
    # =================================================================
    # Test Category 1: 初期化テスト
    # =================================================================
    
    def test_renderer_initialization(self):
        """Test Case 1.1: レンダラー初期化"""
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # インスタンスが作成されることを確認
        self.assertIsNotNone(renderer)
        
        # フォント取得が呼ばれたことを確認
        self.mock_asset_manager.get_font.assert_any_call('main', 22)
        
        # 設定が正しく読み込まれたことを確認
        self.assertEqual(renderer.margins_x, 24)
        self.assertEqual(renderer.margins_y, 16)
        self.assertEqual(renderer.font_size, 22)
        self.assertEqual(renderer.panel_width, 420)
        self.assertEqual(renderer.panel_height, 280)
    
    def test_renderer_initialization_with_defaults(self):
        """Test Case 1.2: デフォルト値での初期化"""
        # 最小限の設定
        minimal_settings = {}
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, minimal_settings)
        
        # デフォルト値が使用されることを確認
        self.assertEqual(renderer.margins_x, renderer.MARGIN_X)
        self.assertEqual(renderer.margins_y, renderer.MARGIN_Y)
        self.assertEqual(renderer.font_size, renderer.DEFAULT_FONT_SIZE)
        self.assertEqual(renderer.panel_width, renderer.DEFAULT_PANEL_WIDTH)
        self.assertEqual(renderer.panel_height, renderer.DEFAULT_PANEL_HEIGHT)
    
    # =================================================================
    # Test Category 2: データ更新テスト
    # =================================================================
    
    def test_update_weather_data(self):
        """Test Case 2.1: 天気データ更新"""
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # データ更新
        renderer.update(self.test_weather_data)
        
        # データが保存されたことを確認
        self.assertIsNotNone(renderer._weather_data)
        self.assertEqual(len(renderer._weather_data['forecasts']), 3)
    
    def test_update_with_none_data(self):
        """Test Case 2.2: None データでの更新"""
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # None で更新
        renderer.update(None)
        
        # データが更新されないことを確認
        self.assertIsNone(renderer._weather_data)
    
    # =================================================================
    # Test Category 3: 描画テスト
    # =================================================================
    
    @patch('pygame.Surface')
    @patch('pygame.draw.circle')
    @patch('pygame.draw.rect')
    def test_render_with_data(self, mock_rect, mock_circle, mock_surface_class):
        """Test Case 3.1: データありの描画"""
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_screen.blit = Mock()
        
        # モックパネルサーフェス
        mock_panel_surface = Mock()
        mock_surface_class.return_value = mock_panel_surface
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        renderer.update(self.test_weather_data)
        
        # 描画実行
        renderer.render(mock_screen)
        
        # パネル背景が作成されたことを確認
        mock_surface_class.assert_called_with((420, 280), pygame.SRCALPHA)
        
        # パネルが画面に描画されたことを確認
        mock_screen.blit.assert_any_call(mock_panel_surface, (24, 304))
        
        # フォントレンダリングが呼ばれたことを確認
        # 日付表示（3日分）
        self.assertGreaterEqual(self.mock_font.render.call_count, 3)
    
    def test_render_without_data(self):
        """Test Case 3.2: データなしの描画"""
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_screen.blit = Mock()
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # データなしで描画
        renderer.render(mock_screen)
        
        # 何も描画されないことを確認
        mock_screen.blit.assert_not_called()
    
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    @patch('pygame.Surface')
    def test_render_panel_position(self, mock_surface_class, mock_circle, mock_rect):
        """Test Case 3.3: パネル位置計算"""
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_screen.blit = Mock()
        
        # モックパネルサーフェス
        mock_panel_surface = Mock()
        mock_surface_class.return_value = mock_panel_surface
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        renderer.update(self.test_weather_data)
        
        # 描画実行
        renderer.render(mock_screen)
        
        # パネル位置計算（左下）
        expected_x = 24  # margins_x
        expected_y = 600 - 16 - 280  # screen_height - margins_y - panel_height = 304
        
        # 正しい位置に描画されたことを確認
        mock_screen.blit.assert_any_call(mock_panel_surface, (expected_x, expected_y))
    
    # =================================================================
    # Test Category 4: 天気アイコン描画テスト
    # =================================================================
    
    @patch('pygame.draw.circle')
    def test_weather_icon_rendering(self, mock_circle):
        """Test Case 4.1: 天気アイコン描画"""
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_screen.blit = Mock()
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # 各アイコンタイプのテスト
        icon_tests = [
            ('sunny', (255, 200, 0)),
            ('cloudy', (150, 150, 150)),
            ('rain', (100, 150, 255)),
            ('thunder', (200, 100, 255)),
            ('fog', (200, 200, 200))
        ]
        
        for icon_name, expected_color in icon_tests:
            with self.subTest(icon=icon_name):
                # アイコン描画
                renderer._draw_weather_icon(mock_screen, icon_name, 100, 100)
                
                # 円が描画されたことを確認
                mock_circle.assert_called_with(
                    mock_screen, expected_color, (130, 130), 30
                )
    
    # =================================================================
    # Test Category 5: 日付フォーマットテスト
    # =================================================================
    
    @patch('pygame.draw.circle')
    def test_forecast_date_formatting(self, mock_circle):
        """Test Case 5.1: 予報日付のフォーマット"""
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # 単一予報の描画
        forecast = {
            'date': '2025-01-11',
            'icon': 'sunny',
            'temperature': {'min': 5, 'max': 13},
            'precipitation_probability': 10
        }
        
        renderer._draw_forecast(mock_screen, forecast, 0, 0, 0)
        
        # 日付が正しくフォーマットされたことを確認
        # "01/11(土)" のような形式になるはず
        calls = self.mock_font.render.call_args_list
        date_call = calls[0]  # 最初の呼び出しが日付
        self.assertIn('01/11', date_call[0][0])
    
    # =================================================================
    # Test Category 6: 更新時刻表示テスト
    # =================================================================
    
    def test_update_time_display(self):
        """Test Case 6.1: 更新時刻表示"""
        # モックスクリーン
        mock_screen = Mock()
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # 更新時刻付きデータ
        data_with_time = {
            'updated': 1705123200,  # 2025-01-13 12:00:00
            'forecasts': []
        }
        
        renderer._weather_data = data_with_time
        renderer._draw_update_time(mock_screen, 0, 0)
        
        # 更新時刻が表示されたことを確認
        calls = self.mock_small_font.render.call_args_list
        self.assertGreater(len(calls), 0)
        
        # 時刻フォーマットが含まれることを確認
        time_text = calls[0][0][0]
        self.assertIn('更新:', time_text)
    
    # =================================================================
    # Test Category 7: クリーンアップテスト
    # =================================================================
    
    def test_cleanup(self):
        """Test Case 7.1: リソースクリーンアップ"""
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # データを設定
        renderer.update(self.test_weather_data)
        renderer._icon_cache['test'] = Mock()
        
        # クリーンアップ実行
        renderer.cleanup()
        
        # リソースがクリアされたことを確認
        self.assertIsNone(renderer._weather_data)
        self.assertEqual(len(renderer._icon_cache), 0)
    
    # =================================================================
    # Test Category 8: 境界値テスト
    # =================================================================
    
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    @patch('pygame.Surface')
    def test_render_with_many_forecasts(self, mock_surface_class, mock_circle, mock_rect):
        """Test Case 8.1: 多数の予報データ"""
        # モックパネルサーフェス
        mock_panel_surface = Mock()
        mock_surface_class.return_value = mock_panel_surface
        
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_screen.blit = Mock()
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # 5日分のデータ（3日分のみ表示されるはず）
        many_forecasts = {
            'updated': 1705123200,
            'forecasts': [
                {
                    'date': f'2025-01-{11+i}',
                    'icon': 'sunny',
                    'temperature': {'min': 5, 'max': 13},
                    'precipitation_probability': 10
                }
                for i in range(5)
            ]
        }
        
        renderer.update(many_forecasts)
        renderer.render(mock_screen)
        
        # 最大3日分のみ描画されることを確認
        # 日付表示は3回のみ
        date_render_calls = [
            call for call in self.mock_font.render.call_args_list
            if '01/' in call[0][0]
        ]
        self.assertLessEqual(len(date_render_calls), 3)
    
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    @patch('pygame.Surface')
    def test_render_with_missing_fields(self, mock_surface_class, mock_circle, mock_rect):
        """Test Case 8.2: 不完全なデータ"""
        # モックパネルサーフェス
        mock_panel_surface = Mock()
        mock_surface_class.return_value = mock_panel_surface
        
        # モックスクリーン
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        
        renderer = WeatherPanelRenderer(self.mock_asset_manager, self.test_settings)
        
        # 一部フィールドが欠けているデータ
        incomplete_data = {
            'forecasts': [
                {
                    'date': '2025-01-11',
                    # icon なし
                    'temperature': {'min': 5},  # max なし
                    # precipitation_probability なし
                }
            ]
        }
        
        renderer.update(incomplete_data)
        
        # エラーなく描画できることを確認
        try:
            renderer.render(mock_screen)
        except Exception as e:
            self.fail(f"Render failed with incomplete data: {e}")


if __name__ == '__main__':
    unittest.main()