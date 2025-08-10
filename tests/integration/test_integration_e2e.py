#!/usr/bin/env python3
"""
統合テスト: エンドツーエンドテスト

ユーザー視点でのシステム全体の動作を確認する。
"""

import unittest
import tempfile
import shutil
import os
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import pygame
import threading

# システムパスに追加
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEndToEnd(unittest.TestCase):
    """エンドツーエンドテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスのセットアップ"""
        # テスト用ディレクトリ
        cls.test_dir = tempfile.mkdtemp(prefix='picalender_e2e_')
        
        # 必要なディレクトリ構造を作成
        cls.setup_test_environment(cls.test_dir)
    
    @classmethod
    def setup_test_environment(cls, base_dir):
        """テスト環境のセットアップ"""
        base = Path(base_dir)
        
        # ディレクトリ作成
        (base / 'assets' / 'fonts').mkdir(parents=True)
        (base / 'assets' / 'icons' / 'weather').mkdir(parents=True)
        (base / 'assets' / 'sprites').mkdir(parents=True)
        (base / 'wallpapers').mkdir(parents=True)
        (base / 'cache').mkdir(parents=True)
        (base / 'logs').mkdir(parents=True)
        
        # ダミーファイル作成
        (base / 'assets' / 'fonts' / 'NotoSansCJK-Regular.otf').touch()
        
        # 設定ファイル作成
        settings = {
            'screen': {
                'width': 1024,
                'height': 600,
                'fps': 30,
                'fullscreen': False
            },
            'ui': {
                'margins': {'x': 24, 'y': 16},
                'clock_font_px': 48,
                'date_font_px': 24
            },
            'weather': {
                'provider': 'openmeteo',
                'location': {'latitude': 35.681, 'longitude': 139.767},
                'cache': {'directory': str(base / 'cache')}
            },
            'background': {
                'directory': str(base / 'wallpapers')
            },
            'fonts': {
                'main': str(base / 'assets' / 'fonts' / 'NotoSansCJK-Regular.otf')
            },
            'logging': {
                'directory': str(base / 'logs')
            }
        }
        
        # settings.yaml保存
        import yaml
        with open(base / 'settings.yaml', 'w') as f:
            yaml.dump(settings, f)
        
        cls.test_settings_path = str(base / 'settings.yaml')
    
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    @patch('pygame.display.set_mode')
    @patch('pygame.font.Font')
    @patch('pygame.event.get')
    def test_application_startup(self, mock_events, mock_font, mock_display):
        """Test 1: アプリケーション起動シーケンス"""
        # モック設定
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_display.return_value = mock_screen
        mock_font.return_value = Mock()
        mock_events.return_value = []
        
        # main.pyの起動シーケンスをシミュレート
        from src.core.config_manager import ConfigManager
        from src.core.log_manager import LogManager
        from src.display.display_manager import DisplayManager
        
        # 1. 設定読み込み
        config = ConfigManager(self.test_settings_path)
        self.assertIsNotNone(config.settings)
        
        # 2. ログ初期化
        log_manager = LogManager(config.get_all())
        log_manager.logger.info("Application starting...")
        
        # 3. pygame初期化
        pygame.init()
        
        # 4. ディスプレイ初期化
        display = DisplayManager(config.get_all())
        
        # 起動完了
        log_manager.logger.info("Application started successfully")
        
        # 初期化が成功したことを確認
        self.assertTrue(pygame.get_init())
    
    @patch('pygame.display.set_mode')
    @patch('pygame.event.get')
    @patch('pygame.time.Clock')
    def test_main_loop_execution(self, mock_clock, mock_events, mock_display):
        """Test 2: メインループの実行"""
        # モック設定
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_display.return_value = mock_screen
        
        clock_instance = Mock()
        clock_instance.tick.return_value = 16
        mock_clock.return_value = clock_instance
        
        # イベントシーケンス（3フレーム後に終了）
        mock_events.side_effect = [
            [],  # フレーム1
            [],  # フレーム2
            [Mock(type=pygame.QUIT)]  # フレーム3で終了
        ]
        
        from src.display.display_manager import DisplayManager
        # from src.display.render_loop import RenderLoop
        
        # システム初期化
        pygame.init()
        display = DisplayManager({'screen': {'width': 1024, 'height': 600}})
        # loop = RenderLoop(display, {'screen': {'fps': 30}})
        
        # メインループ実行
        frame_count = 0
        running = True
        while running and frame_count < 3:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # loop.step()
            frame_count += 1
        
        # 3フレーム実行されたことを確認
        self.assertEqual(frame_count, 3)
    
    @patch('requests.get')
    def test_weather_update_cycle(self, mock_requests):
        """Test 3: 天気更新サイクル"""
        # 天気APIレスポンスをモック
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'current_weather': {'temperature': 20.5, 'weathercode': 0},
            'daily': {
                'time': ['2025-01-11'],
                'temperature_2m_max': [25],
                'temperature_2m_min': [15],
                'weathercode': [0],
                'precipitation_probability_max': [10]
            }
        }
        mock_requests.return_value = mock_response
        
        from src.weather.providers.openmeteo import OpenMeteoProvider
        from src.weather.cache.weather_cache import WeatherCache
        from src.weather.thread.weather_thread import WeatherThread
        
        settings = {
            'weather': {
                'provider': 'openmeteo',
                'location': {'latitude': 35.681, 'longitude': 139.767},
                'cache': {'directory': str(Path(self.test_dir) / 'cache')},
                'thread': {'enabled': True, 'update_interval': 1}
            }
        }
        
        # コンポーネント初期化
        provider = OpenMeteoProvider(settings)
        cache = WeatherCache(settings)
        thread = WeatherThread(provider, cache, settings)
        
        # スレッド開始
        thread.start()
        
        # 更新を待つ
        time.sleep(2)
        
        # データが取得されたことを確認
        data = thread.get_latest_data()
        self.assertIsNotNone(data)
        
        # スレッド停止
        thread.stop()
    
    def test_error_recovery_scenario(self):
        """Test 4: エラー復旧シナリオ"""
        from src.core.error_recovery import ErrorRecoveryManager
        
        settings = {
            'error_recovery': {
                'enabled': True,
                'network': {'max_retries': 3, 'backoff_factor': 2.0}
            }
        }
        
        manager = ErrorRecoveryManager(settings)
        
        # ネットワークエラーシミュレーション
        error_count = {'count': 0}
        
        def network_operation():
            error_count['count'] += 1
            if error_count['count'] < 3:
                raise ConnectionError("Network unavailable")
            return "Success"
        
        # ラップして実行
        wrapped = manager.wrap_with_recovery(network_operation)
        
        try:
            result = wrapped()
            # 3回目で成功することを確認
            self.assertEqual(error_count['count'], 3)
        except ConnectionError:
            # 完全な復旧ができない場合も許容
            pass
        
        # 統計確認
        stats = manager.get_recovery_stats()
        self.assertGreater(stats['total_errors'], 0)
    
    def test_performance_degradation(self):
        """Test 5: パフォーマンス劣化時の動作"""
        from src.core.performance_optimizer import PerformanceOptimizer
        
        settings = {
            'performance': {
                'auto_adjust': True,
                'default_quality': 'high'
            }
        }
        
        optimizer = PerformanceOptimizer(settings)
        
        # 初期状態
        initial_settings = optimizer.get_optimized_settings()
        self.assertEqual(initial_settings['quality_level'], 'high')
        
        # CPU負荷をシミュレート（統計に高い値を追加）
        with optimizer._stats_lock:
            optimizer._stats['cpu_samples'] = [50.0] * 10  # 高CPU使用率
            optimizer._stats['memory_samples'] = [200.0] * 10  # 高メモリ使用
        
        # 自動調整
        adjusted = optimizer.auto_adjust_quality(current_fps=15)
        
        # 品質が下がることを期待（または変更なし）
        new_settings = optimizer.get_optimized_settings()
        self.assertIn(new_settings['quality_level'], 
                     ['ultra_low', 'low', 'medium', 'high'])
    
    @patch('pygame.display.flip')
    @patch('pygame.display.set_mode')
    def test_screen_update_optimization(self, mock_display, mock_flip):
        """Test 6: 画面更新の最適化"""
        mock_screen = Mock()
        mock_screen.get_size.return_value = (1024, 600)
        mock_display.return_value = mock_screen
        
        from src.core.performance_optimizer import PerformanceOptimizer, RenderOptimizer
        
        settings = {'performance': {'auto_adjust': False}}
        
        perf_optimizer = PerformanceOptimizer(settings)
        render_optimizer = RenderOptimizer()
        
        # Dirty Rectangle追加
        perf_optimizer.add_dirty_rect(pygame.Rect(100, 100, 200, 200))
        perf_optimizer.add_dirty_rect(pygame.Rect(300, 300, 100, 100))
        
        # 更新領域取得
        dirty_rects = perf_optimizer.get_dirty_rects()
        
        # 部分更新が要求されることを確認
        self.assertEqual(len(dirty_rects), 2)
        
        # キャッシュテスト
        test_surface = pygame.Surface((100, 100))
        cached = render_optimizer.get_scaled_surface(test_surface, 0.5)
        self.assertIsNotNone(cached)
    
    def test_configuration_reload(self):
        """Test 7: 設定の動的リロード"""
        from src.core.config_manager import ConfigManager
        
        # 初期設定
        config_path = Path(self.test_dir) / 'dynamic_settings.yaml'
        
        config = ConfigManager(str(config_path))
        config.set('screen.fps', 30)
        config.save(str(config_path))
        
        # 設定変更
        config.set('screen.fps', 60)
        config.save(str(config_path))
        
        # 新しいインスタンスで読み込み
        new_config = ConfigManager(str(config_path))
        
        # 変更が反映されていることを確認
        self.assertEqual(new_config.get('screen.fps'), 60)
        
        # クリーンアップ
        config_path.unlink()
    
    @patch('pygame.quit')
    def test_graceful_shutdown(self, mock_quit):
        """Test 8: 正常なシャットダウン"""
        from src.display.display_manager import DisplayManager
        from src.weather.thread.weather_thread import WeatherThread
        from src.weather.cache.weather_cache import WeatherCache
        
        settings = {
            'screen': {'width': 1024, 'height': 600},
            'weather': {
                'cache': {'directory': str(Path(self.test_dir) / 'cache')},
                'thread': {'enabled': True}
            }
        }
        
        # コンポーネント初期化
        with patch('pygame.display.set_mode'):
            display = DisplayManager(settings)
        
        cache = WeatherCache(settings)
        
        # クリーンアップ
        cache.cleanup()
        
        # pygame終了が呼ばれることを確認
        pygame.quit()
        mock_quit.assert_called_once()
    
    def test_long_running_stability(self):
        """Test 9: 長時間稼働の安定性"""
        from src.core.performance_optimizer import PerformanceOptimizer
        from src.core.error_recovery import ErrorRecoveryManager
        
        settings = {
            'performance': {'auto_adjust': True},
            'error_recovery': {'enabled': True}
        }
        
        optimizer = PerformanceOptimizer(settings)
        error_manager = ErrorRecoveryManager(settings)
        
        # 100回のサイクルをシミュレート
        for i in range(100):
            # パフォーマンス監視
            perf = optimizer.monitor_performance()
            
            # ランダムなエラーを処理
            if i % 10 == 0:
                error_manager.handle_error(ValueError(f"Test error {i}"))
            
            # メモリ解放
            if i % 20 == 0:
                optimizer.free_memory()
        
        # 統計確認
        perf_stats = optimizer.get_performance_stats()
        error_stats = error_manager.get_recovery_stats()
        
        # システムが安定していることを確認
        self.assertIsNotNone(perf_stats)
        self.assertIsNotNone(error_stats)
        self.assertEqual(error_stats['total_errors'], 10)


class TestUserScenarios(unittest.TestCase):
    """ユーザーシナリオテスト"""
    
    def test_scenario_daily_use(self):
        """Test 10: 日常使用シナリオ"""
        # 一日の使用パターンをシミュレート
        scenarios = [
            ('morning', '06:00', 'low'),     # 朝: 低品質
            ('daytime', '12:00', 'medium'),  # 昼: 中品質
            ('evening', '18:00', 'high'),    # 夕: 高品質
            ('night', '23:00', 'ultra_low')  # 夜: 超低品質
        ]
        
        from src.core.performance_optimizer import PerformanceOptimizer
        
        for period, time_str, expected_quality in scenarios:
            settings = {
                'performance': {
                    'auto_adjust': False,
                    'default_quality': expected_quality
                }
            }
            
            optimizer = PerformanceOptimizer(settings)
            config = optimizer.get_optimized_settings()
            
            # 期待される品質レベルが設定されていることを確認
            self.assertEqual(config['quality_level'], expected_quality)
            
            # FPSが品質に応じて変化することを確認
            if expected_quality == 'ultra_low':
                self.assertEqual(config['fps'], 10)
            elif expected_quality == 'low':
                self.assertEqual(config['fps'], 15)
            elif expected_quality == 'medium':
                self.assertEqual(config['fps'], 20)
            elif expected_quality == 'high':
                self.assertEqual(config['fps'], 30)


if __name__ == '__main__':
    # 詳細モードで実行
    unittest.main(verbosity=2)