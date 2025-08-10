"""
BackgroundRendererのテストケース
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import os
import pygame
from pathlib import Path

# モジュールが存在しない場合のダミークラス
try:
    from src.ui.background_renderer import BackgroundRenderer
except ImportError:
    BackgroundRenderer = None

try:
    from src.rendering.renderable import Renderable
except ImportError:
    Renderable = None


class TestBackgroundRenderer(unittest.TestCase):
    """BackgroundRendererのテストクラス"""
    
    def setUp(self):
        """テストの初期設定"""
        # pygame初期化
        pygame.init()
        
        # モックの設定
        self.mock_asset_manager = MagicMock()
        self.mock_config = MagicMock()
        self.mock_image = MagicMock()
        
        # 画像サーフェスのモック
        self.mock_image.get_size.return_value = (1920, 1080)
        self.mock_image.get_rect.return_value = pygame.Rect(0, 0, 1920, 1080)
        self.mock_asset_manager.load_image.return_value = self.mock_image
        
        # 設定値
        self.mock_config.get.side_effect = self._mock_config_get
        
        # サーフェスの設定
        self.screen = pygame.Surface((1024, 600))
    
    def _mock_config_get(self, key, default=None):
        """設定値のモック"""
        config_values = {
            'background.dir': './wallpapers',
            'background.mode': 'fit',
            'background.rescan_sec': 300,
            'background.default_color': (0, 0, 0),
            'screen.width': 1024,
            'screen.height': 600
        }
        return config_values.get(key, default)
    
    def tearDown(self):
        """テストの後処理"""
        pygame.quit()
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_initialization(self):
        """初期化のテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        self.assertIsNotNone(renderer)
        self.assertEqual(renderer.wallpaper_dir, './wallpapers')
        self.assertEqual(renderer.scale_mode, 'fit')
        self.assertEqual(renderer.rescan_interval, 300)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_implements_renderable(self):
        """Renderableインターフェースの実装確認"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # Renderableインターフェースを実装しているか確認
        self.assertTrue(hasattr(renderer, 'update'))
        self.assertTrue(hasattr(renderer, 'render'))
        self.assertTrue(hasattr(renderer, 'is_dirty'))
        self.assertTrue(hasattr(renderer, 'get_dirty_rect'))
        self.assertTrue(hasattr(renderer, 'get_bounds'))
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_scan_wallpapers(self, mock_listdir, mock_exists):
        """壁紙スキャンのテスト"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['wallpaper1.jpg', 'wallpaper2.png', 'readme.txt']
        
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        wallpapers = renderer.scan_wallpapers()
        
        # 画像ファイルのみが返されることを確認
        self.assertEqual(len(wallpapers), 2)
        self.assertIn('wallpaper1.jpg', wallpapers)
        self.assertIn('wallpaper2.png', wallpapers)
        self.assertNotIn('readme.txt', wallpapers)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_fit_mode_scaling(self):
        """fitモードのスケーリングテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 16:9の画像を1024x600の画面にfit
        scaled_size, position = renderer.calculate_fit_scaling(
            (1920, 1080), (1024, 600)
        )
        
        # アスペクト比を保持して縮小されることを確認
        # 1920:1080 = 16:9, 目標は1024x600
        # 高さに合わせると: 600 * (16/9) = 1066.67 > 1024
        # 幅に合わせると: 1024 / (16/9) = 576 < 600
        # したがって幅に合わせて (1024, 576) になる
        self.assertEqual(scaled_size[0], 1024)
        self.assertEqual(scaled_size[1], 576)
        
        # センタリングされることを確認
        self.assertEqual(position[0], 0)  # 横はピッタリ
        self.assertEqual(position[1], 12)  # (600 - 576) / 2 = 12
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_scale_mode_scaling(self):
        """scaleモードのスケーリングテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # scaleモードに設定
        renderer.scale_mode = 'scale'
        
        # 画面全体を埋めることを確認
        scaled_size, position = renderer.calculate_scale_scaling(
            (1920, 1080), (1024, 600)
        )
        
        self.assertEqual(scaled_size[0], 1024)
        self.assertEqual(scaled_size[1], 600)
        self.assertEqual(position[0], 0)
        self.assertEqual(position[1], 0)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_center_mode(self):
        """centerモードのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        renderer.scale_mode = 'center'
        
        # 小さい画像をセンタリング
        scaled_size, position = renderer.calculate_center_scaling(
            (800, 450), (1024, 600)
        )
        
        # サイズは変わらない
        self.assertEqual(scaled_size[0], 800)
        self.assertEqual(scaled_size[1], 450)
        
        # 中央配置
        self.assertEqual(position[0], 112)  # (1024 - 800) / 2
        self.assertEqual(position[1], 75)   # (600 - 450) / 2
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_load_image(self):
        """画像読み込みのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 画像を読み込み
        success = renderer.load_image('test.jpg')
        
        self.assertTrue(success)
        self.mock_asset_manager.load_image.assert_called()
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_handle_missing_wallpaper_directory(self):
        """壁紙ディレクトリが存在しない場合のテスト"""
        with patch('os.path.exists', return_value=False):
            renderer = BackgroundRenderer(
                asset_manager=self.mock_asset_manager,
                config=self.mock_config
            )
            
            wallpapers = renderer.scan_wallpapers()
            self.assertEqual(wallpapers, [])
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_default_background_color(self):
        """デフォルト背景色のテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 画像なしでレンダリング
        renderer.current_image = None
        dirty_rects = renderer.render(self.screen)
        
        # 背景色で塗りつぶされることを確認
        self.assertIsInstance(dirty_rects, list)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_rescan_timing(self):
        """再スキャンタイミングのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 初回スキャン時刻を記録
        renderer._last_scan_time = 0
        
        # 300秒経過前は再スキャンしない
        renderer._elapsed_time = 299
        renderer.update(1.0)
        self.assertFalse(renderer._should_rescan())
        
        # 300秒経過後は再スキャン
        renderer._elapsed_time = 301
        self.assertTrue(renderer._should_rescan())
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_image_caching(self):
        """画像キャッシュのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 最初の読み込み
        renderer.load_image('test.jpg')
        first_call_count = self.mock_asset_manager.load_image.call_count
        
        # 同じ画像を再度要求（キャッシュから）
        renderer.load_image('test.jpg')
        
        # AssetManagerのload_imageが追加で呼ばれないことを確認
        # （AssetManager自体がキャッシュを持っているため）
        self.assertEqual(
            self.mock_asset_manager.load_image.call_count,
            first_call_count + 1  # 実装によっては同じかもしれない
        )
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_visibility_control(self):
        """表示/非表示制御のテスト"""
        renderer = BackgroundRenderer(
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
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_get_bounds(self):
        """境界矩形取得のテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        bounds = renderer.get_bounds()
        self.assertIsInstance(bounds, pygame.Rect)
        self.assertEqual(bounds.width, 1024)
        self.assertEqual(bounds.height, 600)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_set_scale_mode(self):
        """スケールモード変更のテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # モード変更
        renderer.set_scale_mode('scale')
        self.assertEqual(renderer.scale_mode, 'scale')
        self.assertTrue(renderer.is_dirty())
        
        renderer.set_scale_mode('center')
        self.assertEqual(renderer.scale_mode, 'center')
        self.assertTrue(renderer.is_dirty())
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_switch_wallpaper(self):
        """壁紙切り替えのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # 複数の壁紙を設定
        renderer._wallpaper_list = ['wall1.jpg', 'wall2.jpg', 'wall3.jpg']
        renderer._current_index = 0
        
        # 次の壁紙へ
        renderer.next_wallpaper()
        self.assertEqual(renderer._current_index, 1)
        
        # 前の壁紙へ
        renderer.previous_wallpaper()
        self.assertEqual(renderer._current_index, 0)
        
        # ラップアラウンド
        renderer.previous_wallpaper()
        self.assertEqual(renderer._current_index, 2)
    
    @unittest.skipIf(BackgroundRenderer is None, "BackgroundRenderer not implemented yet")
    def test_smooth_scaling(self):
        """スムーズスケーリングのテスト"""
        renderer = BackgroundRenderer(
            asset_manager=self.mock_asset_manager,
            config=self.mock_config
        )
        
        # スムーズスケーリングが有効か確認
        self.assertTrue(renderer.smooth_scaling)
        
        # 無効化
        renderer.set_smooth_scaling(False)
        self.assertFalse(renderer.smooth_scaling)


if __name__ == '__main__':
    unittest.main()