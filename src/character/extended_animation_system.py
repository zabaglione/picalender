"""
拡張アニメーションシステム

TASK-402 Step 3/6: 15状態対応のアニメーション管理システム
"""

import json
import logging
from typing import Dict, Any, Optional, List
import pygame

from .animation_system import Animation, AnimationController, SpriteSheetLoader
from .extended_state_machine import ExtendedCharacterState
from .animation_transition_system import AnimationTransitionManager, TransitionType, EasingFunction

logger = logging.getLogger(__name__)


class ExtendedSpriteSheetLoader:
    """拡張スプライトシートローダー"""
    
    @staticmethod
    def load_extended(image_path: str, metadata_path: Optional[str] = None) -> Dict[str, Animation]:
        """
        拡張スプライトシートからアニメーションを読み込み
        
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
            logger.info(f"Loaded extended sprite sheet: {image_path}")
            
            # メタデータを読み込み
            if metadata_path:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                frame_size = metadata.get('frame_size', [128, 128])
                frame_width, frame_height = frame_size
                
                logger.info(f"Extended metadata loaded - {len(metadata.get('animations', {}))} animations")
                
                # 各アニメーションを処理
                for anim_name, anim_data in metadata.get('animations', {}).items():
                    frames = []
                    
                    row = anim_data.get('row', 0)
                    frame_count = anim_data.get('frames', 8)
                    fps = anim_data.get('fps', 8)
                    loop = anim_data.get('loop', True)
                    
                    # フレームを抽出
                    for i in range(frame_count):
                        x = i * frame_width
                        y = row * frame_height
                        
                        # 画像サイズチェック
                        if (x + frame_width <= sprite_sheet.get_width() and 
                            y + frame_height <= sprite_sheet.get_height()):
                            # フレームを切り出し
                            frame_rect = pygame.Rect(x, y, frame_width, frame_height)
                            frame = sprite_sheet.subsurface(frame_rect).copy()
                            frames.append(frame)
                        else:
                            logger.warning(f"Frame {i} of {anim_name} exceeds sprite sheet bounds")
                    
                    # アニメーションを作成
                    if frames:
                        animations[anim_name] = Animation(frames, fps, loop)
                        logger.debug(f"Created animation: {anim_name} ({len(frames)} frames, {fps}fps)")
            
            else:
                # メタデータなしの場合（フォールバック）
                animations['idle'] = Animation([sprite_sheet], 1, False)
                logger.warning("No metadata provided, created single idle animation")
                
        except Exception as e:
            logger.error(f"Failed to load extended sprite sheet: {e}")
        
        return animations


class ExtendedAnimationController(AnimationController):
    """拡張アニメーションコントローラー"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        self.animation_metadata = {}  # アニメーションのメタデータ保持
        self.mood_modifiers = {}      # 気分による修正値
        
        # 遷移管理システム
        self.transition_manager = AnimationTransitionManager()
        self.previous_animation = None
        self.transitioning = False
    
    def add_animation_with_metadata(self, name: str, animation: Animation, metadata: Dict[str, Any]):
        """メタデータ付きでアニメーションを追加"""
        self.add_animation(name, animation)
        self.animation_metadata[name] = metadata
    
    def play_with_mood(self, name: str, mood: str, reset: bool = True, enable_transition: bool = True) -> bool:
        """
        気分を考慮してアニメーションを再生
        
        Args:
            name: アニメーション名
            mood: 現在の気分
            reset: アニメーションをリセットするか
            enable_transition: 遷移を有効にするか
            
        Returns:
            再生開始できた場合True
        """
        # 遷移処理
        if enable_transition and self.current_animation != name and self.current_animation is not None:
            from_frame = self.get_current_frame()
            
            # 新しいアニメーションを一時的に再生して最初のフレームを取得
            temp_current = self.current_animation
            if self.play(name, reset):
                to_frame = self.get_current_frame()
                
                # 元のアニメーションに戻す
                self.current_animation = temp_current
                
                # 遷移を開始
                transition_started = self.transition_manager.start_transition(
                    self.current_animation or 'idle', name, from_frame, to_frame
                )
                
                if transition_started:
                    self.transitioning = True
                    self.previous_animation = self.current_animation
                    logger.debug(f"Started transition from {self.current_animation} to {name}")
        
        if not self.play(name, reset):
            return False
        
        # 気分による速度調整
        if name in self.animations:
            speed_modifier = self._get_mood_speed_modifier(mood)
            logger.debug(f"Playing {name} with mood {mood} (speed: {speed_modifier})")
        
        return True
    
    def _get_mood_speed_modifier(self, mood: str) -> float:
        """気分による速度修正値を取得"""
        mood_modifiers = {
            'energetic': 1.3,
            'joyful': 1.2,
            'ecstatic': 1.5,
            'cheerful': 1.1,
            'neutral': 1.0,
            'tired': 0.8,
            'sleepy': 0.6,
            'exhausted': 0.5,
            'anxious': 1.4,
            'nervous': 1.3,
            'peaceful': 0.7,
            'focused': 0.9
        }
        return mood_modifiers.get(mood, 1.0)
    
    def get_animation_info(self, name: str) -> Optional[Dict[str, Any]]:
        """アニメーション情報を取得"""
        if name not in self.animation_metadata:
            return None
        
        metadata = self.animation_metadata[name].copy()
        if name in self.animations:
            animation = self.animations[name]
            metadata.update({
                'frame_count': len(animation.frames),
                'current_frame': animation.current_frame,
                'finished': animation.finished,
                'fps': animation.fps
            })
        
        return metadata
    
    def update(self, dt: float) -> None:
        """アニメーションコントローラーの更新"""
        # 遷移中の場合
        if self.transitioning:
            transition_complete = self.transition_manager.update(dt)
            if transition_complete:
                self.transitioning = False
                logger.debug("Transition completed")
        
        # 通常のアニメーション更新
        super().update(dt)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """現在のフレームを取得（遷移考慮）"""
        # 遷移中の場合は遷移フレームを返す
        if self.transitioning:
            transition_frame = self.transition_manager.get_current_frame()
            if transition_frame:
                return transition_frame
        
        # 通常のフレームを返す
        return super().get_current_frame()
    
    def is_transitioning(self) -> bool:
        """遷移中かどうか"""
        return self.transitioning
    
    def get_transition_progress(self) -> float:
        """遷移進行度を取得"""
        return self.transition_manager.get_transition_progress()
    
    def set_transition_settings(self, transition_type: TransitionType, duration: float, 
                              easing: EasingFunction = EasingFunction.EASE_OUT):
        """遷移設定を変更"""
        self.transition_manager.set_default_transition(transition_type, duration, easing)
    
    def skip_current_transition(self):
        """現在の遷移をスキップ"""
        if self.transitioning:
            self.transition_manager.skip_transition()
            self.transitioning = False


class ExtendedCharacterAnimator:
    """拡張キャラクターアニメーター"""
    
    def __init__(self, sprite_sheet_path: str, metadata_path: Optional[str] = None):
        """
        初期化
        
        Args:
            sprite_sheet_path: 拡張スプライトシート画像パス
            metadata_path: メタデータJSONパス
        """
        self.controller = ExtendedAnimationController()
        self.current_mood = 'neutral'
        self.state_mapping = {}
        
        # 拡張スプライトシートを読み込み
        animations = ExtendedSpriteSheetLoader.load_extended(sprite_sheet_path, metadata_path)
        
        # メタデータも読み込み
        metadata = {}
        if metadata_path:
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    full_metadata = json.load(f)
                    metadata = full_metadata.get('animations', {})
            except Exception as e:
                logger.error(f"Failed to load animation metadata: {e}")
        
        # アニメーションを登録
        for name, animation in animations.items():
            anim_metadata = metadata.get(name, {})
            self.controller.add_animation_with_metadata(name, animation, anim_metadata)
        
        # デフォルトをidleに設定
        if 'idle' in animations:
            self.controller.set_default('idle')
        
        # 状態からアニメーションへのマッピングを構築
        self._build_state_mapping()
        
        logger.info(f"Extended character animator initialized with {len(animations)} animations")
    
    def _build_state_mapping(self):
        """状態からアニメーションへのマッピングを構築"""
        self.state_mapping = {
            ExtendedCharacterState.IDLE: 'idle',
            ExtendedCharacterState.WALK: 'walk',
            ExtendedCharacterState.WAVE: 'wave',
            ExtendedCharacterState.HAPPY: 'celebrating',  # 後方互換
            ExtendedCharacterState.EXCITED: 'dancing',    # 後方互換
            ExtendedCharacterState.SLEEPING: 'sleeping',
            ExtendedCharacterState.UMBRELLA: 'umbrella',
            ExtendedCharacterState.SHIVERING: 'shivering',
            ExtendedCharacterState.SUNBATHING: 'sunbathing',
            ExtendedCharacterState.HIDING: 'hiding',
            ExtendedCharacterState.STRETCHING: 'stretching',
            ExtendedCharacterState.YAWNING: 'yawning',
            ExtendedCharacterState.READING: 'reading',
            ExtendedCharacterState.CELEBRATING: 'celebrating',
            ExtendedCharacterState.PONDERING: 'pondering',
            ExtendedCharacterState.DANCING: 'dancing',
            ExtendedCharacterState.EATING: 'eating'
        }
    
    def play_for_state(self, state: ExtendedCharacterState, mood: str = 'neutral', 
                      enable_transition: bool = True) -> bool:
        """
        状態に対応するアニメーションを再生
        
        Args:
            state: キャラクター状態
            mood: 気分
            enable_transition: 遷移を有効にするか
            
        Returns:
            再生開始できた場合True
        """
        animation_name = self.state_mapping.get(state, 'idle')
        self.current_mood = mood
        return self.controller.play_with_mood(animation_name, mood, True, enable_transition)
    
    def play(self, animation_name: str, mood: str = 'neutral', enable_transition: bool = True) -> bool:
        """
        アニメーションを再生
        
        Args:
            animation_name: アニメーション名
            mood: 気分
            enable_transition: 遷移を有効にするか
            
        Returns:
            再生開始できた場合True
        """
        self.current_mood = mood
        return self.controller.play_with_mood(animation_name, mood, True, enable_transition)
    
    def update(self, dt: float) -> None:
        """更新"""
        self.controller.update(dt)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """現在のフレームを取得"""
        return self.controller.get_current_frame()
    
    def get_available_animations(self) -> List[str]:
        """利用可能なアニメーション一覧を取得"""
        return list(self.controller.animations.keys())
    
    def get_animation_info(self, name: str) -> Optional[Dict[str, Any]]:
        """アニメーション情報を取得"""
        return self.controller.get_animation_info(name)
    
    def get_current_animation_info(self) -> Optional[Dict[str, Any]]:
        """現在のアニメーション情報を取得"""
        if self.controller.current_animation:
            return self.get_animation_info(self.controller.current_animation)
        return None
    
    def set_mood(self, mood: str):
        """気分を設定"""
        self.current_mood = mood
        # 現在のアニメーションを気分で再調整
        if self.controller.current_animation:
            self.controller.play_with_mood(self.controller.current_animation, mood, False)
    
    def is_animation_finished(self) -> bool:
        """現在のアニメーションが終了したかどうか"""
        if (self.controller.current_animation and 
            self.controller.current_animation in self.controller.animations):
            return self.controller.animations[self.controller.current_animation].finished
        return False
    
    def has_animation(self, name: str) -> bool:
        """指定されたアニメーションが存在するか"""
        return name in self.controller.animations
    
    def get_state_for_animation(self, animation_name: str) -> Optional[ExtendedCharacterState]:
        """アニメーション名から対応する状態を取得"""
        for state, anim_name in self.state_mapping.items():
            if anim_name == animation_name:
                return state
        return None
    
    def is_transitioning(self) -> bool:
        """遷移中かどうか"""
        return self.controller.is_transitioning()
    
    def get_transition_progress(self) -> float:
        """遷移進行度を取得"""
        return self.controller.get_transition_progress()
    
    def set_transition_settings(self, transition_type: TransitionType, duration: float, 
                              easing: EasingFunction = EasingFunction.EASE_OUT):
        """遷移設定を変更"""
        self.controller.set_transition_settings(transition_type, duration, easing)
    
    def skip_current_transition(self):
        """現在の遷移をスキップ"""
        self.controller.skip_current_transition()
    
    def get_available_transitions(self) -> Dict[str, List[str]]:
        """利用可能な遷移タイプとイージング関数を取得"""
        return {
            'transition_types': self.controller.transition_manager.get_available_transition_types(),
            'easing_functions': self.controller.transition_manager.get_available_easing_functions()
        }


# 後方互換のためのエイリアス
CharacterAnimatorExtended = ExtendedCharacterAnimator