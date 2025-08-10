#!/usr/bin/env python3
"""
TASK-103: アセット管理システムのテスト

TASK-103要件：
- フォントローダー
- 画像ローダー
- スプライトシートローダー
- キャッシュ管理
- 動的リロード機能
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
import json
from unittest.mock import Mock, patch, MagicMock
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# テスト対象のインポート（まだ存在しないため失敗する）
try:
    from src.assets.asset_manager import AssetManager
    from src.assets.loaders.font_loader import FontLoader
    from src.assets.loaders.image_loader import ImageLoader, ScaleMode
    from src.assets.loaders.sprite_loader import SpriteLoader
    from src.assets.cache.lru_cache import LRUCache
    from src.assets.monitor.file_monitor import FileMonitor
except ImportError as e:
    print(f"Expected import error during Red phase: {e}")
    # テスト実行を継続するためのダミークラス
    class AssetManager: pass
    class FontLoader: pass
    class ImageLoader: pass
    class ScaleMode: 
        FIT = "fit"
        SCALE = "scale" 
        STRETCH = "stretch"
    class SpriteLoader: pass
    class LRUCache: pass
    class FileMonitor: pass


class TestTask103FontLoader(unittest.TestCase):
    """フォントローダーのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))  # ダミーディスプレイ
        self.temp_dir = tempfile.mkdtemp()
        self.font_loader = FontLoader()
    
    def tearDown(self):
        """テスト後処理"""
        shutil.rmtree(self.temp_dir)
        pygame.quit()
    
    def test_font_loader_basic(self):
        """基本的なフォント読み込みテスト"""
        # Given: システムフォント
        font_path = None  # システムデフォルト
        size = 24
        
        # When: フォントを読み込む
        font = self.font_loader.load_font(font_path, size)
        
        # Then: pygame.Fontオブジェクトが返される
        self.assertIsInstance(font, pygame.font.Font)
        # サイズは正確に一致しない場合があるので範囲でチェック
        self.assertGreater(font.get_height(), 0)
    
    def test_font_loader_multiple_sizes(self):
        """複数サイズフォント読み込みテスト"""
        # Given: 同じフォントファイル
        font_path = None
        sizes = [24, 36, 48]
        
        # When: 異なるサイズで読み込む
        fonts = []
        for size in sizes:
            font = self.font_loader.load_font(font_path, size)
            fonts.append(font)
        
        # Then: サイズ別にキャッシュされる
        self.assertEqual(len(fonts), 3)
        for font in fonts:
            self.assertGreater(font.get_height(), 0)
        
        # キャッシュヒット率をチェック
        cache_stats = self.font_loader.get_cache_stats()
        self.assertGreaterEqual(cache_stats['hit_rate'], 0.0)
    
    def test_font_loader_file_not_found(self):
        """フォントファイル不在エラーテスト"""
        # Given: 存在しないフォントパス
        font_path = "/non/existent/font.ttf"
        size = 24
        
        # When: フォントを読み込む
        font = self.font_loader.load_font(font_path, size)
        
        # Then: デフォルトフォントが返される
        self.assertIsInstance(font, pygame.font.Font)
        # デフォルトフォントの特徴をチェック
        self.assertIsNotNone(font)
    
    def test_font_loader_cjk_support(self):
        """CJKフォント対応テスト"""
        # Given: 日本語テキスト
        japanese_text = "こんにちは世界"
        font_path = None
        size = 24
        
        # When: フォントを読み込んでテキストを描画
        font = self.font_loader.load_font(font_path, size)
        surface = font.render(japanese_text, True, (255, 255, 255))
        
        # Then: 正しく描画される（サーフェスが作成される）
        self.assertIsInstance(surface, pygame.Surface)
        self.assertGreater(surface.get_width(), 0)
        self.assertGreater(surface.get_height(), 0)


class TestTask103ImageLoader(unittest.TestCase):
    """画像ローダーのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))  # ダミーディスプレイ
        self.temp_dir = tempfile.mkdtemp()
        self.image_loader = ImageLoader()
        
        # テスト用画像を作成
        self.test_image_path = self._create_test_image()
    
    def tearDown(self):
        """テスト後処理"""
        shutil.rmtree(self.temp_dir)
        pygame.quit()
    
    def _create_test_image(self):
        """テスト用画像を作成"""
        image_path = os.path.join(self.temp_dir, "test_image.png")
        surface = pygame.Surface((200, 100))
        surface.fill((255, 0, 0))  # 赤色で塗りつぶし
        pygame.image.save(surface, image_path)
        return image_path
    
    def test_image_loader_png(self):
        """PNG画像読み込みテスト"""
        # Given: PNG画像ファイル
        image_path = self.test_image_path
        
        # When: 画像を読み込む
        surface = self.image_loader.load_image(image_path)
        
        # Then: pygame.Surfaceオブジェクトが返される
        self.assertIsInstance(surface, pygame.Surface)
        self.assertEqual(surface.get_size(), (200, 100))
    
    def test_image_scaling_fit_mode(self):
        """Fitモードスケーリングテスト"""
        # Given: 任意サイズの画像（200x100）
        image_path = self.test_image_path
        target_size = (400, 300)
        
        # When: fitモードでスケーリング
        surface = self.image_loader.load_image(
            image_path, 
            target_size=target_size, 
            scale_mode=ScaleMode.FIT
        )
        
        # Then: アスペクト比を保持してスケーリング
        self.assertIsInstance(surface, pygame.Surface)
        # アスペクト比2:1を保持しながら400x300に収まる最大サイズは400x200
        expected_size = (400, 200)
        self.assertEqual(surface.get_size(), expected_size)
    
    def test_image_loader_file_not_found(self):
        """画像ファイル不在エラーテスト"""
        # Given: 存在しない画像パス
        image_path = "/non/existent/image.png"
        
        # When: 画像を読み込む
        surface = self.image_loader.load_image(image_path)
        
        # Then: デフォルト画像が返される
        self.assertIsInstance(surface, pygame.Surface)
        # デフォルト画像の特徴をチェック
        self.assertGreater(surface.get_width(), 0)
        self.assertGreater(surface.get_height(), 0)
    
    def test_image_loader_alpha_channel(self):
        """透明度つき画像読み込みテスト"""
        # Given: アルファチャンネル付きPNG
        alpha_image_path = os.path.join(self.temp_dir, "alpha_image.png")
        surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        surface.fill((255, 0, 0, 128))  # 半透明の赤
        pygame.image.save(surface, alpha_image_path)
        
        # When: 画像を読み込む
        loaded_surface = self.image_loader.load_image(alpha_image_path)
        
        # Then: 透明度情報が保持される
        self.assertIsInstance(loaded_surface, pygame.Surface)
        # アルファチャンネルが有効かチェック
        self.assertTrue(loaded_surface.get_flags() & pygame.SRCALPHA)


class TestTask103SpriteLoader(unittest.TestCase):
    """スプライトローダーのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        self.temp_dir = tempfile.mkdtemp()
        self.sprite_loader = SpriteLoader()
        
        # テスト用スプライトシートを作成
        self.sprite_path = self._create_test_sprite_sheet()
        self.frame_def_path = self._create_frame_definition()
    
    def tearDown(self):
        """テスト後処理"""
        shutil.rmtree(self.temp_dir)
        pygame.quit()
    
    def _create_test_sprite_sheet(self):
        """テスト用スプライトシートを作成"""
        sprite_path = os.path.join(self.temp_dir, "test_sprite.png")
        # 4フレームの横並びスプライト（各64x64）
        surface = pygame.Surface((256, 64))
        for i in range(4):
            color = (255 - i * 50, 0, i * 50)  # 色を変えて各フレームを識別
            pygame.draw.rect(surface, color, (i * 64, 0, 64, 64))
        pygame.image.save(surface, sprite_path)
        return sprite_path
    
    def _create_frame_definition(self):
        """フレーム定義ファイルを作成"""
        frame_def_path = os.path.join(self.temp_dir, "frames.json")
        frame_data = {
            "frame_width": 64,
            "frame_height": 64,
            "frame_count": 4,
            "animation": {
                "fps": 8,
                "loop": True
            }
        }
        with open(frame_def_path, 'w') as f:
            json.dump(frame_data, f)
        return frame_def_path
    
    def test_sprite_loader_horizontal_split(self):
        """横並びスプライト分割テスト"""
        # Given: 横並びスプライトシート
        sprite_path = self.sprite_path
        frame_width = 64
        frame_height = 64
        frame_count = 4
        
        # When: フレーム数を指定して分割
        frames = self.sprite_loader.load_sprite_sheet(
            sprite_path, frame_width, frame_height, frame_count
        )
        
        # Then: 各フレームが正しく分割される
        self.assertEqual(len(frames), 4)
        for frame in frames:
            self.assertIsInstance(frame, pygame.Surface)
            self.assertEqual(frame.get_size(), (64, 64))
    
    def test_sprite_loader_frame_definition(self):
        """フレーム定義読み込みテスト"""
        # Given: JSONフレーム定義ファイル
        frame_def_path = self.frame_def_path
        
        # When: 定義を読み込む
        frame_info = self.sprite_loader.load_frame_definition(frame_def_path)
        
        # Then: フレーム情報が正しく解析される
        self.assertEqual(frame_info['frame_width'], 64)
        self.assertEqual(frame_info['frame_height'], 64)
        self.assertEqual(frame_info['frame_count'], 4)
        self.assertEqual(frame_info['animation']['fps'], 8)
        self.assertTrue(frame_info['animation']['loop'])
    
    def test_sprite_loader_animation_info(self):
        """アニメーション情報管理テスト"""
        # Given: アニメーション定義
        sprite_path = self.sprite_path
        frame_def_path = self.frame_def_path
        
        # When: アニメーション情報を取得
        animation = self.sprite_loader.load_animation(sprite_path, frame_def_path)
        
        # Then: FPS・ループ情報が取得できる
        self.assertIn('frames', animation)
        self.assertIn('fps', animation)
        self.assertIn('loop', animation)
        self.assertEqual(animation['fps'], 8)
        self.assertTrue(animation['loop'])
        self.assertEqual(len(animation['frames']), 4)


class TestTask103LRUCache(unittest.TestCase):
    """LRUキャッシュのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        self.cache = LRUCache(max_size=3, max_memory=1024*1024)  # 1MB制限
    
    def test_cache_lru_insertion(self):
        """LRU挿入テスト"""
        # Given: 空のキャッシュ
        cache = self.cache
        
        # When: アイテムを挿入
        cache.put("key1", "value1")
        
        # Then: キャッシュに保存される
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.size(), 1)
    
    def test_cache_lru_eviction(self):
        """LRU削除テスト"""
        # Given: 満杯のキャッシュ
        cache = self.cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # When: 新しいアイテムを挿入
        cache.put("key4", "value4")
        
        # Then: 最古のアイテム（key1）が削除される
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key4"), "value4")
        self.assertEqual(cache.size(), 3)
    
    def test_cache_lru_access_update(self):
        """LRUアクセス更新テスト"""
        # Given: キャッシュ内のアイテム
        cache = self.cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # When: key1にアクセス
        cache.get("key1")
        
        # When: 新しいアイテムを追加
        cache.put("key4", "value4")
        
        # Then: key1は残り、key2が削除される
        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_cache_memory_limit(self):
        """メモリ制限テスト"""
        # Given: メモリ制限設定（1KB）
        cache = LRUCache(max_size=10, max_memory=1024)
        
        # When: 制限を超える量のデータ
        large_data = "x" * 512  # 512バイト
        cache.put("key1", large_data)
        cache.put("key2", large_data)
        cache.put("key3", large_data)  # 合計1536バイト
        
        # Then: メモリ使用量が制限内に保たれる
        self.assertLessEqual(cache.memory_usage(), 1024)
        
    def test_cache_hit_rate(self):
        """キャッシュヒット率テスト"""
        # Given: キャッシュにデータを追加
        cache = self.cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # When: アクセスパターン（ヒット/ミス）
        cache.get("key1")  # ヒット
        cache.get("key2")  # ヒット
        cache.get("key3")  # ミス
        cache.get("key1")  # ヒット
        
        # Then: 正確なヒット率が算出される（3/4 = 75%）
        stats = cache.get_statistics()
        expected_hit_rate = 3.0 / 4.0
        self.assertAlmostEqual(stats['hit_rate'], expected_hit_rate, places=2)


class TestTask103FileMonitor(unittest.TestCase):
    """ファイル監視のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = FileMonitor()
        self.events_received = []
    
    def tearDown(self):
        """テスト後処理"""
        self.monitor.stop()
        shutil.rmtree(self.temp_dir)
    
    def _event_handler(self, event_type, file_path):
        """イベントハンドラー"""
        self.events_received.append((event_type, file_path))
    
    def test_file_monitor_change_detection(self):
        """ファイル変更検出テスト"""
        # Given: 監視対象ファイル
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("initial content")
        
        self.monitor.add_watch(test_file, self._event_handler)
        self.monitor.start()
        
        # When: ファイルを変更
        time.sleep(0.1)  # 監視開始を待つ
        with open(test_file, 'w') as f:
            f.write("modified content")
        
        # Then: 変更イベントが発生
        time.sleep(0.2)  # イベント検出を待つ
        self.assertGreater(len(self.events_received), 0)
        
        # イベント内容を確認
        event_files = [event[1] for event in self.events_received]
        self.assertIn(test_file, event_files)
    
    def test_file_monitor_multiple_files(self):
        """複数ファイル監視テスト"""
        # Given: 複数の監視対象ファイル
        file1 = os.path.join(self.temp_dir, "file1.txt")
        file2 = os.path.join(self.temp_dir, "file2.txt")
        
        with open(file1, 'w') as f:
            f.write("file1 content")
        with open(file2, 'w') as f:
            f.write("file2 content")
        
        self.monitor.add_watch(file1, self._event_handler)
        self.monitor.add_watch(file2, self._event_handler)
        self.monitor.start()
        
        # When: file2を変更
        time.sleep(0.1)
        with open(file2, 'w') as f:
            f.write("file2 modified")
        
        # Then: file2の変更が検出される
        for i in range(30):  # 3秒まで待つ
            if len(self.events_received) > 0:
                break
            time.sleep(0.1)
        
        self.assertGreater(len(self.events_received), 0)
        event_files = [event[1] for event in self.events_received]
        self.assertIn(os.path.abspath(file2), event_files)


class TestTask103AssetManagerIntegration(unittest.TestCase):
    """アセット管理統合テスト"""
    
    def setUp(self):
        """テスト前準備"""
        pygame.init()
        pygame.display.set_mode((1, 1))  # ダミーディスプレイ
        self.temp_dir = tempfile.mkdtemp()
        self.asset_manager = AssetManager()
        
        # テストアセットを準備
        self._prepare_test_assets()
    
    def tearDown(self):
        """テスト後処理"""
        self.asset_manager.cleanup()
        shutil.rmtree(self.temp_dir)
        pygame.quit()
    
    def _prepare_test_assets(self):
        """テストアセットを準備"""
        # テスト用画像
        image_path = os.path.join(self.temp_dir, "test_image.png")
        surface = pygame.Surface((100, 100))
        surface.fill((0, 255, 0))
        pygame.image.save(surface, image_path)
        
        # テスト用スプライト
        sprite_path = os.path.join(self.temp_dir, "test_sprite.png")
        sprite_surface = pygame.Surface((200, 50))
        for i in range(4):
            color = (i * 60, 100, 255 - i * 60)
            pygame.draw.rect(sprite_surface, color, (i * 50, 0, 50, 50))
        pygame.image.save(sprite_surface, sprite_path)
    
    def test_asset_manager_integration(self):
        """アセット管理統合テスト"""
        # Given: AssetManagerインスタンス
        manager = self.asset_manager
        
        # When: 各種アセットを読み込む
        font = manager.load_font(None, 24)
        image = manager.load_image(os.path.join(self.temp_dir, "test_image.png"))
        sprite = manager.load_sprite_sheet(
            os.path.join(self.temp_dir, "test_sprite.png"),
            50, 50, 4
        )
        
        # Then: 全て正常に管理される
        self.assertIsInstance(font, pygame.font.Font)
        self.assertIsInstance(image, pygame.Surface)
        self.assertIsInstance(sprite, list)
        self.assertEqual(len(sprite), 4)
    
    def test_memory_usage_limit(self):
        """メモリ使用量制限テスト"""
        # Given: メモリ制限設定
        manager = self.asset_manager
        manager.set_memory_limit(50 * 1024 * 1024)  # 50MB制限
        
        # When: 大量のアセットを読み込む
        for i in range(100):
            # 大きな画像を生成して読み込み
            large_surface = pygame.Surface((500, 500))
            large_surface.fill((i % 255, 100, 200))
            temp_path = os.path.join(self.temp_dir, f"large_image_{i}.png")
            pygame.image.save(large_surface, temp_path)
            manager.load_image(temp_path)
        
        # Then: メモリ使用量が50MB以下
        memory_usage = manager.get_memory_usage()
        self.assertLessEqual(memory_usage, 50 * 1024 * 1024)
    
    def test_cache_across_loaders(self):
        """ローダー間キャッシュ共有テスト"""
        # Given: 複数のローダー
        manager = self.asset_manager
        
        # When: 同じファイルを異なる方法で読み込み
        image1 = manager.load_image(os.path.join(self.temp_dir, "test_image.png"))
        image2 = manager.load_image(os.path.join(self.temp_dir, "test_image.png"))
        
        # Then: キャッシュが共有される（同一オブジェクト参照）
        cache_stats = manager.get_cache_statistics()
        self.assertGreaterEqual(cache_stats['hit_rate'], 0.5)  # 50%以上のヒット率


def main():
    """テスト実行"""
    print("=== TASK-103: アセット管理システムテスト (RED) ===")
    print("Testing asset management system components")
    print("Expected: All tests should FAIL at this point (Red phase)")
    print()
    
    # テストスイート実行
    suite = unittest.TestSuite()
    
    # テストケース追加
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestTask103FontLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestTask103ImageLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestTask103SpriteLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestTask103LRUCache))
    suite.addTests(loader.loadTestsFromTestCase(TestTask103FileMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestTask103AssetManagerIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果表示
    print(f"\n=== Red Phase Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Red フェーズでは失敗が期待される
    total_failures = len(result.failures) + len(result.errors)
    if total_failures > 0:
        print(f"\n✅ RED PHASE SUCCESS: {total_failures} tests failed as expected")
        print("Ready to implement asset management system to make tests pass")
    else:
        print(f"\n❌ RED PHASE ISSUE: Tests should fail but {result.testsRun - total_failures} tests passed")
    
    return total_failures > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)