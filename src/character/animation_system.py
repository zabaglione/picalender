"""
キャラクターアニメーションシステム

スプライトベースのアニメーション管理
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import pygame

logger = logging.getLogger(__name__)


class Animation:
    """個別のアニメーション"""
    
    def __init__(self, frames: List[pygame.Surface], fps: float = 10, loop: bool = True):
        """
        初期化
        
        Args:
            frames: フレームのリスト
            fps: フレームレート
            loop: ループするかどうか
        """
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.frame_duration = 1.0 / fps if fps > 0 else 0.1
        
        self.current_frame = 0
        self.elapsed_time = 0
        self.finished = False
    
    def update(self, dt: float) -> None:
        """
        アニメーション更新
        
        Args:
            dt: デルタタイム（秒）
        """
        if self.finished and not self.loop:
            return
        
        self.elapsed_time += dt
        
        # フレーム進行
        while self.elapsed_time >= self.frame_duration:
            self.elapsed_time -= self.frame_duration
            self.current_frame += 1
            
            # ループ処理
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """
        現在のフレームを取得
        
        Returns:
            現在のフレーム画像
        """
        if 0 <= self.current_frame < len(self.frames):
            return self.frames[self.current_frame]
        return None
    
    def reset(self) -> None:
        """アニメーションをリセット"""
        self.current_frame = 0
        self.elapsed_time = 0
        self.finished = False


class AnimationController:
    """アニメーションコントローラー"""
    
    def __init__(self):
        """初期化"""
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self.default_animation: Optional[str] = None
    
    def add_animation(self, name: str, animation: Animation) -> None:
        """
        アニメーションを追加
        
        Args:
            name: アニメーション名
            animation: アニメーションオブジェクト
        """
        self.animations[name] = animation
        
        # デフォルトアニメーションを設定
        if self.default_animation is None:
            self.default_animation = name
            self.current_animation = name
    
    def play(self, name: str, reset: bool = True) -> bool:
        """
        アニメーションを再生
        
        Args:
            name: アニメーション名
            reset: アニメーションをリセットするか
            
        Returns:
            再生開始できた場合True
        """
        if name not in self.animations:
            logger.warning(f"Animation '{name}' not found")
            return False
        
        # 同じアニメーションの場合
        if name == self.current_animation and not reset:
            return True
        
        self.current_animation = name
        
        if reset:
            self.animations[name].reset()
        
        return True
    
    def update(self, dt: float) -> None:
        """
        現在のアニメーションを更新
        
        Args:
            dt: デルタタイム（秒）
        """
        if self.current_animation and self.current_animation in self.animations:
            animation = self.animations[self.current_animation]
            animation.update(dt)
            
            # アニメーションが終了した場合
            if animation.finished and not animation.loop:
                # デフォルトアニメーションに戻る
                if self.default_animation and self.default_animation != self.current_animation:
                    self.play(self.default_animation)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """
        現在のフレームを取得
        
        Returns:
            現在のフレーム画像
        """
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].get_current_frame()
        return None
    
    def set_default(self, name: str) -> None:
        """
        デフォルトアニメーションを設定
        
        Args:
            name: アニメーション名
        """
        if name in self.animations:
            self.default_animation = name


class SpriteSheetLoader:
    """スプライトシートローダー"""
    
    @staticmethod
    def load(image_path: str, metadata_path: Optional[str] = None) -> Dict[str, Animation]:
        """
        スプライトシートからアニメーションを読み込み
        
        Args:
            image_path: スプライトシート画像パス
            metadata_path: メタデータJSONパス
            
        Returns:
            アニメーション辞書
        """
        animations = {}
        
        try:
            # 画像を読み込み
            sprite_sheet = pygame.image.load(image_path).convert_alpha()
            
            # メタデータを読み込み
            if metadata_path:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                frame_size = metadata.get('frame_size', [128, 128])
                frame_width, frame_height = frame_size
                
                # 各アニメーションを処理
                for anim_name, anim_data in metadata.get('animations', {}).items():
                    frames = []
                    
                    row = anim_data.get('row', 0)
                    frame_count = anim_data.get('frames', 1)
                    fps = anim_data.get('fps', 10)
                    loop = anim_data.get('loop', True)
                    
                    # フレームを抽出
                    for i in range(frame_count):
                        x = i * frame_width
                        y = row * frame_height
                        
                        # フレームを切り出し
                        frame_rect = pygame.Rect(x, y, frame_width, frame_height)
                        frame = sprite_sheet.subsurface(frame_rect).copy()
                        frames.append(frame)
                    
                    # アニメーションを作成
                    if frames:
                        animations[anim_name] = Animation(frames, fps, loop)
                        logger.info(f"Loaded animation: {anim_name} ({frame_count} frames)")
            
            else:
                # メタデータなしの場合（単一フレーム）
                animations['default'] = Animation([sprite_sheet], 1, False)
                
        except Exception as e:
            logger.error(f"Failed to load sprite sheet: {e}")
        
        return animations


class CharacterAnimator:
    """キャラクターアニメーター"""
    
    def __init__(self, sprite_sheet_path: str, metadata_path: Optional[str] = None):
        """
        初期化
        
        Args:
            sprite_sheet_path: スプライトシート画像パス
            metadata_path: メタデータJSONパス
        """
        self.controller = AnimationController()
        
        # スプライトシートを読み込み
        animations = SpriteSheetLoader.load(sprite_sheet_path, metadata_path)
        
        # アニメーションを登録
        for name, animation in animations.items():
            self.controller.add_animation(name, animation)
        
        # デフォルトをidleに設定
        if 'idle' in animations:
            self.controller.set_default('idle')
    
    def play(self, animation_name: str) -> None:
        """アニメーションを再生"""
        self.controller.play(animation_name)
    
    def update(self, dt: float) -> None:
        """更新"""
        self.controller.update(dt)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """現在のフレームを取得"""
        return self.controller.get_current_frame()
    
    def set_state(self, state: str) -> None:
        """
        状態に応じたアニメーションを設定
        
        Args:
            state: 状態名
        """
        # 状態名をアニメーション名にマッピング
        animation_map = {
            'idle': 'idle',
            'walking': 'walk',
            'greeting': 'wave',
            'happy': 'wave',
            'sleeping': 'idle'
        }
        
        animation_name = animation_map.get(state, 'idle')
        self.play(animation_name)