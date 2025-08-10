#!/usr/bin/env python3
"""
TASK-204: 背景画像レンダラー実装のテスト

TASK-204要件：
- 背景画像表示（wallpapers/から選択）
- fit/scaleモード対応
- 定期再スキャン（300秒間隔）
- アスペクト比維持・黒帯埋め
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# テスト対象のインポート（まだ存在しないため失敗する）
try:
    from src.renderers.background_image_renderer import BackgroundImageRenderer
    from src.assets.asset_manager import AssetManager
except ImportError as e:
    print(f"Expected import error during Red phase: {e}")
    # テスト実行を継続するためのダミークラス
    class BackgroundImageRenderer:
        def __init__(self, asset_manager, settings): pass
        def update(self): pass
        def render(self, surface): pass
        def get_current_image_path(self): return None
        def set_wallpaper_directory(self, path): pass
        def set_scale_mode(self, mode): pass
        def force_rescan(self): pass
        def cleanup(self): pass
    class AssetManager: pass


class TestTask204BackgroundImageRendererBasic(unittest.TestCase):
    """基本機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))  # ダミーディスプレイ
        
        # AssetManagerモック
        self.asset_manager = Mock()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        
        # テスト設定
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit',
                'rescan_sec': 300,
                'fallback_color': [0, 0, 0],
                'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'gif']
            },
            'ui': {
                'screen_width': 1024,
                'screen_height': 600
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
        # 一時ディレクトリ削除
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_image(self, filename: str, size: tuple = (100, 100)):
        """テスト用画像ファイル作成"""
        surface = pygame.Surface(size)
        surface.fill((255, 0, 0))  # 赤色
        filepath = os.path.join(self.wallpapers_dir, filename)
        pygame.image.save(surface, filepath)
        return filepath
    
    def test_background_renderer_initialization(self):
        """BackgroundImageRenderer初期化テスト"""
        # Given: AssetManagerと設定
        asset_manager = self.asset_manager
        settings = self.test_settings
        
        # When: BackgroundImageRendererを初期化
        renderer = BackgroundImageRenderer(asset_manager, settings)
        
        # Then: 正常に初期化される
        self.assertIsInstance(renderer, BackgroundImageRenderer)
        self.assertEqual(renderer.asset_manager, asset_manager)
        self.assertEqual(renderer.settings, settings)
    
    def test_settings_loading(self):
        """設定値読み込みテスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 設定値を確認
        wallpaper_dir = renderer.wallpaper_directory
        scale_mode = renderer.scale_mode
        rescan_interval = renderer.rescan_interval
        
        # Then: 設定値が正確に読み込まれる
        self.assertEqual(wallpaper_dir, self.wallpapers_dir)
        self.assertEqual(scale_mode, 'fit')
        self.assertEqual(rescan_interval, 300)
    
    def test_default_values_application(self):
        """デフォルト値適用テスト"""
        # Given: 不完全な設定
        minimal_settings = {}
        
        # When: BackgroundImageRendererを初期化
        renderer = BackgroundImageRenderer(self.asset_manager, minimal_settings)
        
        # Then: デフォルト値で正常動作
        self.assertIsInstance(renderer, BackgroundImageRenderer)
        self.assertIsNotNone(renderer.wallpaper_directory)
        self.assertIsNotNone(renderer.scale_mode)
        self.assertIsNotNone(renderer.rescan_interval)


class TestTask204ImageLoadingAndScanning(unittest.TestCase):
    """画像検索・読み込み機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))
        
        self.asset_manager = Mock()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit',
                'supported_formats': ['jpg', 'jpeg', 'png', 'bmp']
            },
            'ui': {
                'screen_width': 1024,
                'screen_height': 600
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_image(self, filename: str, size: tuple = (200, 150)):
        """テスト用画像ファイル作成"""
        surface = pygame.Surface(size)
        surface.fill((0, 255, 0))  # 緑色
        filepath = os.path.join(self.wallpapers_dir, filename)
        pygame.image.save(surface, filepath)
        return filepath
    
    def test_directory_scanning(self):
        """ディレクトリスキャンテスト"""
        # Given: 複数の画像ファイル
        self._create_test_image('image1.jpg')
        self._create_test_image('image2.png')
        self._create_test_image('image3.bmp')
        
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: ディレクトリスキャン実行
        found_images = renderer._scan_wallpaper_directory()
        
        # Then: 対応形式のファイルが検出される
        self.assertIsInstance(found_images, list)
        self.assertGreater(len(found_images), 0)
        
        # ファイル名が含まれることを確認
        image_names = [os.path.basename(path) for path in found_images]
        self.assertIn('image1.jpg', image_names)
        self.assertIn('image2.png', image_names)
        self.assertIn('image3.bmp', image_names)
    
    def test_supported_format_detection(self):
        """対応形式判定テスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 各種ファイル形式で判定
        jpg_result = renderer._is_supported_format('test.jpg')
        png_result = renderer._is_supported_format('test.PNG')  # 大文字小文字
        bmp_result = renderer._is_supported_format('test.bmp')
        unsupported_result = renderer._is_supported_format('test.tiff')
        
        # Then: 対応形式のみTrueが返される
        self.assertTrue(jpg_result)
        self.assertTrue(png_result)  # 大文字小文字不問
        self.assertTrue(bmp_result)
        self.assertFalse(unsupported_result)
    
    def test_image_selection_alphabetical(self):
        """アルファベット順画像選択テスト"""
        # Given: 複数画像をアルファベット順でない順序で作成
        self._create_test_image('zebra.jpg')
        self._create_test_image('apple.png')
        self._create_test_image('banana.bmp')
        
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 最適画像を選択
        selected_image = renderer._select_best_image()
        
        # Then: アルファベット順最初の画像が選択される
        self.assertIsNotNone(selected_image)
        self.assertTrue(selected_image.endswith('apple.png'))
    
    def test_image_loading(self):
        """画像読み込みテスト"""
        # Given: テスト画像
        image_path = self._create_test_image('test_load.jpg', (300, 200))
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 画像読み込み実行
        loaded_surface = renderer._load_and_scale_image(image_path)
        
        # Then: 正常なSurfaceオブジェクトが取得される
        self.assertIsInstance(loaded_surface, pygame.Surface)
        self.assertGreater(loaded_surface.get_width(), 0)
        self.assertGreater(loaded_surface.get_height(), 0)


class TestTask204ScalingAndRendering(unittest.TestCase):
    """スケーリング・描画機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))
        
        self.asset_manager = Mock()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        
        # テスト用画像作成
        self.test_image = self._create_test_image('test.jpg', (800, 600))
        
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit',
                'fallback_color': [0, 0, 0]
            },
            'ui': {
                'screen_width': 1024,
                'screen_height': 600
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_image(self, filename: str, size: tuple):
        """テスト用画像ファイル作成"""
        surface = pygame.Surface(size)
        surface.fill((0, 0, 255))  # 青色
        filepath = os.path.join(self.wallpapers_dir, filename)
        pygame.image.save(surface, filepath)
        return filepath
    
    def test_fit_mode_scaling(self):
        """fitモードスケーリングテスト"""
        # Given: 異なるアスペクト比の画像情報
        test_cases = [
            {'original': (1920, 1080), 'expected_fit': True},  # 横長
            {'original': (1080, 1920), 'expected_fit': True},  # 縦長
            {'original': (1000, 1000), 'expected_fit': True},  # 正方形
        ]
        
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        for case in test_cases:
            with self.subTest(original_size=case['original']):
                # When: fitモードで座標計算
                dimensions = renderer._calculate_fit_dimensions(
                    case['original'], (1024, 600)
                )
                
                # Then: アスペクト比が維持され適切な座標が返される
                self.assertIsInstance(dimensions, dict)
                self.assertIn('x', dimensions)
                self.assertIn('y', dimensions)
                self.assertIn('width', dimensions)
                self.assertIn('height', dimensions)
                
                # 画面内に収まることを確認
                self.assertGreaterEqual(dimensions['x'], 0)
                self.assertGreaterEqual(dimensions['y'], 0)
                self.assertLessEqual(dimensions['x'] + dimensions['width'], 1024)
                self.assertLessEqual(dimensions['y'] + dimensions['height'], 600)
    
    def test_scale_mode_scaling(self):
        """scaleモードスケーリングテスト"""
        # Given: 様々なサイズの画像
        test_sizes = [(800, 600), (1600, 900), (640, 480)]
        
        self.test_settings['background']['mode'] = 'scale'
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        for original_size in test_sizes:
            with self.subTest(original_size=original_size):
                # When: scaleモードで座標計算
                dimensions = renderer._calculate_scale_dimensions(
                    original_size, (1024, 600)
                )
                
                # Then: 画面サイズに正確に拡張される
                self.assertEqual(dimensions['x'], 0)
                self.assertEqual(dimensions['y'], 0)
                self.assertEqual(dimensions['width'], 1024)
                self.assertEqual(dimensions['height'], 600)
    
    def test_basic_rendering(self):
        """基本描画テスト"""
        # Given: 画像が存在する状態
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        renderer.render(surface)
        
        # Then: 描画が正常に実行される（例外が発生しない）
        # 実際の描画確認はpygameの仕様上困難だが、エラーが無いことを確認
        self.assertIsInstance(surface, pygame.Surface)
    
    def test_fallback_background_rendering(self):
        """単色背景描画テスト"""
        # Given: 画像ファイルがない状態
        empty_settings = {
            'background': {
                'dir': '/nonexistent/path',
                'mode': 'fit',
                'fallback_color': [128, 128, 128]  # グレー
            },
            'ui': {
                'screen_width': 1024,
                'screen_height': 600
            }
        }
        
        renderer = BackgroundImageRenderer(self.asset_manager, empty_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        renderer.render(surface)
        
        # Then: 単色背景が描画される（例外が発生しない）
        self.assertIsInstance(surface, pygame.Surface)


class TestTask204UpdateAndMonitoring(unittest.TestCase):
    """定期更新・監視機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit',
                'rescan_sec': 60  # 短い間隔でテスト
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_rescan_timing_check(self):
        """再スキャン判定テスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # 初回は再スキャンが必要
        initial_check = renderer._should_rescan()
        self.assertTrue(initial_check)
        
        # 初回スキャン実行
        renderer._scan_wallpaper_directory()
        
        # When: 即座に再チェック（間隔未経過）
        immediate_check = renderer._should_rescan()
        
        # Then: 間隔未経過なのでFalse
        self.assertFalse(immediate_check)
    
    @patch('time.time')
    def test_periodic_update_execution(self, mock_time):
        """定期更新実行テスト"""
        # Given: 時間制御のモック
        mock_time.side_effect = [1000, 1000, 1070]  # 70秒後
        
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 初回update()
        renderer.update()
        
        # When: 時間経過後のupdate()
        mock_time.return_value = 1070
        renderer.update()
        
        # Then: 再スキャンが実行される
        # 実装依存の詳細確認は実装後に調整
        self.assertIsInstance(renderer, BackgroundImageRenderer)
    
    def test_force_rescan(self):
        """強制再スキャンテスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: 強制再スキャン実行
        renderer.force_rescan()
        
        # Then: 即座に再スキャンが実行される
        # （実装後に具体的な動作確認を追加）
        self.assertIsInstance(renderer, BackgroundImageRenderer)


class TestTask204Configuration(unittest.TestCase):
    """設定変更・カスタマイズ機能のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        self.alt_wallpapers_dir = os.path.join(self.test_dir, 'alt_wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        os.makedirs(self.alt_wallpapers_dir, exist_ok=True)
        
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit'
            }
        }
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_directory_change(self):
        """ディレクトリ変更テスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        
        # When: ディレクトリを変更
        renderer.set_wallpaper_directory(self.alt_wallpapers_dir)
        
        # Then: 新ディレクトリが設定される
        self.assertEqual(renderer.wallpaper_directory, self.alt_wallpapers_dir)
    
    def test_scale_mode_change(self):
        """スケールモード変更テスト"""
        # Given: fitモードで初期化
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        initial_mode = renderer.scale_mode
        
        # When: scaleモードに変更
        renderer.set_scale_mode('scale')
        
        # Then: モードが変更される
        self.assertNotEqual(renderer.scale_mode, initial_mode)
        self.assertEqual(renderer.scale_mode, 'scale')


class TestTask204ErrorHandling(unittest.TestCase):
    """エラーハンドリングテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))
        
        self.asset_manager = Mock()
        
    def tearDown(self):
        """テスト後処理"""
        pygame.quit()
    
    def test_nonexistent_directory_handling(self):
        """存在しないディレクトリ処理テスト"""
        # Given: 存在しないディレクトリパス
        invalid_settings = {
            'background': {
                'dir': '/this/path/does/not/exist',
                'fallback_color': [64, 64, 64]
            }
        }
        
        # When: BackgroundImageRendererを初期化
        try:
            renderer = BackgroundImageRenderer(self.asset_manager, invalid_settings)
            # Then: 例外を投げずに初期化される
            self.assertIsInstance(renderer, BackgroundImageRenderer)
        except Exception as e:
            self.fail(f"Should handle nonexistent directory gracefully: {e}")
    
    def test_corrupted_image_skip(self):
        """破損画像スキップテスト"""
        # Given: 破損ファイルと正常ファイルが混在
        test_dir = tempfile.mkdtemp()
        try:
            wallpapers_dir = os.path.join(test_dir, 'wallpapers')
            os.makedirs(wallpapers_dir, exist_ok=True)
            
            # 破損ファイル作成（テキストファイルをJPGとして保存）
            corrupted_path = os.path.join(wallpapers_dir, 'corrupted.jpg')
            with open(corrupted_path, 'w') as f:
                f.write('This is not an image file')
            
            # 正常画像作成
            surface = pygame.Surface((100, 100))
            normal_path = os.path.join(wallpapers_dir, 'normal.jpg')
            pygame.image.save(surface, normal_path)
            
            settings = {
                'background': {
                    'dir': wallpapers_dir,
                    'mode': 'fit'
                }
            }
            
            # When: 初期化・スキャン実行
            renderer = BackgroundImageRenderer(self.asset_manager, settings)
            
            # Then: 破損ファイルをスキップし正常ファイルを選択
            self.assertIsInstance(renderer, BackgroundImageRenderer)
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_all_images_load_failure(self):
        """全画像読み込み失敗テスト"""
        # Given: 非対応形式のファイルのみ
        test_dir = tempfile.mkdtemp()
        try:
            wallpapers_dir = os.path.join(test_dir, 'wallpapers')
            os.makedirs(wallpapers_dir, exist_ok=True)
            
            # 非対応形式ファイル作成
            unsupported_path = os.path.join(wallpapers_dir, 'test.tiff')
            with open(unsupported_path, 'w') as f:
                f.write('Unsupported format')
            
            settings = {
                'background': {
                    'dir': wallpapers_dir,
                    'fallback_color': [255, 0, 0]
                }
            }
            
            # When: 初期化実行
            try:
                renderer = BackgroundImageRenderer(self.asset_manager, settings)
                # Then: 単色背景で安全に動作
                self.assertIsInstance(renderer, BackgroundImageRenderer)
            except Exception as e:
                self.fail(f"Should handle all load failures gracefully: {e}")
                
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


class TestTask204Integration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1024, 600))
        
        # 実際のAssetManagerを使用
        from src.assets.asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
        # テスト用一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.wallpapers_dir = os.path.join(self.test_dir, 'wallpapers')
        os.makedirs(self.wallpapers_dir, exist_ok=True)
        
        # テスト用画像作成
        self._create_test_image('test_integration.jpg')
        
        self.test_settings = {
            'background': {
                'dir': self.wallpapers_dir,
                'mode': 'fit',
                'rescan_sec': 300,
                'fallback_color': [0, 0, 0]
            },
            'ui': {
                'screen_width': 1024,
                'screen_height': 600
            }
        }
    
    def tearDown(self):
        """テスト後処理"""
        self.asset_manager.cleanup()
        pygame.quit()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_image(self, filename: str):
        """テスト用画像作成"""
        surface = pygame.Surface((800, 600))
        surface.fill((255, 255, 0))  # 黄色
        filepath = os.path.join(self.wallpapers_dir, filename)
        pygame.image.save(surface, filepath)
        return filepath
    
    def test_asset_manager_integration(self):
        """AssetManager統合テスト"""
        # Given: 実際のAssetManagerとBackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: レンダリング実行
        renderer.render(surface)
        
        # Then: 正常に動作する
        self.assertIsInstance(renderer, BackgroundImageRenderer)
    
    def test_full_system_workflow(self):
        """全体システムワークフローテスト"""
        # Given: BackgroundImageRenderer
        renderer = BackgroundImageRenderer(self.asset_manager, self.test_settings)
        surface = pygame.Surface((1024, 600))
        
        # When: 完全ワークフロー実行
        renderer.update()  # 更新
        renderer.render(surface)  # 描画
        
        # 設定変更テスト
        renderer.set_scale_mode('scale')
        renderer.render(surface)  # 再描画
        
        # 強制更新テスト
        renderer.force_rescan()
        renderer.render(surface)  # 再描画
        
        # Then: エラーなく実行完了
        current_path = renderer.get_current_image_path()
        self.assertIsInstance(current_path, (str, type(None)))


if __name__ == '__main__':
    # テストスイート実行
    unittest.main(verbosity=2)