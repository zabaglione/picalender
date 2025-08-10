"""
メインレンダリングループ
"""

import time
import threading
from enum import Enum
from typing import Dict, List, Any, Callable, Optional, Tuple
import pygame

from src.display import DisplayManager
from .layer import Layer
from .dirty_region import DirtyRegionManager


class LoopState(Enum):
    """ループの状態"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class RenderLoop:
    """メインレンダリングループクラス"""
    
    def __init__(self, display_manager: DisplayManager, target_fps: int = 30):
        """
        初期化
        
        Args:
            display_manager: ディスプレイ管理オブジェクト
            target_fps: 目標FPS
        """
        self.display_manager = display_manager
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps  # 秒単位
        
        # 状態管理
        self.state = LoopState.STOPPED
        self._state_lock = threading.Lock()
        
        # レイヤー管理
        self.layers: List[Tuple[Layer, int]] = []  # (layer, priority)
        self._layers_lock = threading.Lock()
        
        # イベントハンドラー
        self.event_handlers: Dict[int, List[Callable]] = {}
        
        # 統計情報
        self.stats = {
            'frames_rendered': 0,
            'frames_skipped': 0,
            'total_time': 0.0,
            'errors': 0,
            'current_fps': 0.0,
            'average_fps': 0.0,
            'average_frame_time': 0.0
        }
        
        # パフォーマンス制御
        self.reduced_quality = False
        self._fps_history = []
        self._frame_times = []
        
        # ダーティリージョン管理
        self.dirty_manager = DirtyRegionManager()
    
    def start(self, duration: Optional[float] = None) -> None:
        """
        レンダリングループを開始
        
        Args:
            duration: 実行時間（秒）。Noneの場合は無限ループ
        """
        with self._state_lock:
            if self.state != LoopState.STOPPED:
                return
            self.state = LoopState.RUNNING
        
        start_time = time.time()
        last_frame_time = start_time
        
        clock = self.display_manager.get_clock()
        
        while True:
            # 状態チェック
            with self._state_lock:
                if self.state == LoopState.STOPPING:
                    self.state = LoopState.STOPPED
                    break
                elif self.state == LoopState.PAUSED:
                    time.sleep(0.01)
                    continue
            
            # 時間制限チェック
            if duration and (time.time() - start_time) >= duration:
                break
            
            # フレーム開始時刻
            frame_start = time.time()
            
            # デルタタイム計算
            current_time = time.time()
            dt = current_time - last_frame_time
            last_frame_time = current_time
            
            # イベント処理
            self._process_events()
            
            # 更新処理
            self._update_frame(dt)
            
            # フレームスキップ判定
            if time.time() - frame_start < self.frame_time * 1.5:
                # レンダリング
                self._render_frame()
                self.stats['frames_rendered'] += 1
            else:
                # フレームスキップ
                self.stats['frames_skipped'] += 1
            
            # FPS制御
            if clock:
                clock.tick(self.target_fps)
            else:
                # 手動でFPS制御
                elapsed = time.time() - frame_start
                if elapsed < self.frame_time:
                    time.sleep(self.frame_time - elapsed)
            
            # 統計更新
            self._update_stats(frame_start)
        
        # 終了処理
        self._cleanup()
    
    def stop(self) -> None:
        """レンダリングループを停止"""
        with self._state_lock:
            if self.state == LoopState.RUNNING or self.state == LoopState.PAUSED:
                self.state = LoopState.STOPPING
    
    def pause(self) -> None:
        """一時停止"""
        with self._state_lock:
            if self.state == LoopState.RUNNING:
                self.state = LoopState.PAUSED
    
    def resume(self) -> None:
        """再開"""
        with self._state_lock:
            if self.state == LoopState.PAUSED:
                self.state = LoopState.RUNNING
    
    def add_layer(self, layer: Layer, priority: int = 0) -> None:
        """
        レイヤーを追加
        
        Args:
            layer: 追加するレイヤー
            priority: 優先順位（小さいほど背面）
        """
        with self._layers_lock:
            self.layers.append((layer, priority))
            # 優先順位でソート
            self.layers.sort(key=lambda x: x[1])
    
    def remove_layer(self, layer: Layer) -> None:
        """
        レイヤーを削除
        
        Args:
            layer: 削除するレイヤー
        """
        with self._layers_lock:
            self.layers = [(l, p) for l, p in self.layers if l != layer]
    
    def get_layer_priority(self, layer: Layer) -> Optional[int]:
        """
        レイヤーの優先順位を取得
        
        Args:
            layer: レイヤー
            
        Returns:
            優先順位、存在しない場合はNone
        """
        with self._layers_lock:
            for l, priority in self.layers:
                if l == layer:
                    return priority
        return None
    
    def get_sorted_layers(self) -> List[Layer]:
        """
        優先順位順にソートされたレイヤーリストを取得
        
        Returns:
            レイヤーのリスト
        """
        with self._layers_lock:
            return [layer for layer, _ in self.layers]
    
    def add_event_handler(self, event_type: int, handler: Callable) -> None:
        """
        イベントハンドラーを登録
        
        Args:
            event_type: イベントタイプ（pygame.KEYDOWN等）
            handler: ハンドラー関数
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        if handler not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: int, handler: Callable) -> None:
        """
        イベントハンドラーを削除
        
        Args:
            event_type: イベントタイプ
            handler: ハンドラー関数
        """
        if event_type in self.event_handlers:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
    
    def get_fps(self) -> float:
        """
        現在のFPSを取得
        
        Returns:
            現在のFPS
        """
        return self.stats['current_fps']
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return self.stats.copy()
    
    def _process_events(self) -> None:
        """イベント処理"""
        # pygameが初期化されていない場合はスキップ
        if not pygame.get_init():
            return
            
        for event in pygame.event.get():
            # システムイベント処理
            if event.type == pygame.QUIT:
                self.stop()
                return
            
            # 登録されたハンドラーを実行
            if event.type in self.event_handlers:
                for handler in self.event_handlers[event.type]:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"Error in event handler: {e}")
                        self.stats['errors'] += 1
    
    def _update_frame(self, dt: float) -> None:
        """
        フレーム更新処理
        
        Args:
            dt: デルタタイム（秒）
        """
        with self._layers_lock:
            for layer, _ in self.layers:
                try:
                    layer.update(dt)
                except Exception as e:
                    print(f"Error updating layer {layer.name}: {e}")
                    self.stats['errors'] += 1
    
    def _render_frame(self) -> None:
        """フレーム描画処理"""
        # pygameが初期化されていない場合はスキップ
        if not pygame.get_init():
            return
            
        screen = self.display_manager.get_screen()
        self.dirty_manager.clear()
        
        # レイヤーを描画
        with self._layers_lock:
            for layer, _ in self.layers:
                if not layer.is_visible():
                    continue
                
                try:
                    dirty_rects = layer.render(screen)
                    for rect in dirty_rects:
                        self.dirty_manager.add_rect(rect)
                except Exception as e:
                    print(f"Error rendering layer {layer.name}: {e}")
                    self.stats['errors'] += 1
        
        # 画面更新
        dirty_rects = self.dirty_manager.get_dirty_rects()
        if dirty_rects:
            # 部分更新
            pygame.display.update(dirty_rects)
        else:
            # 全画面更新（フォールバック）
            self.display_manager.flip()
    
    def _update_stats(self, frame_start: float) -> None:
        """
        統計情報を更新
        
        Args:
            frame_start: フレーム開始時刻
        """
        frame_time = time.time() - frame_start
        self._frame_times.append(frame_time)
        
        # 最新100フレームのみ保持
        if len(self._frame_times) > 100:
            self._frame_times.pop(0)
        
        # FPS計算
        if frame_time > 0:
            instant_fps = 1.0 / frame_time
            self._fps_history.append(instant_fps)
            
            if len(self._fps_history) > 100:
                self._fps_history.pop(0)
            
            self.stats['current_fps'] = instant_fps
            self.stats['average_fps'] = sum(self._fps_history) / len(self._fps_history)
        
        # 平均フレーム時間
        if self._frame_times:
            self.stats['average_frame_time'] = sum(self._frame_times) / len(self._frame_times)
        
        # 総時間
        self.stats['total_time'] += frame_time
    
    def _cleanup(self) -> None:
        """終了処理"""
        # レイヤーのクリア
        with self._layers_lock:
            self.layers.clear()
        
        # イベントハンドラーのクリア
        self.event_handlers.clear()
        
        # ダーティリージョンのクリア
        self.dirty_manager.clear()
    
    def _handle_memory_shortage(self) -> None:
        """メモリ不足時の処理"""
        # 品質を下げる
        self.reduced_quality = True
        print("Warning: Memory shortage detected, reducing quality")
        
        # 不要なリソースを解放
        import gc
        gc.collect()


def check_memory() -> bool:
    """
    メモリ使用状況をチェック
    
    Returns:
        メモリが十分な場合True
    """
    try:
        import psutil
        process = psutil.Process()
        memory_percent = process.memory_percent()
        return memory_percent < 80  # 80%未満なら十分
    except ImportError:
        # psutilがない場合は常にTrue
        return True