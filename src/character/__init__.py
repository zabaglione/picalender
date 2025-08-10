"""
キャラクターモジュール
"""

from .animation_system import (
    Animation,
    AnimationController,
    SpriteSheetLoader,
    CharacterAnimator
)
from .state_machine import (
    CharacterState,
    StateTransition,
    CharacterStateMachine
)
from .extended_animation_system import (
    ExtendedCharacterAnimator,
    ExtendedAnimationController,
    ExtendedSpriteSheetLoader
)
from .extended_state_machine import (
    ExtendedCharacterState,
    ExtendedCharacterStateMachine,
    StateContext,
    Priority
)
from .animation_transition_system import (
    TransitionType,
    EasingFunction,
    TransitionEffect,
    AnimationTransitionManager
)
from .weather_behavior_system import (
    WeatherIntensity,
    WeatherCondition,
    SeasonalBehaviorModifier,
    WeatherBehaviorPattern,
    WeatherSpecificBehaviorSystem
)

__all__ = [
    # 基本システム (TASK-401)
    'Animation',
    'AnimationController',
    'SpriteSheetLoader',
    'CharacterAnimator',
    'CharacterState',
    'StateTransition',
    'CharacterStateMachine',
    
    # 拡張システム (TASK-402)
    'ExtendedCharacterAnimator',
    'ExtendedAnimationController',
    'ExtendedSpriteSheetLoader',
    'ExtendedCharacterState',
    'ExtendedCharacterStateMachine',
    'StateContext',
    'Priority',
    
    # 遷移システム (TASK-402 Step 4)
    'TransitionType',
    'EasingFunction',
    'TransitionEffect',
    'AnimationTransitionManager',
    
    # 天気行動システム (TASK-402 Step 5)
    'WeatherIntensity',
    'WeatherCondition',
    'SeasonalBehaviorModifier',
    'WeatherBehaviorPattern',
    'WeatherSpecificBehaviorSystem'
]