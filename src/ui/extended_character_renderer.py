"""
拡張キャラクターレンダラー

TASK-402 Step 3/6: 15状態対応の高度なキャラクター表示システム
"""

import logging
import random
import time
from typing import Optional, Tuple, Any, Dict
import pygame

from .renderable import Renderable
from ..character.extended_animation_system import ExtendedCharacterAnimator
from ..character.extended_state_machine import ExtendedCharacterStateMachine, ExtendedCharacterState

logger = logging.getLogger(__name__)


class ExtendedCharacterRenderer(Renderable):
    """
    拡張2Dキャラクターレンダラー
    
    15種類のアニメーション状態と高度な行動システムを持つキャラクター
    """
    
    def __init__(self, asset_manager: Any, config: Any):
        """
        初期化
        
        Args:
            asset_manager: アセット管理オブジェクト
            config: 設定オブジェクト
        """
        self.asset_manager = asset_manager
        self.config = config
        
        # 表示設定
        self.enabled = config.get('character.enabled', True)
        self.x = config.get('character.position.x', 50)
        self.y = config.get('character.position.y', 50)
        self.scale = config.get('character.scale', 1.0)
        
        # 拡張アニメーター
        self.animator: Optional[ExtendedCharacterAnimator] = None
        
        # 拡張状態マシン
        self.state_machine = ExtendedCharacterStateMachine()
        
        if self.enabled:
            sprite_path = config.get('character.sprite_path_extended', 'sprites/character_sheet_extended.png')
            metadata_path = config.get('character.metadata_path_extended', 'sprites/character_sheet_extended.json')
            
            try:
                # アセットパスを解決
                full_sprite_path = f"assets/{sprite_path}"
                full_metadata_path = f"assets/{metadata_path}"
                
                self.animator = ExtendedCharacterAnimator(full_sprite_path, full_metadata_path)
                logger.info(f"Extended character animator initialized with {len(self.animator.get_available_animations())} animations")
                
            except Exception as e:
                logger.error(f"Failed to initialize extended character: {e}")
                # フォールバックとして基本システムを試す
                try:
                    basic_sprite_path = f"assets/sprites/character_sheet.png"
                    basic_metadata_path = f"assets/sprites/character_sheet.json"
                    self.animator = ExtendedCharacterAnimator(basic_sprite_path, basic_metadata_path)
                    logger.info("Fallback to basic character system")
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    self.enabled = False
        
        # インタラクション設定
        self.interactive = config.get('character.interactive', True)
        self.weather_reactive = config.get('character.weather_reactive', True)
        self.time_reactive = config.get('character.time_reactive', True)
        
        # 表示状態
        self.visible = True
        self._dirty = True
        
        # パフォーマンス追跡
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # デバッグ情報表示
        self.show_debug = config.get('character.show_debug', False)
        self.debug_font = None
        if self.show_debug:
            try:
                self.debug_font = pygame.font.Font(None, 20)
            except:
                logger.warning("Could not load debug font")
    
    def render(self, screen: pygame.Surface) -> None:
        """
        キャラクターを描画
        
        Args:
            screen: 描画対象のサーフェス
        """
        if not self.visible or not self.enabled or not self.animator:
            return
        
        # 現在のフレームを取得
        frame = self.animator.get_current_frame()
        if frame:
            # スケーリング
            if self.scale != 1.0:
                size = frame.get_size()
                new_size = (int(size[0] * self.scale), int(size[1] * self.scale))
                frame = pygame.transform.smoothscale(frame, new_size)
            
            # 描画
            screen.blit(frame, (self.x, self.y))
            
            # デバッグ情報描画
            if self.show_debug and self.debug_font:
                self._render_debug_info(screen)
        
        self._dirty = False
        
        # FPS計測
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _render_debug_info(self, screen: pygame.Surface):
        """デバッグ情報を描画"""
        if not self.debug_font:
            return
        
        debug_info = self.state_machine.get_debug_info()
        anim_info = self.animator.get_current_animation_info()
        
        # デバッグ情報を収集
        debug_lines = [
            f"State: {debug_info['current_state']}",
            f"Timer: {debug_info['state_timer']}s",
            f"Energy: {debug_info['energy']}",
            f"Weather: {debug_info['weather']}",
            f"Temp: {debug_info['temperature']}°C",
            f"Hour: {debug_info['hour']}",
            f"Season: {debug_info['season']}",
            f"Mood: {debug_info['mood']}",
            f"Clicks: {debug_info['click_count']}",
            f"FPS: {self.current_fps:.1f}"
        ]
        
        if anim_info:
            debug_lines.extend([
                f"Anim: {anim_info.get('description', 'N/A')}",
                f"Frame: {anim_info.get('current_frame', 0)}/{anim_info.get('frame_count', 0)}"
            ])
        
        # デバッグボックス背景
        box_width = 180
        box_height = len(debug_lines) * 22 + 10
        debug_rect = pygame.Rect(self.x + 140, self.y, box_width, box_height)
        pygame.draw.rect(screen, (0, 0, 0, 180), debug_rect)
        pygame.draw.rect(screen, (100, 100, 100), debug_rect, 1)
        
        # テキスト描画
        for i, line in enumerate(debug_lines):
            text_surface = self.debug_font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (self.x + 145, self.y + 5 + i * 22))
    
    def update(self, dt: float) -> None:
        """
        状態を更新
        
        Args:
            dt: デルタタイム（秒）
        """
        if not self.enabled or not self.animator:
            return
        
        # 状態マシン更新
        new_state = self.state_machine.update(dt)
        
        # 状態変更があった場合アニメーション更新
        if new_state:
            self._update_animation_for_state(new_state)
        
        # アニメーション更新
        self.animator.update(dt)
        
        # 気分変更の反映
        current_mood = self.state_machine.get_mood_indicator()
        if hasattr(self.animator, 'current_mood') and current_mood != self.animator.current_mood:
            self.animator.set_mood(current_mood)
    
    def _update_animation_for_state(self, state: ExtendedCharacterState) -> None:
        """
        状態に応じてアニメーションを更新
        
        Args:
            state: 新しい状態
        """
        if not self.animator:
            return
        
        mood = self.state_machine.get_mood_indicator()
        success = self.animator.play_for_state(state, mood)
        
        if success:
            self._dirty = True
            logger.debug(f"Animation changed to {state.value} with mood {mood}")
        else:
            logger.warning(f"Failed to play animation for state {state.value}")
    
    def update_weather(self, weather: Optional[str], temperature: Optional[float] = None) -> None:
        """
        天気情報を更新
        
        Args:
            weather: 天気タイプ
            temperature: 気温（摂氏）
        """
        if not self.weather_reactive or not self.enabled:
            return
        
        self.state_machine.on_weather_change(weather or 'unknown', temperature)
    
    def update_time(self, hour: int) -> None:
        """
        時刻情報を更新
        
        Args:
            hour: 時刻（0-23）
        """
        if not self.time_reactive or not self.enabled:
            return
        
        self.state_machine.context.hour = hour
    
    def on_click(self, x: int, y: int) -> bool:
        """
        クリックイベント処理
        
        Args:
            x: クリックX座標
            y: クリックY座標
            
        Returns:
            キャラクターがクリックされた場合True
        """
        if not self.enabled or not self.animator:
            return False
        
        # 現在のフレームのサイズを取得
        frame = self.animator.get_current_frame()
        if frame:
            width = int(frame.get_width() * self.scale)
            height = int(frame.get_height() * self.scale)
            
            # クリック判定
            if (self.x <= x <= self.x + width and 
                self.y <= y <= self.y + height):
                # 状態マシンにクリックイベントを通知
                self.state_machine.on_click()
                return True
        
        return False
    
    def on_hover(self, x: int, y: int) -> bool:
        """
        ホバーイベント処理（新機能）
        
        Args:
            x: マウスX座標
            y: マウスY座標
            
        Returns:
            キャラクターにホバーされた場合True
        """
        if not self.enabled or not self.animator:
            return False
        
        frame = self.animator.get_current_frame()
        if frame:
            width = int(frame.get_width() * self.scale)
            height = int(frame.get_height() * self.scale)
            
            if (self.x <= x <= self.x + width and 
                self.y <= y <= self.y + height):
                # ホバー時の軽い反応
                if random.random() < 0.1:  # 10%の確率で反応
                    self.state_machine.context.click_count += 0.1
                return True
        
        return False
    
    def force_state(self, state_name: str) -> bool:
        """
        キャラクターの状態を強制的に設定
        
        Args:
            state_name: 状態名
            
        Returns:
            設定に成功した場合True
        """
        try:
            state = ExtendedCharacterState(state_name)
            self.state_machine.force_state(state)
            self._update_animation_for_state(state)
            logger.info(f"Character state forced to: {state_name}")
            return True
        except ValueError:
            logger.warning(f"Invalid extended state name: {state_name}")
            return False
    
    def add_special_event(self, event: str):
        """
        特別イベントを追加
        
        Args:
            event: イベント名
        """
        self.state_machine.context.add_special_event(event)
    
    def remove_special_event(self, event: str):
        """
        特別イベントを削除
        
        Args:
            event: イベント名
        """
        self.state_machine.context.remove_special_event(event)
    
    def is_dirty(self) -> bool:
        """
        再描画が必要かどうか
        
        Returns:
            再描画が必要な場合True
        """
        # 拡張アニメーション中は常にdirty
        return self.enabled and self.animator is not None
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        self.visible = visible
        self._dirty = True
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """
        描画領域を返す
        
        Returns:
            (x, y, width, height)のタプル
        """
        if self.animator:
            frame = self.animator.get_current_frame()
            if frame:
                width = int(frame.get_width() * self.scale)
                height = int(frame.get_height() * self.scale)
                return (self.x, self.y, width, height)
        
        return (self.x, self.y, int(128 * self.scale), int(128 * self.scale))
    
    def set_position(self, x: int, y: int) -> None:
        """
        位置を設定
        
        Args:
            x: X座標
            y: Y座標
        """
        self.x = x
        self.y = y
        self._dirty = True
    
    def set_scale(self, scale: float) -> None:
        """
        スケールを設定
        
        Args:
            scale: スケール値
        """
        self.scale = max(0.1, min(3.0, scale))
        self._dirty = True
    
    def get_status(self) -> Dict[str, Any]:
        """
        現在の状態情報を取得
        
        Returns:
            状態情報辞書
        """
        status = self.state_machine.get_debug_info()
        status.update({
            'position': (self.x, self.y),
            'scale': self.scale,
            'visible': self.visible,
            'enabled': self.enabled,
            'fps': self.current_fps
        })
        
        if self.animator:
            anim_info = self.animator.get_current_animation_info()
            if anim_info:
                status['animation'] = anim_info
            
            status['available_animations'] = self.animator.get_available_animations()
        
        return status
    
    def toggle_debug(self) -> bool:
        """
        デバッグ表示を切り替え
        
        Returns:
            デバッグ表示がONの場合True
        """
        self.show_debug = not self.show_debug
        if self.show_debug and not self.debug_font:
            try:
                self.debug_font = pygame.font.Font(None, 20)
            except:
                logger.warning("Could not load debug font for toggle")
        return self.show_debug
    
    def get_available_states(self) -> List[str]:
        """利用可能な状態一覧を取得"""
        return [state.value for state in ExtendedCharacterState]
    
    def play_animation_directly(self, animation_name: str) -> bool:
        """
        アニメーションを直接再生
        
        Args:
            animation_name: アニメーション名
            
        Returns:
            再生開始できた場合True
        """
        if not self.animator:
            return False
        
        mood = self.state_machine.get_mood_indicator()
        success = self.animator.play(animation_name, mood)
        if success:
            self._dirty = True
        return success