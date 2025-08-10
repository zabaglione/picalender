#!/usr/bin/env python3
"""
TASK-101: pygame/SDL2初期化のテスト

TASK-101要件：
- pygame初期化成功確認
- 1024x600解像度確認  
- フルスクリーン動作確認
- SDL初期化失敗時の処理
- ディスプレイ未接続時の処理
- 黒画面でフルスクリーン表示
- マウスカーソル非表示確認
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config_manager import ConfigManager
from src.display.display_manager import DisplayManager


class TestTask101DisplayManager(unittest.TestCase):
    """TASK-101: pygame/SDL2初期化のテスト"""
    
    def setUp(self):
        """テスト前準備"""
        # モック設定管理を作成
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.get.side_effect = lambda key, default=None: {
            'screen': {'width': 1024, 'height': 600, 'fps': 30},
            'ui': {'fullscreen': True, 'hide_cursor': True},
            'logging': {'level': 'INFO', 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}
        }.get(key, default)
        
        # DisplayManagerインスタンス作成
        with patch('src.core.log_manager.LogManager.__init__', return_value=None), \
             patch('src.core.log_manager.LogManager.get_logger', return_value=Mock()):
            self.display_manager = DisplayManager(self.mock_config)
    
    @patch('src.display.environment_detector.EnvironmentDetector.is_raspberry_pi')
    @patch('src.display.environment_detector.EnvironmentDetector.has_display')
    @patch('src.display.environment_detector.EnvironmentDetector.get_video_driver')
    @patch('pygame.init')
    @patch('pygame.get_init')
    def test_pygame_initialization_success(self, mock_get_init, mock_init, 
                                         mock_video_driver, mock_has_display, mock_is_rpi):
        """単体テスト: pygame初期化成功確認"""
        # モック設定
        mock_is_rpi.return_value = True
        mock_has_display.return_value = True
        mock_video_driver.return_value = 'kmsdrm'
        mock_init.return_value = None
        mock_get_init.return_value = True
        
        # 初期化実行
        result = self.display_manager.initialize()
        
        # 検証
        self.assertTrue(result)
        mock_init.assert_called_once()
        self.assertEqual(os.environ.get('SDL_VIDEODRIVER'), 'kmsdrm')
    
    @patch('src.display.environment_detector.EnvironmentDetector.is_raspberry_pi')
    @patch('src.display.environment_detector.EnvironmentDetector.has_display')
    @patch('pygame.init')
    @patch('pygame.get_init')
    def test_pygame_initialization_failure_fallback(self, mock_get_init, mock_init,
                                                   mock_has_display, mock_is_rpi):
        """エラーテスト: SDL初期化失敗時のダミーモード処理"""
        # モック設定：最初の初期化は失敗、フォールバックは成功
        mock_is_rpi.return_value = True
        mock_has_display.return_value = True
        mock_init.side_effect = [Exception("SDL init failed"), None]
        mock_get_init.return_value = True
        
        # 初期化実行
        result = self.display_manager.initialize()
        
        # 検証：フォールバックが成功
        self.assertTrue(result)
        self.assertTrue(self.display_manager.dummy_mode)
        self.assertEqual(os.environ.get('SDL_VIDEODRIVER'), 'dummy')
    
    @patch('src.display.environment_detector.EnvironmentDetector.has_display')
    def test_headless_mode_detection(self, mock_has_display):
        """エラーテスト: ディスプレイ未接続時の処理"""
        # ディスプレイなし
        mock_has_display.return_value = False
        
        with patch('pygame.init'), patch('pygame.get_init', return_value=True):
            result = self.display_manager.initialize()
            
            # ヘッドレスモードとして初期化される
            self.assertTrue(result)
            self.assertTrue(self.display_manager.headless)
            self.assertEqual(os.environ.get('SDL_VIDEODRIVER'), 'dummy')
    
    @patch('pygame.display.set_mode')
    @patch('pygame.get_init')
    def test_target_resolution_1024x600(self, mock_get_init, mock_set_mode):
        """統合テスト: 1024x600解像度確認"""
        mock_get_init.return_value = True
        mock_surface = Mock()
        mock_set_mode.return_value = mock_surface
        
        # 画面作成
        screen = self.display_manager.create_screen()
        
        # 1024x600で最初に呼び出されることを確認
        mock_set_mode.assert_called()
        first_call_args = mock_set_mode.call_args_list[0]
        self.assertEqual(first_call_args[0][0], (1024, 600))
        # 最終的な解像度確認（フォールバック後でも元の解像度設定は保持）
        self.assertIn(self.display_manager.resolution, [(1024, 600), (640, 480)])
    
    @patch('src.display.environment_detector.EnvironmentDetector.is_raspberry_pi')
    @patch('pygame.display.set_mode')
    @patch('pygame.get_init')
    def test_fullscreen_mode_raspberry_pi(self, mock_get_init, mock_set_mode, mock_is_rpi):
        """統合テスト: フルスクリーン動作確認（Raspberry Pi）"""
        mock_get_init.return_value = True
        mock_is_rpi.return_value = True
        mock_surface = Mock()
        mock_set_mode.return_value = mock_surface
        
        # フルスクリーンで画面作成
        self.display_manager.fullscreen = True
        screen = self.display_manager.create_screen()
        
        # フルスクリーンフラグが設定されることを確認
        mock_set_mode.assert_called()
        call_args = mock_set_mode.call_args
        if len(call_args[0]) > 1:
            flags = call_args[0][1]
            self.assertNotEqual(flags & 1, 0)  # pygame.FULLSCREEN = 1
    
    @patch('pygame.mouse.set_visible')
    @patch('pygame.display.set_mode')
    @patch('pygame.get_init')
    def test_mouse_cursor_hidden(self, mock_get_init, mock_set_mode, mock_set_visible):
        """完了条件: マウスカーソル非表示確認"""
        mock_get_init.return_value = True
        mock_set_mode.return_value = Mock()
        
        # カーソル非表示設定で画面作成
        self.display_manager.hide_cursor_on_init = True
        self.display_manager.create_screen()
        
        # マウスカーソルが非表示に設定されることを確認
        mock_set_visible.assert_called_with(False)
    
    def test_fps_control(self):
        """完了条件: FPS制御機能確認"""
        with patch('pygame.time.Clock') as mock_clock_class:
            mock_clock = Mock()
            mock_clock_class.return_value = mock_clock
            
            # Clock取得
            clock = self.display_manager.get_clock()
            
            # FPS制御が有効か確認
            self.assertIsNotNone(clock)
            mock_clock_class.assert_called_once()
    
    def test_fps_tick_functionality(self):
        """FPS制御とフレーム時間取得テスト"""
        mock_clock = Mock()
        mock_clock.tick.return_value = 33  # 33ms = ~30fps
        self.display_manager.clock = mock_clock
        
        # tick実行
        dt = self.display_manager.tick()
        
        # 30fps設定で呼ばれ、秒単位で返される
        mock_clock.tick.assert_called_with(30)
        self.assertAlmostEqual(dt, 0.033, places=3)
    
    def test_requirements_validation(self):
        """TASK-101要件検証テスト"""
        # 初期化済み状態をモック
        self.display_manager.screen = Mock()
        self.display_manager.clock = Mock()
        self.display_manager.resolution = (1024, 600)
        
        with patch('pygame.get_init', return_value=True), \
             patch('pygame.mouse.get_visible', return_value=False):
            
            os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
            
            requirements = self.display_manager.validate_display_requirements()
            
            # 主要要件の確認
            self.assertTrue(requirements['pygame_initialized'])
            self.assertTrue(requirements['screen_created'])
            self.assertTrue(requirements['target_resolution'])
            self.assertTrue(requirements['cursor_hidden'])
            self.assertTrue(requirements['fps_control'])
            self.assertTrue(requirements['kmsdrm_driver'])
    
    def test_initialization_report_generation(self):
        """初期化レポート生成テスト"""
        # 初期化済み状態をモック
        self.display_manager.screen = Mock()
        self.display_manager.clock = Mock()
        self.display_manager.clock.get_fps.return_value = 30.0
        
        with patch('pygame.get_init', return_value=True), \
             patch('pygame.mouse.get_visible', return_value=False):
            
            report = self.display_manager.get_initialization_report()
            
            # レポートの内容確認
            self.assertIn("TASK-101 Display Initialization Report", report)
            self.assertIn("1024x600", report)
            self.assertIn("FPS Target: 30.0", report)
            self.assertIn("✅", report)  # 成功要件があることを確認
    
    @patch('pygame.display.set_mode')
    @patch('pygame.display.list_modes')
    @patch('pygame.get_init')
    def test_screen_creation_fallback_resolution(self, mock_get_init, mock_list_modes, mock_set_mode):
        """画面作成失敗時のフォールバック処理テスト"""
        mock_get_init.return_value = True
        mock_list_modes.return_value = [(800, 600)]
        mock_fallback_screen = Mock()
        
        # 最初の解像度は失敗、フォールバックでスクリーンを直接返す
        mock_set_mode.side_effect = pygame.error("Resolution not supported")
        
        with patch.object(self.display_manager, '_create_fallback_screen', return_value=mock_fallback_screen) as mock_fallback:
            screen = self.display_manager.create_screen()
            
            # フォールバック処理が呼ばれる
            mock_fallback.assert_called_once()
            self.assertEqual(screen, mock_fallback_screen)
    
    def test_fps_stats_collection(self):
        """FPS統計情報収集テスト"""
        mock_clock = Mock()
        mock_clock.get_fps.return_value = 29.5
        self.display_manager.clock = mock_clock
        self.display_manager.fps = 30
        
        stats = self.display_manager.get_fps_stats()
        
        # 統計情報の確認
        self.assertEqual(stats['current_fps'], 29.5)
        self.assertEqual(stats['target_fps'], 30.0)
        self.assertAlmostEqual(stats['frame_time_ms'], 33.89, places=1)


class TestTask101IntegrationTests(unittest.TestCase):
    """TASK-101統合テスト"""
    
    def setUp(self):
        """テスト前準備"""
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.get.side_effect = lambda key, default=None: {
            'screen': {'width': 1024, 'height': 600, 'fps': 30},
            'ui': {'fullscreen': True, 'hide_cursor': True},
            'logging': {'level': 'INFO', 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}
        }.get(key, default)
    
    @patch('src.display.environment_detector.EnvironmentDetector.is_raspberry_pi')
    @patch('src.display.environment_detector.EnvironmentDetector.has_display')
    @patch('pygame.init')
    @patch('pygame.get_init')
    @patch('pygame.display.set_mode')
    @patch('pygame.mouse.set_visible')
    @patch('pygame.mouse.get_visible')
    def test_complete_initialization_sequence(self, mock_get_visible, mock_set_visible, mock_set_mode, 
                                            mock_get_init, mock_init,
                                            mock_has_display, mock_is_rpi):
        """完全な初期化シーケンスのテスト"""
        # Raspberry Pi環境を模擬
        mock_is_rpi.return_value = True
        mock_has_display.return_value = True
        mock_init.return_value = None
        mock_get_init.return_value = True
        mock_set_mode.return_value = Mock()
        mock_get_visible.return_value = False
        
        # DisplayManager作成・初期化
        with patch('src.core.log_manager.LogManager.__init__', return_value=None), \
             patch('src.core.log_manager.LogManager.get_logger', return_value=Mock()):
            display_manager = DisplayManager(self.mock_config)
        
        # 初期化実行
        init_result = display_manager.initialize()
        self.assertTrue(init_result)
        
        # 画面作成
        screen = display_manager.create_screen()
        self.assertIsNotNone(screen)
        
        # 要件検証
        requirements = display_manager.validate_display_requirements()
        
        # 主要要件が満たされることを確認
        critical_requirements = [
            'pygame_initialized', 'screen_created', 'target_resolution', 
            'cursor_hidden', 'fps_control'
        ]
        
        for req in critical_requirements:
            self.assertTrue(requirements.get(req, False), 
                          f"Critical requirement '{req}' not met")


def main():
    """テスト実行"""
    print("=== TASK-101: pygame/SDL2初期化テスト ===")
    print("Testing display manager initialization and requirements")
    print()
    
    # テストスイート実行
    suite = unittest.TestSuite()
    
    # テストケース追加
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestTask101DisplayManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTask101IntegrationTests))
    
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
    print(f"\nTASK-101: pygame/SDL2初期化 - {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎮 pygame/SDL2初期化システムが正常に動作しています！")
        print("✨ 検証済み機能:")
        print("  - pygame初期化とKMSDRM設定")
        print("  - 1024×600解像度対応")
        print("  - フルスクリーン・マウスカーソル制御")
        print("  - FPS制御システム")
        print("  - エラーハンドリングとフォールバック")
        print("  - 要件検証とレポート生成")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)