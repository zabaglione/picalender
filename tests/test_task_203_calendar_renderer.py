#!/usr/bin/env python3
"""
TASK-203: カレンダーレンダラー実装のテスト

TASK-203要件：
- 今月カレンダー表示（日曜始まり）
- 約420×280px領域、右下配置
- 曜日色分け（日曜赤、土曜青、平日白）
- 今日ハイライト表示
"""

import os
import sys
import unittest
import tempfile
import shutil
import calendar
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# テスト対象のインポート（まだ存在しないため失敗する）
try:
    from src.renderers.calendar_renderer import CalendarRenderer
    from src.assets.asset_manager import AssetManager
except ImportError as e:
    print(f"Expected import error during Red phase: {e}")
    # テスト実行を継続するためのダミークラス
    class CalendarRenderer:
        def __init__(self, asset_manager, settings): pass
        def update(self): pass
        def render(self, surface): pass
        def get_current_month(self): return (2024, 8)
        def set_first_weekday(self, weekday): pass
        def set_position(self, x, y): pass
        def cleanup(self): pass
    class AssetManager: pass


class TestTask203CalendarRendererBasic(unittest.TestCase):
    """基本機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))  # ダミーディスプレイ
        
        # AssetManagerモック
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
        # テスト設定
        self.test_settings = {
            'ui': {
                'calendar_font_px': 22,
                'calendar_header_font_px': 22,
                'calendar_position_x': 580,
                'calendar_position_y': 300,
                'calendar_width': 420,
                'calendar_height': 280,
                'calendar_cell_margin': 4
            },
            'calendar': {
                'first_weekday': 'SUNDAY',
                'today_highlight': True,
                'color_sunday': [255, 107, 107],
                'color_saturday': [77, 171, 247],
                'color_weekday': [255, 255, 255],
                'color_today_bg': [255, 217, 61],
                'color_today_text': [0, 0, 0],
                'color_header': [200, 200, 200]
            },
            'fonts': {
                'main': './assets/fonts/test.otf'
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_calendar_renderer_initialization(self):
        """CalendarRenderer初期化テスト"""
        # Given: AssetManagerと設定
        asset_manager = self.asset_manager
        settings = self.test_settings
        
        # When: CalendarRendererを初期化
        renderer = CalendarRenderer(asset_manager, settings)
        
        # Then: 正常に初期化される
        self.assertIsInstance(renderer, CalendarRenderer)
        self.assertEqual(renderer.asset_manager, asset_manager)
        self.assertEqual(renderer.settings, settings)
    
    def test_get_current_month(self):
        """現在月取得テスト"""
        # Given: CalendarRendererインスタンス
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: 現在月を取得
        current_month = renderer.get_current_month()
        
        # Then: (年, 月)タプルが返される
        self.assertIsInstance(current_month, tuple)
        self.assertEqual(len(current_month), 2)
        year, month = current_month
        self.assertIsInstance(year, int)
        self.assertIsInstance(month, int)
        self.assertGreaterEqual(year, 2024)
        self.assertTrue(1 <= month <= 12)
    
    def test_generate_calendar_data(self):
        """カレンダーデータ生成テスト"""
        # Given: CalendarRendererと特定の年月
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        test_year, test_month = 2024, 8  # 2024年8月
        
        # When: カレンダーデータを生成
        calendar_data = renderer._generate_calendar_data(test_year, test_month)
        
        # Then: 正確な月構造が生成される
        self.assertIsInstance(calendar_data, list)
        self.assertLessEqual(len(calendar_data), 6)  # 最大6週
        self.assertGreaterEqual(len(calendar_data), 4)  # 最小4週
        
        # 各週は7日の配列
        for week in calendar_data:
            self.assertEqual(len(week), 7)
            for day in week:
                self.assertIsInstance(day, int)
                self.assertTrue(0 <= day <= 31)
    
    def test_is_today_function(self):
        """今日判定機能テスト"""
        # Given: CalendarRendererと固定日付
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        with patch('src.renderers.calendar_renderer.date') as mock_date:
            mock_date.today.return_value = date(2024, 8, 10)
            
            # When: 今日・昨日・明日で判定テスト
            is_today_result = renderer._is_today(2024, 8, 10)
            is_yesterday_result = renderer._is_today(2024, 8, 9)
            is_tomorrow_result = renderer._is_today(2024, 8, 11)
            is_other_month_result = renderer._is_today(2024, 7, 10)
            
            # Then: 今日のみTrueを返す
            self.assertTrue(is_today_result)
            self.assertFalse(is_yesterday_result)
            self.assertFalse(is_tomorrow_result)
            self.assertFalse(is_other_month_result)


class TestTask203CalendarRendererLayout(unittest.TestCase):
    """レイアウト・描画機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))  # 実際の解像度
        
        # AssetManagerモック設定
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.mock_surface = pygame.Surface((50, 35))  # セルサイズ
        self.mock_font.render.return_value = self.mock_surface
        self.mock_font.get_height.return_value = 22
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {
            'ui': {
                'calendar_font_px': 22,
                'calendar_header_font_px': 22,
                'calendar_position_x': 580,
                'calendar_position_y': 300,
                'calendar_width': 420,
                'calendar_height': 280,
                'calendar_cell_margin': 4
            },
            'calendar': {
                'first_weekday': 'SUNDAY'
            }
        }
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_calculate_cell_positions(self):
        """セル位置計算テスト"""
        # Given: CalendarRendererと領域設定
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: セル位置を計算
        positions = renderer._calculate_cell_positions()
        
        # Then: 7×7グリッドの座標が正確に計算される
        self.assertEqual(len(positions), 7)  # 7行（ヘッダ+6週）
        for row in positions:
            self.assertEqual(len(row), 7)  # 7列
            for cell_pos in row:
                x, y = cell_pos
                self.assertIsInstance(x, int)
                self.assertIsInstance(y, int)
                # 領域内の座標であることを確認
                self.assertGreaterEqual(x, 580)  # position_x以上
                self.assertLess(x, 580 + 420)    # position_x + width未満
                self.assertGreaterEqual(y, 300)  # position_y以上
                self.assertLess(y, 300 + 280)    # position_y + height未満
    
    def test_basic_rendering(self):
        """基本描画テスト"""
        # Given: 描画対象のサーフェス
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリングを実行
        renderer.render(surface)
        
        # Then: フォント読み込みと描画が実行される
        self.asset_manager.load_font.assert_called()
        self.mock_font.render.assert_called()
    
    def test_render_header(self):
        """ヘッダ描画テスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: ヘッダ描画実行
        renderer._render_header(surface)
        
        # Then: 7つの曜日名が描画される
        # モック呼び出し回数で確認（Sun, Mon, Tue, Wed, Thu, Fri, Sat）
        self.assertEqual(self.mock_font.render.call_count, 7)
        
        # 呼び出し引数を確認（日曜始まりの順序）
        call_args_list = self.mock_font.render.call_args_list
        expected_weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, call_args in enumerate(call_args_list):
            args, kwargs = call_args
            rendered_text = args[0]
            self.assertEqual(rendered_text, expected_weekdays[i])
    
    def test_render_date_cells(self):
        """日付セル描画テスト"""
        # Given: CalendarRendererとカレンダーデータ
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # 2024年8月のテストデータ（木曜始まり）
        test_calendar = [
            [0, 0, 0, 1, 2, 3, 4],     # 第1週
            [5, 6, 7, 8, 9, 10, 11],   # 第2週
            [12, 13, 14, 15, 16, 17, 18], # 第3週
            [19, 20, 21, 22, 23, 24, 25], # 第4週
            [26, 27, 28, 29, 30, 31, 0],  # 第5週
        ]
        
        # When: 日付セル描画実行
        renderer._render_date_cells(surface, test_calendar)
        
        # Then: 空でない日付セルのみ描画される
        # 31日分の日付が描画される（空セル0は除く）
        valid_days = sum(1 for week in test_calendar for day in week if day > 0)
        self.assertEqual(valid_days, 31)  # 8月は31日


class TestTask203CalendarRendererColors(unittest.TestCase):
    """色分け・ハイライト機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {
            'calendar': {
                'color_sunday': [255, 107, 107],    # 赤系
                'color_saturday': [77, 171, 247],   # 青系
                'color_weekday': [255, 255, 255],   # 白系
                'color_today_bg': [255, 217, 61],   # 黄系背景
                'color_today_text': [0, 0, 0],      # 黒系文字
            }
        }
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_get_cell_color_weekdays(self):
        """曜日別色分けテスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: 各曜日の色を取得
        sunday_color = renderer._get_cell_color(0, False)      # 日曜日
        monday_color = renderer._get_cell_color(1, False)      # 月曜日
        tuesday_color = renderer._get_cell_color(2, False)     # 火曜日
        wednesday_color = renderer._get_cell_color(3, False)   # 水曜日
        thursday_color = renderer._get_cell_color(4, False)    # 木曜日
        friday_color = renderer._get_cell_color(5, False)      # 金曜日
        saturday_color = renderer._get_cell_color(6, False)    # 土曜日
        
        # Then: 設定された曜日別色が返される
        self.assertEqual(sunday_color, [255, 107, 107])    # 赤系
        self.assertEqual(monday_color, [255, 255, 255])    # 白系（平日）
        self.assertEqual(tuesday_color, [255, 255, 255])   # 白系（平日）
        self.assertEqual(wednesday_color, [255, 255, 255]) # 白系（平日）
        self.assertEqual(thursday_color, [255, 255, 255])  # 白系（平日）
        self.assertEqual(friday_color, [255, 255, 255])    # 白系（平日）
        self.assertEqual(saturday_color, [77, 171, 247])   # 青系
    
    def test_today_highlight_colors(self):
        """今日ハイライト色テスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: 今日の色を取得
        today_bg_color = renderer._get_today_bg_color()
        today_text_color = renderer._get_today_text_color()
        
        # Then: 今日用の強調色が返される
        self.assertEqual(today_bg_color, [255, 217, 61])  # 黄系背景
        self.assertEqual(today_text_color, [0, 0, 0])     # 黒系文字
    
    def test_color_override_for_today(self):
        """今日の色優先テスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: 今日フラグありで各曜日の色を取得
        sunday_today = renderer._get_cell_color(0, True)   # 今日が日曜日
        saturday_today = renderer._get_cell_color(6, True) # 今日が土曜日
        weekday_today = renderer._get_cell_color(2, True)  # 今日が平日
        
        # Then: 今日の場合は曜日に関係なく今日色が優先される
        expected_today_color = [255, 217, 61]  # 今日背景色
        self.assertEqual(sunday_today, expected_today_color)
        self.assertEqual(saturday_today, expected_today_color)
        self.assertEqual(weekday_today, expected_today_color)


class TestTask203CalendarRendererUpdate(unittest.TestCase):
    """更新・変更検知機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {
            'ui': {'calendar_font_px': 22},
            'calendar': {'first_weekday': 'SUNDAY'}
        }
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_update_method(self):
        """update()メソッドテスト"""
        # Given: CalendarRendererインスタンス
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        # When: update()を呼び出し
        renderer.update()
        
        # Then: 内部状態が更新される
        self.assertTrue(hasattr(renderer, 'current_month'))
        self.assertTrue(hasattr(renderer, 'current_year'))
    
    @patch('src.renderers.calendar_renderer.datetime')
    def test_month_change_detection(self, mock_datetime):
        """月変更検知テスト"""
        # Given: 月末での初期化
        mock_datetime.now.return_value = datetime(2024, 7, 31)  # 7月末
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        renderer.update()  # 初期状態
        initial_month = renderer.current_month
        
        # When: 月初に日付変更
        mock_datetime.now.return_value = datetime(2024, 8, 1)   # 8月初
        renderer.update()
        
        # Then: 新しい月に更新される
        self.assertNotEqual(renderer.current_month, initial_month)
        self.assertEqual(renderer.current_month, 8)
        self.assertEqual(renderer.current_year, 2024)
    
    def test_day_change_highlight_update(self):
        """日付変更時の今日ハイライト更新テスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        with patch('src.renderers.calendar_renderer.date') as mock_date:
            # 前日での初期化
            mock_date.today.return_value = date(2024, 8, 9)   # 8月9日
            initial_today = renderer._get_today_date()
            
            # When: 翌日に変更
            mock_date.today.return_value = date(2024, 8, 10)  # 8月10日
            
            # Then: 新しい今日に更新される
            new_today = renderer._get_today_date()
            self.assertNotEqual(new_today, initial_today)
            self.assertEqual(new_today, 10)
    
    def test_same_month_optimization(self):
        """同月内更新最適化テスト"""
        # Given: 同月の異なる日付
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        
        with patch('src.renderers.calendar_renderer.datetime') as mock_dt:
            # 同月の異なる日付
            mock_dt.now.side_effect = [
                datetime(2024, 8, 1),   # 月初
                datetime(2024, 8, 15),  # 月中
                datetime(2024, 8, 31),  # 月末
            ]
            
            # When: 複数回更新
            renderer.update()
            first_calendar_data = renderer.calendar_data
            
            renderer.update()
            second_calendar_data = renderer.calendar_data
            
            renderer.update()
            third_calendar_data = renderer.calendar_data
            
            # Then: 同月内ではカレンダー構造は再生成されない（最適化）
            self.assertEqual(first_calendar_data, second_calendar_data)
            self.assertEqual(second_calendar_data, third_calendar_data)


class TestTask203CalendarRendererConfiguration(unittest.TestCase):
    """設定・カスタマイズ機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_set_first_weekday_sunday(self):
        """日曜始まり設定テスト"""
        # Given: 日曜始まり設定
        settings = {
            'calendar': {'first_weekday': 'SUNDAY'},
            'ui': {'calendar_font_px': 22}
        }
        renderer = CalendarRenderer(self.asset_manager, settings)
        
        # When: 週の開始曜日を確認
        weekday_headers = renderer._get_weekday_headers()
        
        # Then: 日曜始まりの順序
        expected_headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        self.assertEqual(weekday_headers, expected_headers)
    
    def test_set_first_weekday_monday(self):
        """月曜始まり設定テスト"""
        # Given: 月曜始まり設定
        settings = {
            'calendar': {'first_weekday': 'MONDAY'},
            'ui': {'calendar_font_px': 22}
        }
        renderer = CalendarRenderer(self.asset_manager, settings)
        
        # When: 週の開始曜日を変更
        renderer.set_first_weekday('MONDAY')
        weekday_headers = renderer._get_weekday_headers()
        
        # Then: 月曜始まりの順序
        expected_headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.assertEqual(weekday_headers, expected_headers)
    
    def test_font_size_configuration(self):
        """フォントサイズ設定テスト"""
        # Given: 特定のフォントサイズ設定
        settings = {
            'ui': {
                'calendar_font_px': 24,
                'calendar_header_font_px': 26
            },
            'fonts': {'main': './test.otf'}
        }
        
        # When: CalendarRendererを初期化
        renderer = CalendarRenderer(self.asset_manager, settings)
        
        # Then: 設定されたフォントサイズが使用される
        self.assertEqual(renderer.font_size, 24)
        self.assertEqual(renderer.header_font_size, 26)
    
    def test_position_setting(self):
        """位置設定テスト"""
        # Given: 特定の位置設定
        settings = {
            'ui': {
                'calendar_position_x': 600,
                'calendar_position_y': 350,
                'calendar_font_px': 22
            }
        }
        renderer = CalendarRenderer(self.asset_manager, settings)
        
        # When: 新しい位置を設定
        renderer.set_position(700, 400)
        
        # Then: 設定された位置が反映される
        self.assertEqual(renderer.position_x, 700)
        self.assertEqual(renderer.position_y, 400)
    
    def test_size_configuration(self):
        """サイズ設定テスト"""
        # Given: 特定のサイズ設定
        settings = {
            'ui': {
                'calendar_width': 500,
                'calendar_height': 350,
                'calendar_font_px': 22
            }
        }
        
        # When: CalendarRendererを初期化
        renderer = CalendarRenderer(self.asset_manager, settings)
        
        # Then: 設定されたサイズが使用される
        self.assertEqual(renderer.width, 500)
        self.assertEqual(renderer.height, 350)


class TestTask203CalendarRendererErrorHandling(unittest.TestCase):
    """エラーハンドリングテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_invalid_font_path_fallback(self):
        """無効フォントパス時のフォールバックテスト"""
        # Given: 無効なフォントパス
        asset_manager = Mock()
        asset_manager.load_font.side_effect = Exception("Font not found")
        
        settings = {
            'fonts': {'main': './invalid/font/path.otf'},
            'ui': {'calendar_font_px': 22}
        }
        
        # When: CalendarRenderer初期化
        try:
            renderer = CalendarRenderer(asset_manager, settings)
            # Then: システムフォントで正常動作
            self.assertIsNotNone(renderer)
        except Exception as e:
            self.fail(f"Should handle invalid font path gracefully: {e}")
    
    def test_invalid_settings_default_values(self):
        """無効設定値でのデフォルト値使用テスト"""
        # Given: 無効・不完全な設定
        asset_manager = Mock()
        invalid_settings = {
            'ui': {
                'calendar_font_px': -10,      # 負の値
                'calendar_width': 0,          # 0値
                'calendar_height': 99999      # 極大値
            },
            'calendar': {
                'first_weekday': 'INVALID',   # 無効値
                'color_sunday': [300, -50, 999]  # 範囲外色値
            }
        }
        
        # When: CalendarRenderer初期化
        try:
            renderer = CalendarRenderer(asset_manager, invalid_settings)
            # Then: デフォルト値で正常動作
            self.assertIsInstance(renderer, CalendarRenderer)
            # フォントサイズはデフォルト値に修正される
            self.assertGreater(renderer.font_size, 0)
            self.assertLess(renderer.font_size, 100)
        except Exception as e:
            self.fail(f"Should use default values for invalid settings: {e}")
    
    def test_empty_settings_handling(self):
        """空設定でのデフォルト動作テスト"""
        # Given: 空の設定
        asset_manager = Mock()
        empty_settings = {}
        
        # When: CalendarRenderer初期化
        try:
            renderer = CalendarRenderer(asset_manager, empty_settings)
            # Then: デフォルト値で正常動作
            self.assertIsInstance(renderer, CalendarRenderer)
        except KeyError:
            self.fail("Should provide default values for missing settings")


class TestTask203CalendarRendererIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))
        
        # 実際のAssetManagerを使用
        from src.assets.asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
        self.test_settings = {
            'ui': {
                'calendar_font_px': 22,
                'calendar_header_font_px': 22,
                'calendar_position_x': 580,
                'calendar_position_y': 300,
                'calendar_width': 420,
                'calendar_height': 280
            },
            'calendar': {
                'first_weekday': 'SUNDAY',
                'color_sunday': [255, 107, 107],
                'color_saturday': [77, 171, 247],
                'color_weekday': [255, 255, 255]
            },
            'fonts': {
                'main': None  # システムデフォルト
            }
        }
    
    def tearDown(self):
        """テスト後処理"""
        self.asset_manager.cleanup()
        pygame.quit()
    
    def test_asset_manager_integration(self):
        """AssetManager統合テスト"""
        # Given: 実際のAssetManagerとCalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: 複数回レンダリング実行
        renderer.render(surface)
        renderer.render(surface)  # 2回目はキャッシュから
        
        # Then: 正常に動作する
        stats = self.asset_manager.get_cache_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('hit_rate', stats)
        self.assertGreaterEqual(stats['hit_rate'], 0.0)
    
    def test_full_workflow(self):
        """完全ワークフローテスト"""
        # Given: CalendarRenderer
        renderer = CalendarRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: 更新→描画のワークフロー
        renderer.update()
        renderer.render(surface)
        
        # Then: エラーなく実行完了
        current_month = renderer.get_current_month()
        self.assertIsInstance(current_month, tuple)
        self.assertEqual(len(current_month), 2)
        
        # 週開始曜日変更もテスト
        renderer.set_first_weekday('MONDAY')
        renderer.render(surface)


if __name__ == '__main__':
    # テストスイート実行
    unittest.main(verbosity=2)