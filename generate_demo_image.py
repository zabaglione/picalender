#!/usr/bin/env python3
"""
PiCalendarのデモ画像を生成するスクリプト
"""

import pygame
import os
from datetime import datetime, timedelta
import calendar
from pathlib import Path

# 初期化
pygame.init()

# 画面サイズ
WIDTH = 1024
HEIGHT = 600

# カラー定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)
GREEN = (100, 255, 100)
DARK_BLUE = (20, 30, 60)
LIGHT_BLUE = (135, 206, 235)

# Surface作成
screen = pygame.Surface((WIDTH, HEIGHT))

# 背景グラデーション描画
def draw_gradient_background(surface):
    """グラデーション背景を描画"""
    for y in range(HEIGHT):
        # 上から下へのグラデーション（濃い青から薄い青へ）
        ratio = y / HEIGHT
        color = (
            int(20 + (50 - 20) * ratio),
            int(30 + (80 - 30) * ratio),
            int(60 + (120 - 60) * ratio)
        )
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

# フォント設定
try:
    # システムフォントを使用
    font_clock = pygame.font.Font(None, 120)
    font_date = pygame.font.Font(None, 36)
    font_calendar = pygame.font.Font(None, 24)
    font_weather = pygame.font.Font(None, 22)
    font_small = pygame.font.Font(None, 18)
except:
    print("フォント読み込みエラー - デフォルトフォントを使用")
    font_clock = pygame.font.Font(None, 120)
    font_date = pygame.font.Font(None, 36)
    font_calendar = pygame.font.Font(None, 24)
    font_weather = pygame.font.Font(None, 22)
    font_small = pygame.font.Font(None, 18)

# 背景描画
draw_gradient_background(screen)

# 装飾的な背景パターン（ドット）
for x in range(0, WIDTH, 50):
    for y in range(0, HEIGHT, 50):
        pygame.draw.circle(screen, (30, 40, 70), (x, y), 1)

# 時計表示
current_time = "14:35:27"
clock_text = font_clock.render(current_time, True, WHITE)
clock_rect = clock_text.get_rect(center=(WIDTH // 2, 100))
# ドロップシャドウ
shadow_text = font_clock.render(current_time, True, (10, 10, 20))
screen.blit(shadow_text, (clock_rect.x + 3, clock_rect.y + 3))
screen.blit(clock_text, clock_rect)

# 日付表示
current_date = "2025-01-11 (Sat)"
date_text = font_date.render(current_date, True, LIGHT_GRAY)
date_rect = date_text.get_rect(center=(WIDTH // 2, 170))
screen.blit(date_text, date_rect)

# カレンダー描画（右下）
cal_x = WIDTH - 380
cal_y = HEIGHT - 280
cal_width = 350
cal_height = 250

# カレンダー背景
cal_surface = pygame.Surface((cal_width, cal_height), pygame.SRCALPHA)
pygame.draw.rect(cal_surface, (20, 20, 30, 200), (0, 0, cal_width, cal_height), border_radius=10)
screen.blit(cal_surface, (cal_x, cal_y))

# カレンダーヘッダー
month_year = "January 2025"
month_text = font_calendar.render(month_year, True, WHITE)
month_rect = month_text.get_rect(center=(cal_x + cal_width // 2, cal_y + 20))
screen.blit(month_text, month_rect)

# 曜日ヘッダー
weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
day_width = cal_width // 7
for i, day in enumerate(weekdays):
    color = RED if i == 0 else BLUE if i == 6 else WHITE
    day_text = font_small.render(day, True, color)
    day_x = cal_x + i * day_width + day_width // 2
    day_rect = day_text.get_rect(center=(day_x, cal_y + 50))
    screen.blit(day_text, day_rect)

# カレンダー日付
cal_obj = calendar.monthcalendar(2025, 1)
day_y = cal_y + 80
for week in cal_obj:
    for i, day in enumerate(week):
        if day > 0:
            # 今日をハイライト
            if day == 11:
                pygame.draw.circle(screen, YELLOW, 
                                 (cal_x + i * day_width + day_width // 2, day_y), 
                                 15)
                color = BLACK
            else:
                color = RED if i == 0 else BLUE if i == 6 else WHITE
            
            day_text = font_small.render(str(day), True, color)
            day_x = cal_x + i * day_width + day_width // 2
            day_rect = day_text.get_rect(center=(day_x, day_y))
            screen.blit(day_text, day_rect)
    day_y += 30

# 天気パネル（左下）
weather_x = 30
weather_y = HEIGHT - 280
weather_width = 420
weather_height = 250

# 天気パネル背景
weather_surface = pygame.Surface((weather_width, weather_height), pygame.SRCALPHA)
pygame.draw.rect(weather_surface, (20, 20, 30, 200), (0, 0, weather_width, weather_height), border_radius=10)
screen.blit(weather_surface, (weather_x, weather_y))

# 天気タイトル
weather_title = "3-Day Forecast - Tokyo"
title_text = font_calendar.render(weather_title, True, WHITE)
title_rect = title_text.get_rect(center=(weather_x + weather_width // 2, weather_y + 25))
screen.blit(title_text, title_rect)

# 3日分の天気
forecasts = [
    {"date": "Today", "icon": "☀", "high": "15°", "low": "5°", "pop": "10%"},
    {"date": "Tomorrow", "icon": "☁", "high": "17°", "low": "7°", "pop": "20%"},
    {"date": "Sun", "icon": "🌧", "high": "16°", "low": "8°", "pop": "80%"}
]

forecast_width = weather_width // 3
for i, forecast in enumerate(forecasts):
    fx = weather_x + i * forecast_width + forecast_width // 2
    fy = weather_y + 60
    
    # 日付
    date_text = font_weather.render(forecast["date"], True, WHITE)
    date_rect = date_text.get_rect(center=(fx, fy))
    screen.blit(date_text, date_rect)
    
    # アイコン（シンプルな図形で代替）
    icon_y = fy + 35
    if forecast["icon"] == "☀":
        # 太陽
        pygame.draw.circle(screen, YELLOW, (fx, icon_y), 20)
        for angle in range(0, 360, 45):
            import math
            x1 = fx + 25 * math.cos(math.radians(angle))
            y1 = icon_y + 25 * math.sin(math.radians(angle))
            x2 = fx + 35 * math.cos(math.radians(angle))
            y2 = icon_y + 35 * math.sin(math.radians(angle))
            pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 2)
    elif forecast["icon"] == "☁":
        # 曇り
        pygame.draw.circle(screen, LIGHT_GRAY, (fx - 10, icon_y), 15)
        pygame.draw.circle(screen, LIGHT_GRAY, (fx + 10, icon_y), 15)
        pygame.draw.circle(screen, LIGHT_GRAY, (fx, icon_y - 5), 18)
    else:
        # 雨
        pygame.draw.circle(screen, GRAY, (fx, icon_y - 10), 15)
        for j in range(3):
            x = fx - 10 + j * 10
            pygame.draw.line(screen, LIGHT_BLUE, (x, icon_y + 5), (x - 5, icon_y + 20), 2)
    
    # 気温
    temp_y = icon_y + 50
    temp_text = font_weather.render(f"{forecast['high']}/{forecast['low']}", True, WHITE)
    temp_rect = temp_text.get_rect(center=(fx, temp_y))
    screen.blit(temp_text, temp_rect)
    
    # 降水確率
    pop_y = temp_y + 25
    pop_text = font_small.render(f"☔ {forecast['pop']}", True, LIGHT_BLUE)
    pop_rect = pop_text.get_rect(center=(fx, pop_y))
    screen.blit(pop_text, pop_rect)

# 2Dキャラクター（左上）
char_x = 50
char_y = 50
char_size = 100

# キャラクター本体（簡単な図形で表現）
# 体
body_rect = pygame.Rect(char_x, char_y + 30, char_size, char_size)
pygame.draw.ellipse(screen, GREEN, body_rect)
pygame.draw.ellipse(screen, (50, 150, 50), body_rect, 2)

# 顔
face_rect = pygame.Rect(char_x + 10, char_y, char_size - 20, char_size - 20)
pygame.draw.ellipse(screen, (255, 220, 177), face_rect)

# 目
eye_size = 8
pygame.draw.circle(screen, BLACK, (char_x + 30, char_y + 35), eye_size)
pygame.draw.circle(screen, BLACK, (char_x + 70, char_y + 35), eye_size)
pygame.draw.circle(screen, WHITE, (char_x + 32, char_y + 33), 3)
pygame.draw.circle(screen, WHITE, (char_x + 72, char_y + 33), 3)

# 口（笑顔）
pygame.draw.arc(screen, BLACK, (char_x + 35, char_y + 40, 30, 20), 0, 3.14, 2)

# 手
pygame.draw.circle(screen, (255, 220, 177), (char_x - 10, char_y + 60), 15)
pygame.draw.circle(screen, (255, 220, 177), (char_x + char_size + 10, char_y + 60), 15)

# キャラクター名
char_name = "Pi-chan"
name_text = font_small.render(char_name, True, WHITE)
name_rect = name_text.get_rect(center=(char_x + char_size // 2, char_y + char_size + 50))
screen.blit(name_text, name_rect)

# アプリケーション名とバージョン（右上）
app_name = "PiCalendar v1.0.0"
app_text = font_small.render(app_name, True, LIGHT_GRAY)
app_rect = app_text.get_rect(topright=(WIDTH - 20, 20))
screen.blit(app_text, app_rect)

# ステータスインジケーター（右上）
status_x = WIDTH - 150
status_y = 50
# WiFi アイコン
pygame.draw.lines(screen, GREEN, False, 
                 [(status_x, status_y + 10), (status_x + 5, status_y + 5), 
                  (status_x + 10, status_y + 10)], 2)
pygame.draw.lines(screen, GREEN, False, 
                 [(status_x - 3, status_y + 13), (status_x + 5, status_y + 8), 
                  (status_x + 13, status_y + 13)], 2)

# 画像保存
output_dir = Path("docs/images")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "demo.png"

pygame.image.save(screen, str(output_file))
print(f"デモ画像を生成しました: {output_file}")

# Pygameを終了
pygame.quit()