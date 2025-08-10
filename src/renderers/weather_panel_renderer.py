#!/usr/bin/env python3
"""
天気パネルレンダラー

3日分の天気予報を表示パネルに描画する。
"""

import pygame
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import logging


class WeatherPanelRenderer:
    """天気パネルレンダラークラス
    
    左下に3日分の天気予報を表示する。
    角丸の濃色パネル背景に、日付、気温、降水確率、天気アイコンを表示。
    """
    
    # デフォルト設定
    DEFAULT_PANEL_WIDTH = 420
    DEFAULT_PANEL_HEIGHT = 280
    DEFAULT_PANEL_RADIUS = 15
    DEFAULT_PANEL_COLOR = (30, 30, 40, 200)  # 半透明の濃色
    DEFAULT_TEXT_COLOR = (255, 255, 255)
    DEFAULT_FONT_SIZE = 22
    
    # レイアウト設定
    MARGIN_X = 24
    MARGIN_Y = 16
    PANEL_PADDING = 20
    DAY_SPACING = 130  # 各日の間隔
    
    def __init__(self, asset_manager: Any, settings: Dict[str, Any]):
        """初期化
        
        Args:
            asset_manager: アセット管理システム
            settings: 設定辞書
        """
        self.logger = logging.getLogger(__name__)
        self.asset_manager = asset_manager
        
        # 設定読み込み
        ui_config = settings.get('ui', {})
        self.margins_x = ui_config.get('margins', {}).get('x', self.MARGIN_X)
        self.margins_y = ui_config.get('margins', {}).get('y', self.MARGIN_Y)
        self.font_size = ui_config.get('weather_font_px', self.DEFAULT_FONT_SIZE)
        
        # パネル設定
        weather_config = settings.get('weather', {})
        panel_config = weather_config.get('panel', {})
        self.panel_width = panel_config.get('width', self.DEFAULT_PANEL_WIDTH)
        self.panel_height = panel_config.get('height', self.DEFAULT_PANEL_HEIGHT)
        self.panel_radius = panel_config.get('radius', self.DEFAULT_PANEL_RADIUS)
        self.panel_color = panel_config.get('color', self.DEFAULT_PANEL_COLOR)
        
        # フォント取得
        self.font = asset_manager.get_font('main', self.font_size)
        self.small_font = asset_manager.get_font('main', int(self.font_size * 0.8))
        
        # アイコンキャッシュ
        self._icon_cache = {}
        
        # 天気データキャッシュ
        self._weather_data = None
        
        self.logger.info("WeatherPanelRenderer initialized")
    
    def update(self, weather_data: Optional[Dict[str, Any]]) -> None:
        """天気データの更新
        
        Args:
            weather_data: 天気データ（プロバイダから取得した標準形式）
        """
        if weather_data:
            self._weather_data = weather_data
            self.logger.debug(f"Weather data updated: {len(weather_data.get('forecasts', []))} days")
    
    def render(self, screen: pygame.Surface) -> None:
        """画面に描画
        
        Args:
            screen: 描画対象のサーフェス
        """
        if not self._weather_data or 'forecasts' not in self._weather_data:
            # データがない場合は何も描画しない
            return
        
        # パネル位置計算（左下）
        screen_width, screen_height = screen.get_size()
        panel_x = self.margins_x
        panel_y = screen_height - self.margins_y - self.panel_height
        
        # パネル背景描画
        self._draw_panel_background(screen, panel_x, panel_y)
        
        # 天気予報描画（最大3日分）
        forecasts = self._weather_data['forecasts'][:3]
        for i, forecast in enumerate(forecasts):
            self._draw_forecast(screen, forecast, panel_x, panel_y, i)
        
        # 更新時刻表示（オプション）
        if 'updated' in self._weather_data:
            self._draw_update_time(screen, panel_x, panel_y)
    
    def _draw_panel_background(self, screen: pygame.Surface, x: int, y: int) -> None:
        """パネル背景の描画（角丸矩形）
        
        Args:
            screen: 描画対象
            x: パネルX座標
            y: パネルY座標
        """
        # 角丸矩形を描画（簡易版：通常の矩形で代替）
        panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        
        # 背景色で塗りつぶし
        if len(self.panel_color) == 4:
            # アルファ値付き
            panel_surface.fill(self.panel_color)
        else:
            # アルファ値なし
            panel_surface.fill((*self.panel_color, 200))
        
        # 角丸効果（簡易版：四隅に円を描画）
        if self.panel_radius > 0:
            radius = self.panel_radius
            color = self.panel_color[:3] if len(self.panel_color) >= 3 else (30, 30, 40)
            
            # 四隅の円
            pygame.draw.circle(panel_surface, color, (radius, radius), radius)
            pygame.draw.circle(panel_surface, color, (self.panel_width - radius, radius), radius)
            pygame.draw.circle(panel_surface, color, (radius, self.panel_height - radius), radius)
            pygame.draw.circle(panel_surface, color, (self.panel_width - radius, self.panel_height - radius), radius)
            
            # 矩形で隙間を埋める
            pygame.draw.rect(panel_surface, color, (radius, 0, self.panel_width - 2*radius, self.panel_height))
            pygame.draw.rect(panel_surface, color, (0, radius, self.panel_width, self.panel_height - 2*radius))
        
        # 画面に描画
        screen.blit(panel_surface, (x, y))
    
    def _draw_forecast(self, screen: pygame.Surface, forecast: Dict[str, Any], 
                      panel_x: int, panel_y: int, index: int) -> None:
        """1日分の予報を描画
        
        Args:
            screen: 描画対象
            forecast: 予報データ
            panel_x: パネルX座標
            panel_y: パネルY座標
            index: 日付インデックス（0-2）
        """
        # 各日の描画位置
        day_x = panel_x + self.PANEL_PADDING + (index * self.DAY_SPACING)
        day_y = panel_y + self.PANEL_PADDING
        
        # 日付表示
        date_str = forecast.get('date', '')
        if date_str:
            # 日付を解析してフォーマット
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d')
                weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
                date_text = f"{formatted_date}({weekday})"
            except:
                date_text = date_str[:5]  # MM-DD部分のみ
            
            text_surface = self.font.render(date_text, True, self.DEFAULT_TEXT_COLOR)
            screen.blit(text_surface, (day_x, day_y))
        
        # 天気アイコン描画
        icon_name = forecast.get('icon', 'cloudy')
        icon_y = day_y + 40
        self._draw_weather_icon(screen, icon_name, day_x + 20, icon_y)
        
        # 気温表示
        temp_data = forecast.get('temperature', {})
        if temp_data:
            min_temp = temp_data.get('min', '--')
            max_temp = temp_data.get('max', '--')
            temp_text = f"{min_temp}°/{max_temp}°"
            
            temp_surface = self.font.render(temp_text, True, self.DEFAULT_TEXT_COLOR)
            temp_y = icon_y + 80
            screen.blit(temp_surface, (day_x, temp_y))
        
        # 降水確率表示
        precipitation = forecast.get('precipitation_probability')
        if precipitation is not None:
            rain_text = f"☔ {precipitation}%"
            rain_surface = self.small_font.render(rain_text, True, (150, 200, 255))
            rain_y = icon_y + 110
            screen.blit(rain_surface, (day_x, rain_y))
    
    def _draw_weather_icon(self, screen: pygame.Surface, icon_name: str, x: int, y: int) -> None:
        """天気アイコンの描画
        
        Args:
            screen: 描画対象
            icon_name: アイコン名（sunny, cloudy, rain, thunder, fog）
            x: X座標
            y: Y座標
        """
        # アイコンサイズ
        icon_size = 60
        
        # 簡易アイコン描画（実際のアイコン画像がない場合の代替）
        icon_colors = {
            'sunny': (255, 200, 0),      # 黄色
            'cloudy': (150, 150, 150),   # グレー
            'rain': (100, 150, 255),     # 青
            'thunder': (200, 100, 255),  # 紫
            'fog': (200, 200, 200)       # 薄いグレー
        }
        
        icon_symbols = {
            'sunny': '☀',
            'cloudy': '☁',
            'rain': '🌧',
            'thunder': '⚡',
            'fog': '🌫'
        }
        
        # 色を取得
        color = icon_colors.get(icon_name, (150, 150, 150))
        
        # 簡易的に円で表現
        pygame.draw.circle(screen, color, (x + icon_size//2, y + icon_size//2), icon_size//2)
        
        # テキストシンボル（フォントがサポートしている場合）
        try:
            symbol = icon_symbols.get(icon_name, '?')
            symbol_surface = self.font.render(symbol, True, (255, 255, 255))
            symbol_rect = symbol_surface.get_rect(center=(x + icon_size//2, y + icon_size//2))
            screen.blit(symbol_surface, symbol_rect)
        except:
            # シンボル描画失敗時は無視
            pass
    
    def _draw_update_time(self, screen: pygame.Surface, panel_x: int, panel_y: int) -> None:
        """更新時刻の表示
        
        Args:
            screen: 描画対象
            panel_x: パネルX座標
            panel_y: パネルY座標
        """
        if 'updated' in self._weather_data:
            timestamp = self._weather_data['updated']
            try:
                update_time = datetime.fromtimestamp(timestamp)
                time_str = f"更新: {update_time.strftime('%H:%M')}"
                
                time_surface = self.small_font.render(time_str, True, (150, 150, 150))
                time_x = panel_x + self.panel_width - self.PANEL_PADDING - time_surface.get_width()
                time_y = panel_y + self.panel_height - self.PANEL_PADDING - time_surface.get_height()
                screen.blit(time_surface, (time_x, time_y))
            except:
                pass
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self._icon_cache.clear()
        self._weather_data = None
        self.logger.info("WeatherPanelRenderer cleaned up")