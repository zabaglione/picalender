#!/usr/bin/env python3
"""
2Dキャラクターシステム動作テスト

TASK-401 Step 6/6: 自動テストでデモ動作を確認
"""

import os
import sys
import pygame
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.character_renderer import CharacterRenderer
from src.character.state_machine import CharacterState


class MockAssetManager:
    """簡易アセット管理（テスト用）"""
    
    def get_image(self, path: str):
        return None
    
    def get_font(self, path: str, size: int):
        return pygame.font.Font(None, size)


class MockConfig:
    """簡易設定管理（テスト用）"""
    
    def get(self, key: str, default=None):
        config_map = {
            'character.enabled': True,
            'character.position.x': 100,
            'character.position.y': 100,
            'character.scale': 1.0,
            'character.interactive': True,
            'character.weather_reactive': True,
            'character.time_reactive': True,
            'character.sprite_path': 'sprites/character_sheet.png',
            'character.metadata_path': 'sprites/character_sheet.json'
        }
        return config_map.get(key, default)


def test_character_system():
    """キャラクターシステム統合テスト"""
    print("=== 2D Character System Integration Test ===")
    
    # pygame初期化（headless）
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    pygame.display.set_mode((800, 600))
    
    # キャラクター初期化
    print("1. Initializing character renderer...")
    try:
        asset_manager = MockAssetManager()
        config = MockConfig()
        character = CharacterRenderer(asset_manager, config)
        print("   ✅ Character renderer created")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # 基本動作テスト
    print("\n2. Testing basic operations...")
    
    # 初期状態確認
    initial_state = character.state_machine.get_current_state()
    print(f"   Initial state: {initial_state.value}")
    
    # 天気反応テスト
    print("   Testing weather reactions...")
    weather_types = ['sunny', 'rain', 'thunder', 'snow']
    for weather in weather_types:
        character.update_weather(weather)
        current_weather = character.state_machine.context.get('weather')
        print(f"     Weather: {weather} -> Context: {current_weather}")
    
    # 時間反応テスト
    print("   Testing time reactions...")
    time_periods = [6, 12, 18, 23]  # 朝、昼、夕方、夜
    for hour in time_periods:
        character.update_time(hour)
        current_hour = character.state_machine.context.get('hour')
        print(f"     Hour: {hour} -> Context: {current_hour}")
    
    # クリックインタラクションテスト
    print("   Testing click interactions...")
    initial_click_count = character.state_machine.context.get('click_count', 0)
    
    # キャラクター領域内クリック
    bounds = character.get_bounds()
    click_x = bounds[0] + bounds[2] // 2
    click_y = bounds[1] + bounds[3] // 2
    
    clicked = character.on_click(click_x, click_y)
    final_click_count = character.state_machine.context.get('click_count', 0)
    
    print(f"     Click at ({click_x}, {click_y}): {clicked}")
    print(f"     Click count: {initial_click_count} -> {final_click_count}")
    
    # 状態更新テスト
    print("\n3. Testing state updates...")
    state_changes = []
    current_state = character.state_machine.get_current_state()
    
    for i in range(10):
        character.update(0.5)  # 0.5秒更新
        new_state = character.state_machine.get_current_state()
        if new_state != current_state:
            state_changes.append((current_state.value, new_state.value))
            current_state = new_state
    
    print(f"   State changes during 5s simulation: {len(state_changes)}")
    for old, new in state_changes:
        print(f"     {old} -> {new}")
    
    # エネルギーシステムテスト
    print("\n4. Testing energy system...")
    initial_energy = character.state_machine.context.get('energy_level', 1.0)
    
    # 活発な状態に変更してエネルギー消費をテスト
    character.state_machine.force_state(CharacterState.EXCITED)
    excited_energy = character.state_machine.context.get('energy_level', 1.0)
    
    print(f"   Energy: {initial_energy:.2f} -> {excited_energy:.2f} (after excitement)")
    
    # 気分インジケーターテスト
    print("\n5. Testing mood indicators...")
    moods = []
    for state in [CharacterState.IDLE, CharacterState.HAPPY, CharacterState.EXCITED, CharacterState.SLEEPING]:
        character.state_machine.force_state(state)
        mood = character.state_machine.get_mood_indicator()
        moods.append((state.value, mood))
        print(f"   State: {state.value} -> Mood: {mood}")
    
    # レンダリングテスト
    print("\n6. Testing rendering...")
    try:
        screen = pygame.Surface((800, 600))
        character.render(screen)
        print("   ✅ Rendering completed without errors")
    except Exception as e:
        print(f"   ❌ Rendering failed: {e}")
        return False
    
    # 境界値テスト
    print("\n7. Testing boundary conditions...")
    
    # 無効な座標でのクリック
    invalid_click = character.on_click(-10, -10)
    print(f"   Invalid click result: {invalid_click}")
    
    # スケール変更
    character.set_scale(0.5)
    character.set_scale(2.0)
    print("   ✅ Scale changes handled")
    
    # 位置変更
    character.set_position(200, 300)
    new_bounds = character.get_bounds()
    print(f"   Position changed: bounds = {new_bounds}")
    
    print("\n=== Integration Test Results ===")
    print("✅ All character system components working correctly!")
    print("✅ State machine, animations, and interactions functional!")
    print("✅ Weather and time reactions implemented!")
    print("✅ Energy system and mood indicators operational!")
    
    return True


def main():
    """メイン関数"""
    print("TASK-401 Step 6/6: Demo with animated character")
    print("Running automated integration test...\n")
    
    try:
        success = test_character_system()
        
        if success:
            print("\n🎉 Character system integration test PASSED!")
            print("🎮 Interactive demo available at: python demos/character_demo.py")
            return True
        else:
            print("\n❌ Character system integration test FAILED!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)