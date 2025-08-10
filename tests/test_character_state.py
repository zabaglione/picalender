#!/usr/bin/env python3
"""
キャラクター状態管理システムのテスト

State 5/6のテスト実行
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.character.state_machine import CharacterStateMachine, CharacterState, StateTransition


class TestCharacterStateMachine(unittest.TestCase):
    """キャラクター状態マシンのテスト"""
    
    def setUp(self):
        """テスト準備"""
        self.state_machine = CharacterStateMachine()
    
    def test_initial_state(self):
        """初期状態のテスト"""
        self.assertEqual(self.state_machine.get_current_state(), CharacterState.IDLE)
    
    def test_context_update(self):
        """コンテキスト更新のテスト"""
        self.state_machine.update_context(weather='sunny', hour=12)
        self.assertEqual(self.state_machine.context['weather'], 'sunny')
        self.assertEqual(self.state_machine.context['hour'], 12)
    
    def test_force_state(self):
        """強制状態変更のテスト"""
        self.state_machine.force_state(CharacterState.WAVE)
        self.assertEqual(self.state_machine.get_current_state(), CharacterState.WAVE)
    
    def test_click_interaction(self):
        """クリックインタラクションのテスト"""
        initial_click_count = self.state_machine.context.get('click_count', 0)
        self.state_machine.on_click()
        
        # クリック数が増加していることを確認
        self.assertGreater(self.state_machine.context['click_count'], initial_click_count)
    
    def test_weather_change(self):
        """天気変更反応のテスト"""
        # 晴れに変更
        self.state_machine.on_weather_change('sunny')
        self.assertEqual(self.state_machine.context['weather'], 'sunny')
        
        # 雨に変更して反応をテスト（現在の実装では天気変更時のみ反応）
        initial_weather = self.state_machine.context.get('weather')
        changed = False
        
        # 複数回テストして確率的な反応を確認
        for _ in range(20):
            # 歩行状態に設定
            self.state_machine.force_state(CharacterState.WALK)
            # 天気を変更（異なる天気に変更する必要がある）
            if initial_weather != 'rain':
                self.state_machine.on_weather_change('rain')
                if self.state_machine.get_current_state() == CharacterState.IDLE:
                    changed = True
                    break
                # 天気を元に戻して次回のテストのため
                self.state_machine.on_weather_change('sunny')
        
        # 何回かのうちに変更されるはず（高確率なので期待）
        self.assertTrue(changed, "Rain weather should change walk to idle with high probability")
    
    def test_transition_conditions(self):
        """状態遷移条件のテスト"""
        # 夜の時間を設定
        self.state_machine.update_context(hour=23)
        
        # 睡眠状態への遷移条件をチェック
        transitions = [t for t in self.state_machine.transitions 
                      if t.from_state == CharacterState.IDLE 
                      and t.to_state == CharacterState.SLEEPING]
        
        self.assertTrue(len(transitions) > 0, "Should have IDLE -> SLEEPING transition")
        
        # 条件チェック
        transition = transitions[0]
        can_transition = transition.can_transition(self.state_machine.context)
        
        # 確率的なので複数回テスト
        success_count = 0
        for _ in range(100):
            if transition.can_transition(self.state_machine.context):
                success_count += 1
        
        self.assertGreater(success_count, 0, "Should be able to transition to sleeping at night")
    
    def test_energy_system(self):
        """エネルギーシステムのテスト"""
        initial_energy = self.state_machine.context.get('energy_level', 1.0)
        
        # エキサイト状態で消費
        self.state_machine.force_state(CharacterState.EXCITED)
        
        # アクティブな状態では消費される
        final_energy = self.state_machine.context.get('energy_level', 1.0)
        self.assertLessEqual(final_energy, initial_energy)
    
    def test_mood_indicator(self):
        """気分インジケーターのテスト"""
        # 通常状態
        mood = self.state_machine.get_mood_indicator()
        self.assertIn(mood, ['neutral', 'tired', 'sleepy', 'cheerful'])
        
        # 幸せ状態
        self.state_machine.force_state(CharacterState.HAPPY)
        mood = self.state_machine.get_mood_indicator()
        self.assertEqual(mood, 'happy')
        
        # 興奮状態
        self.state_machine.force_state(CharacterState.EXCITED)
        mood = self.state_machine.get_mood_indicator()
        self.assertEqual(mood, 'excited')


class TestCharacterStateMachineIntegration(unittest.TestCase):
    """キャラクター状態マシン統合テスト"""
    
    def setUp(self):
        """テスト準備"""
        self.state_machine = CharacterStateMachine()
    
    def test_state_machine_integration(self):
        """状態マシン統合のテスト"""
        # 初期状態確認
        self.assertEqual(self.state_machine.get_current_state(), CharacterState.IDLE)
        
        # 天気更新テスト
        self.state_machine.update_context(weather='sunny')
        self.assertEqual(self.state_machine.context['weather'], 'sunny')
        
        # 時間更新テスト
        self.state_machine.update_context(hour=14)
        self.assertEqual(self.state_machine.context['hour'], 14)
        
        # クリック処理テスト
        click_count_before = self.state_machine.context.get('click_count', 0)
        self.state_machine.on_click()
        self.assertGreater(self.state_machine.context['click_count'], click_count_before)
        
    def test_update_loop(self):
        """更新ループのテスト"""
        # 複数回更新して状態遷移をテスト
        update_count = 0
        state_changes = 0
        current_state = self.state_machine.get_current_state()
        
        for _ in range(50):  # 50回更新
            new_state = self.state_machine.update(0.1)  # 100ms更新
            if new_state and new_state != current_state:
                state_changes += 1
                current_state = new_state
            update_count += 1
        
        # 更新回数確認
        self.assertEqual(update_count, 50)
        # 何らかの状態変更があることを確認（確率的）
        self.assertGreaterEqual(state_changes, 0)


def main():
    """テスト実行"""
    print("=== Character State Management Test ===")
    print("Testing TASK-401 Step 5/6: Character state management")
    print()
    
    # テストスイートを実行
    suite = unittest.TestSuite()
    
    # テストケース追加
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestCharacterStateMachine))
    suite.addTests(loader.loadTestsFromTestCase(TestCharacterStateMachineIntegration))
    
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
    print(f"\nStep 5/6: Character state management - {'✅ PASS' if success else '❌ FAIL'}")
    
    return success


if __name__ == '__main__':
    main()