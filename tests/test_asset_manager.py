"""
AssetManager のテスト
"""

import os
import json
import time
import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from typing import Tuple
import tempfile
import shutil

# テスト対象（まだ存在しない - RED phase）

class TestAssetManager(unittest.TestCase):
    """AssetManager のテストクラス"""
    
    def setUp(self):
        """各テストの前処理"""
        # テスト用の一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.assets_dir = os.path.join(self.test_dir, "assets")
        os.makedirs(os.path.join(self.assets_dir, "fonts"), exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "sprites"), exist_ok=True)
        
        # ダミーファイル作成
        self._create_dummy_files()
    
    def tearDown(self):
        """各テストの後処理"""
        # 一時ディレクトリ削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_dummy_files(self):
        """ダミーファイルを作成"""
        # ダミーフォントファイル（実際には空ファイル）
        with open(os.path.join(self.assets_dir, "fonts", "test.ttf"), "wb") as f:
            f.write(b"DUMMY_FONT")
        
        # ダミー画像ファイル（最小のPNGヘッダー）
        png_header = b'\x89PNG\r\n\x1a\n'
        with open(os.path.join(self.assets_dir, "images", "test.png"), "wb") as f:
            f.write(png_header)
        
        # マニフェストファイル
        manifest = {
            "fonts": {
                "test": {
                    "path": "fonts/test.ttf",
                    "sizes": [16, 24, 32]
                }
            },
            "images": {
                "test": "images/test.png"
            }
        }
        with open(os.path.join(self.assets_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
    
    # === AssetManager基本テスト ===
    
    def test_TC001_asset_manager_initialization(self):
        """TC-001: AssetManagerの初期化"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir)
        
        # 検証
        self.assertIsNotNone(manager)
        self.assertEqual(manager.base_path, self.assets_dir)
        self.assertIsNotNone(manager.font_manager)
        self.assertIsNotNone(manager.image_loader)
        self.assertIsNotNone(manager.cache)
    
    def test_TC002_asset_preload(self):
        """TC-002: アセットの事前読み込み"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir)
        
        # マニフェスト読み込み
        with open(os.path.join(self.assets_dir, "manifest.json")) as f:
            manifest = json.load(f)
        
        manager.preload(manifest)
        
        # 検証（実際のファイル読み込みはモックが必要）
        self.assertTrue(True)  # 実装後に詳細な検証を追加
    
    # === フォント管理テスト ===
    
    @patch('pygame.font.Font')
    def test_TC003_font_loading(self, mock_font):
        """TC-003: フォント読み込み"""
        from src.assets.asset_manager import AssetManager
        
        mock_font_instance = MagicMock()
        mock_font.return_value = mock_font_instance
        
        manager = AssetManager(self.assets_dir)
        font = manager.load_font("test", 24)
        
        # 検証
        self.assertIsNotNone(font)
        self.assertEqual(font, mock_font_instance)
    
    @patch('pygame.font.Font')
    def test_TC004_japanese_font_support(self, mock_font):
        """TC-004: 日本語フォント対応"""
        from src.assets.font_manager import FontManager
        import pygame
        
        # pygame.Surfaceのモック
        mock_surface = MagicMock()
        mock_font_instance = MagicMock()
        mock_font_instance.render.return_value = mock_surface
        mock_font.return_value = mock_font_instance
        
        font_manager = FontManager(self.assets_dir)
        font = font_manager.load("fonts/test.ttf", 24)
        
        # 日本語テキストレンダリング
        surface = font_manager.render_text(font, "こんにちは", (255, 255, 255))
        
        # 検証
        self.assertIsNotNone(surface)
        mock_font_instance.render.assert_called()
    
    @patch('pygame.font.SysFont')
    def test_TC005_system_font_fallback(self, mock_sysfont):
        """TC-005: システムフォントフォールバック"""
        from src.assets.font_manager import FontManager
        
        mock_sysfont.return_value = MagicMock()
        
        font_manager = FontManager(self.assets_dir)
        
        # 存在しないフォントを読み込み
        font = font_manager.load("nonexistent.ttf", 24)
        
        # システムフォントが使用されることを確認
        self.assertIsNotNone(font)
        mock_sysfont.assert_called()
    
    def test_TC006_multiple_size_management(self):
        """TC-006: 複数サイズ管理"""
        from src.assets.asset_manager import AssetManager
        
        with patch('pygame.font.Font') as mock_font:
            mock_font.return_value = MagicMock()
            
            manager = AssetManager(self.assets_dir)
            
            # 異なるサイズで読み込み
            font16 = manager.load_font("test", 16)
            font24 = manager.load_font("test", 24)
            font32 = manager.load_font("test", 32)
            
            # 検証
            self.assertIsNotNone(font16)
            self.assertIsNotNone(font24)
            self.assertIsNotNone(font32)
            # キャッシュから取得される
            font16_2 = manager.load_font("test", 16)
            self.assertEqual(font16, font16_2)
    
    # === 画像管理テスト ===
    
    @patch('pygame.image.load')
    def test_TC007_png_image_loading(self, mock_load):
        """TC-007: PNG画像読み込み"""
        from src.assets.asset_manager import AssetManager
        
        mock_surface = MagicMock()
        mock_surface.convert_alpha.return_value = mock_surface
        mock_load.return_value = mock_surface
        
        manager = AssetManager(self.assets_dir)
        image = manager.load_image("images/test.png")
        
        # 検証
        self.assertIsNotNone(image)
        mock_surface.convert_alpha.assert_called()
    
    @patch('pygame.image.load')
    def test_TC008_jpg_image_loading(self, mock_load):
        """TC-008: JPG画像読み込み"""
        from src.assets.image_loader import ImageLoader
        
        mock_surface = MagicMock()
        mock_surface.convert.return_value = mock_surface
        mock_load.return_value = mock_surface
        
        loader = ImageLoader(self.assets_dir)
        image = loader.load("test.jpg", alpha=False)
        
        # 検証
        self.assertIsNotNone(image)
    
    def test_TC009_image_scaling(self):
        """TC-009: 画像スケーリング"""
        from src.assets.image_loader import ImageLoader
        import pygame
        
        # モックサーフェス
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_scaled = MagicMock(spec=pygame.Surface)
        mock_surface.get_size.return_value = (100, 100)
        
        with patch('pygame.transform.scale', return_value=mock_scaled):
            loader = ImageLoader(self.assets_dir)
            scaled = loader.scale(mock_surface, (200, 200))
            
            # 検証
            self.assertEqual(scaled, mock_scaled)
    
    def test_TC010_image_rotation_flip(self):
        """TC-010: 画像回転・反転"""
        from src.assets.image_loader import ImageLoader
        import pygame
        
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_rotated = MagicMock(spec=pygame.Surface)
        mock_flipped = MagicMock(spec=pygame.Surface)
        
        loader = ImageLoader(self.assets_dir)
        
        with patch('pygame.transform.rotate', return_value=mock_rotated):
            rotated = loader.rotate(mock_surface, 90)
            self.assertEqual(rotated, mock_rotated)
        
        with patch('pygame.transform.flip', return_value=mock_flipped):
            flipped = loader.flip(mock_surface, True, False)
            self.assertEqual(flipped, mock_flipped)
    
    # === スプライトシートテスト ===
    
    def test_TC011_sprite_sheet_loading(self):
        """TC-011: スプライトシート読み込み"""
        from src.assets.asset_manager import AssetManager
        import pygame
        
        with patch('pygame.image.load') as mock_load:
            mock_surface = MagicMock(spec=pygame.Surface)
            mock_surface.get_size.return_value = (512, 128)
            mock_load.return_value = mock_surface
            
            manager = AssetManager(self.assets_dir)
            sprite_sheet = manager.load_sprite_sheet("sprites/test.png", (128, 128))
            
            # 検証
            self.assertIsNotNone(sprite_sheet)
            self.assertEqual(sprite_sheet.frame_size, (128, 128))
            self.assertEqual(sprite_sheet.frame_count, 4)
    
    def test_TC012_frame_extraction(self):
        """TC-012: フレーム分割"""
        from src.assets.sprite_sheet import SpriteSheet
        import pygame
        
        # モックサーフェス（512x128）
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_surface.get_size.return_value = (512, 128)
        mock_surface.subsurface.return_value = MagicMock(spec=pygame.Surface)
        
        sheet = SpriteSheet(mock_surface, (128, 128))
        frame = sheet.get_frame(0)
        
        # 検証
        self.assertIsNotNone(frame)
        mock_surface.subsurface.assert_called_with(pygame.Rect(0, 0, 128, 128))
    
    def test_TC013_animation_extraction(self):
        """TC-013: アニメーション取得"""
        from src.assets.sprite_sheet import SpriteSheet
        import pygame
        
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_surface.get_size.return_value = (512, 128)
        mock_frame = MagicMock(spec=pygame.Surface)
        mock_surface.subsurface.return_value = mock_frame
        
        sheet = SpriteSheet(mock_surface, (128, 128))
        animation = sheet.get_animation(0, 3)
        
        # 検証
        self.assertIsInstance(animation, list)
        self.assertEqual(len(animation), 4)
    
    def test_TC014_metadata_support(self):
        """TC-014: メタデータサポート"""
        from src.assets.sprite_sheet import SpriteSheet
        
        metadata = {
            "animations": {
                "idle": [0, 3],
                "walk": [4, 7]
            }
        }
        
        mock_surface = MagicMock()
        mock_surface.get_size.return_value = (1024, 128)
        
        sheet = SpriteSheet(mock_surface, (128, 128), metadata=metadata)
        
        # 検証
        self.assertIn("idle", sheet.animations)
        self.assertEqual(sheet.animations["idle"], [0, 3])
    
    # === キャッシュ管理テスト ===
    
    def test_TC015_cache_addition(self):
        """TC-015: キャッシュ追加"""
        from src.assets.asset_cache import AssetCache
        
        cache = AssetCache(max_size=3)
        cache.put("key1", "value1")
        
        # 検証
        self.assertEqual(cache.get("key1"), "value1")
    
    def test_TC016_lru_algorithm(self):
        """TC-016: LRUアルゴリズム"""
        from src.assets.asset_cache import AssetCache
        
        cache = AssetCache(max_size=3)
        
        # キャッシュを満杯にする
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # key1にアクセス（最近使用）
        cache.get("key1")
        
        # 新しいアイテム追加（key2が削除されるはず）
        cache.put("key4", "value4")
        
        # 検証
        self.assertIsNotNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        self.assertIsNotNone(cache.get("key3"))
        self.assertIsNotNone(cache.get("key4"))
    
    def test_TC017_cache_hit_rate(self):
        """TC-017: キャッシュヒット率"""
        from src.assets.asset_cache import AssetCache
        
        cache = AssetCache()
        cache.put("key1", "value1")
        
        # アクセスパターン
        cache.get("key1")  # ヒット
        cache.get("key1")  # ヒット
        cache.get("key2")  # ミス
        
        stats = cache.get_stats()
        
        # 検証
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 0.667, places=2)
    
    def test_TC018_manual_purge(self):
        """TC-018: 手動パージ"""
        from src.assets.asset_cache import AssetCache
        
        cache = AssetCache()
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        cache.clear()
        
        # 検証
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        stats = cache.get_stats()
        self.assertEqual(stats["size"], 0)
    
    # === 動的リロードテスト ===
    
    def test_TC019_file_change_detection(self):
        """TC-019: ファイル変更検出"""
        from src.assets.file_watcher import FileWatcher
        
        # テストファイル作成
        test_file = os.path.join(self.test_dir, "watch_test.txt")
        with open(test_file, "w") as f:
            f.write("initial")
        
        watcher = FileWatcher([test_file])
        watcher.start()
        
        # ファイル変更
        time.sleep(0.1)
        with open(test_file, "w") as f:
            f.write("modified")
        
        time.sleep(0.5)
        changes = watcher.check_changes()
        watcher.stop()
        
        # 検証
        self.assertIn(test_file, changes)
    
    def test_TC020_hot_reload(self):
        """TC-020: ホットリロード"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir, dev_mode=True)
        
        # 最初の読み込み
        with patch('pygame.image.load') as mock_load:
            mock_load.return_value = MagicMock()
            image1 = manager.load_image("images/test.png")
        
        # ファイル変更をシミュレート
        manager._trigger_reload("images/test.png")
        
        # 再読み込み確認
        with patch('pygame.image.load') as mock_load:
            mock_load.return_value = MagicMock()
            image2 = manager.load_image("images/test.png")
        
        # 検証（キャッシュが更新されている）
        self.assertIsNotNone(image2)
    
    def test_TC021_callback_execution(self):
        """TC-021: コールバック実行"""
        from src.assets.file_watcher import FileWatcher
        
        callback_called = False
        callback_args = None
        
        def callback(path):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = path
        
        test_file = os.path.join(self.test_dir, "callback_test.txt")
        with open(test_file, "w") as f:
            f.write("initial")
        
        watcher = FileWatcher([test_file])
        watcher.add_callback(callback)
        watcher.start()
        
        # ファイル変更
        time.sleep(0.1)
        with open(test_file, "w") as f:
            f.write("modified")
        
        time.sleep(0.5)
        watcher.check_changes()
        watcher.stop()
        
        # 検証
        self.assertTrue(callback_called)
        self.assertEqual(callback_args, test_file)
    
    # === パス管理テスト ===
    
    def test_TC022_relative_path_resolution(self):
        """TC-022: 相対パス解決"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir)
        
        # 相対パスを絶対パスに変換
        abs_path = manager._resolve_path("fonts/test.ttf")
        
        # 検証
        self.assertTrue(os.path.isabs(abs_path))
        self.assertTrue(abs_path.endswith("fonts/test.ttf"))
    
    def test_TC023_absolute_path_handling(self):
        """TC-023: 絶対パス処理"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir)
        
        # 絶対パス
        abs_path = "/absolute/path/to/file.png"
        resolved = manager._resolve_path(abs_path)
        
        # 検証
        self.assertEqual(resolved, abs_path)
    
    # === エラー処理テスト ===
    
    def test_TC024_file_not_found_error(self):
        """TC-024: ファイル不在エラー"""
        from src.assets.asset_manager import AssetManager
        
        manager = AssetManager(self.assets_dir)
        
        # 存在しないファイル
        with patch('src.assets.asset_manager.logger') as mock_logger:
            result = manager.load_image("nonexistent.png")
            
            # 検証
            self.assertIsNone(result)
            mock_logger.error.assert_called()
    
    def test_TC025_corrupted_file_handling(self):
        """TC-025: 破損ファイル処理"""
        from src.assets.asset_manager import AssetManager
        
        # 破損ファイル作成
        corrupted_file = os.path.join(self.assets_dir, "images", "corrupted.png")
        with open(corrupted_file, "wb") as f:
            f.write(b"CORRUPTED_DATA")
        
        manager = AssetManager(self.assets_dir)
        
        with patch('src.assets.asset_manager.logger') as mock_logger:
            result = manager.load_image("images/corrupted.png")
            
            # 検証
            self.assertIsNone(result)
            mock_logger.error.assert_called()
    
    def test_TC026_memory_shortage_handling(self):
        """TC-026: メモリ不足対応"""
        from src.assets.asset_cache import AssetCache
        
        cache = AssetCache(max_size=2)
        
        # キャッシュを満杯にする
        cache.put("key1", "large_data_1")
        cache.put("key2", "large_data_2")
        
        # メモリ制限に達した状態で新規追加
        cache.put("key3", "large_data_3")
        
        # 検証（自動パージ）
        stats = cache.get_stats()
        self.assertLessEqual(stats["size"], 2)


class TestFontManager(unittest.TestCase):
    """FontManager のテストクラス"""
    
    def test_font_manager_initialization(self):
        """FontManagerの初期化"""
        from src.assets.font_manager import FontManager
        
        manager = FontManager("assets")
        
        self.assertIsNotNone(manager)
        self.assertEqual(manager.base_path, "assets")


class TestImageLoader(unittest.TestCase):
    """ImageLoader のテストクラス"""
    
    def test_image_loader_initialization(self):
        """ImageLoaderの初期化"""
        from src.assets.image_loader import ImageLoader
        
        loader = ImageLoader("assets")
        
        self.assertIsNotNone(loader)
        self.assertEqual(loader.base_path, "assets")


class TestSpriteSheet(unittest.TestCase):
    """SpriteSheet のテストクラス"""
    
    def test_sprite_sheet_initialization(self):
        """SpriteSheetの初期化"""
        from src.assets.sprite_sheet import SpriteSheet
        import pygame
        
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_surface.get_size.return_value = (512, 128)
        
        sheet = SpriteSheet(mock_surface, (128, 128))
        
        self.assertIsNotNone(sheet)
        self.assertEqual(sheet.frame_size, (128, 128))
        self.assertEqual(sheet.frame_count, 4)


if __name__ == '__main__':
    unittest.main()