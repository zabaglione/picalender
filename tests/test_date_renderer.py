"""
DateRendererのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
import pygame
from freezegun import freeze_time

# モジュールが存在しない場合のダミークラス
try:
    from src.ui.date_renderer import DateRenderer
except ImportError:
    DateRenderer = None

try:
    from src.rendering.renderable import Renderable
except ImportError:
    Renderable = None


class TestDateRenderer(unittest.TestCase):
    """DateRendererのテストクラス"""
    
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
        self.mock_font.size.return_value = (250, 36)
        self.mock_asset_manager.load_font.return_value = self.mock_font
        
        # 設定値
        self.mock_config.get.side_effect = self._mock_config_get
        
        # サーフェスの設定
        self.screen = pygame.Surface((1024, 600))
    
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'ui.date_font_px': 36,
            'ui.date_color': (255, 255, 255),
            'ui.date_position': 'below_clock',
            'ui.date_weekday_lang': 'jp',
            'ui.clock_font_px': 130,
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }
        return config_values.get(key, default)
    
    def tearDown(self):
        """テストの後処理"""
        pygame.quit()
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertIsNotNone(renderer)
        self.assertEqual(renderer.font_size, 36)
        self.assertEqual(renderer.color, (255, 255, 255))
        self.assertEqual(renderer.weekday_lang, 'jp')
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_implements_renderable(self):
        """Renderableインターフェースの実装確認"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # Renderableインターフェースを実装しているか確認
        self.assertTrue(hasattr(renderer, 'update'))
        self.assertTrue(hasattr(renderer, 'render'))
        self.assertTrue(hasattr(renderer, 'is_dirty'))
        self.assertTrue(hasattr(renderer, 'get_dirty_rect'))
        self.assertTrue(hasattr(renderer, 'get_bounds'))
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-01-15 12:34:56")
    def test_date_formatting_japanese(self):
        """日本語曜日フォーマットのテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 月曜日の確認
        date_str = renderer.get_current_date()
        self.assertEqual(date_str, "2024-01-15 (月)")
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-01-20 12:34:56")
    def test_date_formatting_saturday_japanese(self):
        """土曜日の日本語表示テスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 土曜日の確認
        date_str = renderer.get_current_date()
        self.assertEqual(date_str, "2024-01-20 (土)")
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-01-21 12:34:56")
    def test_date_formatting_sunday_japanese(self):
        """日曜日の日本語表示テスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 日曜日の確認
        date_str = renderer.get_current_date()
        self.assertEqual(date_str, "2024-01-21 (日)")
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-01-15 12:34:56")
    def test_date_formatting_english(self):
        """英語曜日フォーマットのテスト"""
        # 英語設定
        self.mock_config.get.side_effect = lambda k, d=None: {
            'ui.date_font_px': 36,
            'ui.date_color': (255, 255, 255),
            'ui.date_position': 'below_clock',
            'ui.date_weekday_lang': 'en',
            'ui.clock_font_px': 130,
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }.get(k, d)
        
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 月曜日の確認（英語）
        date_str = renderer.get_current_date()
        self.assertEqual(date_str, "2024-01-15 (Mon)")
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-01-15 23:59:59")
    def test_update_marks_dirty_on_date_change(self):
        """日付変更時のdirtyフラグのテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 初期状態
        renderer.update(0.016)
        self.assertTrue(renderer.is_dirty())
        
        # renderでクリア
        renderer.render(self.screen)
        self.assertFalse(renderer.is_dirty())
        
        # 同じ日の更新
        renderer.update(0.5)
        self.assertFalse(renderer.is_dirty())
        
        # 次の日への更新（日付変更）
        with freeze_time("2024-01-16 00:00:00"):
            renderer.update(1.0)
            self.assertTrue(renderer.is_dirty())
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_position_below_clock(self):
        """時計の下配置のテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # テキストサイズの設定
        self.mock_font.size.return_value = (250, 36)
        
        # 位置計算の確認
        position = renderer.calculate_position()
        expected_x = (1024 - 250) // 2  # 中央配置
        # 時計の高さ(130px) + マージン(16px) + 間隔
        expected_y = 16 + 130 + 10
        
        self.assertEqual(position[0], expected_x)
        self.assertGreaterEqual(position[1], expected_y)
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_caching_rendered_text(self):
        """レンダリング済みテキストのキャッシュテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 最初のレンダリング
        renderer.update(0.016)
        renderer.render(self.screen)
        first_call_count = self.mock_font.render.call_count
        
        # 同じ日付での再レンダリング（キャッシュ使用）
        renderer._dirty = True  # 強制的にdirtyにする
        renderer.render(self.screen)
        
        # フォントのrenderが再度呼ばれないことを確認
        self.assertEqual(self.mock_font.render.call_count, first_call_count)
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_weekday_colors(self):
        """曜日による色分けのテスト"""
        # 日曜日のテスト（赤系の色）
        with freeze_time("2024-01-21"):  # 日曜日
            renderer = DateRenderer(
                asset_manager=self.mock_asset_manager,
                config=self.mock_config
            )
            renderer.update(0.016)
            
            # get_weekday_colorメソッドがある場合
            if hasattr(renderer, 'get_weekday_color'):
                color = renderer.get_weekday_color(6)  # 日曜日
                self.assertGreater(color[0], color[1])  # 赤成分が大きい
                self.assertGreater(color[0], color[2])
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_custom_color_configuration(self):
        """カスタムカラー設定のテスト"""
        # カスタムカラーの設定
        self.mock_config.get.side_effect = lambda k, d=None: {
            'ui.date_font_px': 36,
            'ui.date_color': (0, 255, 0),  # 緑色
            'ui.date_position': 'below_clock',
            'ui.date_weekday_lang': 'jp',
            'ui.clock_font_px': 130,
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }.get(k, d)
        
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertEqual(renderer.color, (0, 255, 0))
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_visibility_control(self):
        """表示/非表示制御のテスト"""
        renderer = DateRenderer(
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
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_get_bounds(self):
        """境界矩形取得のテスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        bounds = renderer.get_bounds()
        self.assertIsInstance(bounds, pygame.Rect)
        self.assertGreater(bounds.width, 0)
        self.assertGreater(bounds.height, 0)
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_handle_font_load_failure(self):
        """フォント読み込み失敗時のハンドリング"""
        # フォント読み込み失敗をシミュレート
        self.mock_asset_manager.load_font.return_value = None
        
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # エラーでクラッシュしないことを確認
        renderer.update(0.016)
        dirty_rects = renderer.render(self.screen)
        self.assertIsInstance(dirty_rects, list)
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_performance_update_frequency(self):
        """更新頻度のパフォーマンステスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 1分間の更新（60秒 * 60FPS = 3600回）
        update_count = 0
        dirty_count = 0
        
        for i in range(3600):
            renderer.update(0.016667)  # ~16.67ms
            update_count += 1
            if renderer.is_dirty():
                dirty_count += 1
                renderer.render(self.screen)
        
        # 更新は3600回でもdirtyは1回程度であるべき（日付が変わらない限り）
        self.assertEqual(update_count, 3600)
        self.assertLessEqual(dirty_count, 2)
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    @freeze_time("2024-02-29 12:00:00")
    def test_leap_year_handling(self):
        """うるう年の処理テスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 2月29日の表示
        date_str = renderer.get_current_date()
        self.assertEqual(date_str, "2024-02-29 (木)")
    
    @unittest.skipIf(DateRenderer is None, "DateRenderer not implemented yet")
    def test_set_weekday_language(self):
        """曜日言語の動的変更テスト"""
        renderer = DateRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 日本語から英語に変更
        renderer.set_weekday_language('en')
        self.assertEqual(renderer.weekday_lang, 'en')
        self.assertTrue(renderer.is_dirty())
        
        # 英語から日本語に変更
        renderer.set_weekday_language('jp')
        self.assertEqual(renderer.weekday_lang, 'jp')
        self.assertTrue(renderer.is_dirty())


if __name__ == '__main__':
    unittest.main()