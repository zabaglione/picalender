"""
天気エフェクトマネージャー

天気状態に応じたエフェクトを管理
"""

import logging
from typing import Dict, Optional, Any
import pygame

from .particle_system import (
    RainParticleSystem,
    SnowParticleSystem,
    FogLayer,
    LightningEffect
)

logger = logging.getLogger(__name__)


class WeatherEffects:
    """
    天気エフェクト管理クラス
    
    現在の天気に応じて適切なエフェクトを表示
    """
    
    def __init__(self, screen_width: int, screen_height: int, config: Any = None):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
            config: 設定オブジェクト
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = config
        
        # エフェクトの有効/無効
        self.enabled = config.get('effects.enabled', True) if config else True
        
        # エフェクト強度
        self.intensity = config.get('effects.intensity', 0.5) if config else 0.5
        
        # 各エフェクトインスタンス
        self.effects: Dict[str, Any] = {}
        self.active_effects = []
        
        # エフェクトを初期化
        self._initialize_effects()
        
        # 現在の天気状態
        self.current_weather = None
    
    def _initialize_effects(self) -> None:
        """エフェクトを初期化"""
        try:
            # 雨エフェクト
            self.effects['rain'] = RainParticleSystem(
                self.screen_width, 
                self.screen_height,
                self.intensity
            )
            
            # 雪エフェクト
            self.effects['snow'] = SnowParticleSystem(
                self.screen_width,
                self.screen_height,
                self.intensity
            )
            
            # 霧エフェクト
            self.effects['fog'] = FogLayer(
                self.screen_width,
                self.screen_height,
                self.intensity
            )
            
            # 雷エフェクト
            self.effects['thunder'] = LightningEffect(
                self.screen_width,
                self.screen_height
            )
            
            logger.info("Weather effects initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize effects: {e}")
            self.enabled = False
    
    def set_weather(self, weather_type: str) -> None:
        """
        天気タイプを設定
        
        Args:
            weather_type: 天気タイプ（sunny, rain, snow, thunder, fog, cloudy, partly_cloudy）
        """
        if not self.enabled:
            return
        
        self.current_weather = weather_type
        self.active_effects.clear()
        
        # 天気タイプに応じてエフェクトを選択
        if weather_type == 'rain':
            self.active_effects.append(self.effects['rain'])
            
        elif weather_type == 'thunder':
            self.active_effects.append(self.effects['rain'])
            self.active_effects.append(self.effects['thunder'])
            
        elif weather_type == 'snow':
            self.active_effects.append(self.effects['snow'])
            
        elif weather_type == 'fog':
            self.active_effects.append(self.effects['fog'])
        
        logger.info(f"Weather effects set to: {weather_type}")
    
    def update(self, dt: float) -> None:
        """
        エフェクトを更新
        
        Args:
            dt: デルタタイム（秒）
        """
        if not self.enabled:
            return
        
        for effect in self.active_effects:
            effect.update(dt)
    
    def render(self, screen: pygame.Surface) -> None:
        """
        エフェクトを描画
        
        Args:
            screen: 描画対象サーフェス
        """
        if not self.enabled:
            return
        
        for effect in self.active_effects:
            effect.render(screen)
    
    def set_intensity(self, intensity: float) -> None:
        """
        エフェクト強度を設定
        
        Args:
            intensity: 強度（0-1）
        """
        self.intensity = max(0, min(1, intensity))
        
        # 各エフェクトの強度を更新
        if 'rain' in self.effects:
            self.effects['rain'].intensity = self.intensity
        
        if 'snow' in self.effects:
            self.effects['snow'].intensity = self.intensity
        
        if 'fog' in self.effects:
            self.effects['fog'].density = self.intensity
    
    def set_enabled(self, enabled: bool) -> None:
        """
        エフェクトの有効/無効を設定
        
        Args:
            enabled: 有効にする場合True
        """
        self.enabled = enabled
        
        if not enabled:
            self.active_effects.clear()
    
    def clear(self) -> None:
        """全エフェクトをクリア"""
        for effect in self.effects.values():
            if hasattr(effect, 'clear'):
                effect.clear()
        
        self.active_effects.clear()
    
    def trigger_lightning(self) -> None:
        """雷を手動でトリガー"""
        if 'thunder' in self.effects:
            self.effects['thunder'].trigger()


class WeatherEffectRenderer:
    """
    天気エフェクトレンダラー
    
    WeatherRendererと統合して使用
    """
    
    def __init__(self, screen_width: int, screen_height: int, config: Any = None):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
            config: 設定オブジェクト
        """
        self.weather_effects = WeatherEffects(screen_width, screen_height, config)
        self.auto_update = config.get('effects.auto_update', True) if config else True
        self._last_weather = None
    
    def update_from_weather_data(self, weather_data: Optional[Dict[str, Any]]) -> None:
        """
        天気データからエフェクトを自動更新
        
        Args:
            weather_data: 天気データ
        """
        if not self.auto_update or not weather_data:
            return
        
        # 現在の天気アイコンを取得
        if 'current' in weather_data:
            icon = weather_data['current'].get('icon', 'cloudy')
            
            # アイコンが変わった場合のみ更新
            if icon != self._last_weather:
                self.weather_effects.set_weather(icon)
                self._last_weather = icon
                
                # 降水確率に応じて強度を調整
                if 'forecasts' in weather_data and weather_data['forecasts']:
                    pop = weather_data['forecasts'][0].get('pop', 0)
                    intensity = min(1.0, pop / 100.0 + 0.3)
                    self.weather_effects.set_intensity(intensity)
    
    def update(self, dt: float) -> None:
        """
        更新
        
        Args:
            dt: デルタタイム（秒）
        """
        self.weather_effects.update(dt)
    
    def render(self, screen: pygame.Surface) -> None:
        """
        描画
        
        Args:
            screen: 描画対象サーフェス
        """
        self.weather_effects.render(screen)
    
    def set_weather(self, weather_type: str) -> None:
        """
        天気タイプを手動設定
        
        Args:
            weather_type: 天気タイプ
        """
        self.weather_effects.set_weather(weather_type)
        self._last_weather = weather_type
    
    def set_enabled(self, enabled: bool) -> None:
        """
        有効/無効を設定
        
        Args:
            enabled: 有効にする場合True
        """
        self.weather_effects.set_enabled(enabled)