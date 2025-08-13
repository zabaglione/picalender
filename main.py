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
import traceback

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数の設定（macOSは除外）
if ('arm' in os.uname().machine or 'aarch64' in os.uname().machine) and os.uname().sysname != 'Darwin':
    os.environ.setdefault('SDL_VIDEODRIVER', 'kmsdrm')

# 音声を無効化してALSA警告を防ぐ
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

# YAMLライブラリを安全にインポート
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Using default settings.")
    print("To install: pip3 install pyyaml")

# src.renderersパッケージを経由せずに直接インポート
import sys
sys.path.append(str(Path(__file__).parent / 'src' / 'renderers'))
from simple_clock_renderer import SimpleClockRenderer
from simple_date_renderer import SimpleDateRenderer
from simple_calendar_renderer import SimpleCalendarRenderer
from simple_moon_renderer import SimpleMoonRenderer


class PiCalendarApp:
    """PiCalendarアプリケーション"""
    
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
        self.logger.info("PiCalendar Application Starting")
        self.logger.info(f"Python: {sys.version}")
        self.logger.info(f"Pygame: {pygame.version.ver}")
        self.logger.info("="*50)
        
        # 設定を読み込み（settings.yamlがあれば使用）
        self.settings = self._load_settings()
        
        # フルスクリーン設定（環境変数で制御可能）
        if os.environ.get('PICALENDER_WINDOWED', '').lower() == 'true':
            self.settings['screen']['fullscreen'] = False
        
        self.screen = None
        self.renderers = []
    
    def _load_settings(self):
        """設定ファイルを読み込み"""
        # デフォルト設定
        default_settings = {
            'screen': {
                'width': 1024,
                'height': 600,
                'fps': 30,
                'fullscreen': True
            },
            'ui': {
                'clock_font_px': 130,
                'date_font_px': 36,
                'cal_font_px': 22,
                'calendar_font_px': 22,
                'weather_font_px': 20
            },
            'calendar': {
                'holidays_enabled': True,
                'holidays_country': 'JP',
                'show_holiday_names': False,
                'rokuyou_enabled': True,
                'show_rokuyou_names': True,
                'rokuyou_format': 'single'
            }
        }
        
        # settings.yamlを読み込み（YAMLが利用可能な場合）
        if YAML_AVAILABLE:
            settings_file = Path(__file__).parent / 'settings.yaml'
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        user_settings = yaml.safe_load(f) or {}
                    
                    # ユーザー設定をマージ
                    self._merge_settings(default_settings, user_settings)
                    self.logger.info(f"Settings loaded from {settings_file}")
                    
                    return default_settings
                except Exception as e:
                    self.logger.warning(f"Failed to load settings.yaml: {e}")
                    self.logger.info("Using default settings")
            else:
                self.logger.info("settings.yaml not found, using default settings")
        else:
            self.logger.info("PyYAML not installed, using default settings")
        
        return default_settings
    
    def _merge_settings(self, base, override):
        """設定を再帰的にマージ"""
        for key, value in override.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    self._merge_settings(base[key], value)
                else:
                    base[key] = value
            else:
                base[key] = value
    
    def initialize(self):
        """アプリケーションの初期化"""
        try:
            self.logger.info("Initializing PiCalendar...")
            
            # pygame初期化（音声なし）
            pygame.init()
            pygame.mixer.quit()  # 音声ミキサーを明示的に無効化
            
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
            
            # 月相レンダラー
            try:
                moon_renderer = SimpleMoonRenderer(self.settings)
                self.renderers.append(('moon', moon_renderer))
                self.logger.info("Moon phase renderer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize moon renderer: {e}")
            
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
        
        fps = self.settings['screen'].get('fps', 10)  # FPSを10に下げる
        frame_count = 0
        last_log = time.time()
        
        # 更新制御用
        last_second = -1
        last_minute = -1
        last_update_times = {}
        
        # 初期描画
        self.draw_gradient_background(self.screen)
        for name, renderer in self.renderers:
            try:
                renderer.render(self.screen)
                last_update_times[name] = time.time()
            except Exception as e:
                self.logger.error(f"Initial render failed for {name}: {e}")
        pygame.display.flip()
        
        try:
            while self.running:
                current_time = time.time()
                local_time = time.localtime(current_time)
                
                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_q:
                            self.running = False
                
                # 更新が必要なレンダラーを判定
                need_update = False
                
                # 秒が変わったら時計を更新
                if local_time.tm_sec != last_second:
                    last_second = local_time.tm_sec
                    
                    # 時計部分の背景をクリア（グラデーション背景で上書き）
                    self.draw_gradient_background(self.screen)
                    
                    # 全レンダラーを再描画（秒更新時も全体を更新）
                    for name, renderer in self.renderers:
                        try:
                            renderer.render(self.screen)
                            last_update_times[name] = current_time
                        except Exception as e:
                            self.logger.error(f"{name} update failed: {e}")
                    
                    need_update = True
                
                # 分が変わったら日付とカレンダーを更新（秒更新と重複しないように）
                elif local_time.tm_min != last_minute:
                    last_minute = local_time.tm_min
                    
                    # 背景を再描画（分単位の更新時のみ）
                    self.draw_gradient_background(self.screen)
                    
                    # 全レンダラーを再描画
                    for name, renderer in self.renderers:
                        try:
                            renderer.render(self.screen)
                            last_update_times[name] = current_time
                        except Exception as e:
                            self.logger.error(f"{name} update failed: {e}")
                    
                    need_update = True
                
                # その他のレンダラーは設定された間隔で更新
                update_intervals = {
                    'weather': 1800,  # 30分
                    'moon': 3600,     # 1時間
                    'wallpaper': 300  # 5分
                }
                
                for name, renderer in self.renderers:
                    if name in update_intervals:
                        interval = update_intervals[name]
                        last_update = last_update_times.get(name, 0)
                        if current_time - last_update >= interval:
                            try:
                                # 壁紙更新時は全体を再描画
                                if name == 'wallpaper':
                                    self.draw_gradient_background(self.screen)
                                    for n, r in self.renderers:
                                        r.render(self.screen)
                                else:
                                    renderer.render(self.screen)
                                last_update_times[name] = current_time
                                need_update = True
                            except Exception as e:
                                self.logger.error(f"{name} update failed: {e}")
                
                # 画面更新（必要な時のみ）
                if need_update:
                    pygame.display.flip()
                
                # FPS制御
                self.clock.tick(fps)
                frame_count += 1
                
                # 定期ログ（30秒ごと）
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