#!/usr/bin/env python3
"""
インタラクティブキャラクターデモ

TASK-402 Step 6/6: 拡張キャラクターアニメーションシステムの総合デモ

使用方法:
  python demos/interactive_character_demo.py

キーボード操作:
  - 数字キー 1-6: 天気シナリオ切替
  - S: 季節切替 (春->夏->秋->冬)
  - T: 時間帯切替 (朝->昼->夕->夜)
  - M: 気分切替 (neutral->cheerful->joyful->ecstatic)
  - E: エネルギーレベル調整 (+0.2)
  - R: エネルギーレベルリセット
  - SPACE: 強制状態切替 (idle->walk->wave->celebrating...)
  - F: 遷移スキップ
  - Q/ESC: 終了

マウス操作:
  - 左クリック: ランダム状態遷移
  - 右クリック: 天気シナリオランダム変更
"""

import os
import sys
import time
import random
import logging
from typing import Dict, Any, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame
from src.character.extended_state_machine import ExtendedCharacterState
from src.character.weather_aware_character_renderer import WeatherAwareCharacterRenderer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractiveCharacterDemo:
    """インタラクティブキャラクターデモ"""
    
    def __init__(self):
        """初期化"""
        self.screen_width = 1024
        self.screen_height = 768
        self.fps = 60
        
        # pygame初期化
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Interactive Character Demo - TASK-402")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # キャラクターレンダラー初期化
        # 実際のスプライトシートがない場合はテスト用パスを使用
        sprite_path = self._find_sprite_sheet()
        metadata_path = self._find_metadata()
        
        try:
            self.character_renderer = WeatherAwareCharacterRenderer(sprite_path, metadata_path)
        except Exception as e:
            logger.error(f"Failed to initialize character renderer: {e}")
            # フォールバック: ダミーレンダラーを作成
            self.character_renderer = self._create_dummy_renderer()
        
        # デモ状態
        self.running = True
        self.show_help = True
        self.last_update_time = time.time()
        
        # UI要素
        self.info_panel_width = 300
        self.character_area = pygame.Rect(self.info_panel_width, 0, 
                                        self.screen_width - self.info_panel_width, 
                                        self.screen_height)
        
        # キャラクター表示位置
        self.character_x = self.character_area.centerx - 64
        self.character_y = self.character_area.centery - 64
        
        # 天気シナリオ管理
        self.weather_scenarios = self.character_renderer.get_available_scenarios()
        self.current_scenario_index = 0
        
        # 状態管理
        self.seasons = ['spring', 'summer', 'autumn', 'winter']
        self.times_of_day = ['morning', 'afternoon', 'evening', 'night']
        self.moods = ['neutral', 'cheerful', 'joyful', 'ecstatic']
        self.force_states = list(ExtendedCharacterState)
        
        self.current_season_index = 0
        self.current_time_index = 0
        self.current_mood_index = 0
        self.current_force_state_index = 0
        
        # 初期設定
        self._setup_initial_state()
        
        logger.info("Interactive Character Demo initialized")
    
    def _find_sprite_sheet(self) -> str:
        """スプライトシートパスを検索"""
        possible_paths = [
            "assets/sprites/extended_character_sheet.png",
            "tools/extended_character_sheet.png",
            "tests/test_sprite.png"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # フォールバック: ダミー画像を作成
        return self._create_dummy_sprite_sheet()
    
    def _find_metadata(self) -> Optional[str]:
        """メタデータファイルを検索"""
        possible_paths = [
            "assets/sprites/extended_character_metadata.json",
            "tools/extended_character_metadata.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _create_dummy_sprite_sheet(self) -> str:
        """ダミースプライトシートを作成"""
        dummy_path = "dummy_sprite_sheet.png"
        
        # 1024x1920のダミー画像を作成
        dummy_surface = pygame.Surface((1024, 1920), pygame.SRCALPHA)
        
        # 15行8列のキャラクタースプライトを描画
        frame_width, frame_height = 128, 128
        
        for row in range(15):
            for col in range(8):
                x = col * frame_width
                y = row * frame_height
                
                # カラフルなダミーキャラクターを描画
                color = (
                    (row * 17 + col * 32) % 255,
                    (row * 23 + col * 41) % 255,
                    (row * 31 + col * 47) % 255,
                    255
                )
                
                # 丸いキャラクター
                center_x = x + frame_width // 2
                center_y = y + frame_height // 2
                pygame.draw.circle(dummy_surface, color, (center_x, center_y), 40)
                
                # 目
                eye_size = 8
                pygame.draw.circle(dummy_surface, (0, 0, 0), (center_x - 15, center_y - 10), eye_size)
                pygame.draw.circle(dummy_surface, (0, 0, 0), (center_x + 15, center_y - 10), eye_size)
                
                # 口
                mouth_rect = pygame.Rect(center_x - 10, center_y + 10, 20, 8)
                pygame.draw.ellipse(dummy_surface, (0, 0, 0), mouth_rect)
        
        pygame.image.save(dummy_surface, dummy_path)
        logger.info(f"Created dummy sprite sheet: {dummy_path}")
        return dummy_path
    
    def _create_dummy_renderer(self):
        """ダミーレンダラーを作成"""
        class DummyRenderer:
            def __init__(self):
                self.current_frame = pygame.Surface((128, 128), pygame.SRCALPHA)
                self.current_frame.fill((100, 150, 200, 128))
                pygame.draw.circle(self.current_frame, (255, 255, 255), (64, 64), 50)
                pygame.draw.circle(self.current_frame, (0, 0, 0), (50, 50), 8)
                pygame.draw.circle(self.current_frame, (0, 0, 0), (78, 50), 8)
                pygame.draw.ellipse(self.current_frame, (0, 0, 0), (54, 70, 20, 8))
            
            def update_weather(self, *args, **kwargs): pass
            def update_context(self, *args, **kwargs): pass
            def update(self, dt): pass
            def get_current_frame(self): return self.current_frame
            def get_status(self): return {'current_state': 'dummy', 'weather_description': 'N/A'}
            def get_available_scenarios(self): return ['sunny_day', 'rainy_day']
            def simulate_weather_scenario(self, scenario): pass
            def force_state(self, state, mood=None): return True
        
        return DummyRenderer()
    
    def _setup_initial_state(self):
        """初期状態を設定"""
        # 初期天気: 晴れ
        self.character_renderer.simulate_weather_scenario('sunny_day')
        
        # 初期コンテキスト
        self.character_renderer.update_context(
            season=self.seasons[self.current_season_index],
            time_of_day=self.times_of_day[self.current_time_index],
            energy_level=0.7,
            mood=self.moods[self.current_mood_index]
        )
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse(event.button, event.pos)
    
    def _handle_keyboard(self, key):
        """キーボード入力処理"""
        if key in [pygame.K_q, pygame.K_ESCAPE]:
            self.running = False
        
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        
        # 天気シナリオ (1-6)
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
            scenario_index = key - pygame.K_1
            if scenario_index < len(self.weather_scenarios):
                scenario = self.weather_scenarios[scenario_index]
                self.character_renderer.simulate_weather_scenario(scenario)
                logger.info(f"Applied weather scenario: {scenario}")
        
        # 季節切替 (S)
        elif key == pygame.K_s:
            self.current_season_index = (self.current_season_index + 1) % len(self.seasons)
            season = self.seasons[self.current_season_index]
            self.character_renderer.update_context(season=season)
            logger.info(f"Season changed to: {season}")
        
        # 時間切替 (T)
        elif key == pygame.K_t:
            self.current_time_index = (self.current_time_index + 1) % len(self.times_of_day)
            time_of_day = self.times_of_day[self.current_time_index]
            self.character_renderer.update_context(time_of_day=time_of_day)
            logger.info(f"Time changed to: {time_of_day}")
        
        # 気分切替 (M)
        elif key == pygame.K_m:
            self.current_mood_index = (self.current_mood_index + 1) % len(self.moods)
            mood = self.moods[self.current_mood_index]
            self.character_renderer.update_context(mood=mood)
            logger.info(f"Mood changed to: {mood}")
        
        # エネルギー調整 (E)
        elif key == pygame.K_e:
            current_status = self.character_renderer.get_status()
            current_energy = current_status.get('context', {}).get('energy_level', 0.7)
            new_energy = min(1.0, current_energy + 0.2)
            self.character_renderer.update_context(energy_level=new_energy)
            logger.info(f"Energy level: {new_energy:.1f}")
        
        # エネルギーリセット (R)
        elif key == pygame.K_r:
            self.character_renderer.update_context(energy_level=0.7)
            logger.info("Energy level reset to 0.7")
        
        # 強制状態切替 (SPACE)
        elif key == pygame.K_SPACE:
            self.current_force_state_index = (self.current_force_state_index + 1) % len(self.force_states)
            state = self.force_states[self.current_force_state_index]
            mood = self.moods[self.current_mood_index]
            self.character_renderer.force_state(state, mood)
            logger.info(f"Forced state: {state.value}")
        
        # 遷移スキップ (F)
        elif key == pygame.K_f:
            if hasattr(self.character_renderer, 'animator'):
                self.character_renderer.animator.skip_current_transition()
            logger.info("Transition skipped")
    
    def _handle_mouse(self, button, pos):
        """マウス入力処理"""
        if button == 1:  # 左クリック
            # ランダム状態遷移
            random_state = random.choice(self.force_states)
            random_mood = random.choice(self.moods)
            self.character_renderer.force_state(random_state, random_mood)
            logger.info(f"Random state: {random_state.value} with mood {random_mood}")
        
        elif button == 3:  # 右クリック
            # ランダム天気シナリオ
            random_scenario = random.choice(self.weather_scenarios)
            self.character_renderer.simulate_weather_scenario(random_scenario)
            logger.info(f"Random weather: {random_scenario}")
    
    def update(self):
        """更新処理"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # キャラクターレンダラーの更新
        self.character_renderer.update(dt)
    
    def draw(self):
        """描画処理"""
        # 背景を暗いグレーで塗りつぶし
        self.screen.fill((32, 32, 32))
        
        # 情報パネル背景
        info_panel = pygame.Rect(0, 0, self.info_panel_width, self.screen_height)
        pygame.draw.rect(self.screen, (48, 48, 48), info_panel)
        pygame.draw.line(self.screen, (64, 64, 64), 
                        (self.info_panel_width, 0), (self.info_panel_width, self.screen_height), 2)
        
        # キャラクター表示エリア背景
        pygame.draw.rect(self.screen, (24, 32, 40), self.character_area)
        
        # キャラクター描画
        self._draw_character()
        
        # 情報パネル描画
        self._draw_info_panel()
        
        # ヘルプ表示
        if self.show_help:
            self._draw_help()
        
        pygame.display.flip()
    
    def _draw_character(self):
        """キャラクター描画"""
        frame = self.character_renderer.get_current_frame()
        if frame:
            # キャラクターを中央に描画
            char_rect = frame.get_rect()
            char_rect.center = (self.character_x + 64, self.character_y + 64)
            self.screen.blit(frame, char_rect)
            
            # 遷移中の場合は進行度を表示
            if hasattr(self.character_renderer, 'animator'):
                if self.character_renderer.animator.is_transitioning():
                    progress = self.character_renderer.animator.get_transition_progress()
                    self._draw_transition_progress(progress)
    
    def _draw_transition_progress(self, progress: float):
        """遷移進行度を描画"""
        bar_width = 200
        bar_height = 8
        bar_x = self.character_area.centerx - bar_width // 2
        bar_y = self.character_y + 150
        
        # 背景
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (64, 64, 64), bg_rect)
        
        # 進行度
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
            pygame.draw.rect(self.screen, (100, 200, 100), progress_rect)
        
        # ラベル
        label = self.font.render(f"Transition: {progress:.1%}", True, (200, 200, 200))
        label_rect = label.get_rect()
        label_rect.centerx = self.character_area.centerx
        label_rect.y = bar_y + bar_height + 4
        self.screen.blit(label, label_rect)
    
    def _draw_info_panel(self):
        """情報パネル描画"""
        y_offset = 10
        
        # タイトル
        title = self.title_font.render("Character Demo", True, (255, 255, 255))
        self.screen.blit(title, (10, y_offset))
        y_offset += 50
        
        # 現在の状態情報
        status = self.character_renderer.get_status()
        
        info_items = [
            ("State", status.get('current_state', 'Unknown')),
            ("Animation", status.get('current_animation', 'Unknown')),
            ("Weather", status.get('weather_description', 'N/A')),
            ("", ""),
            ("Season", status.get('context', {}).get('season', 'N/A')),
            ("Time", status.get('context', {}).get('time_of_day', 'N/A')),
            ("Mood", status.get('context', {}).get('mood', 'N/A')),
            ("Energy", f"{status.get('context', {}).get('energy_level', 0.0):.1f}"),
        ]
        
        # 天気詳細情報
        if 'weather_details' in status:
            weather = status['weather_details']
            info_items.extend([
                ("", ""),
                ("Temperature", f"{weather.get('temperature', 0):.1f}°C"),
                ("Feels Like", f"{weather.get('feels_like', 0):.1f}°C"),
                ("Comfort", weather.get('comfort_level', 'N/A')),
                ("Severity", f"{weather.get('severity', 0.0):.1%}"),
            ])
        
        # 適応状況
        if 'adaptation' in status:
            adapt = status['adaptation']
            info_items.extend([
                ("", ""),
                ("Adaptation", f"{adapt.get('adaptation_level', 0.0):.1%}"),
                ("Weather Variety", str(adapt.get('weather_variety', 0))),
                ("Records", str(adapt.get('total_weather_records', 0))),
            ])
        
        # 情報項目を描画
        for label, value in info_items:
            if label:
                text = self.font.render(f"{label}: {value}", True, (200, 200, 200))
            else:
                text = self.font.render("", True, (200, 200, 200))  # 空行
            
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
    
    def _draw_help(self):
        """ヘルプ表示"""
        help_surface = pygame.Surface((400, 400), pygame.SRCALPHA)
        help_surface.fill((0, 0, 0, 180))
        
        help_texts = [
            "=== CONTROLS ===",
            "",
            "1-6: Weather scenarios",
            "S: Cycle seasons",
            "T: Cycle time of day",
            "M: Cycle moods",
            "E: Increase energy (+0.2)",
            "R: Reset energy (0.7)",
            "SPACE: Cycle forced states",
            "F: Skip transition",
            "",
            "Left Click: Random state",
            "Right Click: Random weather",
            "",
            "H: Toggle this help",
            "Q/ESC: Quit",
            "",
            "Weather Scenarios:",
        ]
        
        # 利用可能な天気シナリオを追加
        for i, scenario in enumerate(self.weather_scenarios[:6]):
            help_texts.append(f"{i+1}: {scenario.replace('_', ' ').title()}")
        
        y_offset = 10
        for text in help_texts:
            if text.startswith("==="):
                color = (255, 255, 100)
                font = self.title_font
            elif text.endswith(":"):
                color = (150, 255, 150)
                font = self.font
            else:
                color = (200, 200, 200)
                font = self.font
            
            rendered = font.render(text, True, color)
            help_surface.blit(rendered, (10, y_offset))
            y_offset += 20 if font == self.font else 25
        
        # ヘルプサーフェスを中央に描画
        help_rect = help_surface.get_rect()
        help_rect.center = self.screen.get_rect().center
        self.screen.blit(help_surface, help_rect)
    
    def run(self):
        """メインループ実行"""
        logger.info("Starting interactive character demo...")
        logger.info("Press H for help, Q or ESC to quit")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)
        
        logger.info("Demo finished")
        pygame.quit()


def main():
    """メイン関数"""
    print("=== Interactive Character Demo ===")
    print("TASK-402 Step 6/6: Complete Character Animation System Demo")
    print()
    print("Features:")
    print("  ✨ 15-state character animation system")
    print("  🌦️ Weather-reactive character behaviors") 
    print("  🎭 Smooth animation transitions")
    print("  🎮 Interactive controls")
    print("  📊 Real-time status display")
    print()
    print("Press H in the demo for help, Q or ESC to quit")
    print("Starting demo...")
    print()
    
    try:
        demo = InteractiveCharacterDemo()
        demo.run()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)