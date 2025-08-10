"""
天気情報レンダラー

現在の天気と3日間の予報を表示
"""

import pygame
import logging
import time
import math
import concurrent.futures
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime

from .renderable import Renderable

logger = logging.getLogger(__name__)


class WeatherRenderer(Renderable):
    """
    天気情報を表示するレンダラー
    
    現在の天気と3日間の予報を半透明パネル上に表示
    """
    
    def __init__(self, asset_manager: Any, config: Any, weather_provider: Any):
        """
        初期化
        
        Args:
            asset_manager: アセット管理オブジェクト
            config: 設定オブジェクト
            weather_provider: 天気プロバイダー
        """
        self.asset_manager = asset_manager
        self.config = config
        self.weather_provider = weather_provider
        
        # 表示位置とサイズ
        self.x = config.get('weather.position.x', 24)
        self.y = config.get('weather.position.y', 320)
        self.width = config.get('weather.panel.width', 420)
        self.height = config.get('weather.panel.height', 260)
        
        # パネル設定
        self.bg_color = config.get('weather.panel.bg_color', (0, 0, 0, 180))
        self.corner_radius = config.get('weather.panel.corner_radius', 10)
        
        # フォント設定
        self.font_size = config.get('weather.font.size', 22)
        self.font_size_large = config.get('weather.font.size_large', 36)
        self.font_color = config.get('weather.font.color', (255, 255, 255))
        
        # 更新間隔
        self.update_interval = config.get('weather.update_interval', 1800)  # 30分
        
        # オプション
        self.show_location = config.get('weather.show_location', True)
        self.animation_enabled = config.get('weather.animation.enabled', False)
        
        # エフェクト
        self.effects_enabled = config.get('weather.effects.enabled', False)
        self._weather_effects = None
        if self.effects_enabled:
            try:
                from ..effects.weather_effects import WeatherEffectRenderer
                screen_width = config.get('screen.width', 1024)
                screen_height = config.get('screen.height', 600)
                self._weather_effects = WeatherEffectRenderer(screen_width, screen_height, config)
            except ImportError:
                logger.warning("Weather effects module not available")
                self.effects_enabled = False
        
        # フォントを取得
        self.font = asset_manager.get_font('main', self.font_size)
        self.font_large = asset_manager.get_font('main', self.font_size_large)
        self.font_small = asset_manager.get_font('main', int(self.font_size * 0.8))
        
        # 状態管理
        self.visible = True
        self._dirty = True
        self._last_update = 0
        self._weather_data = None
        self._panel_surface = None
        self._icon_cache = {}
        
        # 非同期更新用
        self._update_future = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # 初回データ取得を試みる
        self._fetch_weather_data()
    
    def render(self, screen: pygame.Surface) -> None:
        """
        画面に天気情報を描画
        
        Args:
            screen: 描画対象のサーフェス
        """
        if not self.visible:
            return
        
        # パネル背景を描画
        if self._panel_surface is None:
            self._panel_surface = self.create_panel_surface()
        
        screen.blit(self._panel_surface, (self.x, self.y))
        
        # 天気データがある場合
        if self._weather_data:
            self._render_weather_data(screen)
        else:
            # データがない場合
            self._render_no_data(screen)
        
        self._dirty = False
    
    def render_effects(self, screen: pygame.Surface) -> None:
        """
        天気エフェクトを描画（別レイヤーとして）
        
        Args:
            screen: 描画対象のサーフェス
        """
        if self.effects_enabled and self._weather_effects:
            self._weather_effects.render(screen)
    
    def _render_weather_data(self, screen: pygame.Surface) -> None:
        """
        天気データを描画
        
        Args:
            screen: 描画対象のサーフェス
        """
        # 現在の天気を描画
        self._render_current_weather(screen)
        
        # 3日間予報を描画
        self._render_forecasts(screen)
        
        # 更新時刻を描画
        self._render_update_time(screen)
        
        # 位置情報を表示（オプション）
        if self.show_location:
            self._render_location(screen)
    
    def _render_current_weather(self, screen: pygame.Surface) -> None:
        """現在の天気を描画"""
        if 'current' not in self._weather_data:
            return
        
        current = self._weather_data['current']
        
        # 基準位置
        base_x = self.x + 20
        base_y = self.y + 20
        
        # 気温（大きく表示）
        temp_text = self.format_temperature(current['temperature'])
        temp_surface = self.font_large.render(temp_text, True, self.font_color)
        screen.blit(temp_surface, (base_x, base_y))
        
        # 天気アイコン
        icon_name = current.get('icon', 'cloudy')
        icon = self.get_weather_icon(icon_name)
        if icon:
            icon_x = base_x + temp_surface.get_width() + 20
            icon_y = base_y
            screen.blit(icon, (icon_x, icon_y))
        
        # 詳細情報（湿度、風速）
        detail_y = base_y + 50
        
        # 湿度
        humidity_text = f"湿度: {self.format_humidity(current['humidity'])}"
        humidity_surface = self.font_small.render(humidity_text, True, self.font_color)
        screen.blit(humidity_surface, (base_x, detail_y))
        
        # 風速
        wind_text = f"風速: {self.format_wind_speed(current['wind_speed'])}"
        wind_surface = self.font_small.render(wind_text, True, self.font_color)
        screen.blit(wind_surface, (base_x + 120, detail_y))
    
    def _render_forecasts(self, screen: pygame.Surface) -> None:
        """3日間予報を描画"""
        if 'forecasts' not in self._weather_data:
            return
        
        forecasts = self._weather_data['forecasts'][:3]  # 最初の3日分
        positions = self.calculate_forecast_positions()
        
        for i, (forecast, pos) in enumerate(zip(forecasts, positions)):
            self._render_single_forecast(screen, forecast, pos)
    
    def _render_single_forecast(self, screen: pygame.Surface, 
                                forecast: Dict[str, Any], 
                                position: Tuple[int, int]) -> None:
        """
        単一の予報を描画
        
        Args:
            screen: 描画対象
            forecast: 予報データ
            position: 描画位置
        """
        x, y = position
        
        # 日付
        date_text = self.format_forecast_date(forecast['date'])
        date_surface = self.font_small.render(date_text, True, self.font_color)
        screen.blit(date_surface, (x, y))
        
        # アイコン（小さめ）
        icon_name = forecast.get('icon', 'cloudy')
        icon = self.get_weather_icon(icon_name, size=48)
        if icon:
            icon_x = x + (100 - icon.get_width()) // 2
            icon_y = y + 25
            screen.blit(icon, (icon_x, icon_y))
        
        # 気温（最高/最低）
        temp_y = y + 80
        temp_text = f"{forecast['tmax']}°/{forecast['tmin']}°"
        temp_surface = self.font_small.render(temp_text, True, self.font_color)
        temp_x = x + (100 - temp_surface.get_width()) // 2
        screen.blit(temp_surface, (temp_x, temp_y))
        
        # 降水確率
        if 'pop' in forecast and forecast['pop'] > 0:
            pop_text = f"{forecast['pop']}%"
            pop_color = (100, 150, 255)  # 水色
            pop_surface = self.font_small.render(pop_text, True, pop_color)
            pop_x = x + (100 - pop_surface.get_width()) // 2
            screen.blit(pop_surface, (pop_x, temp_y + 20))
    
    def _render_update_time(self, screen: pygame.Surface) -> None:
        """更新時刻を描画"""
        if 'updated' not in self._weather_data:
            return
        
        update_time = datetime.fromtimestamp(self._weather_data['updated'])
        time_text = f"更新: {update_time.strftime('%H:%M')}"
        
        time_surface = self.font_small.render(time_text, True, (180, 180, 180))
        x = self.x + self.width - time_surface.get_width() - 10
        y = self.y + self.height - 25
        screen.blit(time_surface, (x, y))
    
    def _render_location(self, screen: pygame.Surface) -> None:
        """位置情報を描画"""
        if 'location' not in self._weather_data:
            return
        
        loc = self._weather_data['location']
        location_text = self.format_location(loc['lat'], loc['lon'])
        
        loc_surface = self.font_small.render(location_text, True, (180, 180, 180))
        x = self.x + 10
        y = self.y + self.height - 25
        screen.blit(loc_surface, (x, y))
    
    def _render_no_data(self, screen: pygame.Surface) -> None:
        """データがない場合の表示"""
        text = "天気データを取得中..."
        text_surface = self.font.render(text, True, self.font_color)
        
        x = self.x + (self.width - text_surface.get_width()) // 2
        y = self.y + (self.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (x, y))
    
    def update(self, dt: float) -> None:
        """
        状態を更新
        
        Args:
            dt: 前回の更新からの経過時間（秒）
        """
        # 累積時間を加算
        self._last_update += dt
        
        # 更新間隔チェック
        if self._last_update >= self.update_interval:
            self._fetch_weather_data()
            self._last_update = 0
        
        # エフェクトを更新
        if self.effects_enabled and self._weather_effects:
            self._weather_effects.update(dt)
    
    def _fetch_weather_data(self) -> None:
        """天気データを取得"""
        try:
            self._weather_data = self.weather_provider.fetch()
            self._dirty = True
            
            # エフェクトを更新
            if self.effects_enabled and self._weather_effects and self._weather_data:
                self._weather_effects.update_from_weather_data(self._weather_data)
                
        except Exception as e:
            logger.error(f"Weather data fetch error: {e}")
    
    def update_async(self) -> concurrent.futures.Future:
        """
        非同期で天気データを更新
        
        Returns:
            Future オブジェクト
        """
        if self._update_future and not self._update_future.done():
            return self._update_future
        
        def _async_fetch():
            self._weather_data = self.weather_provider.fetch()
            self._dirty = True
            return self._weather_data
        
        self._update_future = self._executor.submit(_async_fetch)
        return self._update_future
    
    def is_dirty(self) -> bool:
        """
        再描画が必要かどうかを返す
        
        Returns:
            再描画が必要な場合True
        """
        return self._dirty
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self.visible != visible:
            self.visible = visible
            self._dirty = True
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """
        描画領域を返す
        
        Returns:
            (x, y, width, height)のタプル
        """
        return (self.x, self.y, self.width, self.height)
    
    def create_panel_surface(self) -> pygame.Surface:
        """
        パネル背景サーフェスを作成
        
        Returns:
            パネル背景のサーフェス
        """
        # 透明度をサポートするサーフェスを作成
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 角丸四角形を描画
        if self.corner_radius > 0:
            # 角丸の描画（簡易版）
            pygame.draw.rect(panel, self.bg_color, 
                           (self.corner_radius, 0, 
                            self.width - 2 * self.corner_radius, self.height))
            pygame.draw.rect(panel, self.bg_color,
                           (0, self.corner_radius,
                            self.width, self.height - 2 * self.corner_radius))
            
            # 角を描画
            for corner_x, corner_y in [(self.corner_radius, self.corner_radius),
                                       (self.width - self.corner_radius, self.corner_radius),
                                       (self.corner_radius, self.height - self.corner_radius),
                                       (self.width - self.corner_radius, self.height - self.corner_radius)]:
                pygame.draw.circle(panel, self.bg_color, (corner_x, corner_y), self.corner_radius)
        else:
            # 通常の四角形
            panel.fill(self.bg_color)
        
        return panel
    
    def get_weather_icon(self, icon_name: str, size: int = 64) -> Optional[pygame.Surface]:
        """
        天気アイコンを取得
        
        Args:
            icon_name: アイコン名
            size: アイコンサイズ
            
        Returns:
            アイコンサーフェス
        """
        cache_key = f"{icon_name}_{size}"
        
        if cache_key not in self._icon_cache:
            try:
                # 最も近いサイズのアイコンを選択
                available_sizes = [32, 48, 64, 128]
                best_size = min(available_sizes, key=lambda x: abs(x - size))
                
                # アイコンファイルパスを構築
                icon_filename = f"{icon_name}_{best_size}.png"
                icon_path = f"icons/weather/{icon_filename}"
                
                # アイコンを読み込み
                icon = self.asset_manager.get_image(icon_path)
                
                if not icon:
                    # フォールバック: unknownアイコンを試す
                    icon_path = f"icons/weather/unknown_{best_size}.png"
                    icon = self.asset_manager.get_image(icon_path)
                
                if icon:
                    # 要求サイズに調整
                    if best_size != size:
                        icon = pygame.transform.smoothscale(icon, (size, size))
                    self._icon_cache[cache_key] = icon
                else:
                    # 最終フォールバック: 単色の円を作成
                    icon = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.circle(icon, (200, 200, 200, 150), 
                                     (size // 2, size // 2), size // 2 - 2)
                    self._icon_cache[cache_key] = icon
                    logger.warning(f"Using fallback icon for {icon_name}")
                    
            except Exception as e:
                logger.error(f"Icon loading error: {e}")
                # エラー時のフォールバック
                icon = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(icon, (150, 150, 150, 100), 
                                 (size // 2, size // 2), size // 2 - 2)
                self._icon_cache[cache_key] = icon
        
        return self._icon_cache.get(cache_key)
    
    def calculate_forecast_positions(self) -> List[Tuple[int, int]]:
        """
        予報の表示位置を計算
        
        Returns:
            各予報の(x, y)位置のリスト
        """
        positions = []
        base_x = self.x + 20
        base_y = self.y + 120
        spacing = 130
        
        for i in range(3):
            x = base_x + i * spacing
            positions.append((x, base_y))
        
        return positions
    
    def format_temperature(self, temp: float) -> str:
        """
        温度をフォーマット
        
        Args:
            temp: 温度
            
        Returns:
            フォーマット済み文字列
        """
        # 0.5以上で切り上げ
        import math
        return f"{math.floor(temp + 0.5)}°C"
    
    def format_forecast_date(self, date_str: str) -> str:
        """
        予報日付をフォーマット
        
        Args:
            date_str: YYYY-MM-DD形式の日付
            
        Returns:
            フォーマット済み文字列
        """
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%m/%d")
        except:
            return date_str
    
    def format_wind_speed(self, speed: float) -> str:
        """
        風速をフォーマット
        
        Args:
            speed: 風速(m/s)
            
        Returns:
            フォーマット済み文字列
        """
        return f"{speed:.1f} m/s"
    
    def format_humidity(self, humidity: int) -> str:
        """
        湿度をフォーマット
        
        Args:
            humidity: 湿度(%)
            
        Returns:
            フォーマット済み文字列
        """
        return f"{humidity}%"
    
    def format_location(self, lat: float, lon: float) -> str:
        """
        位置情報をフォーマット
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            フォーマット済み文字列
        """
        return f"{lat:.2f}, {lon:.2f}"
    
    def cleanup(self) -> None:
        """リソースをクリーンアップ"""
        # 非同期タスクをキャンセル
        if self._update_future and not self._update_future.done():
            self._update_future.cancel()
        
        # エグゼキューターをシャットダウン
        self._executor.shutdown(wait=False)
        
        # アイコンキャッシュをクリア
        self._icon_cache.clear()