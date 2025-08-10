"""
RenderLoop のテスト
"""

import time
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Optional, List
import threading

# テスト対象（まだ存在しない - RED phase）

class TestRenderLoop(unittest.TestCase):
    """RenderLoop のテストクラス"""
    
    def setUp(self):
        """各テストの前処理"""
        # DisplayManagerのモック
        self.mock_display = MagicMock()
        self.mock_display.get_screen.return_value = MagicMock()
        self.mock_display.get_clock.return_value = MagicMock()
        self.mock_display.flip = MagicMock()
        self.mock_display.clear = MagicMock()
        
    def tearDown(self):
        """各テストの後処理"""
        # 実行中のループを停止
        try:
            if hasattr(self, 'render_loop') and self.render_loop:
                self.render_loop.stop()
        except:
            pass
    
    # === RenderLoop基本テスト ===
    
    def test_TC001_render_loop_initialization(self):
        """TC-001: RenderLoopの初期化"""
        from src.rendering.render_loop import RenderLoop, LoopState
        
        render_loop = RenderLoop(self.mock_display, target_fps=30)
        
        # 検証
        self.assertIsNotNone(render_loop)
        self.assertEqual(render_loop.target_fps, 30)
        self.assertEqual(render_loop.state, LoopState.STOPPED)
        self.assertEqual(render_loop.display_manager, self.mock_display)
    
    def test_TC002_loop_start(self):
        """TC-002: ループの開始"""
        from src.rendering.render_loop import RenderLoop, LoopState
        
        render_loop = RenderLoop(self.mock_display)
        
        # 別スレッドで開始（ブロッキングを避ける）
        thread = threading.Thread(target=render_loop.start)
        thread.daemon = True
        thread.start()
        
        # 少し待つ
        time.sleep(0.1)
        
        # 検証
        self.assertEqual(render_loop.state, LoopState.RUNNING)
        
        # 停止
        render_loop.stop()
        thread.join(timeout=1)
    
    def test_TC003_loop_stop(self):
        """TC-003: ループの停止"""
        from src.rendering.render_loop import RenderLoop, LoopState
        
        render_loop = RenderLoop(self.mock_display)
        
        # 開始と停止（短い時間で実行）
        thread = threading.Thread(target=lambda: render_loop.start(duration=0.2))
        thread.daemon = True
        thread.start()
        time.sleep(0.1)
        
        render_loop.stop()
        thread.join(timeout=1)
        
        # 検証
        self.assertEqual(render_loop.state, LoopState.STOPPED)
    
    def test_TC004_pause_and_resume(self):
        """TC-004: 一時停止と再開"""
        from src.rendering.render_loop import RenderLoop, LoopState
        
        render_loop = RenderLoop(self.mock_display)
        
        # 開始
        thread = threading.Thread(target=render_loop.start)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)
        
        # 一時停止
        render_loop.pause()
        self.assertEqual(render_loop.state, LoopState.PAUSED)
        
        # 再開
        render_loop.resume()
        self.assertEqual(render_loop.state, LoopState.RUNNING)
        
        # 停止
        render_loop.stop()
        thread.join(timeout=1)
    
    # === FPS制御テスト ===
    
    def test_TC005_target_fps_maintenance(self):
        """TC-005: 目標FPS維持"""
        from src.rendering.render_loop import RenderLoop
        
        render_loop = RenderLoop(self.mock_display, target_fps=30)
        
        # モッククロック設定
        mock_clock = MagicMock()
        mock_clock.tick.return_value = 33  # 約30FPS
        mock_clock.get_fps.return_value = 30.0
        self.mock_display.get_clock.return_value = mock_clock
        
        # 短時間実行
        thread = threading.Thread(target=lambda: render_loop.start(duration=0.5))
        thread.daemon = True
        thread.start()
        thread.join(timeout=1)
        
        # FPS確認
        fps = render_loop.get_fps()
        self.assertGreaterEqual(fps, 29)
        self.assertLessEqual(fps, 31)
    
    def test_TC006_frame_skip(self):
        """TC-006: フレームスキップ"""
        from src.rendering.render_loop import RenderLoop
        
        render_loop = RenderLoop(self.mock_display, target_fps=30)
        
        # 遅いレンダリングをシミュレート
        slow_layer = MagicMock()
        slow_layer.update.side_effect = lambda dt: time.sleep(0.05)  # 50ms遅延
        render_loop.add_layer(slow_layer)
        
        # 実行
        thread = threading.Thread(target=lambda: render_loop.start(duration=0.5))
        thread.daemon = True
        thread.start()
        thread.join(timeout=2)
        
        # フレームスキップが発生したか確認
        stats = render_loop.get_stats()
        self.assertGreater(stats['frames_skipped'], 0)
    
    def test_TC007_fps_statistics(self):
        """TC-007: FPS統計取得"""
        from src.rendering.render_loop import RenderLoop
        
        render_loop = RenderLoop(self.mock_display)
        
        # 実行
        thread = threading.Thread(target=lambda: render_loop.start(duration=0.3))
        thread.daemon = True
        thread.start()
        thread.join(timeout=1)
        
        # 統計取得
        stats = render_loop.get_stats()
        
        # 検証
        self.assertIn('current_fps', stats)
        self.assertIn('average_frame_time', stats)
        self.assertIn('frames_rendered', stats)
        self.assertIn('frames_skipped', stats)
        self.assertGreater(stats['frames_rendered'], 0)
    
    # === イベント処理テスト ===
    
    def test_TC008_event_handler_registration(self):
        """TC-008: イベントハンドラー登録"""
        from src.rendering.render_loop import RenderLoop
        import pygame
        
        render_loop = RenderLoop(self.mock_display)
        
        # ハンドラー登録
        handler = Mock()
        render_loop.add_event_handler(pygame.KEYDOWN, handler)
        
        # 検証
        self.assertIn(pygame.KEYDOWN, render_loop.event_handlers)
        self.assertIn(handler, render_loop.event_handlers[pygame.KEYDOWN])
    
    def test_TC009_event_processing(self):
        """TC-009: イベント処理"""
        from src.rendering.render_loop import RenderLoop
        import pygame
        
        render_loop = RenderLoop(self.mock_display)
        
        # ハンドラー登録
        handler = Mock()
        render_loop.add_event_handler(pygame.KEYDOWN, handler)
        
        # イベントをシミュレート
        mock_event = MagicMock()
        mock_event.type = pygame.KEYDOWN
        mock_event.key = pygame.K_SPACE
        
        with patch('pygame.event.get', return_value=[mock_event]):
            render_loop._process_events()
        
        # ハンドラーが呼ばれたか確認
        handler.assert_called_once_with(mock_event)
    
    def test_TC010_system_event_processing(self):
        """TC-010: システムイベント処理"""
        from src.rendering.render_loop import RenderLoop, LoopState
        import pygame
        
        render_loop = RenderLoop(self.mock_display)
        
        # QUITイベントをシミュレート
        mock_event = MagicMock()
        mock_event.type = pygame.QUIT
        
        # 開始
        thread = threading.Thread(target=render_loop.start)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)
        
        # QUITイベントを注入
        with patch('pygame.event.get', return_value=[mock_event]):
            render_loop._process_events()
        
        # 少し待つ
        time.sleep(0.1)
        
        # 停止したか確認
        self.assertEqual(render_loop.state, LoopState.STOPPED)
    
    # === レイヤー管理テスト ===
    
    def test_TC011_layer_add(self):
        """TC-011: レイヤー追加"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        
        render_loop = RenderLoop(self.mock_display)
        layer = Layer("test_layer")
        
        # レイヤー追加
        render_loop.add_layer(layer, priority=10)
        
        # 検証（layersはタプルのリスト）
        layers_only = [l for l, _ in render_loop.layers]
        self.assertIn(layer, layers_only)
        self.assertEqual(render_loop.get_layer_priority(layer), 10)
    
    def test_TC012_layer_remove(self):
        """TC-012: レイヤー削除"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        
        render_loop = RenderLoop(self.mock_display)
        layer = Layer("test_layer")
        
        # 追加と削除
        render_loop.add_layer(layer)
        render_loop.remove_layer(layer)
        
        # 検証
        self.assertNotIn(layer, render_loop.layers)
    
    def test_TC013_layer_priority_order(self):
        """TC-013: レイヤー優先順位"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        
        render_loop = RenderLoop(self.mock_display)
        
        # 異なる優先順位でレイヤー追加
        layer1 = Layer("layer1")
        layer2 = Layer("layer2")
        layer3 = Layer("layer3")
        
        render_loop.add_layer(layer2, priority=20)
        render_loop.add_layer(layer1, priority=10)
        render_loop.add_layer(layer3, priority=30)
        
        # 優先順位順に並んでいるか確認
        sorted_layers = render_loop.get_sorted_layers()
        self.assertEqual(sorted_layers[0], layer1)
        self.assertEqual(sorted_layers[1], layer2)
        self.assertEqual(sorted_layers[2], layer3)
    
    def test_TC014_layer_visibility(self):
        """TC-014: レイヤー表示/非表示"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        
        render_loop = RenderLoop(self.mock_display)
        layer = Layer("test_layer")
        
        # モックのrender設定
        layer.render = Mock(return_value=[])
        layer.update = Mock()
        
        render_loop.add_layer(layer)
        
        # 非表示に設定
        layer.set_visible(False)
        
        # レンダリング実行
        render_loop._render_frame()
        
        # renderが呼ばれていないことを確認
        layer.render.assert_not_called()
        
        # updateは呼ばれることを確認
        render_loop._update_frame(0.033)
        layer.update.assert_called()
    
    # === Renderableインターフェーステスト ===
    
    def test_TC015_renderable_add(self):
        """TC-015: Renderable追加"""
        from src.rendering.layer import Layer
        from src.rendering.renderable import Renderable
        
        layer = Layer("test_layer")
        
        # Renderableモック
        renderable = MagicMock(spec=Renderable)
        
        # 追加
        layer.add_renderable(renderable)
        
        # 検証
        self.assertIn(renderable, layer.renderables)
    
    def test_TC016_renderable_update(self):
        """TC-016: Renderable更新"""
        from src.rendering.layer import Layer
        from src.rendering.renderable import Renderable
        
        layer = Layer("test_layer")
        
        # Renderableモック
        renderable = MagicMock(spec=Renderable)
        layer.add_renderable(renderable)
        
        # 更新
        dt = 0.033
        layer.update(dt)
        
        # updateが呼ばれたか確認
        renderable.update.assert_called_once_with(dt)
    
    def test_TC017_renderable_render(self):
        """TC-017: Renderable描画"""
        from src.rendering.layer import Layer
        from src.rendering.renderable import Renderable
        import pygame
        
        layer = Layer("test_layer")
        surface = MagicMock(spec=pygame.Surface)
        
        # Renderableモック
        renderable = MagicMock(spec=Renderable)
        dirty_rect = pygame.Rect(10, 10, 50, 50)
        renderable.render.return_value = dirty_rect
        renderable.is_dirty.return_value = True
        
        layer.add_renderable(renderable)
        
        # 描画
        dirty_rects = layer.render(surface)
        
        # renderが呼ばれたか確認
        renderable.render.assert_called_once_with(surface)
        self.assertIn(dirty_rect, dirty_rects)
    
    # === ダーティリージョン管理テスト ===
    
    def test_TC018_dirty_region_add(self):
        """TC-018: ダーティ領域追加"""
        from src.rendering.dirty_region import DirtyRegionManager
        import pygame
        
        manager = DirtyRegionManager()
        rect = pygame.Rect(10, 10, 100, 100)
        
        # 領域追加
        manager.add_rect(rect)
        
        # 検証
        dirty_rects = manager.get_dirty_rects()
        self.assertIn(rect, dirty_rects)
    
    def test_TC019_dirty_region_union(self):
        """TC-019: ダーティ領域結合"""
        from src.rendering.dirty_region import DirtyRegionManager
        import pygame
        
        manager = DirtyRegionManager()
        
        # 重なる領域を追加
        rect1 = pygame.Rect(10, 10, 50, 50)
        rect2 = pygame.Rect(30, 30, 50, 50)
        
        manager.add_rect(rect1)
        manager.add_rect(rect2)
        
        # 結合
        union = manager.union_rects()
        
        # 検証（最小包含矩形）
        expected = pygame.Rect(10, 10, 70, 70)
        self.assertEqual(union, expected)
    
    def test_TC020_partial_update(self):
        """TC-020: 部分更新"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        import pygame
        
        render_loop = RenderLoop(self.mock_display)
        layer = Layer("test_layer")
        
        # ダーティ領域を返すモック
        dirty_rect = pygame.Rect(50, 50, 100, 100)
        layer.render = Mock(return_value=[dirty_rect])
        
        render_loop.add_layer(layer)
        
        # レンダリング
        with patch('pygame.display.update') as mock_update:
            render_loop._render_frame()
            
            # 部分更新が呼ばれたか確認
            mock_update.assert_called_with([dirty_rect])
    
    # === エラー処理テスト ===
    
    def test_TC021_rendering_error_handling(self):
        """TC-021: レンダリングエラー処理"""
        from src.rendering.render_loop import RenderLoop
        from src.rendering.layer import Layer
        
        render_loop = RenderLoop(self.mock_display)
        
        # エラーを発生させるレイヤー
        bad_layer = Layer("bad_layer")
        bad_layer.render = Mock(side_effect=Exception("Render error"))
        
        # 正常なレイヤー
        good_layer = Layer("good_layer")
        good_layer.render = Mock(return_value=[])
        
        render_loop.add_layer(bad_layer)
        render_loop.add_layer(good_layer)
        
        # レンダリング（エラーが発生してもクラッシュしない）
        render_loop._render_frame()
        
        # 正常なレイヤーは描画される
        good_layer.render.assert_called()
    
    def test_TC022_event_handler_error(self):
        """TC-022: イベントハンドラーエラー"""
        from src.rendering.render_loop import RenderLoop
        import pygame
        
        render_loop = RenderLoop(self.mock_display)
        
        # エラーを発生させるハンドラー
        bad_handler = Mock(side_effect=Exception("Handler error"))
        good_handler = Mock()
        
        render_loop.add_event_handler(pygame.KEYDOWN, bad_handler)
        render_loop.add_event_handler(pygame.KEYDOWN, good_handler)
        
        # イベント処理
        mock_event = MagicMock()
        mock_event.type = pygame.KEYDOWN
        
        with patch('pygame.event.get', return_value=[mock_event]):
            render_loop._process_events()
        
        # 正常なハンドラーは実行される
        good_handler.assert_called()
    
    def test_TC023_memory_shortage_handling(self):
        """TC-023: メモリ不足対応"""
        from src.rendering.render_loop import RenderLoop
        
        render_loop = RenderLoop(self.mock_display)
        
        # メモリ不足をシミュレート
        with patch('src.rendering.render_loop.check_memory', return_value=False):
            render_loop._handle_memory_shortage()
            
            # 品質設定が下がることを確認
            self.assertTrue(render_loop.reduced_quality)
    
    # === パフォーマンステスト ===
    
    @unittest.skip("CPU measurement is environment dependent")
    def test_TC024_cpu_usage(self):
        """TC-024: CPU使用率"""
        from src.rendering.render_loop import RenderLoop
        import psutil
        import os
        
        render_loop = RenderLoop(self.mock_display)
        
        # CPU使用率測定開始
        process = psutil.Process(os.getpid())
        cpu_before = process.cpu_percent(interval=0.1)
        
        # 実行
        thread = threading.Thread(target=lambda: render_loop.start(duration=2))
        thread.daemon = True
        thread.start()
        thread.join(timeout=3)
        
        # CPU使用率測定
        cpu_after = process.cpu_percent(interval=0.1)
        
        # 30%未満であることを確認（CI環境では緩い制限）
        self.assertLess(cpu_after, 50)  # CI環境用に緩めに設定
    
    def test_TC025_memory_usage(self):
        """TC-025: メモリ使用量"""
        from src.rendering.render_loop import RenderLoop
        import psutil
        import os
        
        # 初期メモリ使用量
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        render_loop = RenderLoop(self.mock_display)
        
        # レイヤー追加
        from src.rendering.layer import Layer
        for i in range(5):
            layer = Layer(f"layer_{i}")
            render_loop.add_layer(layer)
        
        # メモリ使用量測定
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        # 50MB以内の増加であることを確認
        self.assertLess(mem_increase, 50)
    
    @unittest.skip("Long running test - run manually")
    def test_TC026_long_running_stability(self):
        """TC-026: 長時間動作"""
        from src.rendering.render_loop import RenderLoop
        
        render_loop = RenderLoop(self.mock_display)
        
        # 1分間実行（本番は1時間）
        thread = threading.Thread(target=lambda: render_loop.start(duration=60))
        thread.daemon = True
        thread.start()
        thread.join(timeout=65)
        
        # 統計確認
        stats = render_loop.get_stats()
        
        # エラーがないことを確認
        self.assertEqual(stats.get('errors', 0), 0)
        # FPSが安定していることを確認
        self.assertGreater(stats['average_fps'], 25)


class TestLayer(unittest.TestCase):
    """Layer のテストクラス"""
    
    def test_layer_initialization(self):
        """レイヤーの初期化"""
        from src.rendering.layer import Layer
        
        layer = Layer("test_layer")
        
        self.assertEqual(layer.name, "test_layer")
        self.assertTrue(layer.is_visible())
        self.assertEqual(len(layer.renderables), 0)
    
    def test_layer_renderable_management(self):
        """レンダラブル管理"""
        from src.rendering.layer import Layer
        from src.rendering.renderable import Renderable
        
        layer = Layer("test_layer")
        renderable = MagicMock(spec=Renderable)
        
        # 追加
        layer.add_renderable(renderable)
        self.assertIn(renderable, layer.renderables)
        
        # 削除
        layer.remove_renderable(renderable)
        self.assertNotIn(renderable, layer.renderables)


class TestDirtyRegionManager(unittest.TestCase):
    """DirtyRegionManager のテストクラス"""
    
    def test_dirty_region_management(self):
        """ダーティリージョン管理"""
        from src.rendering.dirty_region import DirtyRegionManager
        import pygame
        
        manager = DirtyRegionManager()
        
        # 初期状態
        self.assertEqual(len(manager.get_dirty_rects()), 0)
        
        # 領域追加
        rect1 = pygame.Rect(0, 0, 100, 100)
        manager.add_rect(rect1)
        self.assertEqual(len(manager.get_dirty_rects()), 1)
        
        # クリア
        manager.clear()
        self.assertEqual(len(manager.get_dirty_rects()), 0)


if __name__ == '__main__':
    # psutilのインポート（パフォーマンステスト用）
    try:
        import psutil
    except ImportError:
        print("Warning: psutil not installed. Performance tests will be skipped.")
    
    unittest.main()