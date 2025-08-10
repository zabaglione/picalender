"""
天気特化キャラクター動作システム

TASK-402 Step 5/6: 天気条件に応じた詳細なキャラクター行動制御
"""

import logging
import random
import math
from typing import Dict, Any, Optional, List, Tuple, Set
from enum import Enum
from datetime import datetime, timedelta

from .extended_state_machine import ExtendedCharacterState, StateContext

logger = logging.getLogger(__name__)


class WeatherIntensity(Enum):
    """天気の強度"""
    LIGHT = "light"      # 軽い
    MODERATE = "moderate" # 中程度
    HEAVY = "heavy"      # 強い
    SEVERE = "severe"    # 激しい


class WeatherCondition:
    """天気条件の詳細定義"""
    
    def __init__(self, weather_type: str, intensity: WeatherIntensity = WeatherIntensity.MODERATE,
                 temperature: Optional[float] = None, humidity: Optional[float] = None,
                 wind_speed: Optional[float] = None, visibility: Optional[float] = None):
        """
        初期化
        
        Args:
            weather_type: 天気タイプ
            intensity: 強度
            temperature: 気温（摂氏）
            humidity: 湿度（%）
            wind_speed: 風速（m/s）
            visibility: 視界（km）
        """
        self.weather_type = weather_type
        self.intensity = intensity
        self.temperature = temperature or 20.0
        self.humidity = humidity or 50.0
        self.wind_speed = wind_speed or 0.0
        self.visibility = visibility or 10.0
        
        # 体感温度計算
        self.feels_like = self._calculate_feels_like()
        
        # 不快指数計算
        self.discomfort_index = self._calculate_discomfort_index()
    
    def _calculate_feels_like(self) -> float:
        """体感温度を計算"""
        temp = self.temperature
        humidity = self.humidity
        wind = self.wind_speed
        
        if temp >= 27:
            # 暑い場合：湿度を考慮した暑さ指数
            return temp + 0.36 * (humidity / 100) * temp - 14.4
        elif temp <= 10:
            # 寒い場合：風冷効果を考慮
            if wind > 1.34:
                wind_chill = 13.12 + 0.6215 * temp - 11.37 * (wind ** 0.16) + 0.3965 * temp * (wind ** 0.16)
                return min(temp, wind_chill)
            else:
                return temp
        else:
            # 中間温度：基本的には気温そのまま
            return temp
    
    def _calculate_discomfort_index(self) -> float:
        """不快指数を計算"""
        temp = self.temperature
        humidity = self.humidity
        
        # 不快指数 = 0.81 * T + 0.01 * H * (0.99 * T - 14.3) + 46.3
        di = 0.81 * temp + 0.01 * humidity * (0.99 * temp - 14.3) + 46.3
        return di
    
    def get_comfort_level(self) -> str:
        """快適度レベルを取得"""
        di = self.discomfort_index
        
        if di < 55:
            return 'very_comfortable'
        elif di < 60:
            return 'comfortable'
        elif di < 65:
            return 'slightly_uncomfortable'
        elif di < 70:
            return 'uncomfortable'
        elif di < 75:
            return 'quite_uncomfortable'
        elif di < 80:
            return 'very_uncomfortable'
        else:
            return 'extremely_uncomfortable'
    
    def get_weather_severity(self) -> float:
        """天気の厳しさを0-1で取得"""
        severity = 0.0
        
        # 気温による厳しさ
        feels_like = self.feels_like
        if feels_like < -10 or feels_like > 35:
            severity += 0.4
        elif feels_like < 0 or feels_like > 30:
            severity += 0.2
        elif feels_like < 5 or feels_like > 28:
            severity += 0.1
        
        # 天気タイプによる厳しさ
        severity_map = {
            'thunderstorm': 0.3,
            'tornado': 0.4,
            'hurricane': 0.4,
            'blizzard': 0.3,
            'heavy_rain': 0.2,
            'heavy_snow': 0.2,
            'fog': 0.1,
            'hail': 0.2
        }
        severity += severity_map.get(self.weather_type, 0.0)
        
        # 強度による厳しさ
        intensity_modifier = {
            WeatherIntensity.LIGHT: 0.0,
            WeatherIntensity.MODERATE: 0.1,
            WeatherIntensity.HEAVY: 0.2,
            WeatherIntensity.SEVERE: 0.3
        }
        severity += intensity_modifier.get(self.intensity, 0.0)
        
        # 風速による厳しさ
        if self.wind_speed > 15:
            severity += 0.2
        elif self.wind_speed > 10:
            severity += 0.1
        
        return min(1.0, severity)


class SeasonalBehaviorModifier:
    """季節行動修正"""
    
    def __init__(self):
        """初期化"""
        self.seasonal_preferences = {
            'spring': {
                'preferred_states': [ExtendedCharacterState.WALK, ExtendedCharacterState.CELEBRATING],
                'temperature_comfort': (15, 25),
                'activity_boost': 1.2,
                'mood_bonus': 0.1
            },
            'summer': {
                'preferred_states': [ExtendedCharacterState.SUNBATHING, ExtendedCharacterState.DANCING],
                'temperature_comfort': (20, 30),
                'activity_boost': 1.1,
                'heat_sensitivity': 1.3
            },
            'autumn': {
                'preferred_states': [ExtendedCharacterState.READING, ExtendedCharacterState.PONDERING],
                'temperature_comfort': (10, 20),
                'activity_boost': 0.9,
                'contemplation_bonus': 1.2
            },
            'winter': {
                'preferred_states': [ExtendedCharacterState.SLEEPING, ExtendedCharacterState.SHIVERING],
                'temperature_comfort': (5, 15),
                'activity_boost': 0.8,
                'cold_sensitivity': 1.4
            }
        }
    
    def get_seasonal_modifier(self, season: str, context: StateContext) -> Dict[str, float]:
        """季節修正値を取得"""
        prefs = self.seasonal_preferences.get(season, {})
        
        modifiers = {
            'activity_level': prefs.get('activity_boost', 1.0),
            'mood_bonus': prefs.get('mood_bonus', 0.0),
            'heat_sensitivity': prefs.get('heat_sensitivity', 1.0),
            'cold_sensitivity': prefs.get('cold_sensitivity', 1.0),
            'contemplation_bonus': prefs.get('contemplation_bonus', 1.0)
        }
        
        return modifiers
    
    def get_preferred_states(self, season: str) -> List[ExtendedCharacterState]:
        """季節の好ましい状態を取得"""
        return self.seasonal_preferences.get(season, {}).get('preferred_states', [])


class WeatherBehaviorPattern:
    """天気行動パターン"""
    
    def __init__(self, weather_type: str, required_states: List[ExtendedCharacterState],
                 probability_modifiers: Dict[ExtendedCharacterState, float],
                 duration_modifiers: Dict[ExtendedCharacterState, float],
                 activation_conditions: List[callable]):
        """
        初期化
        
        Args:
            weather_type: 対象天気タイプ
            required_states: 必須状態（この天気時に必ず考慮される状態）
            probability_modifiers: 状態遷移確率修正
            duration_modifiers: 状態継続時間修正
            activation_conditions: 発動条件
        """
        self.weather_type = weather_type
        self.required_states = required_states
        self.probability_modifiers = probability_modifiers
        self.duration_modifiers = duration_modifiers
        self.activation_conditions = activation_conditions
    
    def is_active(self, weather_condition: WeatherCondition, context: StateContext) -> bool:
        """パターンが発動するかチェック"""
        if weather_condition.weather_type != self.weather_type:
            return False
        
        return all(condition(weather_condition, context) for condition in self.activation_conditions)
    
    def get_state_probability(self, state: ExtendedCharacterState) -> float:
        """状態遷移確率修正値を取得"""
        return self.probability_modifiers.get(state, 1.0)
    
    def get_state_duration_modifier(self, state: ExtendedCharacterState) -> float:
        """状態継続時間修正値を取得"""
        return self.duration_modifiers.get(state, 1.0)


class WeatherSpecificBehaviorSystem:
    """天気特化行動システム"""
    
    def __init__(self):
        """初期化"""
        self.seasonal_modifier = SeasonalBehaviorModifier()
        self.behavior_patterns: List[WeatherBehaviorPattern] = []
        self.weather_memory: List[Tuple[datetime, WeatherCondition]] = []
        self.adaptation_level = 0.0  # 天気への適応度 (0.0 - 1.0)
        
        self._setup_weather_patterns()
    
    def _setup_weather_patterns(self):
        """天気パターンを設定"""
        # 雨天パターン
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'rain',
            [ExtendedCharacterState.UMBRELLA, ExtendedCharacterState.READING],
            {
                ExtendedCharacterState.UMBRELLA: 2.0,
                ExtendedCharacterState.READING: 1.5,
                ExtendedCharacterState.WALK: 0.3,
                ExtendedCharacterState.DANCING: 0.2
            },
            {
                ExtendedCharacterState.UMBRELLA: 1.5,
                ExtendedCharacterState.READING: 2.0
            },
            [lambda w, c: w.intensity in [WeatherIntensity.LIGHT, WeatherIntensity.MODERATE]]
        ))
        
        # 激しい雨パターン
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'rain',
            [ExtendedCharacterState.HIDING, ExtendedCharacterState.PONDERING],
            {
                ExtendedCharacterState.HIDING: 3.0,
                ExtendedCharacterState.PONDERING: 1.8,
                ExtendedCharacterState.UMBRELLA: 0.5,
                ExtendedCharacterState.WALK: 0.1
            },
            {
                ExtendedCharacterState.HIDING: 2.0,
                ExtendedCharacterState.PONDERING: 1.5
            },
            [lambda w, c: w.intensity in [WeatherIntensity.HEAVY, WeatherIntensity.SEVERE]]
        ))
        
        # 雷雨パターン
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'thunderstorm',
            [ExtendedCharacterState.HIDING],
            {
                ExtendedCharacterState.HIDING: 5.0,
                ExtendedCharacterState.SHIVERING: 2.0,
                ExtendedCharacterState.WALK: 0.1,
                ExtendedCharacterState.DANCING: 0.05
            },
            {
                ExtendedCharacterState.HIDING: 1.8
            },
            [lambda w, c: True]  # 雷雨は常に発動
        ))
        
        # 雪天パターン（軽い雪）
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'snow',
            [ExtendedCharacterState.CELEBRATING, ExtendedCharacterState.WALK],
            {
                ExtendedCharacterState.CELEBRATING: 1.5,
                ExtendedCharacterState.WALK: 1.2,
                ExtendedCharacterState.SUNBATHING: 0.1
            },
            {
                ExtendedCharacterState.CELEBRATING: 1.3
            },
            [lambda w, c: w.intensity == WeatherIntensity.LIGHT and w.temperature > -5]
        ))
        
        # 雪天パターン（寒い雪）
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'snow',
            [ExtendedCharacterState.SHIVERING, ExtendedCharacterState.SLEEPING],
            {
                ExtendedCharacterState.SHIVERING: 3.0,
                ExtendedCharacterState.SLEEPING: 1.5,
                ExtendedCharacterState.WALK: 0.4,
                ExtendedCharacterState.CELEBRATING: 0.3
            },
            {
                ExtendedCharacterState.SHIVERING: 1.8,
                ExtendedCharacterState.SLEEPING: 1.4
            },
            [lambda w, c: w.temperature <= -5 or w.intensity in [WeatherIntensity.HEAVY, WeatherIntensity.SEVERE]]
        ))
        
        # 晴天パターン（快適）
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'sunny',
            [ExtendedCharacterState.SUNBATHING, ExtendedCharacterState.DANCING],
            {
                ExtendedCharacterState.SUNBATHING: 2.0,
                ExtendedCharacterState.DANCING: 1.5,
                ExtendedCharacterState.WALK: 1.3,
                ExtendedCharacterState.CELEBRATING: 1.2
            },
            {
                ExtendedCharacterState.SUNBATHING: 2.0,
                ExtendedCharacterState.DANCING: 1.2
            },
            [lambda w, c: 18 <= w.feels_like <= 28]
        ))
        
        # 晴天パターン（暑すぎる）
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'sunny',
            [ExtendedCharacterState.SLEEPING, ExtendedCharacterState.IDLE],
            {
                ExtendedCharacterState.SLEEPING: 1.8,
                ExtendedCharacterState.IDLE: 1.5,
                ExtendedCharacterState.SUNBATHING: 0.5,
                ExtendedCharacterState.DANCING: 0.3
            },
            {
                ExtendedCharacterState.SLEEPING: 1.3
            },
            [lambda w, c: w.feels_like > 35]
        ))
        
        # 曇天パターン
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'cloudy',
            [ExtendedCharacterState.PONDERING, ExtendedCharacterState.READING],
            {
                ExtendedCharacterState.PONDERING: 1.4,
                ExtendedCharacterState.READING: 1.3,
                ExtendedCharacterState.WALK: 1.1
            },
            {
                ExtendedCharacterState.PONDERING: 1.5,
                ExtendedCharacterState.READING: 1.4
            },
            [lambda w, c: True]
        ))
        
        # 霧パターン
        self.behavior_patterns.append(WeatherBehaviorPattern(
            'fog',
            [ExtendedCharacterState.PONDERING, ExtendedCharacterState.WALK],
            {
                ExtendedCharacterState.PONDERING: 2.0,
                ExtendedCharacterState.WALK: 0.7,  # 慎重な歩行
                ExtendedCharacterState.DANCING: 0.4
            },
            {
                ExtendedCharacterState.PONDERING: 1.8,
                ExtendedCharacterState.WALK: 0.8
            },
            [lambda w, c: w.visibility < 5.0]
        ))
    
    def update_weather_condition(self, weather_type: str, intensity: str = 'moderate',
                               temperature: Optional[float] = None, humidity: Optional[float] = None,
                               wind_speed: Optional[float] = None, visibility: Optional[float] = None):
        """天気条件を更新"""
        try:
            intensity_enum = WeatherIntensity(intensity)
        except ValueError:
            intensity_enum = WeatherIntensity.MODERATE
        
        condition = WeatherCondition(
            weather_type, intensity_enum, temperature, humidity, wind_speed, visibility
        )
        
        # 天気記録に追加
        self.weather_memory.append((datetime.now(), condition))
        
        # メモリサイズ制限（最新100件）
        if len(self.weather_memory) > 100:
            self.weather_memory = self.weather_memory[-100:]
        
        # 適応度更新
        self._update_adaptation_level(condition)
        
        return condition
    
    def _update_adaptation_level(self, condition: WeatherCondition):
        """天気への適応度を更新"""
        # 同じような天気が続くと適応度が上がる
        recent_weather = [w[1] for w in self.weather_memory[-10:]]  # 最近10回
        similar_count = sum(1 for w in recent_weather 
                           if w.weather_type == condition.weather_type)
        
        if similar_count >= 5:
            self.adaptation_level = min(1.0, self.adaptation_level + 0.1)
        elif similar_count <= 2:
            self.adaptation_level = max(0.0, self.adaptation_level - 0.05)
    
    def get_behavior_modifiers(self, weather_condition: WeatherCondition, 
                             context: StateContext) -> Dict[str, Any]:
        """行動修正値を取得"""
        modifiers = {
            'state_probabilities': {},
            'duration_modifiers': {},
            'forced_states': [],
            'blocked_states': [],
            'mood_adjustment': 0.0,
            'energy_adjustment': 0.0
        }
        
        # 季節修正を適用
        seasonal_mods = self.seasonal_modifier.get_seasonal_modifier(context.season, context)
        
        # アクティブな天気パターンを取得
        active_patterns = [p for p in self.behavior_patterns 
                          if p.is_active(weather_condition, context)]
        
        # 各パターンの修正値を統合
        for pattern in active_patterns:
            for state in ExtendedCharacterState:
                prob_mod = pattern.get_state_probability(state)
                if state not in modifiers['state_probabilities']:
                    modifiers['state_probabilities'][state] = prob_mod
                else:
                    modifiers['state_probabilities'][state] *= prob_mod
                
                dur_mod = pattern.get_state_duration_modifier(state)
                if state not in modifiers['duration_modifiers']:
                    modifiers['duration_modifiers'][state] = dur_mod
                else:
                    modifiers['duration_modifiers'][state] *= dur_mod
        
        # 季節による活動レベル調整
        activity_mod = seasonal_mods.get('activity_level', 1.0)
        for state in [ExtendedCharacterState.WALK, ExtendedCharacterState.DANCING, 
                     ExtendedCharacterState.CELEBRATING]:
            if state in modifiers['state_probabilities']:
                modifiers['state_probabilities'][state] *= activity_mod
        
        # 気温による気分・エネルギー調整
        comfort_level = weather_condition.get_comfort_level()
        comfort_adjustments = {
            'very_comfortable': (0.1, 0.1),
            'comfortable': (0.05, 0.05),
            'slightly_uncomfortable': (0.0, 0.0),
            'uncomfortable': (-0.05, -0.05),
            'quite_uncomfortable': (-0.1, -0.1),
            'very_uncomfortable': (-0.15, -0.15),
            'extremely_uncomfortable': (-0.2, -0.2)
        }
        
        mood_adj, energy_adj = comfort_adjustments.get(comfort_level, (0.0, 0.0))
        modifiers['mood_adjustment'] = mood_adj
        modifiers['energy_adjustment'] = energy_adj
        
        # 適応度による修正
        adaptation_bonus = self.adaptation_level * 0.1
        modifiers['mood_adjustment'] += adaptation_bonus
        modifiers['energy_adjustment'] += adaptation_bonus * 0.5
        
        # 天気の厳しさによるブロック
        severity = weather_condition.get_weather_severity()
        if severity > 0.7:
            modifiers['blocked_states'].extend([
                ExtendedCharacterState.SUNBATHING,
                ExtendedCharacterState.DANCING
            ])
        
        # 強制状態（極端な条件）
        if weather_condition.feels_like < -10:
            modifiers['forced_states'].append(ExtendedCharacterState.SHIVERING)
        elif weather_condition.weather_type == 'thunderstorm' and random.random() < 0.8:
            modifiers['forced_states'].append(ExtendedCharacterState.HIDING)
        
        return modifiers
    
    def get_weather_description(self, weather_condition: WeatherCondition) -> str:
        """天気の詳細説明を取得"""
        desc = f"{weather_condition.weather_type}"
        
        if weather_condition.intensity != WeatherIntensity.MODERATE:
            desc = f"{weather_condition.intensity.value} {desc}"
        
        desc += f" ({weather_condition.temperature:.1f}°C, feels like {weather_condition.feels_like:.1f}°C)"
        
        comfort = weather_condition.get_comfort_level().replace('_', ' ')
        desc += f", {comfort}"
        
        return desc
    
    def get_adaptation_status(self) -> Dict[str, Any]:
        """適応状況を取得"""
        recent_weather_types = {}
        for timestamp, condition in self.weather_memory[-20:]:  # 最近20回
            weather_type = condition.weather_type
            recent_weather_types[weather_type] = recent_weather_types.get(weather_type, 0) + 1
        
        most_common = max(recent_weather_types.items(), key=lambda x: x[1]) if recent_weather_types else ("none", 0)
        
        return {
            'adaptation_level': self.adaptation_level,
            'most_common_weather': most_common[0],
            'weather_variety': len(recent_weather_types),
            'total_weather_records': len(self.weather_memory)
        }
    
    def simulate_seasonal_change(self, new_season: str, context: StateContext):
        """季節変化をシミュレート"""
        if new_season != context.season:
            old_season = context.season
            context.season = new_season
            
            # 季節変化による適応レベルリセット
            self.adaptation_level *= 0.7  # 新しい季節には少し適応が必要
            
            logger.info(f"Season changed from {old_season} to {new_season}")
            
            # 季節の好ましい状態を取得
            preferred_states = self.seasonal_modifier.get_preferred_states(new_season)
            return {
                'season_changed': True,
                'new_season': new_season,
                'preferred_states': preferred_states
            }
        
        return {'season_changed': False}
    
    def get_weather_trend_analysis(self) -> Dict[str, Any]:
        """天気傾向分析"""
        if len(self.weather_memory) < 5:
            return {'insufficient_data': True}
        
        recent_conditions = [w[1] for w in self.weather_memory[-10:]]
        
        # 平均気温
        avg_temp = sum(w.temperature for w in recent_conditions) / len(recent_conditions)
        temp_trend = 'stable'
        
        if len(recent_conditions) >= 5:
            early_temp = sum(w.temperature for w in recent_conditions[:5]) / 5
            late_temp = sum(w.temperature for w in recent_conditions[-5:]) / 5
            
            if late_temp - early_temp > 2:
                temp_trend = 'warming'
            elif early_temp - late_temp > 2:
                temp_trend = 'cooling'
        
        # 天気安定性
        weather_types = [w.weather_type for w in recent_conditions]
        stability = len(set(weather_types)) / len(weather_types)  # 低いほど安定
        
        return {
            'insufficient_data': False,
            'average_temperature': avg_temp,
            'temperature_trend': temp_trend,
            'weather_stability': 1.0 - stability,  # 高いほど安定
            'dominant_weather': max(set(weather_types), key=weather_types.count),
            'comfort_score': sum(1 for w in recent_conditions 
                               if w.get_comfort_level() in ['comfortable', 'very_comfortable']) / len(recent_conditions)
        }