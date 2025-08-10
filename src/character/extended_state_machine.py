"""
拡張キャラクター状態マシン

TASK-402 Step 3/6: 15状態対応の高度な動作状態マシン
"""

import logging
import random
import json
from typing import Dict, Any, Optional, Callable, List, Set
from enum import Enum
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtendedCharacterState(Enum):
    """拡張キャラクター状態"""
    # 基本状態
    IDLE = "idle"
    WALK = "walk"
    WAVE = "wave"
    HAPPY = "happy"  # 後方互換のため保持
    SLEEPING = "sleeping"
    EXCITED = "excited"  # 後方互換のため保持
    
    # 天気対応状態
    UMBRELLA = "umbrella"
    SHIVERING = "shivering"
    SUNBATHING = "sunbathing"
    HIDING = "hiding"
    
    # 時間対応状態
    STRETCHING = "stretching"
    YAWNING = "yawning"
    READING = "reading"
    
    # 感情状態
    CELEBRATING = "celebrating"
    PONDERING = "pondering"
    DANCING = "dancing"
    EATING = "eating"


class Priority(Enum):
    """優先度レベル"""
    HIGHEST = 4  # ユーザーインタラクション
    HIGH = 3     # 天気反応
    MEDIUM = 2   # 時間・季節反応
    LOW = 1      # 自動遷移
    LOWEST = 0   # デフォルト


class StateContext:
    """状態コンテキスト管理"""
    
    def __init__(self):
        """初期化"""
        self.weather = None
        self.temperature = 20  # 摂氏
        self.hour = datetime.now().hour
        self.season = self._get_current_season()
        self.energy_level = 1.0
        self.mood = 'neutral'
        self.click_count = 0
        self.last_interaction = 0
        self.consecutive_weather_days = 0
        self.last_weather = None
        self.special_events = set()
        self.location = 'home'  # デフォルト場所
        self.time_of_day = self._get_time_of_day()  # 時間帯
        
        # 長期状態追跡
        self.state_history = []
        self.daily_interactions = 0
        self.total_uptime = 0
        
        # 学習データ
        self.interaction_times = []  # ユーザーがよくインタラクションする時間
        self.preferred_states = {}   # 状態別の滞在時間
        
    def _get_current_season(self) -> str:
        """現在の季節を取得"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return 'spring'
        elif 6 <= month <= 8:
            return 'summer'
        elif 9 <= month <= 11:
            return 'autumn'
        else:
            return 'winter'
    
    def _get_time_of_day(self) -> str:
        """現在の時間帯を取得"""
        hour = self.hour
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def update_weather(self, weather: str, temperature: Optional[float] = None):
        """天気情報を更新"""
        if weather != self.last_weather:
            if self.last_weather is not None:
                self.consecutive_weather_days = 1
            else:
                self.consecutive_weather_days += 1
            self.last_weather = weather
        else:
            self.consecutive_weather_days += 1
        
        self.weather = weather
        if temperature is not None:
            self.temperature = temperature
    
    def add_interaction(self):
        """インタラクション記録"""
        current_hour = datetime.now().hour
        self.interaction_times.append(current_hour)
        self.daily_interactions += 1
        self.click_count += 1
        self.last_interaction = 0
        
        # 学習データの更新（最新100件のみ保持）
        if len(self.interaction_times) > 100:
            self.interaction_times = self.interaction_times[-100:]
    
    def is_frequent_interaction_time(self) -> bool:
        """よくインタラクションする時間かどうか"""
        if len(self.interaction_times) < 5:
            return False
        
        current_hour = datetime.now().hour
        similar_hour_count = sum(1 for hour in self.interaction_times 
                               if abs(hour - current_hour) <= 1)
        
        return similar_hour_count >= len(self.interaction_times) * 0.3
    
    def add_special_event(self, event: str):
        """特別イベントを追加"""
        self.special_events.add(event)
        logger.info(f"Special event added: {event}")
    
    def remove_special_event(self, event: str):
        """特別イベントを削除"""
        self.special_events.discard(event)


class ExtendedStateTransition:
    """拡張状態遷移"""
    
    def __init__(self, from_state: ExtendedCharacterState, to_state: ExtendedCharacterState,
                 priority: Priority, probability: float = 1.0, 
                 conditions: Optional[List[Callable]] = None,
                 min_duration: float = 0.0, cooldown: float = 0.0):
        """
        初期化
        
        Args:
            from_state: 遷移元状態
            to_state: 遷移先状態
            priority: 優先度
            probability: 遷移確率
            conditions: 遷移条件
            min_duration: 最小継続時間
            cooldown: クールダウン時間
        """
        self.from_state = from_state
        self.to_state = to_state
        self.priority = priority
        self.probability = probability
        self.conditions = conditions or []
        self.min_duration = min_duration
        self.cooldown = cooldown
        self.last_used = 0
    
    def can_transition(self, context: StateContext, current_time: float, 
                      state_duration: float) -> bool:
        """遷移可能かチェック"""
        # 最小継続時間チェック
        if state_duration < self.min_duration:
            return False
        
        # クールダウンチェック
        if current_time - self.last_used < self.cooldown:
            return False
        
        # 確率チェック
        if random.random() > self.probability:
            return False
        
        # 条件チェック
        try:
            return all(condition(context) for condition in self.conditions)
        except Exception as e:
            logger.warning(f"Transition condition failed: {e}")
            return False
    
    def use(self, current_time: float):
        """遷移を使用（クールダウン開始）"""
        self.last_used = current_time


class ExtendedCharacterStateMachine:
    """拡張キャラクター状態マシン"""
    
    def __init__(self):
        """初期化"""
        self.current_state = ExtendedCharacterState.IDLE
        self.context = StateContext()
        self.transitions: Dict[Priority, List[ExtendedStateTransition]] = {
            priority: [] for priority in Priority
        }
        
        self.state_timer = 0.0
        self.total_time = 0.0
        
        # 状態継続時間設定
        self.state_durations = {
            ExtendedCharacterState.IDLE: (3.0, 10.0),
            ExtendedCharacterState.WALK: (2.0, 5.0),
            ExtendedCharacterState.WAVE: (1.0, 3.0),
            ExtendedCharacterState.UMBRELLA: (10.0, 30.0),
            ExtendedCharacterState.SHIVERING: (5.0, 15.0),
            ExtendedCharacterState.SUNBATHING: (20.0, 60.0),
            ExtendedCharacterState.HIDING: (8.0, 20.0),
            ExtendedCharacterState.STRETCHING: (3.0, 8.0),
            ExtendedCharacterState.YAWNING: (2.0, 5.0),
            ExtendedCharacterState.READING: (30.0, 120.0),
            ExtendedCharacterState.CELEBRATING: (5.0, 15.0),
            ExtendedCharacterState.PONDERING: (10.0, 30.0),
            ExtendedCharacterState.DANCING: (8.0, 20.0),
            ExtendedCharacterState.EATING: (10.0, 25.0),
            ExtendedCharacterState.SLEEPING: (300.0, 900.0)  # 5-15分
        }
        
        self.next_transition_time = self._get_next_transition_time()
        self._setup_transitions()
    
    def _setup_transitions(self):
        """状態遷移を設定"""
        # 最高優先度: ユーザーインタラクション
        self._add_user_interactions()
        
        # 高優先度: 天気反応
        self._add_weather_transitions()
        
        # 中優先度: 時間・季節反応
        self._add_time_transitions()
        
        # 低優先度: 自動遷移
        self._add_automatic_transitions()
    
    def _add_user_interactions(self):
        """ユーザーインタラクション遷移"""
        # クリック反応
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.WAVE,
            Priority.HIGHEST, 0.8,
            [lambda ctx: ctx.click_count > 0]
        )
        
        self.add_transition(
            ExtendedCharacterState.WALK, ExtendedCharacterState.CELEBRATING,
            Priority.HIGHEST, 0.6,
            [lambda ctx: ctx.click_count > 2]
        )
        
        # 頻繁なインタラクション時間での特別反応
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.DANCING,
            Priority.HIGHEST, 0.4,
            [lambda ctx: ctx.is_frequent_interaction_time() and ctx.click_count > 1]
        )
    
    def _add_weather_transitions(self):
        """天気反応遷移"""
        # 雨天時
        self.add_transition(
            ExtendedCharacterState.WALK, ExtendedCharacterState.UMBRELLA,
            Priority.HIGH, 0.9,
            [lambda ctx: ctx.weather in ['rain', 'drizzle']]
        )
        
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.READING,
            Priority.HIGH, 0.6,
            [lambda ctx: ctx.weather in ['rain', 'drizzle'] and 16 <= ctx.hour <= 22]
        )
        
        # 雷雨時
        self.add_transition(
            ExtendedCharacterState.WALK, ExtendedCharacterState.HIDING,
            Priority.HIGH, 0.95,
            [lambda ctx: ctx.weather == 'thunderstorm']
        )
        
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.HIDING,
            Priority.HIGH, 0.8,
            [lambda ctx: ctx.weather == 'thunderstorm']
        )
        
        # 雪天時
        self.add_transition(
            ExtendedCharacterState.WALK, ExtendedCharacterState.SHIVERING,
            Priority.HIGH, 0.7,
            [lambda ctx: ctx.weather == 'snow' or ctx.temperature < 5]
        )
        
        # 晴天・暑い時
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.SUNBATHING,
            Priority.HIGH, 0.5,
            [lambda ctx: ctx.weather == 'sunny' and ctx.temperature > 25 and 10 <= ctx.hour <= 16]
        )
        
        # 長期間同じ天気での反応変化
        self.add_transition(
            ExtendedCharacterState.UMBRELLA, ExtendedCharacterState.PONDERING,
            Priority.HIGH, 0.3,
            [lambda ctx: ctx.consecutive_weather_days > 3]
        )
    
    def _add_time_transitions(self):
        """時間・季節反応遷移"""
        # 朝の反応
        self.add_transition(
            ExtendedCharacterState.SLEEPING, ExtendedCharacterState.STRETCHING,
            Priority.MEDIUM, 0.8,
            [lambda ctx: 6 <= ctx.hour <= 8]
        )
        
        self.add_transition(
            ExtendedCharacterState.YAWNING, ExtendedCharacterState.STRETCHING,
            Priority.MEDIUM, 0.6,
            [lambda ctx: 6 <= ctx.hour <= 9]
        )
        
        # 昼食時間
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.EATING,
            Priority.MEDIUM, 0.4,
            [lambda ctx: 11 <= ctx.hour <= 13 or 18 <= ctx.hour <= 20]
        )
        
        # 夕方の読書時間
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.READING,
            Priority.MEDIUM, 0.3,
            [lambda ctx: 17 <= ctx.hour <= 21 and ctx.weather not in ['thunderstorm']]
        )
        
        # 夜の睡眠準備
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.YAWNING,
            Priority.MEDIUM, 0.6,
            [lambda ctx: 22 <= ctx.hour or ctx.hour <= 5]
        )
        
        self.add_transition(
            ExtendedCharacterState.YAWNING, ExtendedCharacterState.SLEEPING,
            Priority.MEDIUM, 0.8,
            [lambda ctx: 23 <= ctx.hour or ctx.hour <= 5]
        )
        
        # 季節反応
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.CELEBRATING,
            Priority.MEDIUM, 0.2,
            [lambda ctx: ctx.season == 'spring' and ctx.weather == 'sunny']
        )
    
    def _add_automatic_transitions(self):
        """自動遷移"""
        # 基本的なランダム遷移
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.WALK,
            Priority.LOW, 0.3, min_duration=5.0
        )
        
        self.add_transition(
            ExtendedCharacterState.WALK, ExtendedCharacterState.IDLE,
            Priority.LOW, 0.6, min_duration=3.0
        )
        
        self.add_transition(
            ExtendedCharacterState.IDLE, ExtendedCharacterState.PONDERING,
            Priority.LOW, 0.2, min_duration=8.0
        )
        
        # 長時間同じ状態での強制遷移
        self.add_transition(
            ExtendedCharacterState.READING, ExtendedCharacterState.STRETCHING,
            Priority.LOW, 0.8, min_duration=60.0
        )
        
        self.add_transition(
            ExtendedCharacterState.SUNBATHING, ExtendedCharacterState.WALK,
            Priority.LOW, 0.5, min_duration=45.0
        )
        
        # エネルギー低下時の遷移
        self.add_transition(
            ExtendedCharacterState.DANCING, ExtendedCharacterState.YAWNING,
            Priority.MEDIUM, 0.7,
            [lambda ctx: ctx.energy_level < 0.3]
        )
        
        # 全状態からIDLEへの復帰（セーフティネット）
        for state in ExtendedCharacterState:
            if state != ExtendedCharacterState.IDLE:
                self.add_transition(
                    state, ExtendedCharacterState.IDLE,
                    Priority.LOWEST, 0.1, min_duration=30.0
                )
    
    def add_transition(self, from_state: ExtendedCharacterState, to_state: ExtendedCharacterState,
                      priority: Priority, probability: float, conditions: Optional[List[Callable]] = None,
                      min_duration: float = 0.0, cooldown: float = 0.0):
        """状態遷移を追加"""
        transition = ExtendedStateTransition(
            from_state, to_state, priority, probability, conditions, min_duration, cooldown
        )
        self.transitions[priority].append(transition)
    
    def update(self, dt: float) -> Optional[ExtendedCharacterState]:
        """状態マシンを更新"""
        self.state_timer += dt
        self.total_time += dt
        self.context.total_uptime += dt
        
        # コンテキストの定期更新
        self._update_context()
        
        # 状態遷移チェック（優先度順）
        for priority in sorted(Priority, key=lambda p: p.value, reverse=True):
            new_state = self._try_priority_transitions(priority)
            if new_state:
                return self._change_state(new_state)
        
        # 自動遷移時間チェック
        if self.state_timer >= self.next_transition_time:
            auto_state = self._try_automatic_transition()
            if auto_state:
                return self._change_state(auto_state)
        
        return None
    
    def _update_context(self):
        """コンテキストの定期更新"""
        current_hour = datetime.now().hour
        if current_hour != self.context.hour:
            self.context.hour = current_hour
        
        # エネルギーレベル更新
        energy_change = self._calculate_energy_change()
        self.context.energy_level = max(0.0, min(1.0, self.context.energy_level + energy_change))
        
        # クリック数の減衰
        if self.context.click_count > 0:
            self.context.click_count = max(0, self.context.click_count - 0.01)
        
        # 季節更新
        new_season = self.context._get_current_season()
        if new_season != self.context.season:
            self.context.season = new_season
            logger.info(f"Season changed to: {new_season}")
    
    def _calculate_energy_change(self) -> float:
        """エネルギー変化を計算"""
        base_recovery = 0.001  # 基本回復量
        
        # 状態による消費・回復
        energy_effects = {
            ExtendedCharacterState.SLEEPING: 0.003,      # 大幅回復
            ExtendedCharacterState.SUNBATHING: 0.002,    # 回復
            ExtendedCharacterState.READING: 0.001,       # 軽い回復
            ExtendedCharacterState.IDLE: 0.0005,         # わずかな回復
            ExtendedCharacterState.DANCING: -0.002,      # 大きく消費
            ExtendedCharacterState.CELEBRATING: -0.001,  # 消費
            ExtendedCharacterState.HIDING: -0.0005,      # 軽い消費
        }
        
        state_effect = energy_effects.get(self.current_state, 0)
        
        # 時間による回復ボーナス
        if 22 <= self.context.hour or self.context.hour <= 6:
            base_recovery *= 1.5
        
        return base_recovery + state_effect
    
    def _try_priority_transitions(self, priority: Priority) -> Optional[ExtendedCharacterState]:
        """指定優先度の遷移を試行"""
        candidates = [
            t for t in self.transitions[priority]
            if (t.from_state == self.current_state and 
                t.can_transition(self.context, self.total_time, self.state_timer))
        ]
        
        if not candidates:
            return None
        
        # 確率重み付けで選択
        weights = [t.probability for t in candidates]
        if sum(weights) > 0:
            transition = random.choices(candidates, weights=weights)[0]
            transition.use(self.total_time)
            return transition.to_state
        
        return None
    
    def _try_automatic_transition(self) -> Optional[ExtendedCharacterState]:
        """自動遷移を試行"""
        return self._try_priority_transitions(Priority.LOW)
    
    def _change_state(self, new_state: ExtendedCharacterState) -> ExtendedCharacterState:
        """状態を変更"""
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_timer = 0.0
            self.next_transition_time = self._get_next_transition_time()
            
            # 履歴記録
            self.context.state_history.append({
                'from': old_state.value,
                'to': new_state.value,
                'time': self.total_time
            })
            
            # 履歴サイズ制限
            if len(self.context.state_history) > 100:
                self.context.state_history = self.context.state_history[-100:]
            
            logger.info(f"State transition: {old_state.value} -> {new_state.value}")
        
        return self.current_state
    
    def _get_next_transition_time(self) -> float:
        """次の遷移時間を計算"""
        duration_range = self.state_durations.get(self.current_state, (3.0, 8.0))
        return random.uniform(duration_range[0], duration_range[1])
    
    def force_state(self, state: ExtendedCharacterState):
        """強制的に状態を変更"""
        self._change_state(state)
    
    def on_click(self):
        """クリックイベント処理"""
        self.context.add_interaction()
    
    def on_weather_change(self, weather: str, temperature: Optional[float] = None):
        """天気変更イベント処理"""
        self.context.update_weather(weather, temperature)
    
    def get_current_state(self) -> ExtendedCharacterState:
        """現在の状態を取得"""
        return self.current_state
    
    def get_mood_indicator(self) -> str:
        """気分インジケーターを取得"""
        energy = self.context.energy_level
        weather = self.context.weather
        hour = self.context.hour
        
        # 状態による気分
        state_moods = {
            ExtendedCharacterState.CELEBRATING: 'ecstatic',
            ExtendedCharacterState.DANCING: 'joyful',
            ExtendedCharacterState.SUNBATHING: 'blissful',
            ExtendedCharacterState.READING: 'focused',
            ExtendedCharacterState.HIDING: 'anxious',
            ExtendedCharacterState.SHIVERING: 'uncomfortable',
            ExtendedCharacterState.SLEEPING: 'peaceful',
            ExtendedCharacterState.EATING: 'satisfied'
        }
        
        if self.current_state in state_moods:
            return state_moods[self.current_state]
        
        # エネルギーレベルによる基本気分
        if energy < 0.2:
            return 'exhausted'
        elif energy < 0.4:
            return 'tired'
        elif energy > 0.8:
            return 'energetic'
        
        # 時間・天気による気分
        if weather == 'sunny' and 6 <= hour < 18:
            return 'cheerful'
        elif weather == 'thunderstorm':
            return 'nervous'
        elif 22 <= hour or hour < 6:
            return 'sleepy'
        else:
            return 'neutral'
    
    def get_next_state(self, context: StateContext) -> ExtendedCharacterState:
        """
        次の状態を取得（実際の遷移は行わず候補を返す）
        
        Args:
            context: 状態コンテキスト
            
        Returns:
            次の状態候補
        """
        # コンテキストを更新
        old_context = self.context
        self.context = context
        
        try:
            # 高優先度から順に遷移候補をチェック
            for priority in sorted(Priority, key=lambda p: p.value, reverse=True):
                next_state = self._try_priority_transitions(priority)
                if next_state:
                    return next_state
            
            # 自動遷移をチェック
            if self.state_timer >= self.next_transition_time:
                auto_state = self._try_automatic_transition()
                if auto_state:
                    return auto_state
            
            # 候補がない場合は現在の状態を維持
            return self.current_state
            
        finally:
            # 元のコンテキストを復元
            self.context = old_context
    
    def transition_to(self, target_state: ExtendedCharacterState, context: StateContext) -> bool:
        """
        指定された状態に遷移を試行
        
        Args:
            target_state: 遷移先状態
            context: 状態コンテキスト
            
        Returns:
            遷移が成功した場合True
        """
        # コンテキストを更新
        self.context = context
        
        # 遷移実行
        if target_state != self.current_state:
            self._change_state(target_state)
            return True
        
        return False
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得"""
        return {
            'current_state': self.current_state.value,
            'state_timer': round(self.state_timer, 2),
            'energy': round(self.context.energy_level, 2),
            'weather': self.context.weather,
            'temperature': self.context.temperature,
            'season': self.context.season,
            'hour': self.context.hour,
            'click_count': round(self.context.click_count, 1),
            'consecutive_weather_days': self.context.consecutive_weather_days,
            'mood': self.get_mood_indicator(),
            'interactions_today': self.context.daily_interactions,
            'frequent_time': self.context.is_frequent_interaction_time()
        }