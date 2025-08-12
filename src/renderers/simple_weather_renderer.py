#!/usr/bin/env python3
"""
簡易天気レンダラー（AssetManager非依存版）
"""

import pygame
import time
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import threading
import requests
import logging


class SimpleWeatherRenderer:
    """簡易天気レンダラー"""
    
    def __init__(self, settings):
        """初期化"""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 表示設定
        self.font_size = settings.get('ui', {}).get('weather_font_px', 20)
        self.font = None
        
        # 天気データ
        self.weather_data = None
        self.last_update = None
        self.update_interval = 1800  # 30分
        
        # キャッシュファイル
        self.cache_file = Path("cache/weather_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # 位置設定（東京のデフォルト）
        self.lat = settings.get('weather', {}).get('location', {}).get('lat', 35.681236)
        self.lon = settings.get('weather', {}).get('location', {}).get('lon', 139.767125)
        
        # 更新スレッド
        self.update_thread = None
        self.stop_event = threading.Event()
        
        self._init_font()
        self._load_cache()
        self._start_update_thread()
    
    def _init_font(self):
        """フォント初期化"""
        try:
            # システムフォントを使用
            self.font = pygame.font.SysFont('notosanscjkjp', self.font_size)
        except:
            # フォールバック
            self.font = pygame.font.Font(None, self.font_size)
    
    def _load_cache(self):
        """キャッシュから天気データを読み込み"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # 24時間以内のキャッシュなら使用
                    cache_time = datetime.fromisoformat(cache.get('timestamp', ''))
                    if datetime.now() - cache_time < timedelta(hours=24):
                        self.weather_data = cache.get('data')
                        self.last_update = cache_time
                        self.logger.info("天気データをキャッシュから読み込みました")
        except Exception as e:
            self.logger.debug(f"キャッシュ読み込みエラー: {e}")
    
    def _save_cache(self):
        """天気データをキャッシュに保存"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': self.weather_data
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)
        except Exception as e:
            self.logger.debug(f"キャッシュ保存エラー: {e}")
    
    def _fetch_weather(self):
        """Open-Meteo APIから天気データを取得"""
        try:
            # Open-Meteo API（無料、認証不要）
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': self.lat,
                'longitude': self.lon,
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
                'timezone': 'Asia/Tokyo',
                'forecast_days': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # データを整形
            daily = data.get('daily', {})
            forecasts = []
            
            for i in range(min(3, len(daily.get('time', [])))):
                forecast = {
                    'date': daily['time'][i],
                    'temp_max': daily['temperature_2m_max'][i],
                    'temp_min': daily['temperature_2m_min'][i],
                    'precip_prob': daily['precipitation_probability_max'][i] or 0,
                    'weather_code': daily['weather_code'][i]
                }
                forecasts.append(forecast)
            
            self.weather_data = forecasts
            self.last_update = datetime.now()
            self._save_cache()
            
            self.logger.info(f"天気データを取得しました（{len(forecasts)}日分）")
            
        except Exception as e:
            self.logger.error(f"天気データ取得エラー: {e}")
    
    def _update_worker(self):
        """バックグラウンドで天気データを更新"""
        while not self.stop_event.is_set():
            try:
                # 初回またはインターバル経過後に更新
                if (self.last_update is None or 
                    datetime.now() - self.last_update > timedelta(seconds=self.update_interval)):
                    self._fetch_weather()
                
                # 次回更新まで待機（1分ごとにチェック）
                self.stop_event.wait(60)
                
            except Exception as e:
                self.logger.error(f"天気更新スレッドエラー: {e}")
                self.stop_event.wait(60)
    
    def _start_update_thread(self):
        """更新スレッドを開始"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=self._update_worker, daemon=True)
            self.update_thread.start()
            self.logger.info("天気更新スレッドを開始しました")
    
    def _get_weather_icon(self, code):
        """天気コードから天気アイコン文字を取得"""
        # WMO Weather Code - テキストで表示
        if code == 0:
            return "晴"  # 晴れ
        elif code in [1, 2]:
            return "晴曇"  # 晴れ時々曇り
        elif code == 3:
            return "曇"  # 曇り
        elif code in [45, 48]:
            return "霧"  # 霧
        elif code in [51, 53, 55, 56, 57]:
            return "小雨"  # 小雨
        elif code in [61, 63, 65, 66, 67]:
            return "雨"  # 雨
        elif code in [71, 73, 75, 77]:
            return "雪"  # 雪
        elif code in [80, 81, 82]:
            return "雷雨"  # にわか雨
        elif code in [85, 86]:
            return "雪"  # にわか雪
        elif code in [95, 96, 99]:
            return "雷雨"  # 雷雨
        else:
            return "---"  # その他
    
    def _get_day_label(self, date_str):
        """日付から曜日ラベルを取得"""
        try:
            date = datetime.fromisoformat(date_str)
            today = datetime.now().date()
            
            if date.date() == today:
                return "今日"
            elif date.date() == today + timedelta(days=1):
                return "明日"
            elif date.date() == today + timedelta(days=2):
                return "明後日"
            else:
                weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                return f"{date.month}/{date.day}({weekdays[date.weekday()]})"
        except:
            return date_str
    
    def render(self, screen):
        """天気を描画"""
        if not self.font or not self.weather_data:
            # データがない場合は「取得中...」を表示
            self._render_loading(screen)
            return
        
        # 天気パネルの背景を描画
        panel_x = 24  # 左マージン
        panel_y = screen.get_height() - 280 - 16  # 下から280px + 下マージン16px
        panel_width = 420
        panel_height = 280
        
        # 半透明の背景パネル
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((30, 40, 50))
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # 枠線
        pygame.draw.rect(screen, (100, 120, 140), 
                        (panel_x, panel_y, panel_width, panel_height), 2)
        
        # タイトル
        title_text = self.font.render("天気予報", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=panel_x + panel_width // 2, y=panel_y + 10)
        screen.blit(title_text, title_rect)
        
        # 3日分の天気を横に並べて表示
        day_width = panel_width // 3
        for i, forecast in enumerate(self.weather_data[:3]):
            x = panel_x + i * day_width
            y = panel_y + 50
            
            # 日付ラベル
            day_label = self._get_day_label(forecast['date'])
            day_text = self.font.render(day_label, True, (255, 255, 255))
            day_rect = day_text.get_rect(centerx=x + day_width // 2, y=y)
            screen.blit(day_text, day_rect)
            
            # 天気アイコン（テキスト）
            icon = self._get_weather_icon(forecast.get('weather_code', 0))
            # 日本語フォントを使用
            try:
                icon_font = pygame.font.SysFont('notosanscjkjp', 32)
            except:
                icon_font = pygame.font.Font(None, 32)
            icon_text = icon_font.render(icon, True, (150, 200, 255))
            icon_rect = icon_text.get_rect(centerx=x + day_width // 2, y=y + 40)
            screen.blit(icon_text, icon_rect)
            
            # 気温
            temp_max = forecast.get('temp_max', 0)
            temp_min = forecast.get('temp_min', 0)
            temp_text = f"{temp_max:.0f}° / {temp_min:.0f}°"
            temp_surface = self.font.render(temp_text, True, (255, 200, 100))
            temp_rect = temp_surface.get_rect(centerx=x + day_width // 2, y=y + 90)
            screen.blit(temp_surface, temp_rect)
            
            # 降水確率
            precip = forecast.get('precip_prob', 0)
            if precip > 0:
                precip_text = f"雨 {precip}%"
                precip_surface = self.font.render(precip_text, True, (150, 200, 255))
                precip_rect = precip_surface.get_rect(centerx=x + day_width // 2, y=y + 120)
                screen.blit(precip_surface, precip_rect)
        
        # 最終更新時刻
        if self.last_update:
            update_text = f"更新: {self.last_update.strftime('%H:%M')}"
            update_surface = pygame.font.Font(None, 16).render(update_text, True, (150, 150, 150))
            update_rect = update_surface.get_rect(right=panel_x + panel_width - 10, 
                                                 bottom=panel_y + panel_height - 10)
            screen.blit(update_surface, update_rect)
    
    def _render_loading(self, screen):
        """読み込み中表示"""
        panel_x = 24
        panel_y = screen.get_height() - 280 - 16
        panel_width = 420
        panel_height = 280
        
        # 半透明の背景パネル
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((30, 40, 50))
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # 枠線
        pygame.draw.rect(screen, (100, 120, 140), 
                        (panel_x, panel_y, panel_width, panel_height), 2)
        
        # メッセージ
        if self.font:
            loading_text = self.font.render("天気データ取得中...", True, (200, 200, 200))
            loading_rect = loading_text.get_rect(center=(panel_x + panel_width // 2, 
                                                        panel_y + panel_height // 2))
            screen.blit(loading_text, loading_rect)
    
    def cleanup(self):
        """クリーンアップ"""
        self.stop_event.set()
        if self.update_thread:
            self.update_thread.join(timeout=1)