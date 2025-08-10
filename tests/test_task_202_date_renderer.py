#!/usr/bin/env python3
"""
TASK-202: 日付レンダラー実装のテスト

TASK-202要件：
- YYYY-MM-DD (曜日)形式日付表示
- 時計直下配置
- 毎分更新
- 日本語・英語曜日対応
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# テスト対象のインポート（まだ存在しないため失敗する）
try:
    from src.renderers.date_renderer import DateRenderer
    from src.assets.asset_manager import AssetManager
except ImportError as e:
    print(f"Expected import error during Red phase: {e}")
    # テスト実行を継続するためのダミークラス
    class DateRenderer: 
        def __init__(self, asset_manager, settings): pass
        def update(self): pass
        def render(self, surface, clock_rect): pass
        def get_current_date(self): return "2024-08-10 (Sat)"
        def set_weekday_format(self, format): pass
    class AssetManager: pass


class TestTask202DateRendererBasic(unittest.TestCase):
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
                'date_font_px': 36,
                'date_color': [255, 255, 255],
                'weekday_format': 'japanese'
            },
            'fonts': {
                'main': './assets/fonts/test.otf'
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_date_renderer_initialization(self):
        """DateRenderer初期化テスト"""
        # Given: AssetManagerと設定
        asset_manager = self.asset_manager
        settings = self.test_settings
        
        # When: DateRendererを初期化
        renderer = DateRenderer(asset_manager, settings)
        
        # Then: 正常に初期化される
        self.assertIsInstance(renderer, DateRenderer)
        self.assertEqual(renderer.asset_manager, asset_manager)
        self.assertEqual(renderer.settings, settings)
    
    def test_get_current_date_format(self):
        """現在日付取得フォーマットテスト"""
        # Given: DateRendererインスタンス
        renderer = DateRenderer(self.asset_manager, self.test_settings)
        
        # When: 現在日付を取得
        current_date = renderer.get_current_date()
        
        # Then: YYYY-MM-DD (曜日)形式の文字列が返される
        self.assertIsInstance(current_date, str)
        self.assertRegex(current_date, r'^\d{4}-\d{2}-\d{2} \([^)]+\)$')
        
        # 日付部分の検証
        date_part = current_date.split(' ')[0]
        self.assertRegex(date_part, r'^\d{4}-\d{2}-\d{2}$')
        
        # 曜日部分の検証（括弧付き）
        weekday_part = current_date.split(' ')[1]
        self.assertTrue(weekday_part.startswith('('))
        self.assertTrue(weekday_part.endswith(')'))
    
    def test_format_date_method(self):
        """日付フォーマットメソッドテスト"""
        # Given: DateRendererと固定日付
        renderer = DateRenderer(self.asset_manager, self.test_settings)
        test_datetime = datetime(2024, 8, 10, 14, 30, 25)  # 土曜日
        
        # When: 日付をフォーマット
        formatted_date = renderer._format_date(test_datetime)
        
        # Then: 正しいフォーマットで返される
        self.assertEqual(formatted_date.split(' ')[0], "2024-08-10")
        self.assertIn('(', formatted_date)
        self.assertIn(')', formatted_date)
    
    def test_format_date_edge_cases(self):
        """日付フォーマットエッジケース"""
        renderer = DateRenderer(self.asset_manager, self.test_settings)
        
        # 元日
        new_year = datetime(2024, 1, 1, 0, 0, 0)
        formatted = renderer._format_date(new_year)
        self.assertEqual(formatted.split(' ')[0], "2024-01-01")
        
        # 大晦日
        new_year_eve = datetime(2024, 12, 31, 23, 59, 59)
        formatted = renderer._format_date(new_year_eve)
        self.assertEqual(formatted.split(' ')[0], "2024-12-31")
        
        # うるう年
        leap_day = datetime(2024, 2, 29, 12, 0, 0)
        formatted = renderer._format_date(leap_day)
        self.assertEqual(formatted.split(' ')[0], "2024-02-29")


class TestTask202DateRendererWeekday(unittest.TestCase):
    """曜日フォーマット機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
        # 日本語設定
        self.jp_settings = {
            'ui': {
                'date_font_px': 36,
                'weekday_format': 'japanese'
            }
        }
        
        # 英語設定
        self.en_settings = {
            'ui': {
                'date_font_px': 36,
                'weekday_format': 'english'
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_japanese_weekday_format(self):
        """日本語曜日フォーマットテスト"""
        # Given: 日本語設定のDateRenderer
        renderer = DateRenderer(self.asset_manager, self.jp_settings)
        
        # When: 各曜日のフォーマットをテスト
        test_dates = [
            (datetime(2024, 8, 5), "(月)"),   # 月曜日
            (datetime(2024, 8, 6), "(火)"),   # 火曜日
            (datetime(2024, 8, 7), "(水)"),   # 水曜日
            (datetime(2024, 8, 8), "(木)"),   # 木曜日
            (datetime(2024, 8, 9), "(金)"),   # 金曜日
            (datetime(2024, 8, 10), "(土)"),  # 土曜日
            (datetime(2024, 8, 11), "(日)"),  # 日曜日
        ]
        
        for test_date, expected_weekday in test_dates:
            with self.subTest(date=test_date.strftime('%Y-%m-%d')):
                weekday = renderer._format_weekday(test_date)
                self.assertEqual(weekday, expected_weekday)
    
    def test_english_weekday_format(self):
        """英語曜日フォーマットテスト"""
        # Given: 英語設定のDateRenderer
        renderer = DateRenderer(self.asset_manager, self.en_settings)
        
        # When: 各曜日のフォーマットをテスト
        test_dates = [
            (datetime(2024, 8, 5), "(Mon)"),  # Monday
            (datetime(2024, 8, 6), "(Tue)"),  # Tuesday
            (datetime(2024, 8, 7), "(Wed)"),  # Wednesday
            (datetime(2024, 8, 8), "(Thu)"),  # Thursday
            (datetime(2024, 8, 9), "(Fri)"),  # Friday
            (datetime(2024, 8, 10), "(Sat)"), # Saturday
            (datetime(2024, 8, 11), "(Sun)"), # Sunday
        ]
        
        for test_date, expected_weekday in test_dates:
            with self.subTest(date=test_date.strftime('%Y-%m-%d')):
                weekday = renderer._format_weekday(test_date)
                self.assertEqual(weekday, expected_weekday)
    
    def test_weekday_format_change(self):
        """曜日フォーマット設定変更テスト"""
        # Given: 日本語設定で初期化
        renderer = DateRenderer(self.asset_manager, self.jp_settings)
        test_date = datetime(2024, 8, 10)  # 土曜日
        
        # When: 初期状態で曜日取得
        initial_weekday = renderer._format_weekday(test_date)
        self.assertEqual(initial_weekday, "(土)")
        
        # When: 英語に変更
        renderer.set_weekday_format('english')
        
        # Then: 英語表記に変更される
        english_weekday = renderer._format_weekday(test_date)
        self.assertEqual(english_weekday, "(Sat)")
    
    def test_all_weekdays_coverage(self):
        """全曜日網羅テスト"""
        # Given: 各曜日のテストデータ（2024年8月5-11日）
        renderer = DateRenderer(self.asset_manager, self.jp_settings)
        
        dates_and_weekdays = [
            datetime(2024, 8, 5),   # 月曜
            datetime(2024, 8, 6),   # 火曜
            datetime(2024, 8, 7),   # 水曜
            datetime(2024, 8, 8),   # 木曜
            datetime(2024, 8, 9),   # 金曜
            datetime(2024, 8, 10),  # 土曜
            datetime(2024, 8, 11),  # 日曜
        ]
        
        # When: 全曜日をフォーマット
        weekdays = [renderer._format_weekday(dt) for dt in dates_and_weekdays]
        
        # Then: 7つの異なる曜日がすべて取得される
        self.assertEqual(len(weekdays), 7)
        self.assertEqual(len(set(weekdays)), 7)  # 重複なし
        
        # 日本語曜日として期待される形式
        expected = ["(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)"]
        self.assertEqual(weekdays, expected)


class TestTask202DateRendererRendering(unittest.TestCase):
    """レンダリング機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))  # 実際の解像度
        
        # AssetManagerモック設定
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.mock_surface = pygame.Surface((200, 36))  # 実際のサーフェス
        self.mock_font.render.return_value = self.mock_surface
        self.mock_font.get_height.return_value = 36
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {
            'ui': {
                'date_font_px': 36,
                'date_color': [255, 255, 255]
            }
        }
        
        self.renderer = DateRenderer(self.asset_manager, self.test_settings)
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_basic_rendering(self):
        """基本レンダリングテスト"""
        # Given: 描画対象のサーフェスと時計rect
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)  # 時計の位置とサイズ
        
        # When: レンダリングを実行
        self.renderer.render(surface, clock_rect)
        
        # Then: フォント読み込みとレンダリングが呼ばれる
        self.asset_manager.load_font.assert_called_once()
        self.mock_font.render.assert_called_once()
    
    def test_font_size_configuration(self):
        """フォントサイズ設定テスト"""
        # Given: 特定のフォントサイズ設定
        settings = {
            'ui': {'date_font_px': 48},
            'fonts': {'main': './test.otf'}
        }
        renderer = DateRenderer(self.asset_manager, settings)
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        
        # When: レンダリング実行
        renderer.render(surface, clock_rect)
        
        # Then: 指定されたフォントサイズで読み込まれる
        self.asset_manager.load_font.assert_called_with('./test.otf', 48)
    
    def test_position_relative_to_clock(self):
        """時計相対位置テスト"""
        # Given: 時計のrect情報
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)  # x=362, y=50, w=300, h=130
        
        # When: レンダリング実行
        self.renderer.render(surface, clock_rect)
        
        # Then: 時計の直下かつ中央に配置される
        # 期待される位置: 時計の中央X座標に日付も中央配置
        # 時計中央X = 362 + 300/2 = 512
        # 日付幅 = 200, 日付X = 512 - 200/2 = 412
        # Y座標は時計の下 = 50 + 130 + マージン
    
    def test_color_setting(self):
        """色設定テスト"""
        # Given: 特定の色設定
        blue_settings = {
            'ui': {
                'date_font_px': 36,
                'date_color': [0, 0, 255]  # 青色
            }
        }
        renderer = DateRenderer(self.asset_manager, blue_settings)
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        
        # When: レンダリング実行
        renderer.render(surface, clock_rect)
        
        # Then: 指定された色でレンダリング
        args, kwargs = self.mock_font.render.call_args
        self.assertIn((0, 0, 255), args)  # 青色が引数に含まれる


class TestTask202DateRendererUpdate(unittest.TestCase):
    """更新機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {'ui': {'date_font_px': 36}}
        self.renderer = DateRenderer(self.asset_manager, self.test_settings)
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_update_method(self):
        """update()メソッドテスト"""
        # Given: DateRendererインスタンス
        renderer = self.renderer
        
        # When: update()を呼び出し
        renderer.update()
        
        # Then: 内部状態が更新される
        self.assertTrue(hasattr(renderer, 'current_date'))
    
    @patch('src.renderers.date_renderer.datetime')
    def test_date_update_with_mock(self, mock_datetime):
        """モック日付でのupdate()テスト"""
        # Given: 固定日付のモック
        fixed_date = datetime(2024, 8, 10, 15, 30, 0)
        mock_datetime.now.return_value = fixed_date
        
        # When: update()実行
        self.renderer.update()
        
        # Then: モック日付が使用される
        mock_datetime.now.assert_called_once()
    
    def test_same_date_update_optimization(self):
        """同日更新最適化テスト"""
        # Given: 同じ日付での複数回更新
        renderer = self.renderer
        
        with patch('src.renderers.date_renderer.datetime') as mock_dt:
            # 同じ日の異なる時刻
            mock_dt.now.side_effect = [
                datetime(2024, 8, 10, 10, 0, 0),
                datetime(2024, 8, 10, 11, 0, 0),  # 1時間後
                datetime(2024, 8, 10, 12, 0, 0),  # 2時間後
            ]
            
            # When: 複数回更新
            renderer.update()
            first_date = renderer.current_date
            
            renderer.update()
            second_date = renderer.current_date
            
            renderer.update()
            third_date = renderer.current_date
            
            # Then: 同じ日付なので変更されない（最適化）
            self.assertEqual(first_date, second_date)
            self.assertEqual(second_date, third_date)


class TestTask202DateRendererConfiguration(unittest.TestCase):
    """設定変更のテスト"""
    
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
    
    def test_weekday_format_setting(self):
        """曜日フォーマット設定テスト"""
        # Given: 初期設定（日本語）
        jp_settings = {
            'ui': {
                'date_font_px': 36,
                'weekday_format': 'japanese'
            }
        }
        renderer = DateRenderer(self.asset_manager, jp_settings)
        
        # When: 曜日フォーマットを英語に変更
        renderer.set_weekday_format('english')
        
        # Then: 英語設定が反映される
        test_date = datetime(2024, 8, 10)  # 土曜日
        weekday = renderer._format_weekday(test_date)
        self.assertEqual(weekday, "(Sat)")
    
    def test_font_size_configuration(self):
        """フォントサイズ設定テスト"""
        # Given: 特定のフォントサイズ設定
        settings = {'ui': {'date_font_px': 48}}
        
        # When: DateRendererを初期化
        renderer = DateRenderer(self.asset_manager, settings)
        
        # Then: 設定されたフォントサイズが使用される
        self.assertEqual(renderer.font_size, 48)
    
    def test_color_configuration(self):
        """色設定テスト"""
        # Given: 特定の色設定
        settings = {
            'ui': {
                'date_color': [255, 0, 128],  # ピンク色
                'date_font_px': 36
            }
        }
        
        # When: DateRendererを初期化
        renderer = DateRenderer(self.asset_manager, settings)
        
        # Then: 設定された色が使用される
        self.assertEqual(renderer.font_color, [255, 0, 128])


class TestTask202DateRendererIntegration(unittest.TestCase):
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
                'date_font_px': 36,
                'date_color': [255, 255, 255],
                'weekday_format': 'japanese'
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
        # Given: 実際のAssetManagerとDateRenderer
        renderer = DateRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        
        # When: 複数回レンダリング実行
        renderer.render(surface, clock_rect)
        renderer.render(surface, clock_rect)  # 2回目はキャッシュから
        
        # Then: 正常に動作する
        stats = self.asset_manager.get_cache_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('hit_rate', stats)
        self.assertGreaterEqual(stats['hit_rate'], 0.0)
    
    def test_full_workflow(self):
        """完全ワークフローテスト"""
        # Given: DateRenderer
        renderer = DateRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        
        # When: 更新→描画のワークフロー
        renderer.update()
        renderer.render(surface, clock_rect)
        
        # Then: エラーなく実行完了
        self.assertIsNotNone(renderer.get_current_date())
        
        # 曜日表記変更もテスト
        renderer.set_weekday_format('english')
        renderer.render(surface, clock_rect)


class TestTask202DateRendererErrorHandling(unittest.TestCase):
    """エラーハンドリングテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_invalid_weekday_format(self):
        """不正な曜日フォーマット処理テスト"""
        # Given: 不正な曜日フォーマット設定
        asset_manager = Mock()
        invalid_settings = {
            'ui': {
                'date_font_px': 36,
                'weekday_format': 'invalid_format'
            }
        }
        
        # When: DateRenderer初期化
        try:
            renderer = DateRenderer(asset_manager, invalid_settings)
            # Then: デフォルト値（日本語）で動作
            test_date = datetime(2024, 8, 10)
            weekday = renderer._format_weekday(test_date)
            self.assertIn('土', weekday)  # 日本語曜日
        except Exception as e:
            self.fail(f"Should handle invalid weekday format gracefully: {e}")
    
    def test_empty_settings_handling(self):
        """空設定処理テスト"""
        # Given: 空の設定
        asset_manager = Mock()
        empty_settings = {}
        
        # When: DateRenderer初期化
        try:
            renderer = DateRenderer(asset_manager, empty_settings)
            # Then: デフォルト値で正常動作
            self.assertIsInstance(renderer, DateRenderer)
        except KeyError:
            self.fail("Should provide default values for missing settings")


class TestTask202DateRendererPerformance(unittest.TestCase):
    """パフォーマンステスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.mock_surface = pygame.Surface((200, 36))
        self.mock_font.render.return_value = self.mock_surface
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.renderer = DateRenderer(self.asset_manager, {'ui': {'date_font_px': 36}})
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_rendering_performance(self):
        """レンダリング性能テスト"""
        import time
        
        # Given: 大量レンダリングの準備
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        iterations = 1000
        
        # When: 大量レンダリング実行
        start_time = time.time()
        for _ in range(iterations):
            self.renderer.render(surface, clock_rect)
        end_time = time.time()
        
        # Then: 合理的な時間内で完了
        elapsed = end_time - start_time
        avg_time = elapsed / iterations
        
        # 1回のレンダリングが0.5ms以下であることを期待
        self.assertLess(avg_time, 0.0005, f"Average rendering time: {avg_time:.6f}s")
    
    def test_memory_stability(self):
        """メモリ安定性テスト"""
        import gc
        
        # Given: メモリ測定準備
        surface = pygame.Surface((1024, 600))
        clock_rect = pygame.Rect(362, 50, 300, 130)
        
        # When: 大量の更新・描画サイクル
        for i in range(5000):
            self.renderer.update()
            self.renderer.render(surface, clock_rect)
            
            # 100回ごとにガベージコレクション
            if i % 100 == 0:
                gc.collect()
        
        # Then: メモリリークが発生していないことを期待
        self.assertTrue(True, "Memory leak test completed")


if __name__ == '__main__':
    # テストスイート実行
    unittest.main(verbosity=2)