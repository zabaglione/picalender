#!/usr/bin/env python3
"""
完全な天気表示デモ

全ての天気アイコンと表示機能をテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.ui.weather_renderer import WeatherRenderer
from src.providers.weather_base import WeatherProvider
from src.assets.asset_manager import AssetManager
from src.core.config_manager import ConfigManager


class DemoWeatherProvider(WeatherProvider):
    """
    デモ用天気プロバイダー
    
    全ての天気状態を順番に表示
    """
    
    def __init__(self, config: Any):
        """初期化"""
        super().__init__(config)
        self.demo_index = 0
        self.weather_patterns = [
            # 晴れ
            {
                "name": "Sunny Day",
                "current": {"temperature": 25, "icon": "sunny", "humidity": 40, "wind_speed": 2.5},
                "forecasts": [
                    {"icon": "sunny", "tmin": 18, "tmax": 28, "pop": 0},
                    {"icon": "partly_cloudy", "tmin": 19, "tmax": 27, "pop": 10},
                    {"icon": "sunny", "tmin": 17, "tmax": 26, "pop": 0}
                ]
            },
            # 曇り
            {
                "name": "Cloudy Day",
                "current": {"temperature": 20, "icon": "cloudy", "humidity": 65, "wind_speed": 3.5},
                "forecasts": [
                    {"icon": "cloudy", "tmin": 15, "tmax": 22, "pop": 20},
                    {"icon": "partly_cloudy", "tmin": 14, "tmax": 23, "pop": 30},
                    {"icon": "cloudy", "tmin": 16, "tmax": 21, "pop": 25}
                ]
            },
            # 雨
            {
                "name": "Rainy Day",
                "current": {"temperature": 18, "icon": "rain", "humidity": 85, "wind_speed": 5.0},
                "forecasts": [
                    {"icon": "rain", "tmin": 12, "tmax": 19, "pop": 80},
                    {"icon": "rain", "tmin": 13, "tmax": 18, "pop": 90},
                    {"icon": "cloudy", "tmin": 14, "tmax": 20, "pop": 40}
                ]
            },
            # 雷雨
            {
                "name": "Thunderstorm",
                "current": {"temperature": 22, "icon": "thunder", "humidity": 90, "wind_speed": 8.0},
                "forecasts": [
                    {"icon": "thunder", "tmin": 18, "tmax": 24, "pop": 95},
                    {"icon": "rain", "tmin": 17, "tmax": 23, "pop": 70},
                    {"icon": "partly_cloudy", "tmin": 16, "tmax": 25, "pop": 30}
                ]
            },
            # 雪
            {
                "name": "Snowy Day",
                "current": {"temperature": -2, "icon": "snow", "humidity": 75, "wind_speed": 4.0},
                "forecasts": [
                    {"icon": "snow", "tmin": -5, "tmax": 0, "pop": 60},
                    {"icon": "snow", "tmin": -6, "tmax": -1, "pop": 70},
                    {"icon": "cloudy", "tmin": -3, "tmax": 2, "pop": 30}
                ]
            },
            # 霧
            {
                "name": "Foggy Morning",
                "current": {"temperature": 15, "icon": "fog", "humidity": 95, "wind_speed": 1.0},
                "forecasts": [
                    {"icon": "fog", "tmin": 10, "tmax": 18, "pop": 10},
                    {"icon": "partly_cloudy", "tmin": 12, "tmax": 20, "pop": 15},
                    {"icon": "sunny", "tmin": 13, "tmax": 22, "pop": 5}
                ]
            },
            # 混合パターン
            {
                "name": "Variable Weather",
                "current": {"temperature": 21, "icon": "partly_cloudy", "humidity": 55, "wind_speed": 3.0},
                "forecasts": [
                    {"icon": "sunny", "tmin": 15, "tmax": 25, "pop": 5},
                    {"icon": "rain", "tmin": 14, "tmax": 21, "pop": 60},
                    {"icon": "thunder", "tmin": 16, "tmax": 23, "pop": 75}
                ]
            }
        ]
    
    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """APIからデータ取得のモック"""
        pattern = self.weather_patterns[self.demo_index]
        
        # 次のパターンへ
        self.demo_index = (self.demo_index + 1) % len(self.weather_patterns)
        
        return {
            "pattern_name": pattern["name"],
            "current_data": pattern["current"],
            "forecast_data": pattern["forecasts"]
        }
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """レスポンスを標準フォーマットに変換"""
        base_date = datetime.now()
        
        forecasts = []
        for i, forecast in enumerate(response["forecast_data"]):
            date = base_date + timedelta(days=i)
            forecasts.append({
                "date": date.strftime("%Y-%m-%d"),
                "icon": forecast["icon"],
                "tmin": forecast["tmin"],
                "tmax": forecast["tmax"],
                "pop": forecast["pop"]
            })
        
        return {
            "updated": int(time.time()),
            "location": self.location,
            "pattern_name": response["pattern_name"],
            "current": response["current_data"],
            "forecasts": forecasts
        }
    
    def _map_icon(self, condition: str) -> str:
        """アイコンマッピング（そのまま返す）"""
        return condition


def main():
    """メイン処理"""
    pygame.init()
    
    # 設定とアセット管理
    config = ConfigManager()
    asset_manager = AssetManager(base_path="assets")
    
    # 画面設定
    screen_width = 1024
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Weather Display Demo - All Conditions")
    
    # デモ用プロバイダー
    demo_provider = DemoWeatherProvider(config)
    
    # 天気レンダラー
    weather_renderer = WeatherRenderer(
        asset_manager=asset_manager,
        config=config,
        weather_provider=demo_provider
    )
    
    # メインループ
    clock = pygame.time.Clock()
    running = True
    
    # 初回データ取得
    weather_data = demo_provider.fetch()
    pattern_name = weather_data.get("pattern_name", "Unknown") if weather_data else "No Data"
    
    # 自動切り替えタイマー
    auto_switch_interval = 5  # 5秒ごとに切り替え
    last_switch_time = time.time()
    
    while running:
        dt = clock.tick(30) / 1000.0
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # スペースキーで手動切り替え
                    weather_data = demo_provider.fetch()
                    pattern_name = weather_data.get("pattern_name", "Unknown") if weather_data else "No Data"
                    weather_renderer._weather_data = weather_data
                    weather_renderer._dirty = True
                elif event.key == pygame.K_v:
                    # Vキーで表示/非表示切り替え
                    weather_renderer.set_visible(not weather_renderer.visible)
                elif event.key == pygame.K_r:
                    # Rキーでリフレッシュ
                    weather_renderer._fetch_weather_data()
        
        # 自動切り替え
        current_time = time.time()
        if current_time - last_switch_time >= auto_switch_interval:
            weather_data = demo_provider.fetch()
            pattern_name = weather_data.get("pattern_name", "Unknown") if weather_data else "No Data"
            weather_renderer._weather_data = weather_data
            weather_renderer._dirty = True
            last_switch_time = current_time
        
        # 更新
        weather_renderer.update(dt)
        
        # 描画
        # 背景色（天気に応じて変更）
        if weather_data and "current" in weather_data:
            icon = weather_data["current"].get("icon", "cloudy")
            if icon == "sunny":
                bg_color = (135, 206, 235)  # スカイブルー
            elif icon == "rain" or icon == "thunder":
                bg_color = (60, 60, 80)  # 暗い青灰色
            elif icon == "snow":
                bg_color = (200, 220, 240)  # 薄い青白
            elif icon == "fog":
                bg_color = (150, 150, 160)  # 灰色
            else:
                bg_color = (100, 120, 140)  # デフォルト
        else:
            bg_color = (50, 50, 50)
        
        screen.fill(bg_color)
        
        # 天気表示
        weather_renderer.render(screen)
        
        # パターン名を表示
        font = pygame.font.Font(None, 36)
        pattern_text = font.render(f"Pattern: {pattern_name}", True, (255, 255, 255))
        screen.blit(pattern_text, (screen_width - pattern_text.get_width() - 20, 20))
        
        # 操作説明
        help_font = pygame.font.Font(None, 20)
        help_texts = [
            "Controls:",
            "  SPACE: Next weather pattern",
            "  V: Toggle visibility",
            "  R: Refresh data",
            "  ESC: Exit",
            f"Auto-switch every {auto_switch_interval}s"
        ]
        
        y = screen_height - 150
        for text in help_texts:
            color = (200, 200, 200) if text.startswith("  ") else (255, 255, 255)
            help_surface = help_font.render(text, True, color)
            screen.blit(help_surface, (screen_width - 250, y))
            y += 22
        
        # アイコン一覧を右側に表示
        icon_names = ["sunny", "partly_cloudy", "cloudy", "rain", "thunder", "snow", "fog", "unknown"]
        icon_y = 100
        for icon_name in icon_names:
            # アイコンを取得
            icon = weather_renderer.get_weather_icon(icon_name, 32)
            if icon:
                screen.blit(icon, (screen_width - 80, icon_y))
                # アイコン名
                name_surface = help_font.render(icon_name, True, (255, 255, 255))
                screen.blit(name_surface, (screen_width - 200, icon_y + 6))
                icon_y += 40
        
        pygame.display.flip()
    
    # クリーンアップ
    weather_renderer.cleanup()
    pygame.quit()


if __name__ == "__main__":
    main()