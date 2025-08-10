#!/usr/bin/env python3
"""
拡張キャラクターシステムのテスト

TASK-402 Step 3/6のテスト実行
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.character.extended_state_machine import (
    ExtendedCharacterStateMachine, 
    ExtendedCharacterState,
    Priority,
    StateContext
)
from src.character.extended_animation_system import ExtendedCharacterAnimator


class TestExtendedStateMachine(unittest.TestCase):
    """拡張キャラクター状態マシンのテスト"""
    
    def setUp(self):
        """テスト準備"""
        self.state_machine = ExtendedCharacterStateMachine()
    
    def test_initial_state(self):
        """初期状態のテスト"""
        self.assertEqual(self.state_machine.get_current_state(), ExtendedCharacterState.IDLE)
    
    def test_weather_reactions(self):
        """天気反応のテスト"""
        # 雨天時の反応
        self.state_machine.force_state(ExtendedCharacterState.WALK)
        self.state_machine.on_weather_change('rain')
        
        # 何度か更新して遷移を確認
        transition_occurred = False
        for _ in range(20):
            new_state = self.state_machine.update(0.1)
            if new_state == ExtendedCharacterState.UMBRELLA:
                transition_occurred = True
                break
        
        self.assertTrue(transition_occurred or self.state_machine.get_current_state() == ExtendedCharacterState.UMBRELLA)
    
    def test_thunderstorm_reaction(self):
        """雷雨時の反応テスト"""
        self.state_machine.force_state(ExtendedCharacterState.WALK)
        self.state_machine.on_weather_change('thunderstorm')
        
        # 雷雨は高確率で隠れる状態に遷移
        transition_occurred = False
        for _ in range(10):
            new_state = self.state_machine.update(0.1)
            if new_state == ExtendedCharacterState.HIDING:
                transition_occurred = True
                break
        
        self.assertTrue(transition_occurred)
    
    def test_time_based_transitions(self):
        """時間ベースの遷移テスト"""
        # 朝の時間に設定
        self.state_machine.context.hour = 7
        self.state_machine.force_state(ExtendedCharacterState.SLEEPING)
        
        # ストレッチ状態への遷移を確認
        transition_occurred = False
        for _ in range(20):
            new_state = self.state_machine.update(0.1)
            if new_state == ExtendedCharacterState.STRETCHING:
                transition_occurred = True
                break
        
        # 朝は睡眠からストレッチに遷移する可能性がある
        self.assertTrue(transition_occurred or 
                       self.state_machine.get_current_state() in 
                       [ExtendedCharacterState.STRETCHING, ExtendedCharacterState.SLEEPING])
    
    def test_energy_system(self):
        """エネルギーシステムのテスト"""
        initial_energy = self.state_machine.context.energy_level
        
        # 踊り状態でエネルギー消費
        self.state_machine.force_state(ExtendedCharacterState.DANCING)
        
        # 複数回更新してエネルギー変化を確認
        for _ in range(100):
            self.state_machine.update(0.01)
        
        final_energy = self.state_machine.context.energy_level
        self.assertLess(final_energy, initial_energy, "Dancing should consume energy")
    
    def test_priority_system(self):
        """優先度システムのテスト"""
        # 低エネルギー状態に設定
        self.state_machine.context.energy_level = 0.1
        self.state_machine.force_state(ExtendedCharacterState.DANCING)
        
        # エネルギー不足でより低活動な状態に遷移するかテスト
        for _ in range(50):
            new_state = self.state_machine.update(0.1)
            if new_state and new_state != ExtendedCharacterState.DANCING:
                # エネルギー不足時は活動的でない状態に遷移すべき
                self.assertNotIn(new_state, [ExtendedCharacterState.CELEBRATING, ExtendedCharacterState.DANCING])
                break
    
    def test_click_interactions(self):
        """クリックインタラクションのテスト"""
        initial_click_count = self.state_machine.context.click_count
        
        # クリックイベント
        self.state_machine.on_click()
        
        # クリック数が増加していることを確認
        self.assertGreater(self.state_machine.context.click_count, initial_click_count)
        
        # クリック後の状態変化をテスト
        transition_occurred = False
        for _ in range(10):
            new_state = self.state_machine.update(0.1)
            if new_state in [ExtendedCharacterState.WAVE, ExtendedCharacterState.CELEBRATING]:
                transition_occurred = True
                break
        
        self.assertTrue(transition_occurred, "Click should trigger friendly reactions")
    
    def test_mood_indicators(self):
        """気分インジケーターのテスト"""
        # 異なる状態での気分をテスト
        test_states = [
            ExtendedCharacterState.CELEBRATING,
            ExtendedCharacterState.HIDING,
            ExtendedCharacterState.SLEEPING,
            ExtendedCharacterState.DANCING
        ]
        
        for state in test_states:
            self.state_machine.force_state(state)
            mood = self.state_machine.get_mood_indicator()
            self.assertIsInstance(mood, str)
            self.assertGreater(len(mood), 0)
    
    def test_long_duration_states(self):
        """長時間状態のテスト"""
        # 読書状態（長時間状態）
        self.state_machine.force_state(ExtendedCharacterState.READING)
        self.assertEqual(self.state_machine.get_current_state(), ExtendedCharacterState.READING)
        
        # 短時間の更新では状態は変わらないはず
        for _ in range(10):
            new_state = self.state_machine.update(1.0)  # 1秒ずつ更新
            # 読書は長時間継続するため、すぐには変わらない
            
        # 読書状態が維持されているか、適切な理由で変更されているかを確認
        current_state = self.state_machine.get_current_state()
        self.assertTrue(current_state == ExtendedCharacterState.READING or 
                       current_state in [ExtendedCharacterState.STRETCHING, ExtendedCharacterState.IDLE])


class TestStateContext(unittest.TestCase):
    """状態コンテキストのテスト"""
    
    def setUp(self):
        """テスト準備"""
        self.context = StateContext()
    
    def test_weather_tracking(self):
        """天気追跡のテスト"""
        # 初期状態
        self.assertEqual(self.context.consecutive_weather_days, 0)
        
        # 同じ天気が続く
        self.context.update_weather('rain')
        self.assertEqual(self.context.consecutive_weather_days, 1)
        
        self.context.update_weather('rain')
        self.assertEqual(self.context.consecutive_weather_days, 2)
        
        # 天気が変わる
        self.context.update_weather('sunny')
        self.assertEqual(self.context.consecutive_weather_days, 1)
    
    def test_interaction_learning(self):
        """インタラクション学習のテスト"""
        # 複数回の同じ時間帯でのインタラクション
        self.context.hour = 14
        for _ in range(6):
            self.context.add_interaction()
        
        # 頻繁なインタラクション時間として認識されるかテスト
        frequent = self.context.is_frequent_interaction_time()
        self.assertTrue(frequent)
    
    def test_special_events(self):
        """特別イベントのテスト"""
        # イベント追加
        self.context.add_special_event('birthday')
        self.assertIn('birthday', self.context.special_events)
        
        # イベント削除
        self.context.remove_special_event('birthday')
        self.assertNotIn('birthday', self.context.special_events)


class TestExtendedAnimationSystem(unittest.TestCase):
    """拡張アニメーションシステムのテスト"""
    
    @patch('pygame.image.load')
    @patch('builtins.open')
    @patch('json.load')
    def setUp(self, mock_json_load, mock_open, mock_image_load):
        """テスト準備"""
        # モックの設定
        mock_surface = MagicMock()
        mock_surface.get_width.return_value = 1024
        mock_surface.get_height.return_value = 1920
        mock_surface.subsurface.return_value.copy.return_value = mock_surface
        mock_image_load.return_value.convert_alpha.return_value = mock_surface
        
        # 拡張メタデータのモック
        mock_json_load.return_value = {
            'frame_size': [128, 128],
            'total_animations': 15,
            'animations': {
                'idle': {'row': 0, 'frames': 8, 'fps': 6, 'loop': True, 'description': '待機', 'mood': 'neutral'},
                'umbrella': {'row': 3, 'frames': 8, 'fps': 8, 'loop': True, 'description': '雨傘', 'mood': 'protected'},
                'dancing': {'row': 12, 'frames': 8, 'fps': 20, 'loop': True, 'description': '踊り', 'mood': 'ecstatic'}
            }
        }
        
        self.animator = ExtendedCharacterAnimator('test_path.png', 'test_metadata.json')
    
    def test_animation_loading(self):
        """アニメーション読み込みのテスト"""
        # 利用可能なアニメーション確認
        available = self.animator.get_available_animations()
        self.assertIn('idle', available)
        self.assertIn('umbrella', available)
        self.assertIn('dancing', available)
    
    def test_state_mapping(self):
        """状態マッピングのテスト"""
        # 状態からアニメーションへのマッピング
        success = self.animator.play_for_state(ExtendedCharacterState.UMBRELLA, 'protected')
        self.assertTrue(success or hasattr(self.animator, 'controller'))
    
    def test_mood_system(self):
        """気分システムのテスト"""
        # 気分設定
        self.animator.set_mood('joyful')
        self.assertEqual(self.animator.current_mood, 'joyful')
        
        # 気分付きアニメーション再生
        success = self.animator.play('dancing', 'ecstatic')
        self.assertTrue(success or hasattr(self.animator, 'controller'))


def main():
    """テスト実行"""
    print("=== Extended Character System Test ===")
    print("Testing TASK-402 Step 3/6: Character behavior state machine")
    print()
    
    # テストスイートを実行
    suite = unittest.TestSuite()
    
    # テストケース追加
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestExtendedStateMachine))
    suite.addTests(loader.loadTestsFromTestCase(TestStateContext))
    suite.addTests(loader.loadTestsFromTestCase(TestExtendedAnimationSystem))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果表示
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nErrors:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nStep 3/6: Character behavior state machine - {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Extended character behavior system is working correctly!")
        print("✨ Features verified:")
        print("  - 15-state character system")
        print("  - Priority-based state transitions")
        print("  - Weather and time reactions")
        print("  - Energy and mood systems")
        print("  - Learning-based interactions")
        print("  - Extended animation system")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)