"""
ClockRendererのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, time
import pygame
from freezegun import freeze_time

# モジュールが存在しない場合のダミークラス
try:
    from src.ui.clock_renderer import ClockRenderer
except ImportError:
    ClockRenderer = None

try:
    from src.rendering.renderable import Renderable
except ImportError:
    Renderable = None


class TestClockRenderer(unittest.TestCase):
    """ClockRendererのテストクラス"""
    
    def setUp(self):
        """テストの初期設定"""
        # pygame初期化
        pygame.init()
        pygame.font.init()
        
        # モックの設定
        self.mock_asset_manager = MagicMock()
        self.mock_config = MagicMock()
        self.mock_font = MagicMock()
        self.mock_surface = MagicMock()
        
        # フォント関連の設定
        self.mock_font.render.return_value = self.mock_surface
        self.mock_font.size.return_value = (300, 130)
        self.mock_asset_manager.load_font.return_value = self.mock_font
        
        # 設定値
        self.mock_config.get.side_effect = self._mock_config_get
        
        # サーフェスの設定
        self.screen = pygame.Surface((1024, 600))
    
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'ui.clock_font_px': 130,
            'ui.clock_color': (255, 255, 255),
            'ui.clock_position': 'top_center',
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }
        return config_values.get(key, default)
    
    def tearDown(self):
        """テストの後処理"""
        pygame.quit()
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertIsNotNone(renderer)
        self.assertEqual(renderer.font_size, 130)
        self.assertEqual(renderer.color, (255, 255, 255))
        self.assertEqual(renderer.position, 'top_center')
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_implements_renderable(self):
        """Renderableインターフェースの実装確認"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # Renderableインターフェースを実装しているか確認
        self.assertTrue(hasattr(renderer, 'update'))
        self.assertTrue(hasattr(renderer, 'render'))
        self.assertTrue(hasattr(renderer, 'is_dirty'))
        self.assertTrue(hasattr(renderer, 'get_dirty_rect'))
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_font_loading(self):
        """フォント読み込みのテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # フォントが読み込まれているか確認
        self.mock_asset_manager.load_font.assert_called()
        call_args = self.mock_asset_manager.load_font.call_args
        self.assertEqual(call_args[0][1], 130)  # フォントサイズ
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    @freeze_time("2024-01-15 12:34:56")
    def test_time_formatting(self):
        """時刻フォーマットのテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 現在時刻の取得
        current_time = renderer.get_current_time()
        self.assertEqual(current_time, "12:34:56")
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    @freeze_time("2024-01-15 09:05:03")
    def test_time_formatting_padding(self):
        """時刻フォーマットのパディングテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # ゼロパディングの確認
        current_time = renderer.get_current_time()
        self.assertEqual(current_time, "09:05:03")
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    @freeze_time("2024-01-15 12:34:56")
    def test_update_marks_dirty_on_time_change(self):
        """時刻変更時のdirtyフラグのテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 初期状態
        renderer.update(0.016)  # 16ms
        self.assertTrue(renderer.is_dirty())
        
        # renderでクリア
        renderer.render(self.screen)
        self.assertFalse(renderer.is_dirty())
        
        # 同じ秒内の更新
        renderer.update(0.5)  # 500ms
        self.assertFalse(renderer.is_dirty())
        
        # 次の秒への更新
        with freeze_time("2024-01-15 12:34:57"):
            renderer.update(0.5)
            self.assertTrue(renderer.is_dirty())
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_render_calls_font_render(self):
        """レンダリング時のフォント描画呼び出しテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        renderer.update(0.016)
        dirty_rects = renderer.render(self.screen)
        
        # フォントのrenderが呼ばれているか確認
        self.mock_font.render.assert_called()
        call_args = self.mock_font.render.call_args
        self.assertTrue(call_args[0][1])  # antialias = True
        self.assertEqual(call_args[0][2], (255, 255, 255))  # color
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_position_top_center(self):
        """上部中央配置のテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # テキストサイズの設定
        self.mock_font.size.return_value = (300, 130)
        
        # 位置計算の確認
        position = renderer.calculate_position()
        expected_x = (1024 - 300) // 2  # 中央配置
        expected_y = 16  # 上部マージン
        
        self.assertEqual(position[0], expected_x)
        self.assertEqual(position[1], expected_y)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_render_returns_dirty_rect(self):
        """dirtyレクトの返却テスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        renderer.update(0.016)
        dirty_rects = renderer.render(self.screen)
        
        # dirtyレクトが返されているか確認
        self.assertIsInstance(dirty_rects, list)
        if dirty_rects:
            self.assertIsInstance(dirty_rects[0], pygame.Rect)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_caching_rendered_text(self):
        """レンダリング済みテキストのキャッシュテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 最初のレンダリング
        renderer.update(0.016)
        renderer.render(self.screen)
        first_call_count = self.mock_font.render.call_count
        
        # 同じ時刻での再レンダリング（キャッシュ使用）
        renderer._dirty = True  # 強制的にdirtyにする
        renderer.render(self.screen)
        
        # フォントのrenderが再度呼ばれないことを確認
        self.assertEqual(self.mock_font.render.call_count, first_call_count)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_custom_color_configuration(self):
        """カスタムカラー設定のテスト"""
        # カスタムカラーの設定
        self.mock_config.get.side_effect = lambda k, d=None: {
            'ui.clock_font_px': 130,
            'ui.clock_color': (255, 0, 0),  # 赤色
            'ui.clock_position': 'top_center',
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }.get(k, d)
        
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertEqual(renderer.color, (255, 0, 0))
        
        # レンダリング時の色確認
        renderer.update(0.016)
        renderer.render(self.screen)
        
        call_args = self.mock_font.render.call_args
        self.assertEqual(call_args[0][2], (255, 0, 0))
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_custom_font_size(self):
        """カスタムフォントサイズのテスト"""
        # カスタムサイズの設定
        self.mock_config.get.side_effect = lambda k, d=None: {
            'ui.clock_font_px': 200,  # 大きめのフォント
            'ui.clock_color': (255, 255, 255),
            'ui.clock_position': 'top_center',
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }.get(k, d)
        
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertEqual(renderer.font_size, 200)
        
        # フォント読み込み時のサイズ確認
        call_args = self.mock_asset_manager.load_font.call_args
        self.assertEqual(call_args[0][1], 200)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_visibility_control(self):
        """表示/非表示制御のテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # デフォルトは表示
        self.assertTrue(renderer.visible)
        
        # 非表示に設定
        renderer.set_visible(False)
        self.assertFalse(renderer.visible)
        
        # 非表示時はrenderが何も返さない
        renderer.update(0.016)
        dirty_rects = renderer.render(self.screen)
        self.assertEqual(dirty_rects, [])
        
        # 表示に戻す
        renderer.set_visible(True)
        self.assertTrue(renderer.visible)
        dirty_rects = renderer.render(self.screen)
        self.assertNotEqual(dirty_rects, [])
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_get_dirty_rect(self):
        """dirtyレクト取得のテスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # dirtyレクトの取得
        rect = renderer.get_dirty_rect()
        
        if rect:
            self.assertIsInstance(rect, pygame.Rect)
            self.assertGreater(rect.width, 0)
            self.assertGreater(rect.height, 0)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_handle_font_load_failure(self):
        """フォント読み込み失敗時のハンドリング"""
        # フォント読み込み失敗をシミュレート
        self.mock_asset_manager.load_font.return_value = None
        
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # エラーでクラッシュしないことを確認
        renderer.update(0.016)
        dirty_rects = renderer.render(self.screen)
        # 結果は空またはエラー表示
        self.assertIsInstance(dirty_rects, list)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    @freeze_time("2024-01-15 23:59:59")
    def test_midnight_transition(self):
        """日付変更時の動作テスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 23:59:59の表示
        renderer.update(0.016)
        time1 = renderer.get_current_time()
        self.assertEqual(time1, "23:59:59")
        
        # 00:00:00への遷移
        with freeze_time("2024-01-16 00:00:00"):
            renderer.update(1.0)
            time2 = renderer.get_current_time()
            self.assertEqual(time2, "00:00:00")
            self.assertTrue(renderer.is_dirty())
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_performance_update_frequency(self):
        """更新頻度のパフォーマンステスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 1秒間に60回更新（60FPS）
        update_count = 0
        dirty_count = 0
        
        for i in range(60):
            renderer.update(0.016667)  # ~16.67ms
            update_count += 1
            if renderer.is_dirty():
                dirty_count += 1
                renderer.render(self.screen)
        
        # 更新は60回でもdirtyは1-2回程度であるべき
        self.assertEqual(update_count, 60)
        self.assertLessEqual(dirty_count, 2)
    
    @unittest.skipIf(ClockRenderer is None, "ClockRenderer not implemented yet")
    def test_memory_leak_prevention(self):
        """メモリリークの防止テスト"""
        renderer = ClockRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 大量の更新とレンダリング
        for _ in range(1000):
            renderer.update(0.001)
            if renderer.is_dirty():
                renderer.render(self.screen)
        
        # キャッシュサイズの確認（無限に増えないこと）
        if hasattr(renderer, '_text_cache'):
            # キャッシュが適切に管理されているか
            self.assertLessEqual(len(renderer._text_cache), 60)  # 最大60秒分


if __name__ == '__main__':
    unittest.main()