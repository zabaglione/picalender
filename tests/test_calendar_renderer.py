"""
CalendarRendererのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
import calendar
import pygame
from freezegun import freeze_time

# モジュールが存在しない場合のダミークラス
try:
    from src.ui.calendar_renderer import CalendarRenderer
except ImportError:
    CalendarRenderer = None

try:
    from src.rendering.renderable import Renderable
except ImportError:
    Renderable = None


class TestCalendarRenderer(unittest.TestCase):
    """CalendarRendererのテストクラス"""
    
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
        self.mock_font.size.return_value = (20, 22)
        self.mock_asset_manager.load_font.return_value = self.mock_font
        
        # 設定値
        self.mock_config.get.side_effect = self._mock_config_get
        
        # サーフェスの設定
        self.screen = pygame.Surface((1024, 600))
    
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'ui.cal_font_px': 22,
            'ui.cal_weekday_color': (200, 200, 200),
            'ui.cal_sunday_color': (255, 128, 128),
            'ui.cal_saturday_color': (128, 128, 255),
            'ui.cal_today_bg_color': (64, 64, 128),
            'ui.cal_position': 'bottom_right',
            'ui.cal_width': 420,
            'ui.cal_height': 280,
            'ui.cal_weekday_lang': 'jp',
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }
        return config_values.get(key, default)
    
    def tearDown(self):
        """テストの後処理"""
        pygame.quit()
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertIsNotNone(renderer)
        self.assertEqual(renderer.font_size, 22)
        self.assertEqual(renderer.width, 420)
        self.assertEqual(renderer.height, 280)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_implements_renderable(self):
        """Renderableインターフェースの実装確認"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # Renderableインターフェースを実装しているか確認
        self.assertTrue(hasattr(renderer, 'update'))
        self.assertTrue(hasattr(renderer, 'render'))
        self.assertTrue(hasattr(renderer, 'is_dirty'))
        self.assertTrue(hasattr(renderer, 'get_dirty_rect'))
        self.assertTrue(hasattr(renderer, 'get_bounds'))
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    @freeze_time("2024-01-15")
    def test_get_calendar_data(self):
        """カレンダーデータ取得のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 2024年1月のカレンダーデータを取得
        cal_data = renderer.get_calendar_data(2024, 1)
        
        # 週数の確認（1月は5週または6週）
        self.assertIn(len(cal_data), [5, 6])
        
        # 各週が7日であることを確認
        for week in cal_data:
            self.assertEqual(len(week), 7)
        
        # 1月1日が月曜日であることを確認（2024年）
        # 日曜始まりなので、最初の週の月曜（インデックス1）が1日
        self.assertEqual(cal_data[0][1], 1)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_sunday_start(self):
        """日曜始まりのテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 曜日ヘッダーの確認
        headers = renderer.get_weekday_headers()
        self.assertEqual(headers[0], '日')  # 日曜が最初
        self.assertEqual(headers[6], '土')  # 土曜が最後
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_weekday_headers_japanese(self):
        """日本語曜日ヘッダーのテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        headers = renderer.get_weekday_headers()
        expected = ['日', '月', '火', '水', '木', '金', '土']
        self.assertEqual(headers, expected)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_weekday_headers_english(self):
        """英語曜日ヘッダーのテスト"""
        # 英語設定
        self.mock_config.get.side_effect = lambda k, d=None: {
            'ui.cal_font_px': 22,
            'ui.cal_weekday_color': (200, 200, 200),
            'ui.cal_sunday_color': (255, 128, 128),
            'ui.cal_saturday_color': (128, 128, 255),
            'ui.cal_today_bg_color': (64, 64, 128),
            'ui.cal_position': 'bottom_right',
            'ui.cal_width': 420,
            'ui.cal_height': 280,
            'ui.cal_weekday_lang': 'en',
            'ui.margins.x': 24,
            'ui.margins.y': 16,
            'screen.width': 1024,
            'screen.height': 600
        }.get(k, d)
        
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        headers = renderer.get_weekday_headers()
        expected = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        self.assertEqual(headers, expected)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    @freeze_time("2024-01-15")
    def test_today_highlight(self):
        """今日の日付ハイライトのテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 今日が15日であることを確認
        self.assertEqual(renderer.get_today(), 15)
        
        # is_todayメソッドのテスト
        self.assertTrue(renderer.is_today(15))
        self.assertFalse(renderer.is_today(14))
        self.assertFalse(renderer.is_today(16))
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_day_color_sunday(self):
        """日曜日の色のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 日曜日（列インデックス0）の色
        color = renderer.get_day_color(0, 15, False)  # 15日、今日ではない
        self.assertEqual(color, (255, 128, 128))  # 赤系
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_day_color_saturday(self):
        """土曜日の色のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 土曜日（列インデックス6）の色
        color = renderer.get_day_color(6, 20, False)  # 20日、今日ではない
        self.assertEqual(color, (128, 128, 255))  # 青系
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_day_color_weekday(self):
        """平日の色のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 月曜日（列インデックス1）の色
        color = renderer.get_day_color(1, 15, False)
        self.assertEqual(color, (200, 200, 200))  # 通常色
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_position_bottom_right(self):
        """右下配置のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        position = renderer.calculate_position()
        expected_x = 1024 - 420 - 24  # screen_width - cal_width - margin_x
        expected_y = 600 - 280 - 16   # screen_height - cal_height - margin_y
        
        self.assertEqual(position[0], expected_x)
        self.assertEqual(position[1], expected_y)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    @freeze_time("2024-01-31 23:59:59")
    def test_month_change_detection(self):
        """月変更の検出テスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 1月31日での初期化
        renderer.update(0.016)
        self.assertTrue(renderer.is_dirty())
        renderer.render(self.screen)
        self.assertFalse(renderer.is_dirty())
        
        # 2月1日への変更
        with freeze_time("2024-02-01 00:00:00"):
            renderer.update(1.0)
            self.assertTrue(renderer.is_dirty())  # 月が変わったのでdirty
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_cell_size_calculation(self):
        """セルサイズ計算のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        cell_width, cell_height = renderer.calculate_cell_size()
        
        # 幅: 420 / 7列 = 60
        self.assertEqual(cell_width, 60)
        
        # 高さ: (280 - ヘッダー高さ) / 6行
        # ヘッダー高さを30pxと仮定すると (280 - 30) / 6 ≈ 41.6
        self.assertGreater(cell_height, 30)
        self.assertLess(cell_height, 50)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    @freeze_time("2024-02-15")
    def test_february_calendar(self):
        """2月のカレンダーテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        cal_data = renderer.get_calendar_data(2024, 2)
        
        # 2024年はうるう年
        # 2月の日数を確認（29日まであるか）
        has_29 = False
        for week in cal_data:
            if 29 in week:
                has_29 = True
                break
        self.assertTrue(has_29)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_visibility_control(self):
        """表示/非表示制御のテスト"""
        renderer = CalendarRenderer(
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
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_get_bounds(self):
        """境界矩形取得のテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        bounds = renderer.get_bounds()
        self.assertIsInstance(bounds, pygame.Rect)
        self.assertEqual(bounds.width, 420)
        self.assertEqual(bounds.height, 280)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_caching_calendar_grid(self):
        """カレンダーグリッドのキャッシュテスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 最初のレンダリング
        renderer.update(0.016)
        renderer.render(self.screen)
        
        # renderメソッドの呼び出し回数を記録
        initial_render_calls = self.mock_font.render.call_count
        
        # 同じ月内での再レンダリング
        renderer._dirty = True
        renderer.render(self.screen)
        
        # フォントのrenderが大量に呼ばれないことを確認（キャッシュ使用）
        # 日付の数（最大31）+ ヘッダー（7）より少ないはず
        additional_calls = self.mock_font.render.call_count - initial_render_calls
        self.assertLess(additional_calls, 40)
    
    @unittest.skipIf(CalendarRenderer is None, "CalendarRenderer not implemented yet")
    def test_performance_update_frequency(self):
        """更新頻度のパフォーマンステスト"""
        renderer = CalendarRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 1時間の更新（60秒 * 60分 * 30FPS = 108000回）を短縮
        update_count = 0
        dirty_count = 0
        
        for i in range(1800):  # 1分相当
            renderer.update(0.033)  # ~33ms (30FPS)
            update_count += 1
            if renderer.is_dirty():
                dirty_count += 1
                renderer.render(self.screen)
        
        # 更新は1800回でもdirtyは2回以下（初回と日付変更時のみ）
        self.assertEqual(update_count, 1800)
        self.assertLessEqual(dirty_count, 2)


if __name__ == '__main__':
    unittest.main()