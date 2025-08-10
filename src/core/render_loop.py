"""
レンダリングループ管理モジュール

TASK-102: レンダリングループ実装
- メインループ構造
- FPS制御（30fps）
- イベント処理
- ダーティリージョン管理
- レイヤー合成
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Callable
from enum import Enum
import logging

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed. Please run: pip install pygame")
    exit(1)

from src.core import ConfigManager, LogManager
from src.display.display_manager import DisplayManager


class RenderLayer(Enum):
    """レンダリングレイヤー"""
    BACKGROUND = 0      # 背景画像
    UI_BASE = 10        # UI基本要素（時計、日付）
    UI_CONTENT = 20     # コンテンツ（カレンダー、天気）
    CHARACTERS = 30     # 2Dキャラクター
    UI_OVERLAY = 40     # オーバーレイ（デバッグ情報など）


class RenderComponent(ABC):
    """レンダリング可能コンポーネントの基底クラス"""
    
    def __init__(self, layer: RenderLayer, name: str):
        """
        初期化
        
        Args:
            layer: レンダリング層
            name: コンポーネント名
        """
        self.layer = layer
        self.name = name
        self.enabled = True
        self.dirty = True  # 再描画が必要か
        self.last_render_time = 0.0
        self.cache_surface: Optional[pygame.Surface] = None
        
    @abstractmethod
    def update(self, dt: float, context: Dict[str, Any]) -> bool:
        """
        コンポーネントを更新
        
        Args:
            dt: フレーム時間（秒）
            context: レンダリングコンテキスト
            
        Returns:
            再描画が必要な場合True
        """
        pass
    
    @abstractmethod
    def render(self, screen: pygame.Surface, context: Dict[str, Any]) -> Optional[pygame.Rect]:
        """
        コンポーネントを描画
        
        Args:
            screen: 描画対象サーフェス
            context: レンダリングコンテキスト
            
        Returns:
            更新された矩形領域（ダーティリージョン用）
        """
        pass
    
    def set_dirty(self, dirty: bool = True):
        """ダーティフラグを設定"""
        self.dirty = dirty
    
    def is_dirty(self) -> bool:
        """ダーティ状態を確認"""
        return self.dirty


class DirtyRegionManager:
    """ダーティリージョン管理"""
    
    def __init__(self, screen_size: Tuple[int, int]):
        """
        初期化
        
        Args:
            screen_size: スクリーンサイズ (width, height)
        """
        self.screen_size = screen_size
        self.dirty_rects: List[pygame.Rect] = []
        self.full_redraw = False
        
    def add_dirty_rect(self, rect: pygame.Rect):
        """ダーティ矩形を追加"""
        if rect and rect.width > 0 and rect.height > 0:
            # スクリーン範囲内にクリップ
            clipped = rect.clip(pygame.Rect(0, 0, *self.screen_size))
            if clipped.width > 0 and clipped.height > 0:
                self.dirty_rects.append(clipped)
    
    def mark_full_redraw(self):
        """全画面再描画をマーク"""
        self.full_redraw = True
        self.dirty_rects.clear()
    
    def get_dirty_rects(self) -> List[pygame.Rect]:
        """ダーティ矩形リストを取得"""
        if self.full_redraw:
            return [pygame.Rect(0, 0, *self.screen_size)]
        return self.dirty_rects.copy()
    
    def optimize_rects(self) -> List[pygame.Rect]:
        """ダーティ矩形を最適化（重複を統合）"""
        if not self.dirty_rects or self.full_redraw:
            return self.get_dirty_rects()
        
        # 面積でソート（大きい順）
        sorted_rects = sorted(self.dirty_rects, key=lambda r: r.width * r.height, reverse=True)
        optimized = []
        
        for rect in sorted_rects:
            # 既存の矩形と統合可能かチェック
            merged = False
            for i, existing in enumerate(optimized):
                union = existing.union(rect)
                # 統合による面積増加が閾値以下なら統合
                if union.width * union.height < (existing.width * existing.height + rect.width * rect.height) * 1.2:
                    optimized[i] = union
                    merged = True
                    break
            
            if not merged:
                optimized.append(rect)
        
        return optimized
    
    def clear(self):
        """ダーティ情報をクリア"""
        self.dirty_rects.clear()
        self.full_redraw = False


class LayerCompositor:
    """レイヤー合成システム"""
    
    def __init__(self, screen_size: Tuple[int, int]):
        """
        初期化
        
        Args:
            screen_size: スクリーンサイズ
        """
        self.screen_size = screen_size
        self.components: Dict[RenderLayer, List[RenderComponent]] = {
            layer: [] for layer in RenderLayer
        }
        self.layer_surfaces: Dict[RenderLayer, pygame.Surface] = {}
        self.layer_dirty: Dict[RenderLayer, bool] = {layer: True for layer in RenderLayer}
        
    def add_component(self, component: RenderComponent):
        """コンポーネントを追加"""
        self.components[component.layer].append(component)
        self.layer_dirty[component.layer] = True
        
    def remove_component(self, component: RenderComponent):
        """コンポーネントを削除"""
        if component in self.components[component.layer]:
            self.components[component.layer].remove(component)
            self.layer_dirty[component.layer] = True
    
    def update_components(self, dt: float, context: Dict[str, Any]):
        """全コンポーネントを更新"""
        for layer in RenderLayer:
            layer_needs_update = False
            for component in self.components[layer]:
                if component.enabled and component.update(dt, context):
                    layer_needs_update = True
            
            if layer_needs_update:
                self.layer_dirty[layer] = True
    
    def render_layers(self, screen: pygame.Surface, context: Dict[str, Any], 
                     dirty_rects: List[pygame.Rect]) -> List[pygame.Rect]:
        """
        レイヤーを合成してレンダリング
        
        Args:
            screen: 描画対象サーフェス
            context: レンダリングコンテキスト
            dirty_rects: 更新対象矩形
            
        Returns:
            実際に更新された矩形リスト
        """
        updated_rects = []
        
        # レイヤー順にレンダリング
        for layer in sorted(RenderLayer, key=lambda l: l.value):
            if not self.components[layer]:
                continue
            
            layer_updated = False
            
            # レイヤーが更新必要かチェック
            if self.layer_dirty[layer] or any(c.is_dirty() for c in self.components[layer] if c.enabled):
                layer_updated = True
                
                # レイヤーサーフェスを作成/更新
                if layer not in self.layer_surfaces:
                    self.layer_surfaces[layer] = pygame.Surface(self.screen_size, pygame.SRCALPHA)
                
                layer_surface = self.layer_surfaces[layer]
                layer_surface.fill((0, 0, 0, 0))  # 透明で初期化
                
                # レイヤー内のコンポーネントをレンダリング
                for component in self.components[layer]:
                    if component.enabled:
                        component_rect = component.render(layer_surface, context)
                        if component_rect:
                            updated_rects.append(component_rect)
                        component.set_dirty(False)
                
                self.layer_dirty[layer] = False
            
            # レイヤーを画面に合成
            if layer in self.layer_surfaces and (layer_updated or dirty_rects):
                if dirty_rects:
                    # ダーティリージョンのみ更新
                    for rect in dirty_rects:
                        screen.blit(self.layer_surfaces[layer], rect, rect)
                else:
                    # 全画面更新
                    screen.blit(self.layer_surfaces[layer], (0, 0))
        
        return updated_rects


class RenderLoop:
    """メインレンダリングループ"""
    
    def __init__(self, config: ConfigManager, display_manager: DisplayManager):
        """
        初期化
        
        Args:
            config: 設定管理
            display_manager: ディスプレイ管理
        """
        self.config = config
        self.display_manager = display_manager
        
        # ログ設定
        self.log_manager = LogManager(config)
        self.logger = self.log_manager.get_logger(__name__)
        
        # レンダリング設定
        self.target_fps = config.get('screen', {}).get('fps', 30)
        self.vsync = config.get('screen', {}).get('vsync', False)
        self.performance_mode = config.get('performance', {}).get('mode', 'balanced')
        
        # システムコンポーネント
        resolution = display_manager.resolution
        self.dirty_manager = DirtyRegionManager(resolution)
        self.compositor = LayerCompositor(resolution)
        
        # ループ制御
        self.running = False
        self.paused = False
        self.frame_count = 0
        self.total_time = 0.0
        self.last_frame_time = 0.0
        
        # パフォーマンス監視
        self.fps_samples = []
        self.max_fps_samples = 60  # 2秒分（30fps）
        self.frame_time_samples = []
        
        # イベントハンドラー
        self.event_handlers: Dict[int, List[Callable]] = {}
        self.update_callbacks: List[Callable] = []
        
        # デバッグ情報
        self.debug_mode = config.get('debug', {}).get('enabled', False)
        self.show_fps = config.get('debug', {}).get('show_fps', False)
        
        self.logger.info(f"RenderLoop initialized: {self.target_fps}fps, {resolution}")
    
    def add_component(self, component: RenderComponent):
        """レンダリングコンポーネントを追加"""
        self.compositor.add_component(component)
        self.dirty_manager.mark_full_redraw()
        self.logger.debug(f"Added component: {component.name} (layer: {component.layer.name})")
    
    def remove_component(self, component: RenderComponent):
        """レンダリングコンポーネントを削除"""
        self.compositor.remove_component(component)
        self.dirty_manager.mark_full_redraw()
        self.logger.debug(f"Removed component: {component.name}")
    
    def add_event_handler(self, event_type: int, handler: Callable):
        """イベントハンドラーを追加"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: int, handler: Callable):
        """イベントハンドラーを削除"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    def add_update_callback(self, callback: Callable):
        """更新コールバックを追加"""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """更新コールバックを削除"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def handle_events(self) -> bool:
        """
        イベントを処理
        
        Returns:
            継続する場合True、終了する場合False
        """
        for event in pygame.event.get():
            # システムイベント処理
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_F11:
                    self.display_manager.set_fullscreen(not self.display_manager.fullscreen)
                elif event.key == pygame.K_F12:
                    self.debug_mode = not self.debug_mode
            
            # 登録されたハンドラーを呼び出し
            if event.type in self.event_handlers:
                for handler in self.event_handlers[event.type]:
                    try:
                        handler(event)
                    except Exception as e:
                        self.logger.error(f"Event handler error: {e}")
        
        return True
    
    def update(self, dt: float):
        """
        フレーム更新
        
        Args:
            dt: フレーム時間（秒）
        """
        # レンダリングコンテキスト作成
        context = {
            'dt': dt,
            'total_time': self.total_time,
            'frame_count': self.frame_count,
            'screen_size': self.display_manager.resolution,
            'debug_mode': self.debug_mode
        }
        
        # 更新コールバック実行
        for callback in self.update_callbacks:
            try:
                callback(dt, context)
            except Exception as e:
                self.logger.error(f"Update callback error: {e}")
        
        # コンポーネント更新
        self.compositor.update_components(dt, context)
    
    def render(self):
        """フレームを描画"""
        screen = self.display_manager.get_screen()
        
        # レンダリングコンテキスト作成
        context = {
            'total_time': self.total_time,
            'frame_count': self.frame_count,
            'screen_size': self.display_manager.resolution,
            'debug_mode': self.debug_mode
        }
        
        # ダーティリージョンを最適化
        dirty_rects = self.dirty_manager.optimize_rects()
        
        # レイヤー合成してレンダリング
        updated_rects = self.compositor.render_layers(screen, context, dirty_rects)
        
        # デバッグ情報描画
        if self.debug_mode or self.show_fps:
            self._render_debug_info(screen)
        
        # 画面更新
        if self.performance_mode == 'fast' and dirty_rects and len(dirty_rects) < 10:
            # 高速モード: ダーティリージョンのみ更新
            pygame.display.update(dirty_rects)
        else:
            # 標準モード: 全画面更新
            self.display_manager.flip()
        
        # ダーティ情報クリア
        self.dirty_manager.clear()
    
    def _render_debug_info(self, screen: pygame.Surface):
        """デバッグ情報を描画"""
        if not hasattr(self, '_debug_font'):
            self._debug_font = pygame.font.Font(None, 24)
        
        y_offset = 10
        line_height = 25
        
        # FPS表示
        if self.fps_samples:
            current_fps = len(self.fps_samples) / sum(self.fps_samples) if self.fps_samples else 0
            fps_text = f"FPS: {current_fps:.1f}/{self.target_fps}"
            fps_surface = self._debug_font.render(fps_text, True, (255, 255, 255))
            screen.blit(fps_surface, (10, y_offset))
            y_offset += line_height
        
        # フレーム時間表示
        if self.frame_time_samples:
            avg_frame_time = sum(self.frame_time_samples) / len(self.frame_time_samples)
            frame_time_text = f"Frame Time: {avg_frame_time*1000:.1f}ms"
            frame_surface = self._debug_font.render(frame_time_text, True, (255, 255, 255))
            screen.blit(frame_surface, (10, y_offset))
            y_offset += line_height
        
        # コンポーネント数
        total_components = sum(len(components) for components in self.compositor.components.values())
        comp_text = f"Components: {total_components}"
        comp_surface = self._debug_font.render(comp_text, True, (255, 255, 255))
        screen.blit(comp_surface, (10, y_offset))
    
    def run(self):
        """メインループを実行"""
        if not self.display_manager.get_screen():
            raise RuntimeError("Display not initialized")
        
        self.running = True
        self.logger.info("Starting render loop")
        
        clock = self.display_manager.get_clock()
        last_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                
                # イベント処理
                if not self.handle_events():
                    break
                
                if not self.paused:
                    # 更新処理
                    self.update(dt)
                    
                    # 描画処理
                    self.render()
                    
                    # 統計更新
                    self._update_performance_stats(dt)
                    
                    # フレームカウント更新
                    self.frame_count += 1
                    self.total_time += dt
                
                # FPS制御
                if self.vsync:
                    pygame.display.flip()
                else:
                    clock.tick(self.target_fps)
        
        except Exception as e:
            self.logger.error(f"Render loop error: {e}")
            raise
        finally:
            self.running = False
            self.logger.info("Render loop stopped")
    
    def _update_performance_stats(self, dt: float):
        """パフォーマンス統計を更新"""
        # フレーム時間統計
        self.frame_time_samples.append(dt)
        if len(self.frame_time_samples) > self.max_fps_samples:
            self.frame_time_samples.pop(0)
        
        # FPS統計
        self.fps_samples.append(dt)
        if len(self.fps_samples) > self.max_fps_samples:
            self.fps_samples.pop(0)
        
        self.last_frame_time = dt
    
    def stop(self):
        """ループを停止"""
        self.running = False
    
    def pause(self):
        """ループを一時停止"""
        self.paused = True
    
    def resume(self):
        """ループを再開"""
        self.paused = False
    
    def get_performance_info(self) -> Dict[str, float]:
        """パフォーマンス情報を取得"""
        current_fps = 0.0
        avg_frame_time = 0.0
        
        if self.fps_samples:
            current_fps = len(self.fps_samples) / sum(self.fps_samples)
        
        if self.frame_time_samples:
            avg_frame_time = sum(self.frame_time_samples) / len(self.frame_time_samples)
        
        return {
            'current_fps': current_fps,
            'target_fps': float(self.target_fps),
            'avg_frame_time_ms': avg_frame_time * 1000,
            'frame_count': self.frame_count,
            'total_time': self.total_time,
            'performance_mode': self.performance_mode
        }