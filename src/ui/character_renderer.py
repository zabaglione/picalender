"""
キャラクターレンダラー

2Dキャラクターの表示と管理
"""

import logging
import random
from typing import Optional, Tuple, Any
import pygame

from .renderable import Renderable
from ..character.animation_system import CharacterAnimator
from ..character.state_machine import CharacterStateMachine, CharacterState

logger = logging.getLogger(__name__)


class CharacterRenderer(Renderable):
    """
    2Dキャラクターレンダラー
    
    アニメーションキャラクターを画面に表示
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
        self.enabled = config.get('character.enabled', False)
        self.x = config.get('character.position.x', 50)
        self.y = config.get('character.position.y', 50)
        self.scale = config.get('character.scale', 1.0)
        
        # アニメーター
        self.animator: Optional[CharacterAnimator] = None
        
        # 状態マシン
        self.state_machine = CharacterStateMachine()
        
        if self.enabled:
            sprite_path = config.get('character.sprite_path', 'sprites/character_sheet.png')
            metadata_path = config.get('character.metadata_path', 'sprites/character_sheet.json')
            
            try:
                # アセットパスを解決
                full_sprite_path = f"assets/{sprite_path}"
                full_metadata_path = f"assets/{metadata_path}"
                
                self.animator = CharacterAnimator(full_sprite_path, full_metadata_path)
                logger.info("Character animator initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize character: {e}")
                self.enabled = False
        
        # インタラクション設定
        self.interactive = config.get('character.interactive', True)
        self.weather_reactive = config.get('character.weather_reactive', True)
        self.time_reactive = config.get('character.time_reactive', True)
        
        # 表示状態
        self.visible = True
        self._dirty = True
    
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
        
        self._dirty = False
    
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
    
    def _update_animation_for_state(self, state: CharacterState) -> None:
        """
        状態に応じてアニメーションを更新
        
        Args:
            state: 新しい状態
        """
        if not self.animator:
            return
        
        # 状態からアニメーション名へのマッピング
        animation_map = {
            CharacterState.IDLE: 'idle',
            CharacterState.WALK: 'walk',
            CharacterState.WAVE: 'wave',
            CharacterState.HAPPY: 'wave',
            CharacterState.SLEEPING: 'idle',
            CharacterState.EXCITED: 'wave'
        }
        
        animation_name = animation_map.get(state, 'idle')
        self.animator.play(animation_name)
        self._dirty = True
    
    def set_state(self, state: str) -> None:
        """
        キャラクターの状態を設定
        
        Args:
            state: 状態名
        """
        try:
            character_state = CharacterState(state)
            self.state_machine.force_state(character_state)
            self._update_animation_for_state(character_state)
            logger.info(f"Character state changed to: {state}")
        except ValueError:
            logger.warning(f"Invalid state name: {state}")
    
    def update_weather(self, weather: Optional[str]) -> None:
        """
        天気情報を更新
        
        Args:
            weather: 天気タイプ
        """
        if not self.weather_reactive or not self.enabled:
            return
        
        self.state_machine.on_weather_change(weather or 'unknown')
    
    def update_time(self, hour: int) -> None:
        """
        時刻情報を更新
        
        Args:
            hour: 時刻（0-23）
        """
        if not self.time_reactive or not self.enabled:
            return
        
        self.state_machine.update_context(hour=hour)
    
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
    
    def is_dirty(self) -> bool:
        """
        再描画が必要かどうか
        
        Returns:
            再描画が必要な場合True
        """
        # アニメーション中は常にdirty
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
        
        return (self.x, self.y, 128, 128)
    
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
        self.scale = max(0.1, min(2.0, scale))
        self._dirty = True