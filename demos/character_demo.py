#!/usr/bin/env python3
"""
2Dキャラクターシステムデモ

TASK-401 Step 6/6: 統合デモ実行
"""

import os
import sys
import pygame
import time
import random
from typing import Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.character_renderer import CharacterRenderer
from src.character.state_machine import CharacterState


class MockAssetManager:
    """簡易アセット管理（デモ用）"""
    
    def get_image(self, path: str) -> Optional[pygame.Surface]:
        """画像を取得（デモ用ダミー）"""
        return None
    
    def get_font(self, path: str, size: int) -> Optional[pygame.font.Font]:
        """フォントを取得（デモ用）"""
        return pygame.font.Font(None, size)


class MockConfig:
    """簡易設定管理（デモ用）"""
    
    def __init__(self):
        self.data = {
            'character': {
                'enabled': True,
                'position': {'x': 100, 'y': 100},
                'scale': 2.0,
                'interactive': True,
                'weather_reactive': True,
                'time_reactive': True,
                'sprite_path': 'sprites/character_sheet.png',
                'metadata_path': 'sprites/character_sheet.json'
            }
        }
    
    def get(self, key: str, default=None):
        """設定値を取得"""
        keys = key.split('.')
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


class CharacterDemo:
    """キャラクターシステムデモ"""
    
    def __init__(self):
        """初期化"""
        pygame.init()
        
        # 画面設定
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("2D Character System Demo")
        
        # フォント
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # 時計
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # キャラクター設定
        self.asset_manager = MockAssetManager()
        self.config = MockConfig()
        
        try:
            self.character = CharacterRenderer(self.asset_manager, self.config)
            print("✅ Character renderer initialized")
        except Exception as e:
            print(f"❌ Failed to initialize character: {e}")
            self.character = None
        
        # デモ制御
        self.weather_types = ['sunny', 'cloudy', 'rain', 'thunder', 'snow', 'fog']
        self.current_weather = 'sunny'
        self.weather_change_timer = 0
        self.weather_change_interval = 5  # 5秒間隔
        
        self.time_speed = 60  # 実時間の60倍速
        self.demo_time = 6 * 3600  # 朝6時から開始（秒）
        
        # UI状態
        self.show_debug = True
        self.running = True
        
        # 統計情報
        self.click_count = 0
        self.state_changes = 0
        self.last_state = None
        
        print("🎮 Demo initialized successfully!")
        print("Controls:")
        print("  - Click on character to interact")
        print("  - Press SPACE to change weather manually")
        print("  - Press D to toggle debug info")
        print("  - Press ESC or close window to quit")
    
    def update(self, dt: float):
        """デモ更新"""
        if not self.character:
            return
        
        # 天気自動変更
        self.weather_change_timer += dt
        if self.weather_change_timer >= self.weather_change_interval:
            self.change_weather()
            self.weather_change_timer = 0
        
        # 時間進行（加速）
        self.demo_time += dt * self.time_speed
        current_hour = int((self.demo_time / 3600) % 24)
        
        # キャラクター更新
        old_state = self.character.state_machine.get_current_state()
        self.character.update_time(current_hour)
        self.character.update_weather(self.current_weather)
        self.character.update(dt)
        
        # 状態変更統計
        new_state = self.character.state_machine.get_current_state()
        if new_state != self.last_state:
            self.state_changes += 1
            self.last_state = new_state
    
    def change_weather(self):
        """天気を変更"""
        old_weather = self.current_weather
        while self.current_weather == old_weather:
            self.current_weather = random.choice(self.weather_types)
        print(f"🌤️ Weather changed: {old_weather} -> {self.current_weather}")
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.change_weather()
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.character:  # 左クリック
                    x, y = event.pos
                    if self.character.on_click(x, y):
                        self.click_count += 1
                        print(f"👆 Character clicked! (Total: {self.click_count})")
    
    def render(self):
        """描画"""
        # 背景を描画（時間帯による色変更）
        hour = int((self.demo_time / 3600) % 24)
        bg_color = self.get_background_color(hour)
        self.screen.fill(bg_color)
        
        # キャラクター描画
        if self.character:
            self.character.render(self.screen)
        
        # UI描画
        self.draw_ui()
        
        pygame.display.flip()
    
    def get_background_color(self, hour: int) -> tuple:
        """時間帯による背景色"""
        if 6 <= hour < 12:  # 朝
            return (135, 206, 235)  # Sky blue
        elif 12 <= hour < 18:  # 昼
            return (173, 216, 230)  # Light blue
        elif 18 <= hour < 22:  # 夕方
            return (255, 165, 0)    # Orange
        else:  # 夜
            return (25, 25, 112)    # Midnight blue
    
    def draw_ui(self):
        """UI描画"""
        if not self.show_debug:
            return
        
        y_offset = 10
        line_height = 25
        
        # タイトル
        title = self.title_font.render("2D Character System Demo", True, (255, 255, 255))
        self.screen.blit(title, (10, y_offset))
        y_offset += 40
        
        # 時間表示
        hour = int((self.demo_time / 3600) % 24)
        minute = int((self.demo_time / 60) % 60)
        time_text = f"Time: {hour:02d}:{minute:02d}"
        time_surface = self.font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (10, y_offset))
        y_offset += line_height
        
        # 天気表示
        weather_text = f"Weather: {self.current_weather}"
        weather_surface = self.font.render(weather_text, True, (255, 255, 255))
        self.screen.blit(weather_surface, (10, y_offset))
        y_offset += line_height
        
        if self.character:
            # 現在の状態
            current_state = self.character.state_machine.get_current_state()
            state_text = f"State: {current_state.value}"
            state_surface = self.font.render(state_text, True, (255, 255, 255))
            self.screen.blit(state_surface, (10, y_offset))
            y_offset += line_height
            
            # 気分
            mood = self.character.state_machine.get_mood_indicator()
            mood_text = f"Mood: {mood}"
            mood_surface = self.font.render(mood_text, True, (255, 255, 255))
            self.screen.blit(mood_surface, (10, y_offset))
            y_offset += line_height
            
            # エネルギー
            energy = self.character.state_machine.context.get('energy_level', 1.0)
            energy_text = f"Energy: {energy:.2f}"
            energy_surface = self.font.render(energy_text, True, (255, 255, 255))
            self.screen.blit(energy_surface, (10, y_offset))
            y_offset += line_height
            
            # クリック数
            click_count = self.character.state_machine.context.get('click_count', 0)
            click_text = f"Click Count: {click_count:.1f}"
            click_surface = self.font.render(click_text, True, (255, 255, 255))
            self.screen.blit(click_surface, (10, y_offset))
            y_offset += line_height
        
        # 統計情報
        stats_text = f"Total Clicks: {self.click_count} | State Changes: {self.state_changes}"
        stats_surface = self.font.render(stats_text, True, (255, 255, 255))
        self.screen.blit(stats_surface, (10, y_offset))
        y_offset += line_height
        
        # 操作説明
        y_offset += 10
        controls = [
            "Controls:",
            "  Click character to interact",
            "  SPACE - Change weather",
            "  D - Toggle debug",
            "  ESC - Exit"
        ]
        
        for control in controls:
            control_surface = self.font.render(control, True, (200, 200, 200))
            self.screen.blit(control_surface, (10, y_offset))
            y_offset += 20
        
        # FPS表示
        fps_text = f"FPS: {self.clock.get_fps():.1f}"
        fps_surface = self.font.render(fps_text, True, (255, 255, 0))
        self.screen.blit(fps_surface, (self.width - 80, 10))
        
        # キャラクター領域表示（デバッグ用）
        if self.character:
            bounds = self.character.get_bounds()
            pygame.draw.rect(self.screen, (0, 255, 0), bounds, 2)
    
    def run(self):
        """デモ実行"""
        print("🚀 Starting character demo...")
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self.handle_events()
            self.update(dt)
            self.render()
            
            self.clock.tick(self.fps)
        
        print("👋 Demo finished!")
        pygame.quit()


def main():
    """メイン関数"""
    print("=== 2D Character System Demo ===")
    print("TASK-401 Step 6/6: Demo with animated character")
    print()
    
    try:
        demo = CharacterDemo()
        demo.run()
        
        print("✅ Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)