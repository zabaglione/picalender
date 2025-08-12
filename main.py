#!/usr/bin/env python3
"""
PiCalendar - メインエントリーポイント
Raspberry Pi向け常時表示型情報端末
"""

import sys
import os
import signal
import logging
import time
from pathlib import Path
from datetime import datetime
import traceback

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数の設定（pygameの初期化前に設定が必要）
os.environ.setdefault('SDL_VIDEODRIVER', 'kmsdrm')

import pygame
from src.core.config_manager import ConfigManager
from src.core.log_manager import LogManager
from src.display.display_manager import DisplayManager
from src.renderers.clock_renderer import ClockRenderer
from src.renderers.date_renderer import DateRenderer
from src.renderers.calendar_renderer import CalendarRenderer
from src.renderers.background_image_renderer import BackgroundImageRenderer
from src.renderers.weather_panel_renderer import WeatherPanelRenderer
from src.weather.providers.openmeteo import OpenMeteoProvider
from src.weather.cache.weather_cache import WeatherCache
from src.weather.thread.weather_thread import WeatherThread
from src.core.error_recovery import ErrorRecoveryManager
from src.core.performance_optimizer import PerformanceOptimizer


class PiCalendarApp:
    """PiCalendarメインアプリケーション"""
    
    def __init__(self, config_path="settings.yaml"):
        """
        アプリケーションの初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.running = False
        self.clock = pygame.time.Clock()
        
        # 設定読み込み
        self.config_manager = ConfigManager(config_path)
        self.settings = self.config_manager.settings
        
        # ログ設定
        self.log_manager = LogManager(self.settings)
        self.logger = self.log_manager.logger
        
        self.logger.info("="*50)
        self.logger.info("PiCalendar Application Starting")
        self.logger.info(f"Version: 1.0.0")
        self.logger.info(f"Python: {sys.version}")
        self.logger.info(f"Pygame: {pygame.version.ver}")
        self.logger.info("="*50)
        
        # コンポーネント初期化
        self.display_manager = None
        self.renderers = []
        self.weather_thread = None
        self.error_recovery = None
        self.performance_optimizer = None
        
    def initialize(self):
        """アプリケーションの初期化"""
        try:
            self.logger.info("Initializing PiCalendar components...")
            
            # pygame初期化
            pygame.init()
            
            # エラーリカバリマネージャー
            self.error_recovery = ErrorRecoveryManager(self.settings)
            
            # パフォーマンス最適化
            self.performance_optimizer = PerformanceOptimizer(self.settings)
            
            # ディスプレイマネージャー初期化
            self.logger.info("Initializing display...")
            self.display_manager = DisplayManager(self.settings)
            self.screen = self.display_manager.screen
            
            # レンダラー初期化
            self.logger.info("Initializing renderers...")
            self._initialize_renderers()
            
            # 天気システム初期化
            if self.settings.get('weather', {}).get('enabled', True):
                self.logger.info("Initializing weather system...")
                self._initialize_weather_system()
            
            self.logger.info("Initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _initialize_renderers(self):
        """レンダラーの初期化"""
        # 背景レンダラー
        try:
            self.background_renderer = BackgroundImageRenderer(self.settings)
            self.renderers.append(('background', self.background_renderer, 0))
        except Exception as e:
            self.logger.warning(f"Failed to initialize background renderer: {e}")
        
        # 時計レンダラー
        try:
            self.clock_renderer = ClockRenderer(self.settings)
            self.renderers.append(('clock', self.clock_renderer, 10))
        except Exception as e:
            self.logger.error(f"Failed to initialize clock renderer: {e}")
        
        # 日付レンダラー
        try:
            self.date_renderer = DateRenderer(self.settings)
            self.renderers.append(('date', self.date_renderer, 11))
        except Exception as e:
            self.logger.error(f"Failed to initialize date renderer: {e}")
        
        # カレンダーレンダラー
        try:
            self.calendar_renderer = CalendarRenderer(self.settings)
            self.renderers.append(('calendar', self.calendar_renderer, 12))
        except Exception as e:
            self.logger.error(f"Failed to initialize calendar renderer: {e}")
        
        # 天気パネルレンダラー
        if self.settings.get('weather', {}).get('enabled', True):
            try:
                self.weather_panel_renderer = WeatherPanelRenderer(self.settings)
                self.renderers.append(('weather', self.weather_panel_renderer, 13))
            except Exception as e:
                self.logger.warning(f"Failed to initialize weather panel renderer: {e}")
        
        # 優先度順にソート
        self.renderers.sort(key=lambda x: x[2])
    
    def _initialize_weather_system(self):
        """天気システムの初期化"""
        try:
            # 天気プロバイダ
            provider_type = self.settings.get('weather', {}).get('provider', 'openmeteo')
            if provider_type == 'openmeteo':
                self.weather_provider = OpenMeteoProvider(self.settings)
            else:
                self.logger.warning(f"Unknown weather provider: {provider_type}")
                return
            
            # 天気キャッシュ
            self.weather_cache = WeatherCache(self.settings)
            
            # 天気取得スレッド
            self.weather_thread = WeatherThread(
                self.weather_provider,
                self.weather_cache,
                self.settings
            )
            self.weather_thread.start()
            
            self.logger.info("Weather system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize weather system: {e}")
    
    def run(self):
        """メインループ"""
        self.running = True
        self.logger.info("Starting main loop...")
        
        fps = self.settings.get('screen', {}).get('fps', 30)
        frame_count = 0
        last_performance_check = time.time()
        
        try:
            while self.running:
                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_F11:
                            self.display_manager.toggle_fullscreen()
                
                # 画面クリア
                self.screen.fill((0, 0, 0))
                
                # レンダラー実行
                for name, renderer, priority in self.renderers:
                    try:
                        renderer.render(self.screen)
                    except Exception as e:
                        self.logger.error(f"Renderer {name} failed: {e}")
                        if self.error_recovery:
                            self.error_recovery.handle_error(e)
                
                # 天気データ更新（利用可能な場合）
                if hasattr(self, 'weather_thread') and self.weather_thread:
                    weather_data = self.weather_thread.get_latest_data()
                    if weather_data and hasattr(self, 'weather_panel_renderer'):
                        self.weather_panel_renderer.set_weather_data(weather_data)
                
                # 画面更新
                pygame.display.flip()
                
                # FPS制御
                self.clock.tick(fps)
                frame_count += 1
                
                # パフォーマンスチェック（10秒ごと）
                current_time = time.time()
                if current_time - last_performance_check > 10:
                    actual_fps = frame_count / (current_time - last_performance_check)
                    self.logger.debug(f"FPS: {actual_fps:.1f}")
                    
                    if self.performance_optimizer:
                        self.performance_optimizer.auto_adjust_quality(actual_fps)
                    
                    frame_count = 0
                    last_performance_check = current_time
        
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.cleanup()
    
    def cleanup(self):
        """クリーンアップ処理"""
        self.logger.info("Cleaning up...")
        
        # 天気スレッド停止
        if self.weather_thread:
            self.logger.info("Stopping weather thread...")
            self.weather_thread.stop(timeout=5)
        
        # pygame終了
        pygame.quit()
        
        self.logger.info("Cleanup complete")
        self.logger.info("PiCalendar stopped")
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """メイン関数"""
    # アプリケーション作成
    app = PiCalendarApp()
    
    # シグナルハンドラー設定
    signal.signal(signal.SIGTERM, app.signal_handler)
    signal.signal(signal.SIGINT, app.signal_handler)
    
    # 初期化
    if not app.initialize():
        app.logger.error("Failed to initialize application")
        return 1
    
    # メインループ実行
    try:
        app.run()
    except Exception as e:
        app.logger.error(f"Application crashed: {e}")
        app.logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())