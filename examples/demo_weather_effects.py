#!/usr/bin/env python3
"""
天気エフェクトデモ

アニメーション天気エフェクトのデモンストレーション
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import time
from src.effects.weather_effects import WeatherEffects

def main():
    """メイン処理"""
    pygame.init()
    
    # 画面設定
    screen_width = 1024
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Weather Effects Demo")
    
    # 設定
    class MockConfig:
        def get(self, key, default=None):
            return {
                'effects.enabled': True,
                'effects.intensity': 0.7,
            }.get(key, default)
    
    config = MockConfig()
    
    # エフェクトマネージャー
    effects = WeatherEffects(screen_width, screen_height, config)
    
    # エフェクトパターン
    weather_patterns = [
        ("Clear Sky", "sunny", (135, 206, 235)),  # スカイブルー
        ("Light Rain", "rain", (80, 90, 100)),    # 暗い青灰色
        ("Thunderstorm", "thunder", (40, 40, 60)), # 非常に暗い
        ("Snowfall", "snow", (200, 220, 240)),    # 薄い青白
        ("Foggy", "fog", (150, 150, 160)),        # 灰色
        ("Heavy Rain", "rain", (60, 70, 80)),     # 暗い
    ]
    
    current_pattern = 0
    pattern_name, weather_type, bg_color = weather_patterns[current_pattern]
    effects.set_weather(weather_type)
    
    # FPS管理
    clock = pygame.time.Clock()
    running = True
    
    # 自動切り替えタイマー
    auto_switch = True
    switch_interval = 5.0  # 5秒ごと
    last_switch = time.time()
    
    # パフォーマンス計測
    frame_times = []
    
    while running:
        dt = clock.tick(60) / 1000.0  # 60 FPS目標
        frame_times.append(dt)
        if len(frame_times) > 60:
            frame_times.pop(0)
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 次のパターンへ
                    current_pattern = (current_pattern + 1) % len(weather_patterns)
                    pattern_name, weather_type, bg_color = weather_patterns[current_pattern]
                    effects.set_weather(weather_type)
                elif event.key == pygame.K_UP:
                    # 強度を上げる
                    new_intensity = min(1.0, effects.intensity + 0.1)
                    effects.set_intensity(new_intensity)
                elif event.key == pygame.K_DOWN:
                    # 強度を下げる
                    new_intensity = max(0.1, effects.intensity - 0.1)
                    effects.set_intensity(new_intensity)
                elif event.key == pygame.K_e:
                    # エフェクトの有効/無効切り替え
                    effects.set_enabled(not effects.enabled)
                elif event.key == pygame.K_a:
                    # 自動切り替えのオン/オフ
                    auto_switch = not auto_switch
                elif event.key == pygame.K_l and weather_type == "thunder":
                    # 雷を手動トリガー
                    effects.trigger_lightning()
        
        # 自動切り替え
        if auto_switch:
            current_time = time.time()
            if current_time - last_switch >= switch_interval:
                current_pattern = (current_pattern + 1) % len(weather_patterns)
                pattern_name, weather_type, bg_color = weather_patterns[current_pattern]
                effects.set_weather(weather_type)
                last_switch = current_time
        
        # 更新
        effects.update(dt)
        
        # 描画
        screen.fill(bg_color)
        
        # エフェクトを描画
        effects.render(screen)
        
        # UI情報を表示
        font = pygame.font.Font(None, 24)
        
        # 現在のパターン
        pattern_text = font.render(f"Pattern: {pattern_name}", True, (255, 255, 255))
        screen.blit(pattern_text, (20, 20))
        
        # 強度
        intensity_text = font.render(f"Intensity: {effects.intensity:.1f}", True, (255, 255, 255))
        screen.blit(intensity_text, (20, 50))
        
        # FPS
        if frame_times:
            avg_frame_time = sum(frame_times) / len(frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
            screen.blit(fps_text, (20, 80))
        
        # エフェクト状態
        status = "ON" if effects.enabled else "OFF"
        status_text = font.render(f"Effects: {status}", True, (255, 255, 255))
        screen.blit(status_text, (20, 110))
        
        # 自動切り替え状態
        auto_status = "ON" if auto_switch else "OFF"
        auto_text = font.render(f"Auto-switch: {auto_status}", True, (255, 255, 255))
        screen.blit(auto_text, (20, 140))
        
        # 操作説明
        help_font = pygame.font.Font(None, 18)
        help_texts = [
            "Controls:",
            "  SPACE: Next weather pattern",
            "  UP/DOWN: Adjust intensity",
            "  E: Toggle effects ON/OFF",
            "  A: Toggle auto-switch",
            "  L: Trigger lightning (thunder only)",
            "  ESC: Exit"
        ]
        
        y = screen_height - 140
        for text in help_texts:
            color = (180, 180, 180) if text.startswith("  ") else (255, 255, 255)
            help_surface = help_font.render(text, True, color)
            screen.blit(help_surface, (screen_width - 280, y))
            y += 20
        
        pygame.display.flip()
    
    # クリーンアップ
    effects.clear()
    pygame.quit()
    
    # パフォーマンスサマリー
    if frame_times:
        avg_frame_time = sum(frame_times) / len(frame_times)
        avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        print(f"\nPerformance Summary:")
        print(f"  Average FPS: {avg_fps:.1f}")
        print(f"  Average frame time: {avg_frame_time*1000:.2f}ms")


if __name__ == "__main__":
    main()