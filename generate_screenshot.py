#!/usr/bin/env python3
"""
スクリーンショット生成スクリプト
実際の動作画面をシミュレートして画像を生成
"""

import pygame
import os
from datetime import datetime
import calendar as cal
from pathlib import Path

# pygameを画像生成モードで初期化（ディスプレイなし）
os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()

# 画面サイズ
WIDTH = 1024
HEIGHT = 600

# Surface作成
screen = pygame.Surface((WIDTH, HEIGHT))

# フォント設定
try:
    font_clock = pygame.font.Font(None, 120)
    font_date = pygame.font.Font(None, 36)
    font_calendar = pygame.font.Font(None, 22)
    font_weather = pygame.font.Font(None, 20)
    font_small = pygame.font.Font(None, 16)
except:
    print("フォント読み込みエラー")
    font_clock = pygame.font.Font(None, 120)
    font_date = pygame.font.Font(None, 36)
    font_calendar = pygame.font.Font(None, 22)
    font_weather = pygame.font.Font(None, 20)
    font_small = pygame.font.Font(None, 16)

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)
GREEN = (100, 255, 100)
DARK_BLUE = (20, 30, 60)
LIGHT_BLUE = (135, 206, 235)

# 背景グラデーション描画
def draw_gradient_background(surface):
    """グラデーション背景を描画"""
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = (
            int(20 + (50 - 20) * ratio),
            int(30 + (80 - 30) * ratio),
            int(60 + (120 - 60) * ratio)
        )
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

# 背景描画
draw_gradient_background(screen)

# 装飾的な背景パターン
for x in range(0, WIDTH, 50):
    for y in range(0, HEIGHT, 50):
        pygame.draw.circle(screen, (30, 40, 70), (x, y), 1)

# 現在時刻（実際の時刻を使用）
now = datetime.now()

# 時計表示
time_str = now.strftime("%H:%M:%S")
clock_text = font_clock.render(time_str, True, WHITE)
clock_rect = clock_text.get_rect(center=(WIDTH // 2, 100))
# ドロップシャドウ
shadow_text = font_clock.render(time_str, True, (10, 10, 20))
screen.blit(shadow_text, (clock_rect.x + 3, clock_rect.y + 3))
screen.blit(clock_text, clock_rect)

# 日付表示
date_str = now.strftime("%Y-%m-%d (%a)")
date_text = font_date.render(date_str, True, LIGHT_GRAY)
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
month_year = now.strftime("%B %Y")
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
cal_obj = cal.monthcalendar(now.year, now.month)
day_y = cal_y + 80
for week in cal_obj:
    for i, day in enumerate(week):
        if day > 0:
            # 今日をハイライト
            if day == now.day:
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

# 実際の天気データをシミュレート
import random
temps = [(random.randint(10, 15), random.randint(20, 28)) for _ in range(3)]
weather_types = ["Sunny", "Cloudy", "Rain"]
random.shuffle(weather_types)

forecasts = [
    {"date": "Today", "icon": weather_types[0], "high": f"{temps[0][1]}°", "low": f"{temps[0][0]}°", "pop": f"{random.randint(0, 30)}%"},
    {"date": "Tomorrow", "icon": weather_types[1], "high": f"{temps[1][1]}°", "low": f"{temps[1][0]}°", "pop": f"{random.randint(10, 50)}%"},
    {"date": (now.replace(day=now.day+2) if now.day < 29 else now).strftime("%a"), "icon": weather_types[2], "high": f"{temps[2][1]}°", "low": f"{temps[2][0]}°", "pop": f"{random.randint(20, 80)}%"}
]

forecast_width = weather_width // 3
for i, forecast in enumerate(forecasts):
    fx = weather_x + i * forecast_width + forecast_width // 2
    fy = weather_y + 60
    
    # 日付
    date_text = font_weather.render(forecast["date"], True, WHITE)
    date_rect = date_text.get_rect(center=(fx, fy))
    screen.blit(date_text, date_rect)
    
    # アイコン
    icon_y = fy + 35
    if forecast["icon"] == "Sunny":
        # 太陽
        pygame.draw.circle(screen, YELLOW, (fx, icon_y), 20)
        import math
        for angle in range(0, 360, 45):
            x1 = fx + 25 * math.cos(math.radians(angle))
            y1 = icon_y + 25 * math.sin(math.radians(angle))
            x2 = fx + 35 * math.cos(math.radians(angle))
            y2 = icon_y + 35 * math.sin(math.radians(angle))
            pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 2)
    elif forecast["icon"] == "Cloudy":
        # 曇り
        pygame.draw.circle(screen, LIGHT_GRAY, (fx - 10, icon_y), 15)
        pygame.draw.circle(screen, LIGHT_GRAY, (fx + 10, icon_y), 15)
        pygame.draw.circle(screen, LIGHT_GRAY, (fx, icon_y - 5), 18)
    else:  # Rain
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

# アプリケーション情報（右上）
app_name = "PiCalendar v1.0.0"
app_text = font_small.render(app_name, True, LIGHT_GRAY)
app_rect = app_text.get_rect(topright=(WIDTH - 20, 20))
screen.blit(app_text, app_rect)

# ステータスインジケーター
status_x = WIDTH - 100
status_y = 50
# WiFi アイコン
pygame.draw.lines(screen, GREEN, False, 
                 [(status_x, status_y + 10), (status_x + 5, status_y + 5), 
                  (status_x + 10, status_y + 10)], 2)

# 実行中インジケーター
status_text = font_small.render("● Running", True, GREEN)
screen.blit(status_text, (WIDTH - 100, 70))

# 出力ディレクトリ作成
output_dir = Path("docs/images")
output_dir.mkdir(parents=True, exist_ok=True)

# スクリーンショット保存
output_file = output_dir / "screenshot.png"
pygame.image.save(screen, str(output_file))
print(f"スクリーンショットを生成しました: {output_file}")

# プレビュー用も生成（小さいサイズ）
preview_surface = pygame.transform.smoothscale(screen, (512, 300))
preview_file = output_dir / "screenshot_preview.png"
pygame.image.save(preview_surface, str(preview_file))
print(f"プレビュー画像を生成しました: {preview_file}")

# pygame終了
pygame.quit()

print("\n生成完了！")
print("フルサイズ: docs/images/screenshot.png (1024x600)")
print("プレビュー: docs/images/screenshot_preview.png (512x300)")