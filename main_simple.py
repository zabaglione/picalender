#!/usr/bin/env python3
"""
PiCalendar - シンプル版メインエントリーポイント
依存関係を最小限にした実装
"""

import sys
import os
import signal
import logging
import time
from pathlib import Path
import traceback

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数の設定
if 'arm' in os.uname().machine or 'aarch64' in os.uname().machine:
    os.environ.setdefault('SDL_VIDEODRIVER', 'kmsdrm')

import pygame

# シンプルなレンダラーをインポート
from src.renderers.simple_clock_renderer import SimpleClockRenderer
from src.renderers.simple_date_renderer import SimpleDateRenderer
from src.renderers.simple_calendar_renderer import SimpleCalendarRenderer


class SimplePiCalendarApp:
    """シンプルなPiCalendarアプリケーション"""
    
    def __init__(self):
        """アプリケーションの初期化"""
        self.running = False
        self.clock = pygame.time.Clock()
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("="*50)
        self.logger.info("SimplePiCalendar Application Starting")
        self.logger.info(f"Python: {sys.version}")
        self.logger.info(f"Pygame: {pygame.version.ver}")
        self.logger.info("="*50)
        
        # 基本設定
        self.settings = {
            'screen': {
                'width': 1024,
                'height': 600,
                'fps': 30,
                'fullscreen': True
            },
            'ui': {
                'clock_font_px': 130,
                'date_font_px': 36,
                'calendar_font_px': 22
            }
        }
        
        # フルスクリーン設定（環境変数で制御可能）
        if os.environ.get('PICALENDER_WINDOWED', '').lower() == 'true':
            self.settings['screen']['fullscreen'] = False
        
        self.screen = None
        self.renderers = []
    
    def initialize(self):
        """アプリケーションの初期化"""
        try:
            self.logger.info("Initializing SimplePiCalendar...")
            
            # pygame初期化
            pygame.init()
            
            # ディスプレイ初期化
            self.logger.info("Initializing display...")
            width = self.settings['screen']['width']
            height = self.settings['screen']['height']
            
            if self.settings['screen']['fullscreen']:
                self.logger.info(f"Setting fullscreen mode: {width}x{height}")
                self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
            else:
                self.logger.info(f"Setting windowed mode: {width}x{height}")
                self.screen = pygame.display.set_mode((width, height))
            
            pygame.display.set_caption("PiCalendar")
            pygame.mouse.set_visible(False)  # マウスカーソルを非表示
            
            # レンダラー初期化
            self.logger.info("Initializing renderers...")
            
            # 時計レンダラー
            try:
                clock_renderer = SimpleClockRenderer(self.settings)
                self.renderers.append(('clock', clock_renderer))
                self.logger.info("Clock renderer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize clock renderer: {e}")
            
            # 日付レンダラー
            try:
                date_renderer = SimpleDateRenderer(self.settings)
                self.renderers.append(('date', date_renderer))
                self.logger.info("Date renderer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize date renderer: {e}")
            
            # カレンダーレンダラー
            try:
                calendar_renderer = SimpleCalendarRenderer(self.settings)
                self.renderers.append(('calendar', calendar_renderer))
                self.logger.info("Calendar renderer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize calendar renderer: {e}")
            
            self.logger.info("Initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def draw_gradient_background(self, screen):
        """グラデーション背景を描画"""
        height = self.settings['screen']['height']
        width = self.settings['screen']['width']
        
        for y in range(height):
            ratio = y / height
            color = (
                int(20 + (50 - 20) * ratio),
                int(30 + (80 - 30) * ratio),
                int(60 + (120 - 60) * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (width, y))
    
    def run(self):
        """メインループ"""
        self.running = True
        self.logger.info("Starting main loop...")
        
        fps = self.settings['screen']['fps']
        frame_count = 0
        last_log = time.time()
        
        try:
            while self.running:
                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_q:
                            self.running = False
                
                # 背景描画
                self.draw_gradient_background(self.screen)
                
                # レンダラー実行
                for name, renderer in self.renderers:
                    try:
                        renderer.render(self.screen)
                    except Exception as e:
                        self.logger.error(f"Renderer {name} failed: {e}")
                
                # 画面更新
                pygame.display.flip()
                
                # FPS制御
                self.clock.tick(fps)
                frame_count += 1
                
                # 定期ログ（30秒ごと）
                current_time = time.time()
                if current_time - last_log > 30:
                    actual_fps = frame_count / (current_time - last_log)
                    self.logger.info(f"Running... FPS: {actual_fps:.1f}")
                    frame_count = 0
                    last_log = current_time
        
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
        pygame.quit()
        self.logger.info("SimplePiCalendar stopped")
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """メイン関数"""
    # アプリケーション作成
    app = SimplePiCalendarApp()
    
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