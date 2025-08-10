"""
天気対応キャラクターレンダラー

TASK-402 Step 5/6: 天気条件に応じたキャラクター表示システム
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .extended_animation_system import ExtendedCharacterAnimator
from .extended_state_machine import ExtendedCharacterStateMachine, StateContext, ExtendedCharacterState
from .weather_behavior_system import WeatherSpecificBehaviorSystem, WeatherCondition, WeatherIntensity

logger = logging.getLogger(__name__)


class WeatherAwareCharacterRenderer:
    """天気対応キャラクターレンダラー"""
    
    def __init__(self, sprite_sheet_path: str, metadata_path: Optional[str] = None):
        """
        初期化
        
        Args:
            sprite_sheet_path: スプライトシート画像パス
            metadata_path: メタデータJSONパス
        """
        self.animator = ExtendedCharacterAnimator(sprite_sheet_path, metadata_path)
        self.state_machine = ExtendedCharacterStateMachine()
        self.weather_system = WeatherSpecificBehaviorSystem()
        
        # 現在の状態
        self.current_weather: Optional[WeatherCondition] = None
        self.current_context = StateContext()
        self.last_weather_update = 0.0
        self.last_state_update = 0.0
        
        # 設定
        self.weather_update_interval = 5.0  # 天気更新間隔（秒）
        self.state_update_interval = 1.0    # 状態更新間隔（秒）
        
        logger.info("Weather-aware character renderer initialized")
    
    def update_weather(self, weather_type: str, intensity: str = 'moderate',
                      temperature: Optional[float] = None, humidity: Optional[float] = None,
                      wind_speed: Optional[float] = None, visibility: Optional[float] = None):
        """
        天気情報を更新
        
        Args:
            weather_type: 天気タイプ
            intensity: 強度
            temperature: 気温（摂氏）
            humidity: 湿度（%）
            wind_speed: 風速（m/s）
            visibility: 視界（km）
        """
        self.current_weather = self.weather_system.update_weather_condition(
            weather_type, intensity, temperature, humidity, wind_speed, visibility
        )
        self.last_weather_update = time.time()
        
        logger.info(f"Weather updated: {self.weather_system.get_weather_description(self.current_weather)}")
    
    def update_context(self, season: str = None, time_of_day: str = None, 
                      energy_level: float = None, mood: str = None,
                      location: str = None):
        """
        状況コンテキストを更新
        
        Args:
            season: 季節
            time_of_day: 時間帯
            energy_level: エネルギーレベル（0.0-1.0）
            mood: 気分
            location: 場所
        """
        if season is not None:
            old_season = self.current_context.season
            self.current_context.season = season
            
            # 季節変化のシミュレーション
            seasonal_change = self.weather_system.simulate_seasonal_change(season, self.current_context)
            if seasonal_change.get('season_changed', False):
                logger.info(f"Season changed to {season}")
        
        if time_of_day is not None:
            self.current_context.time_of_day = time_of_day
        if energy_level is not None:
            self.current_context.energy_level = max(0.0, min(1.0, energy_level))
        if mood is not None:
            self.current_context.mood = mood
        if location is not None:
            self.current_context.location = location
        
        logger.debug(f"Context updated: season={self.current_context.season}, "
                    f"time={self.current_context.time_of_day}, "
                    f"energy={self.current_context.energy_level:.2f}, "
                    f"mood={self.current_context.mood}")
    
    def update(self, dt: float):
        """
        レンダラーの更新
        
        Args:
            dt: デルタタイム
        """
        current_time = time.time()
        
        # 状態機械の更新
        if current_time - self.last_state_update >= self.state_update_interval:
            self._update_character_state()
            self.last_state_update = current_time
        
        # アニメーターの更新
        self.animator.update(dt)
        
        # 状態機械の時間更新
        self.state_machine.update(dt)
    
    def _update_character_state(self):
        """キャラクターの状態を更新"""
        if not self.current_weather:
            return
        
        # 天気による行動修正を取得
        modifiers = self.weather_system.get_behavior_modifiers(
            self.current_weather, self.current_context
        )
        
        # 強制状態がある場合は優先
        forced_states = modifiers.get('forced_states', [])
        if forced_states:
            target_state = forced_states[0]  # 最初の強制状態を採用
            self._transition_to_state(target_state, modifiers)
            return
        
        # 状態機械による次の状態を取得
        next_state = self.state_machine.get_next_state(self.current_context)
        
        # ブロックされた状態をチェック
        blocked_states = modifiers.get('blocked_states', [])
        if next_state in blocked_states:
            # ブロックされた場合は代替状態を探す
            alternatives = [ExtendedCharacterState.IDLE, ExtendedCharacterState.PONDERING, 
                          ExtendedCharacterState.READING]
            for alt_state in alternatives:
                if alt_state not in blocked_states:
                    next_state = alt_state
                    break
        
        # 状態遷移を実行
        if next_state != self.state_machine.current_state:
            self._transition_to_state(next_state, modifiers)
    
    def _transition_to_state(self, target_state: ExtendedCharacterState, modifiers: Dict[str, Any]):
        """
        指定された状態に遷移
        
        Args:
            target_state: 遷移先状態
            modifiers: 行動修正値
        """
        # 状態機械を更新
        if self.state_machine.transition_to(target_state, self.current_context):
            # 気分調整を適用
            mood_adjustment = modifiers.get('mood_adjustment', 0.0)
            adjusted_mood = self._adjust_mood(self.current_context.mood, mood_adjustment)
            
            # アニメーション再生
            success = self.animator.play_for_state(target_state, adjusted_mood, True)
            
            if success:
                logger.debug(f"Transitioned to {target_state.value} with mood {adjusted_mood}")
            else:
                logger.warning(f"Failed to play animation for state {target_state.value}")
        else:
            logger.warning(f"Failed to transition to state {target_state.value}")
    
    def _adjust_mood(self, base_mood: str, adjustment: float) -> str:
        """
        気分を調整
        
        Args:
            base_mood: 基本気分
            adjustment: 調整値（-1.0 to 1.0）
            
        Returns:
            調整された気分
        """
        # 気分の階層マップ
        mood_scale = [
            'exhausted', 'tired', 'neutral', 'cheerful', 'joyful', 'ecstatic'
        ]
        
        try:
            current_index = mood_scale.index(base_mood)
        except ValueError:
            current_index = 2  # neutral
        
        # 調整値を適用
        adjustment_steps = int(adjustment * 2)  # -2 to 2 steps
        new_index = max(0, min(len(mood_scale) - 1, current_index + adjustment_steps))
        
        return mood_scale[new_index]
    
    def get_current_frame(self):
        """現在のフレームを取得"""
        return self.animator.get_current_frame()
    
    def get_current_state(self) -> ExtendedCharacterState:
        """現在の状態を取得"""
        return self.state_machine.current_state
    
    def get_current_animation(self) -> str:
        """現在のアニメーション名を取得"""
        return self.animator.controller.current_animation or 'idle'
    
    def get_weather_description(self) -> str:
        """現在の天気説明を取得"""
        if self.current_weather:
            return self.weather_system.get_weather_description(self.current_weather)
        return "No weather data"
    
    def get_adaptation_status(self) -> Dict[str, Any]:
        """適応状況を取得"""
        return self.weather_system.get_adaptation_status()
    
    def get_weather_trend_analysis(self) -> Dict[str, Any]:
        """天気傾向分析を取得"""
        return self.weather_system.get_weather_trend_analysis()
    
    def get_status(self) -> Dict[str, Any]:
        """レンダラーの状態を取得"""
        status = {
            'current_state': self.get_current_state().value,
            'current_animation': self.get_current_animation(),
            'is_transitioning': self.animator.is_transitioning(),
            'transition_progress': self.animator.get_transition_progress(),
            'weather_description': self.get_weather_description(),
            'context': {
                'season': self.current_context.season,
                'time_of_day': self.current_context.time_of_day,
                'energy_level': self.current_context.energy_level,
                'mood': self.current_context.mood,
                'location': self.current_context.location
            },
            'adaptation': self.get_adaptation_status()
        }
        
        if self.current_weather:
            status['weather_details'] = {
                'type': self.current_weather.weather_type,
                'intensity': self.current_weather.intensity.value,
                'temperature': self.current_weather.temperature,
                'feels_like': self.current_weather.feels_like,
                'comfort_level': self.current_weather.get_comfort_level(),
                'severity': self.current_weather.get_weather_severity()
            }
        
        return status
    
    def force_state(self, state: ExtendedCharacterState, mood: str = None):
        """
        強制的に指定状態に遷移
        
        Args:
            state: 強制遷移先状態
            mood: 気分（指定されない場合は現在の気分を維持）
        """
        if mood is None:
            mood = self.current_context.mood
        
        # 状態機械を強制更新
        self.state_machine.current_state = state
        
        # アニメーション再生
        success = self.animator.play_for_state(state, mood, True)
        
        logger.info(f"Forced transition to {state.value} with mood {mood}")
        return success
    
    def set_weather_update_interval(self, interval: float):
        """天気更新間隔を設定"""
        self.weather_update_interval = max(1.0, interval)
    
    def set_state_update_interval(self, interval: float):
        """状態更新間隔を設定"""
        self.state_update_interval = max(0.1, interval)
    
    def simulate_weather_scenario(self, scenario_name: str):
        """
        天気シナリオをシミュレート
        
        Args:
            scenario_name: シナリオ名
        """
        scenarios = {
            'sunny_day': {
                'weather_type': 'sunny',
                'intensity': 'moderate',
                'temperature': 24.0,
                'humidity': 45.0,
                'wind_speed': 2.0
            },
            'rainy_day': {
                'weather_type': 'rain',
                'intensity': 'moderate',
                'temperature': 18.0,
                'humidity': 85.0,
                'wind_speed': 5.0
            },
            'stormy_weather': {
                'weather_type': 'thunderstorm',
                'intensity': 'heavy',
                'temperature': 16.0,
                'humidity': 90.0,
                'wind_speed': 15.0
            },
            'snowy_day': {
                'weather_type': 'snow',
                'intensity': 'light',
                'temperature': -2.0,
                'humidity': 70.0,
                'wind_speed': 3.0
            },
            'heat_wave': {
                'weather_type': 'sunny',
                'intensity': 'severe',
                'temperature': 38.0,
                'humidity': 30.0,
                'wind_speed': 1.0
            },
            'foggy_morning': {
                'weather_type': 'fog',
                'intensity': 'heavy',
                'temperature': 12.0,
                'humidity': 95.0,
                'wind_speed': 0.5,
                'visibility': 2.0
            }
        }
        
        if scenario_name in scenarios:
            scenario = scenarios[scenario_name]
            self.update_weather(**scenario)
            logger.info(f"Applied weather scenario: {scenario_name}")
        else:
            logger.warning(f"Unknown weather scenario: {scenario_name}")
    
    def get_available_scenarios(self) -> list:
        """利用可能な天気シナリオ一覧を取得"""
        return [
            'sunny_day', 'rainy_day', 'stormy_weather', 
            'snowy_day', 'heat_wave', 'foggy_morning'
        ]