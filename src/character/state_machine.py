"""
キャラクター状態マシン

キャラクターの状態管理とトリガーシステム
"""

import logging
import random
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class CharacterState(Enum):
    """キャラクター状態"""
    IDLE = "idle"
    WALK = "walk"
    WAVE = "wave"
    HAPPY = "happy"
    SLEEPING = "sleeping"
    EXCITED = "excited"


class StateTransition:
    """状態遷移定義"""
    
    def __init__(self, from_state: CharacterState, to_state: CharacterState, 
                 probability: float = 1.0, conditions: Optional[List[Callable]] = None):
        """
        初期化
        
        Args:
            from_state: 遷移元状態
            to_state: 遷移先状態
            probability: 遷移確率 (0.0-1.0)
            conditions: 遷移条件のリスト
        """
        self.from_state = from_state
        self.to_state = to_state
        self.probability = probability
        self.conditions = conditions or []
    
    def can_transition(self, context: Dict[str, Any]) -> bool:
        """
        遷移可能かチェック
        
        Args:
            context: 状態コンテキスト
            
        Returns:
            遷移可能な場合True
        """
        # 確率チェック
        if random.random() > self.probability:
            return False
        
        # 条件チェック
        for condition in self.conditions:
            try:
                if not condition(context):
                    return False
            except Exception as e:
                logger.warning(f"Condition check failed: {e}")
                return False
        
        return True


class CharacterStateMachine:
    """キャラクター状態マシン"""
    
    def __init__(self):
        """初期化"""
        self.current_state = CharacterState.IDLE
        self.state_timer = 0.0
        self.transitions: List[StateTransition] = []
        self.state_durations: Dict[CharacterState, tuple] = {}
        self.context: Dict[str, Any] = {}
        
        # デフォルト状態継続時間 (min, max秒)
        self.state_durations = {
            CharacterState.IDLE: (3.0, 10.0),
            CharacterState.WALK: (2.0, 5.0),
            CharacterState.WAVE: (1.0, 3.0),
            CharacterState.HAPPY: (2.0, 4.0),
            CharacterState.SLEEPING: (5.0, 15.0),
            CharacterState.EXCITED: (1.0, 3.0)
        }
        
        self._setup_default_transitions()
        
        # コンテキストの初期化
        self.context.update({
            'weather': None,
            'hour': datetime.now().hour,
            'last_interaction': 0,
            'energy_level': 1.0,
            'mood': 'neutral',
            'click_count': 0
        })
        
        self.next_transition_time = self._get_next_transition_time()
    
    def _setup_default_transitions(self):
        """デフォルト状態遷移を設定"""
        # 基本的な遷移パターン
        self.add_transition(CharacterState.IDLE, CharacterState.WALK, 0.3)
        self.add_transition(CharacterState.IDLE, CharacterState.WAVE, 0.2)
        
        self.add_transition(CharacterState.WALK, CharacterState.IDLE, 0.6)
        self.add_transition(CharacterState.WALK, CharacterState.WAVE, 0.1)
        
        self.add_transition(CharacterState.WAVE, CharacterState.IDLE, 0.7)
        self.add_transition(CharacterState.WAVE, CharacterState.HAPPY, 0.2)
        
        self.add_transition(CharacterState.HAPPY, CharacterState.IDLE, 0.5)
        self.add_transition(CharacterState.HAPPY, CharacterState.WAVE, 0.3)
        
        # 時間依存の遷移
        self.add_transition(
            CharacterState.IDLE, CharacterState.SLEEPING, 0.8,
            [lambda ctx: 22 <= ctx.get('hour', 12) or ctx.get('hour', 12) < 6]
        )
        
        self.add_transition(
            CharacterState.SLEEPING, CharacterState.IDLE, 0.3,
            [lambda ctx: 6 <= ctx.get('hour', 12) < 22]
        )
        
        # 天気依存の遷移
        self.add_transition(
            CharacterState.IDLE, CharacterState.EXCITED, 0.4,
            [lambda ctx: ctx.get('weather') == 'sunny']
        )
        
        self.add_transition(
            CharacterState.WALK, CharacterState.IDLE, 0.8,
            [lambda ctx: ctx.get('weather') in ['rain', 'thunder']]
        )
        
        # インタラクション依存
        self.add_transition(
            CharacterState.IDLE, CharacterState.HAPPY, 0.6,
            [lambda ctx: ctx.get('click_count', 0) > 0]
        )
    
    def add_transition(self, from_state: CharacterState, to_state: CharacterState,
                      probability: float, conditions: Optional[List[Callable]] = None):
        """
        状態遷移を追加
        
        Args:
            from_state: 遷移元状態
            to_state: 遷移先状態
            probability: 遷移確率
            conditions: 遷移条件
        """
        transition = StateTransition(from_state, to_state, probability, conditions)
        self.transitions.append(transition)
    
    def update_context(self, **kwargs):
        """
        コンテキストを更新
        
        Args:
            **kwargs: 更新する値
        """
        self.context.update(kwargs)
    
    def update(self, dt: float) -> Optional[CharacterState]:
        """
        状態マシンを更新
        
        Args:
            dt: デルタタイム（秒）
            
        Returns:
            状態が変更された場合新しい状態、そうでなければNone
        """
        self.state_timer += dt
        
        # 時刻更新
        current_hour = datetime.now().hour
        if current_hour != self.context.get('hour'):
            self.context['hour'] = current_hour
        
        # エネルギーレベル更新（時間経過で回復）
        energy = self.context.get('energy_level', 1.0)
        if energy < 1.0:
            self.context['energy_level'] = min(1.0, energy + dt * 0.1)
        
        # クリック数の減衰
        if self.context.get('click_count', 0) > 0:
            self.context['click_count'] = max(0, self.context['click_count'] - dt * 0.5)
        
        # 状態遷移チェック
        if self.state_timer >= self.next_transition_time:
            new_state = self._try_transition()
            if new_state:
                return self._change_state(new_state)
        
        return None
    
    def _try_transition(self) -> Optional[CharacterState]:
        """状態遷移を試行"""
        possible_transitions = [
            t for t in self.transitions 
            if t.from_state == self.current_state
        ]
        
        # 条件を満たす遷移をフィルタ
        valid_transitions = [
            t for t in possible_transitions
            if t.can_transition(self.context)
        ]
        
        if valid_transitions:
            # 確率に基づいて遷移を選択
            transition = random.choice(valid_transitions)
            return transition.to_state
        
        return None
    
    def _change_state(self, new_state: CharacterState) -> CharacterState:
        """状態を変更"""
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_timer = 0.0
            self.next_transition_time = self._get_next_transition_time()
            
            logger.info(f"Character state: {old_state.value} -> {new_state.value}")
            
            # 状態変更による効果
            self._apply_state_effects(new_state)
        
        return self.current_state
    
    def _get_next_transition_time(self) -> float:
        """次の遷移時間を計算"""
        duration_range = self.state_durations.get(self.current_state, (3.0, 8.0))
        return random.uniform(duration_range[0], duration_range[1])
    
    def _apply_state_effects(self, state: CharacterState):
        """状態変更による効果を適用"""
        # エネルギー消費
        energy_cost = {
            CharacterState.IDLE: 0.0,
            CharacterState.WALK: 0.1,
            CharacterState.WAVE: 0.05,
            CharacterState.HAPPY: 0.05,
            CharacterState.SLEEPING: -0.2,  # 回復
            CharacterState.EXCITED: 0.15
        }
        
        cost = energy_cost.get(state, 0.0)
        current_energy = self.context.get('energy_level', 1.0)
        self.context['energy_level'] = max(0.0, min(1.0, current_energy - cost))
    
    def force_state(self, state: CharacterState):
        """強制的に状態を変更"""
        self._change_state(state)
    
    def on_click(self):
        """クリックイベント処理"""
        self.context['click_count'] = self.context.get('click_count', 0) + 1
        self.context['last_interaction'] = 0
        
        # 即座に反応する場合
        if self.current_state == CharacterState.IDLE:
            if random.random() < 0.7:
                self.force_state(CharacterState.WAVE)
    
    def on_weather_change(self, weather: str):
        """天気変更イベント処理"""
        old_weather = self.context.get('weather')
        self.context['weather'] = weather
        
        # 天気による即座の反応
        if weather != old_weather:
            if weather == 'sunny' and random.random() < 0.3:
                self.force_state(CharacterState.EXCITED)
            elif weather in ['rain', 'thunder'] and self.current_state == CharacterState.WALK:
                # 雨や雷の時は高確率でアイドルに
                if random.random() < 0.8:
                    self.force_state(CharacterState.IDLE)
    
    def get_current_state(self) -> CharacterState:
        """現在の状態を取得"""
        return self.current_state
    
    def get_mood_indicator(self) -> str:
        """
        気分インジケーターを取得
        
        Returns:
            気分を表す文字列
        """
        energy = self.context.get('energy_level', 1.0)
        weather = self.context.get('weather', 'unknown')
        hour = self.context.get('hour', 12)
        
        if energy < 0.3:
            return 'tired'
        elif self.current_state == CharacterState.HAPPY:
            return 'happy'
        elif self.current_state == CharacterState.EXCITED:
            return 'excited'
        elif weather == 'sunny' and 6 <= hour < 18:
            return 'cheerful'
        elif 22 <= hour or hour < 6:
            return 'sleepy'
        else:
            return 'neutral'