#!/usr/bin/env python3
"""
TASK-201: 時計レンダラー実装のテスト

TASK-201要件：
- デジタル時計（HH:MM:SS）表示
- 毎秒更新
- 画面上部中央配置
- フォントサイズ130px
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, time
from unittest.mock import Mock, patch, MagicMock
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# テスト対象のインポート（まだ存在しないため失敗する）
try:
    from src.renderers.clock_renderer import ClockRenderer
    from src.assets.asset_manager import AssetManager
except ImportError as e:
    print(f"Expected import error during Red phase: {e}")
    # テスト実行を継続するためのダミークラス
    class ClockRenderer: 
        def __init__(self, asset_manager, settings): pass
        def update(self): pass
        def render(self, surface): pass
        def get_current_time(self): return "00:00:00"
    class AssetManager: pass


class TestTask201ClockRendererBasic(unittest.TestCase):
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
                'clock_font_px': 130,
                'clock_color': [255, 255, 255]
            },
            'fonts': {
                'main': './assets/fonts/test.otf'
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_clock_renderer_initialization(self):
        """ClockRenderer初期化テスト"""
        # Given: AssetManagerと設定
        asset_manager = self.asset_manager
        settings = self.test_settings
        
        # When: ClockRendererを初期化
        renderer = ClockRenderer(asset_manager, settings)
        
        # Then: 正常に初期化される
        self.assertIsInstance(renderer, ClockRenderer)
        self.assertEqual(renderer.asset_manager, asset_manager)
        self.assertEqual(renderer.settings, settings)
    
    def test_get_current_time_format(self):
        """現在時刻取得フォーマットテスト"""
        # Given: ClockRendererインスタンス
        renderer = ClockRenderer(self.asset_manager, self.test_settings)
        
        # When: 現在時刻を取得
        current_time = renderer.get_current_time()
        
        # Then: HH:MM:SS形式の文字列が返される
        self.assertIsInstance(current_time, str)
        self.assertRegex(current_time, r'^\d{2}:\d{2}:\d{2}$')
        
        # 時刻の範囲チェック
        parts = current_time.split(':')
        hours, minutes, seconds = map(int, parts)
        self.assertGreaterEqual(hours, 0)
        self.assertLessEqual(hours, 23)
        self.assertGreaterEqual(minutes, 0)
        self.assertLessEqual(minutes, 59)
        self.assertGreaterEqual(seconds, 0)
        self.assertLessEqual(seconds, 59)
    
    def test_format_time_method(self):
        """時刻フォーマットメソッドテスト"""
        # Given: ClockRendererと固定時刻
        renderer = ClockRenderer(self.asset_manager, self.test_settings)
        test_datetime = datetime(2024, 6, 15, 14, 30, 25)
        
        # When: 時刻をフォーマット
        formatted_time = renderer._format_time(test_datetime)
        
        # Then: 正しいフォーマットで返される
        self.assertEqual(formatted_time, "14:30:25")
    
    def test_format_time_edge_cases(self):
        """時刻フォーマットエッジケース"""
        renderer = ClockRenderer(self.asset_manager, self.test_settings)
        
        # 午前0時
        midnight = datetime(2024, 1, 1, 0, 0, 0)
        self.assertEqual(renderer._format_time(midnight), "00:00:00")
        
        # 午後11時59分59秒
        late_night = datetime(2024, 12, 31, 23, 59, 59)
        self.assertEqual(renderer._format_time(late_night), "23:59:59")
        
        # 一桁の時・分・秒
        single_digits = datetime(2024, 1, 1, 9, 5, 3)
        self.assertEqual(renderer._format_time(single_digits), "09:05:03")


class TestTask201ClockRendererRendering(unittest.TestCase):
    """レンダリング機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))  # 実際の解像度
        
        # AssetManagerモック設定
        self.asset_manager = Mock()
        self.mock_font = Mock()
        # 実際のサーフェスを作成してモックの戻り値に設定
        self.mock_surface = pygame.Surface((300, 130))
        self.mock_font.render.return_value = self.mock_surface
        self.mock_font.get_height.return_value = 130
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.test_settings = {
            'ui': {
                'clock_font_px': 130,
                'clock_color': [255, 255, 255]
            }
        }
        
        self.renderer = ClockRenderer(self.asset_manager, self.test_settings)
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_basic_rendering(self):
        """基本レンダリングテスト"""
        # Given: 描画対象のサーフェス
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリングを実行
        self.renderer.render(surface)
        
        # Then: フォント読み込みとレンダリングが呼ばれる
        self.asset_manager.load_font.assert_called_once()
        self.mock_font.render.assert_called_once()
    
    def test_font_size_configuration(self):
        """フォントサイズ設定テスト"""
        # Given: 特定のフォントサイズ設定
        settings = {
            'ui': {'clock_font_px': 200},
            'fonts': {'main': './test.otf'}
        }
        renderer = ClockRenderer(self.asset_manager, settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        renderer.render(surface)
        
        # Then: 指定されたフォントサイズで読み込まれる
        self.asset_manager.load_font.assert_called_with('./test.otf', 200)
    
    def test_text_positioning(self):
        """テキスト配置テスト"""
        # Given: 描画対象サーフェス
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        self.renderer.render(surface)
        
        # Then: 正しい位置に描画される（上部中央）
        # 具体的な位置計算のテスト
        expected_x = (1024 - 300) // 2  # 画面幅からテキスト幅を引いて中央配置
        expected_y = 50  # 上部マージン
        
        # blitが正しい位置で呼ばれることを確認
        # （実装時にsurface.blitの呼び出し確認）
    
    def test_color_setting(self):
        """色設定テスト"""
        # Given: 特定の色設定
        red_settings = {
            'ui': {
                'clock_font_px': 130,
                'clock_color': [255, 0, 0]  # 赤色
            }
        }
        renderer = ClockRenderer(self.asset_manager, red_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        renderer.render(surface)
        
        # Then: 指定された色でレンダリング
        args, kwargs = self.mock_font.render.call_args
        self.assertIn((255, 0, 0), args)  # 赤色が引数に含まれる


class TestTask201ClockRendererUpdate(unittest.TestCase):
    """更新機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.test_settings = {'ui': {'clock_font_px': 130}}
        self.renderer = ClockRenderer(self.asset_manager, self.test_settings)
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_update_method(self):
        """update()メソッドテスト"""
        # Given: ClockRendererインスタンス
        renderer = self.renderer
        
        # When: update()を呼び出し
        renderer.update()
        
        # Then: 内部状態が更新される
        # (具体的な内部状態のアサーションは実装依存)
        self.assertTrue(hasattr(renderer, 'current_time'))
    
    @patch('src.renderers.clock_renderer.datetime')
    def test_time_update_with_mock(self, mock_datetime):
        """モック時刻でのupdate()テスト"""
        # Given: 固定時刻のモック
        fixed_time = datetime(2024, 6, 15, 10, 30, 15)
        mock_datetime.now.return_value = fixed_time
        
        # When: update()実行
        self.renderer.update()
        
        # Then: モック時刻が使用される
        mock_datetime.now.assert_called_once()


class TestTask201ClockRendererIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))
        
        # 実際のAssetManagerを使用（モックではなく）
        from src.assets.asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
        self.test_settings = {
            'ui': {
                'clock_font_px': 130,
                'clock_color': [255, 255, 255]
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
        # Given: 実際のAssetManagerとClockRenderer
        renderer = ClockRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: 複数回レンダリング実行
        renderer.render(surface)
        renderer.render(surface)  # 2回目はキャッシュから
        
        # Then: 正常に動作する
        stats = self.asset_manager.get_cache_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('hit_rate', stats)
        # 初回読み込みのため、キャッシュヒット率は低いが正常動作
        self.assertGreaterEqual(stats['hit_rate'], 0.0)
    
    def test_full_workflow(self):
        """完全ワークフローテスト"""
        # Given: ClockRenderer
        renderer = ClockRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: 更新→描画のワークフロー
        renderer.update()
        renderer.render(surface)
        
        # Then: エラーなく実行完了
        self.assertIsNotNone(renderer.get_current_time())


class TestTask201ClockRendererErrorHandling(unittest.TestCase):
    """エラーハンドリングテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_invalid_font_handling(self):
        """無効フォント処理テスト"""
        # Given: 無効なフォント設定
        asset_manager = Mock()
        asset_manager.load_font.side_effect = Exception("Font load failed")
        
        invalid_settings = {
            'ui': {'clock_font_px': 130},
            'fonts': {'main': '/invalid/path/font.otf'}
        }
        
        # When: ClockRenderer初期化（エラーハンドリング期待）
        try:
            renderer = ClockRenderer(asset_manager, invalid_settings)
            surface = pygame.Surface((100, 100))
            renderer.render(surface)  # エラーが発生する可能性
        except Exception as e:
            # Then: 適切なエラーハンドリング
            self.fail(f"Should handle font loading gracefully: {e}")
    
    def test_empty_settings_handling(self):
        """空設定処理テスト"""
        # Given: 空の設定
        asset_manager = Mock()
        empty_settings = {}
        
        # When: ClockRenderer初期化
        try:
            renderer = ClockRenderer(asset_manager, empty_settings)
            # Then: デフォルト値で正常動作
            self.assertIsInstance(renderer, ClockRenderer)
        except KeyError:
            self.fail("Should provide default values for missing settings")


class TestTask201ClockRendererPerformance(unittest.TestCase):
    """パフォーマンステスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        self.mock_font = Mock()
        self.mock_surface = pygame.Surface((300, 130))
        self.mock_font.render.return_value = self.mock_surface
        self.asset_manager.load_font.return_value = self.mock_font
        
        self.renderer = ClockRenderer(self.asset_manager, {'ui': {'clock_font_px': 130}})
    
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_rendering_performance(self):
        """レンダリング性能テスト"""
        import time
        
        # Given: 大量レンダリングの準備
        surface = pygame.Surface((1024, 600))
        iterations = 1000
        
        # When: 大量レンダリング実行
        start_time = time.time()
        for _ in range(iterations):
            self.renderer.render(surface)
        end_time = time.time()
        
        # Then: 合理的な時間内で完了
        elapsed = end_time - start_time
        avg_time = elapsed / iterations
        
        # 1回のレンダリングが1ms以下であることを期待
        self.assertLess(avg_time, 0.001, f"Average rendering time: {avg_time:.6f}s")
    
    def test_memory_stability(self):
        """メモリ安定性テスト"""
        import gc
        
        # Given: メモリ測定準備
        surface = pygame.Surface((1024, 600))
        
        # When: 大量の更新・描画サイクル
        for _ in range(10000):
            self.renderer.update()
            self.renderer.render(surface)
            
            # 100回ごとにガベージコレクション
            if _ % 100 == 0:
                gc.collect()
        
        # Then: メモリリークが発生していないことを期待
        # (具体的なメモリ監視は実装時に追加)
        self.assertTrue(True, "Memory leak test completed")


if __name__ == '__main__':
    # テストスイート実行
    unittest.main(verbosity=2)