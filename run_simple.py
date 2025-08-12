#!/usr/bin/env python3
"""
シンプルな動作確認用スクリプト（Mac/デスクトップ用）
最小限の機能で動作確認
"""

import sys
import os
import pygame
from datetime import datetime
import calendar as cal

# SDL環境変数をデスクトップ用に設定
os.environ['SDL_VIDEODRIVER'] = ''  # デフォルトドライバを使用

def main():
    """シンプルなメインループ"""
    print("="*50)
    print("PiCalendar - Simple Test Mode")
    print("="*50)
    print("Controls:")
    print("  ESC/Q  : Exit application")
    print("  F11    : Toggle fullscreen")
    print("="*50)
    
    # pygame初期化
    pygame.init()
    
    # 画面設定
    WIDTH, HEIGHT = 1024, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PiCalendar - Simple Test")
    
    # フォント設定
    font_clock = pygame.font.Font(None, 120)
    font_date = pygame.font.Font(None, 36)
    font_calendar = pygame.font.Font(None, 22)
    font_weather = pygame.font.Font(None, 20)
    
    # 色定義
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (200, 200, 200)
    RED = (255, 100, 100)
    BLUE = (100, 100, 255)
    YELLOW = (255, 255, 100)
    DARK_BLUE = (20, 30, 60)
    
    clock = pygame.time.Clock()
    running = True
    fullscreen = False
    
    while running:
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        # 背景描画（グラデーション）
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = (
                int(20 + (50 - 20) * ratio),
                int(30 + (80 - 30) * ratio),
                int(60 + (120 - 60) * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))
        
        # 現在時刻取得
        now = datetime.now()
        
        # 時計表示
        time_str = now.strftime("%H:%M:%S")
        time_text = font_clock.render(time_str, True, WHITE)
        time_rect = time_text.get_rect(center=(WIDTH // 2, 100))
        # ドロップシャドウ
        shadow_text = font_clock.render(time_str, True, (10, 10, 20))
        screen.blit(shadow_text, (time_rect.x + 3, time_rect.y + 3))
        screen.blit(time_text, time_rect)
        
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
        cal_surface = pygame.Surface((cal_width, cal_height))
        cal_surface.set_alpha(200)
        cal_surface.fill((20, 20, 30))
        screen.blit(cal_surface, (cal_x, cal_y))
        pygame.draw.rect(screen, LIGHT_GRAY, (cal_x, cal_y, cal_width, cal_height), 2)
        
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
            day_text = font_calendar.render(day, True, color)
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
                    
                    day_text = font_calendar.render(str(day), True, color)
                    day_x = cal_x + i * day_width + day_width // 2
                    day_rect = day_text.get_rect(center=(day_x, day_y))
                    screen.blit(day_text, day_rect)
            day_y += 30
        
        # 天気パネル（左下）- ダミーデータ
        weather_x = 30
        weather_y = HEIGHT - 280
        weather_width = 420
        weather_height = 250
        
        # 天気パネル背景
        weather_surface = pygame.Surface((weather_width, weather_height))
        weather_surface.set_alpha(200)
        weather_surface.fill((20, 20, 30))
        screen.blit(weather_surface, (weather_x, weather_y))
        pygame.draw.rect(screen, LIGHT_GRAY, (weather_x, weather_y, weather_width, weather_height), 2)
        
        # 天気タイトル
        weather_title = "Weather Forecast - Tokyo"
        title_text = font_calendar.render(weather_title, True, WHITE)
        title_rect = title_text.get_rect(center=(weather_x + weather_width // 2, weather_y + 25))
        screen.blit(title_text, title_rect)
        
        # ダミー天気データ
        forecasts = [
            {"date": "Today", "temp": "15°/25°", "desc": "Sunny"},
            {"date": "Tomorrow", "temp": "17°/27°", "desc": "Cloudy"},
            {"date": now.strftime("%a"), "temp": "16°/26°", "desc": "Rain"}
        ]
        
        forecast_width = weather_width // 3
        for i, forecast in enumerate(forecasts):
            fx = weather_x + i * forecast_width + forecast_width // 2
            fy = weather_y + 60
            
            # 日付
            date_text = font_weather.render(forecast["date"], True, WHITE)
            date_rect = date_text.get_rect(center=(fx, fy))
            screen.blit(date_text, date_rect)
            
            # 天気アイコン（シンプルな図形）
            icon_y = fy + 40
            if "Sunny" in forecast["desc"]:
                pygame.draw.circle(screen, YELLOW, (fx, icon_y), 20)
            elif "Cloud" in forecast["desc"]:
                pygame.draw.circle(screen, GRAY, (fx, icon_y), 18)
            else:  # Rain
                pygame.draw.circle(screen, GRAY, (fx, icon_y - 5), 15)
                for j in range(3):
                    x = fx - 10 + j * 10
                    pygame.draw.line(screen, (135, 206, 235), 
                                   (x, icon_y + 10), (x - 5, icon_y + 25), 2)
            
            # 気温
            temp_text = font_weather.render(forecast["temp"], True, WHITE)
            temp_rect = temp_text.get_rect(center=(fx, icon_y + 40))
            screen.blit(temp_text, temp_rect)
            
            # 説明
            desc_text = font_weather.render(forecast["desc"], True, LIGHT_GRAY)
            desc_rect = desc_text.get_rect(center=(fx, icon_y + 60))
            screen.blit(desc_text, desc_rect)
        
        # FPS表示
        fps_text = font_weather.render(f"FPS: {int(clock.get_fps())}", True, GRAY)
        screen.blit(fps_text, (10, 10))
        
        # 画面更新
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    print("\nPiCalendar stopped.")
    return 0

if __name__ == "__main__":
    sys.exit(main())