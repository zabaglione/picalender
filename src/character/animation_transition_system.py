"""
アニメーション遷移システム

TASK-402 Step 4/6: 滑らかなアニメーション遷移とエフェクトシステム
"""

import logging
import math
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
import pygame

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """遷移タイプ"""
    INSTANT = "instant"           # 即座に切り替え
    FADE = "fade"                # フェード遷移
    SLIDE = "slide"              # スライド遷移
    ZOOM = "zoom"                # ズーム遷移
    MORPH = "morph"              # 変形遷移
    BOUNCE = "bounce"            # バウンス遷移
    ELASTIC = "elastic"          # 弾性遷移


class EasingFunction(Enum):
    """イージング関数"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"


class TransitionEffect:
    """遷移エフェクト定義"""
    
    def __init__(self, transition_type: TransitionType, duration: float,
                 easing: EasingFunction = EasingFunction.EASE_OUT,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            transition_type: 遷移タイプ
            duration: 遷移時間（秒）
            easing: イージング関数
            properties: 追加プロパティ
        """
        self.transition_type = transition_type
        self.duration = duration
        self.easing = easing
        self.properties = properties or {}
        
        self.start_time = 0.0
        self.is_active = False
        self.progress = 0.0
        
        # 遷移中の状態
        self.from_frame = None
        self.to_frame = None
        self.current_frame = None
    
    def start(self, from_frame: pygame.Surface, to_frame: pygame.Surface):
        """遷移を開始"""
        self.from_frame = from_frame.copy() if from_frame else None
        self.to_frame = to_frame.copy() if to_frame else None
        self.start_time = time.time()
        self.is_active = True
        self.progress = 0.0
        logger.debug(f"Started {self.transition_type.value} transition")
    
    def update(self, dt: float) -> bool:
        """
        遷移を更新
        
        Args:
            dt: デルタタイム
            
        Returns:
            遷移が完了した場合True
        """
        if not self.is_active:
            return True
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed >= self.duration:
            self.progress = 1.0
            self.is_active = False
            self.current_frame = self.to_frame
            return True
        
        self.progress = elapsed / self.duration
        
        # イージング適用
        eased_progress = self._apply_easing(self.progress)
        
        # 遷移タイプに応じた処理
        self.current_frame = self._apply_transition(eased_progress)
        
        return False
    
    def _apply_easing(self, t: float) -> float:
        """イージング関数を適用"""
        if self.easing == EasingFunction.LINEAR:
            return t
        elif self.easing == EasingFunction.EASE_IN:
            return t * t
        elif self.easing == EasingFunction.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif self.easing == EasingFunction.EASE_IN_OUT:
            return 3 * t * t - 2 * t * t * t
        elif self.easing == EasingFunction.BOUNCE:
            return self._bounce_ease(t)
        elif self.easing == EasingFunction.ELASTIC:
            return self._elastic_ease(t)
        elif self.easing == EasingFunction.BACK:
            return self._back_ease(t)
        else:
            return t
    
    def _bounce_ease(self, t: float) -> float:
        """バウンスイージング"""
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            t -= 1.5/2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5/2.75:
            t -= 2.25/2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625/2.75
            return 7.5625 * t * t + 0.984375
    
    def _elastic_ease(self, t: float) -> float:
        """弾性イージング"""
        if t <= 0 or t >= 1:
            return t
        
        period = 0.3
        amplitude = 1
        s = period / 4
        
        return amplitude * math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / period) + 1
    
    def _back_ease(self, t: float) -> float:
        """バックイージング"""
        c1 = 1.70158
        c3 = c1 + 1
        
        return c3 * t * t * t - c1 * t * t
    
    def _apply_transition(self, progress: float) -> Optional[pygame.Surface]:
        """遷移タイプを適用"""
        if not self.from_frame or not self.to_frame:
            return self.to_frame
        
        if self.transition_type == TransitionType.INSTANT:
            return self.to_frame.copy() if progress >= 1.0 else self.from_frame.copy()
        
        elif self.transition_type == TransitionType.FADE:
            return self._fade_transition(progress)
        
        elif self.transition_type == TransitionType.SLIDE:
            return self._slide_transition(progress)
        
        elif self.transition_type == TransitionType.ZOOM:
            return self._zoom_transition(progress)
        
        elif self.transition_type == TransitionType.MORPH:
            return self._morph_transition(progress)
        
        elif self.transition_type == TransitionType.BOUNCE:
            return self._bounce_transition(progress)
        
        elif self.transition_type == TransitionType.ELASTIC:
            return self._elastic_transition(progress)
        
        else:
            return self._fade_transition(progress)
    
    def _fade_transition(self, progress: float) -> pygame.Surface:
        """フェード遷移"""
        size = self.from_frame.get_size()
        result = pygame.Surface(size, pygame.SRCALPHA)
        
        # アルファブレンディング
        from_alpha = int(255 * (1 - progress))
        to_alpha = int(255 * progress)
        
        from_temp = self.from_frame.copy()
        from_temp.set_alpha(from_alpha)
        
        to_temp = self.to_frame.copy()
        to_temp.set_alpha(to_alpha)
        
        result.blit(from_temp, (0, 0))
        result.blit(to_temp, (0, 0))
        
        return result
    
    def _slide_transition(self, progress: float) -> pygame.Surface:
        """スライド遷移"""
        size = self.from_frame.get_size()
        result = pygame.Surface(size, pygame.SRCALPHA)
        result.fill((0, 0, 0, 0))
        
        # スライド方向（設定から取得、デフォルトは左から右）
        direction = self.properties.get('direction', 'right')
        
        from_y = 0
        to_y = 0
        
        if direction == 'right':
            from_x = int(-size[0] * progress)
            to_x = int(size[0] * (1 - progress))
        elif direction == 'left':
            from_x = int(size[0] * progress)
            to_x = int(-size[0] * (1 - progress))
        elif direction == 'down':
            from_x, to_x = 0, 0
            from_y = int(-size[1] * progress)
            to_y = int(size[1] * (1 - progress))
        else:  # up
            from_x, to_x = 0, 0
            from_y = int(size[1] * progress)
            to_y = int(-size[1] * (1 - progress))
        
        # クリッピング領域内での描画
        try:
            if direction in ['right', 'left']:
                if from_x > -size[0] and from_x < size[0]:
                    result.blit(self.from_frame, (from_x, 0))
                if to_x > -size[0] and to_x < size[0]:
                    result.blit(self.to_frame, (to_x, 0))
            else:
                if from_y > -size[1] and from_y < size[1]:
                    result.blit(self.from_frame, (0, from_y))
                if to_y > -size[1] and to_y < size[1]:
                    result.blit(self.to_frame, (0, to_y))
        except Exception as e:
            # フォールバック: フェード遷移
            return self._fade_transition(progress)
        
        return result
    
    def _zoom_transition(self, progress: float) -> pygame.Surface:
        """ズーム遷移"""
        size = self.from_frame.get_size()
        result = pygame.Surface(size, pygame.SRCALPHA)
        
        # ズームの中心点
        center = self.properties.get('center', (size[0]//2, size[1]//2))
        
        # FROM フレーム（縮小）
        from_scale = 1.0 - progress * 0.5
        if from_scale > 0:
            from_size = (int(size[0] * from_scale), int(size[1] * from_scale))
            if from_size[0] > 0 and from_size[1] > 0:
                from_scaled = pygame.transform.scale(self.from_frame, from_size)
                from_pos = (center[0] - from_size[0]//2, center[1] - from_size[1]//2)
                
                from_alpha = int(255 * (1 - progress))
                from_scaled.set_alpha(from_alpha)
                result.blit(from_scaled, from_pos)
        
        # TO フレーム（拡大）
        to_scale = progress
        if to_scale > 0:
            to_size = (int(size[0] * to_scale), int(size[1] * to_scale))
            if to_size[0] > 0 and to_size[1] > 0:
                to_scaled = pygame.transform.scale(self.to_frame, to_size)
                to_pos = (center[0] - to_size[0]//2, center[1] - to_size[1]//2)
                
                to_alpha = int(255 * progress)
                to_scaled.set_alpha(to_alpha)
                result.blit(to_scaled, to_pos)
        
        return result
    
    def _morph_transition(self, progress: float) -> pygame.Surface:
        """変形遷移（フェードのバリエーション）"""
        return self._fade_transition(progress)
    
    def _bounce_transition(self, progress: float) -> pygame.Surface:
        """バウンス遷移"""
        size = self.from_frame.get_size()
        result = pygame.Surface(size, pygame.SRCALPHA)
        
        # バウンス効果のスケール
        bounce_scale = 1.0 + math.sin(progress * math.pi) * 0.2
        
        # TO フレームを拡大してバウンス効果
        if bounce_scale > 0:
            bounce_size = (int(size[0] * bounce_scale), int(size[1] * bounce_scale))
            if bounce_size[0] > 0 and bounce_size[1] > 0:
                bounced = pygame.transform.scale(self.to_frame, bounce_size)
                bounce_pos = ((size[0] - bounce_size[0])//2, (size[1] - bounce_size[1])//2)
                
                # アルファ値も調整
                alpha = int(255 * progress)
                bounced.set_alpha(alpha)
                
                # FROM フレームを背景として
                from_alpha = int(255 * (1 - progress))
                from_temp = self.from_frame.copy()
                from_temp.set_alpha(from_alpha)
                
                result.blit(from_temp, (0, 0))
                result.blit(bounced, bounce_pos)
        
        return result
    
    def _elastic_transition(self, progress: float) -> pygame.Surface:
        """弾性遷移"""
        size = self.from_frame.get_size()
        result = pygame.Surface(size, pygame.SRCALPHA)
        
        # 弾性効果の変形
        elastic_factor = 1.0 + math.sin(progress * math.pi * 4) * (1 - progress) * 0.3
        
        if elastic_factor > 0:
            elastic_width = max(1, int(size[0] * elastic_factor))
            elastic_height = max(1, int(size[1] / elastic_factor))  # 幅が伸びたら高さは縮む
            
            elastic_size = (elastic_width, elastic_height)
            if elastic_size[0] > 0 and elastic_size[1] > 0:
                elastic_frame = pygame.transform.scale(self.to_frame, elastic_size)
                elastic_pos = ((size[0] - elastic_width)//2, (size[1] - elastic_height)//2)
                
                # アルファブレンディング
                alpha = int(255 * progress)
                elastic_frame.set_alpha(alpha)
                
                from_alpha = int(255 * (1 - progress))
                from_temp = self.from_frame.copy()
                from_temp.set_alpha(from_alpha)
                
                result.blit(from_temp, (0, 0))
                result.blit(elastic_frame, elastic_pos)
        
        return result
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """現在の遷移フレームを取得"""
        if not self.is_active:
            return self.to_frame
        return self.current_frame
    
    def is_complete(self) -> bool:
        """遷移が完了しているかチェック"""
        return not self.is_active


class AnimationTransitionManager:
    """アニメーション遷移管理"""
    
    def __init__(self):
        """初期化"""
        self.current_transition: Optional[TransitionEffect] = None
        self.transition_rules: Dict[str, Dict[str, TransitionEffect]] = {}
        self.default_transition = TransitionEffect(TransitionType.FADE, 0.3)
        
        # 遷移エフェクト定義
        self._setup_default_transitions()
    
    def _setup_default_transitions(self):
        """デフォルト遷移を設定"""
        # 基本的な遷移ルール
        self.add_transition_rule('idle', 'walk', 
                               TransitionEffect(TransitionType.SLIDE, 0.4, EasingFunction.EASE_OUT,
                                              {'direction': 'right'}))
        
        self.add_transition_rule('walk', 'idle',
                               TransitionEffect(TransitionType.SLIDE, 0.3, EasingFunction.EASE_IN,
                                              {'direction': 'left'}))
        
        self.add_transition_rule('idle', 'wave',
                               TransitionEffect(TransitionType.BOUNCE, 0.5, EasingFunction.BOUNCE))
        
        self.add_transition_rule('wave', 'idle',
                               TransitionEffect(TransitionType.ELASTIC, 0.4, EasingFunction.ELASTIC))
        
        self.add_transition_rule('idle', 'celebrating',
                               TransitionEffect(TransitionType.ZOOM, 0.6, EasingFunction.EASE_OUT,
                                              {'center': (64, 64)}))
        
        self.add_transition_rule('celebrating', 'idle',
                               TransitionEffect(TransitionType.FADE, 0.5, EasingFunction.EASE_IN_OUT))
        
        self.add_transition_rule('idle', 'dancing',
                               TransitionEffect(TransitionType.ZOOM, 0.8, EasingFunction.BOUNCE,
                                              {'center': (64, 64)}))
        
        self.add_transition_rule('dancing', 'idle',
                               TransitionEffect(TransitionType.ELASTIC, 0.6, EasingFunction.ELASTIC))
        
        # 天気遷移
        self.add_transition_rule('walk', 'umbrella',
                               TransitionEffect(TransitionType.SLIDE, 0.5, EasingFunction.EASE_OUT,
                                              {'direction': 'down'}))
        
        self.add_transition_rule('idle', 'shivering',
                               TransitionEffect(TransitionType.FADE, 0.3, EasingFunction.EASE_IN))
        
        self.add_transition_rule('idle', 'sunbathing',
                               TransitionEffect(TransitionType.ZOOM, 0.7, EasingFunction.EASE_OUT,
                                              {'center': (64, 90)}))  # 下の方から
        
        self.add_transition_rule('walk', 'hiding',
                               TransitionEffect(TransitionType.ZOOM, 0.2, EasingFunction.EASE_IN,
                                              {'center': (64, 100)}))  # 素早く縮む
        
        # 時間遷移
        self.add_transition_rule('sleeping', 'stretching',
                               TransitionEffect(TransitionType.ELASTIC, 1.0, EasingFunction.ELASTIC))
        
        self.add_transition_rule('idle', 'yawning',
                               TransitionEffect(TransitionType.FADE, 0.4, EasingFunction.EASE_IN))
        
        self.add_transition_rule('idle', 'reading',
                               TransitionEffect(TransitionType.SLIDE, 0.6, EasingFunction.EASE_OUT,
                                              {'direction': 'right'}))
    
    def add_transition_rule(self, from_animation: str, to_animation: str, effect: TransitionEffect):
        """遷移ルールを追加"""
        if from_animation not in self.transition_rules:
            self.transition_rules[from_animation] = {}
        self.transition_rules[from_animation][to_animation] = effect
    
    def start_transition(self, from_animation: str, to_animation: str,
                        from_frame: Optional[pygame.Surface], to_frame: Optional[pygame.Surface]) -> bool:
        """
        遷移を開始
        
        Args:
            from_animation: 遷移元アニメーション
            to_animation: 遷移先アニメーション
            from_frame: 遷移元フレーム
            to_frame: 遷移先フレーム
            
        Returns:
            遷移を開始した場合True
        """
        if from_animation == to_animation:
            return False
        
        # 既存の遷移を停止
        if self.current_transition and self.current_transition.is_active:
            self.current_transition.is_active = False
        
        # 適切な遷移を選択
        effect = self._get_transition_effect(from_animation, to_animation)
        
        # 新しい遷移を作成（元のeffectをコピー）
        self.current_transition = TransitionEffect(
            effect.transition_type,
            effect.duration,
            effect.easing,
            effect.properties.copy()
        )
        
        self.current_transition.start(from_frame, to_frame)
        logger.debug(f"Started transition: {from_animation} -> {to_animation} ({effect.transition_type.value})")
        return True
    
    def _get_transition_effect(self, from_animation: str, to_animation: str) -> TransitionEffect:
        """適切な遷移エフェクトを取得"""
        if (from_animation in self.transition_rules and 
            to_animation in self.transition_rules[from_animation]):
            return self.transition_rules[from_animation][to_animation]
        
        # デフォルト遷移を返す
        return self.default_transition
    
    def update(self, dt: float) -> bool:
        """
        遷移を更新
        
        Args:
            dt: デルタタイム
            
        Returns:
            遷移が完了した場合True
        """
        if not self.current_transition:
            return True
        
        return self.current_transition.update(dt)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """現在の遷移フレームを取得"""
        if self.current_transition:
            return self.current_transition.get_current_frame()
        return None
    
    def is_transitioning(self) -> bool:
        """遷移中かどうか"""
        return (self.current_transition is not None and 
                self.current_transition.is_active)
    
    def set_default_transition(self, transition_type: TransitionType, duration: float,
                              easing: EasingFunction = EasingFunction.EASE_OUT):
        """デフォルト遷移を設定"""
        self.default_transition = TransitionEffect(transition_type, duration, easing)
    
    def get_transition_progress(self) -> float:
        """現在の遷移進行度を取得"""
        if self.current_transition and self.current_transition.is_active:
            return self.current_transition.progress
        return 1.0
    
    def skip_transition(self):
        """遷移をスキップ"""
        if self.current_transition and self.current_transition.is_active:
            self.current_transition.progress = 1.0
            self.current_transition.is_active = False
    
    def get_available_transition_types(self) -> List[str]:
        """利用可能な遷移タイプ一覧を取得"""
        return [t.value for t in TransitionType]
    
    def get_available_easing_functions(self) -> List[str]:
        """利用可能なイージング関数一覧を取得"""
        return [e.value for e in EasingFunction]