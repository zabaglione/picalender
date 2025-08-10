"""
ディスプレイ管理モジュール
pygame/SDL2の初期化と画面管理を行う

TASK-101: pygame/SDL2初期化
- フルスクリーン・KMSDRM対応
- 1024×600解像度固定
- マウスカーソル非表示
- FPS制御（30fps）
- エラーハンドリング強化
"""

import os
import sys
import logging
from typing import Tuple, Dict, Any, Optional

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed. Please run: pip install pygame")
    sys.exit(1)

from src.core import ConfigManager, LogManager
from .environment_detector import EnvironmentDetector


class DisplayManager:
    """ディスプレイ管理クラス"""
    
    def __init__(self, config: ConfigManager):
        """
        初期化
        
        Args:
            config: 設定管理オブジェクト
        """
        self.config = config
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.fullscreen: bool = False
        self.dummy_mode: bool = False
        self.headless: bool = False
        self.resolution: Tuple[int, int] = (1024, 600)
        self.fps: int = 30
        
        # ログマネージャー初期化
        self.log_manager = LogManager(config)
        self.logger = self.log_manager.get_logger(__name__)
        
        # 設定読み込み
        self._load_config()
    
    def _load_config(self) -> None:
        """設定を読み込む"""
        # 設定の取得
        screen_config = self.config.get('screen', {}) if hasattr(self.config, 'get') else {}
        ui_config = self.config.get('ui', {}) if hasattr(self.config, 'get') else {}
        
        # デフォルト値
        DEFAULT_WIDTH = 1024
        DEFAULT_HEIGHT = 600
        DEFAULT_FPS = 30
        DEFAULT_FULLSCREEN = True
        DEFAULT_HIDE_CURSOR = True
        
        # 解像度
        self.resolution = (
            screen_config.get('width', DEFAULT_WIDTH),
            screen_config.get('height', DEFAULT_HEIGHT)
        )
        
        # FPS
        self.fps = screen_config.get('fps', DEFAULT_FPS)
        
        # フルスクリーン設定
        self.fullscreen = ui_config.get('fullscreen', DEFAULT_FULLSCREEN)
        
        # マウスカーソル設定
        self.hide_cursor_on_init = ui_config.get('hide_cursor', DEFAULT_HIDE_CURSOR)
        
        self.logger.info(f"Display configuration loaded: {self.resolution[0]}x{self.resolution[1]} @ {self.fps}fps")
    
    def initialize(self) -> bool:
        """
        pygame/SDL2を初期化
        
        Returns:
            bool: 初期化成功の場合True
        """
        try:
            # 環境検出
            is_rpi = EnvironmentDetector.is_raspberry_pi()
            has_display = EnvironmentDetector.has_display()
            video_driver = EnvironmentDetector.get_video_driver()
            
            self.logger.info(f"Environment: RPi={is_rpi}, Display={has_display}, Driver={video_driver}")
            
            # ヘッドレスモードの判定
            if not has_display:
                self.logger.warning("No display detected, running in headless mode")
                self.headless = True
                video_driver = 'dummy'
            
            # ビデオドライバー設定
            if video_driver:
                os.environ['SDL_VIDEODRIVER'] = video_driver
                self.logger.info(f"Using video driver: {video_driver}")
            
            # pygame初期化
            pygame.init()
            
            # 初期化確認
            if not pygame.get_init():
                raise RuntimeError("pygame initialization failed")
            
            # Clockオブジェクト作成
            self.clock = pygame.time.Clock()
            
            self.logger.info("pygame initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pygame: {e}")
            
            # フォールバック：ダミーモードで起動
            try:
                os.environ['SDL_VIDEODRIVER'] = 'dummy'
                pygame.init()
                self.dummy_mode = True
                self.clock = pygame.time.Clock()
                self.logger.warning("Running in dummy mode")
                return True
            except Exception as fallback_error:
                self.logger.critical(f"Failed to initialize even in dummy mode: {fallback_error}")
                return False
    
    def create_screen(self) -> pygame.Surface:
        """
        スクリーンサーフェスを作成
        
        Returns:
            pygame.Surface: スクリーンサーフェス
        """
        if not pygame.get_init():
            raise RuntimeError("pygame is not initialized")
        
        try:
            # フラグ設定
            flags = 0
            
            # フルスクリーン設定（本番環境のみ）
            if self.fullscreen and EnvironmentDetector.is_raspberry_pi():
                flags |= pygame.FULLSCREEN
                self.logger.info("Fullscreen mode enabled")
            
            # ハードウェアアクセラレーション（可能な場合）
            if not self.dummy_mode and not self.headless:
                flags |= pygame.HWSURFACE | pygame.DOUBLEBUF
            
            # スクリーン作成
            self.screen = pygame.display.set_mode(self.resolution, flags)
            
            # ウィンドウタイトル設定（ウィンドウモード時）
            if not self.fullscreen:
                pygame.display.set_caption("PiCalendar")
            
            # マウスカーソル設定
            if self.hide_cursor_on_init:
                pygame.mouse.set_visible(False)
            
            self.logger.info(f"Screen created: {self.resolution[0]}x{self.resolution[1]}")
            return self.screen
            
        except pygame.error as e:
            self.logger.error(f"Failed to create screen with resolution {self.resolution}: {e}")
            
            # フォールバック処理
            return self._create_fallback_screen(flags)
    
    def set_fullscreen(self, fullscreen: bool) -> None:
        """
        フルスクリーンモードを設定
        
        Args:
            fullscreen: Trueでフルスクリーン、Falseでウィンドウモード
        """
        self.fullscreen = fullscreen
        
        if self.screen and not self.dummy_mode and not self.headless:
            flags = 0
            if fullscreen:
                flags |= pygame.FULLSCREEN
            
            # 開発環境では実際のフルスクリーン切り替えをスキップ
            if EnvironmentDetector.is_raspberry_pi() or os.environ.get('PICALENDAR_FORCE_FULLSCREEN'):
                try:
                    self.screen = pygame.display.set_mode(self.resolution, flags)
                    self.logger.info(f"Fullscreen mode: {fullscreen}")
                except pygame.error as e:
                    self.logger.error(f"Failed to change fullscreen mode: {e}")
            else:
                self.logger.debug(f"Fullscreen mode set to {fullscreen} (not applied in development)")
    
    def hide_cursor(self, hide: bool) -> None:
        """
        マウスカーソルの表示/非表示
        
        Args:
            hide: Trueで非表示、Falseで表示
        """
        pygame.mouse.set_visible(not hide)
        self.logger.debug(f"Mouse cursor: {'hidden' if hide else 'visible'}")
    
    def get_screen(self) -> pygame.Surface:
        """
        現在のスクリーンサーフェスを取得
        
        Returns:
            pygame.Surface: スクリーンサーフェス
        """
        if not self.screen:
            raise RuntimeError("Screen is not created")
        return self.screen
    
    def get_clock(self) -> pygame.time.Clock:
        """
        FPS制御用のClockオブジェクトを取得
        
        Returns:
            pygame.time.Clock: Clockオブジェクト
        """
        if not self.clock:
            self.clock = pygame.time.Clock()
        return self.clock
    
    def flip(self) -> None:
        """画面を更新（ダブルバッファリング）"""
        if self.screen and not self.dummy_mode:
            pygame.display.flip()
    
    def clear(self, color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """
        画面をクリア
        
        Args:
            color: クリア色 (R, G, B)
        """
        if self.screen:
            self.screen.fill(color)
    
    def quit(self) -> None:
        """pygameを終了"""
        if pygame.get_init():
            pygame.quit()
            self.logger.info("pygame quit")
    
    def _create_fallback_screen(self, flags: int) -> pygame.Surface:
        """フォールバック画面を作成
        
        Args:
            flags: pygame display フラグ
            
        Returns:
            pygame.Surface: フォールバック画面
        """
        # 利用可能な解像度を試す
        try:
            modes = pygame.display.list_modes()
            if modes and modes != -1:  # -1 は任意の解像度が使用可能を意味
                # 最も近い解像度を選択
                fallback_resolution = modes[0] if modes else (800, 600)
                self.screen = pygame.display.set_mode(fallback_resolution, flags)
                self.resolution = fallback_resolution
                self.logger.warning(f"Using fallback resolution: {fallback_resolution}")
                return self.screen
        except Exception as e:
            self.logger.debug(f"Fallback resolution failed: {e}")
        
        # 最終フォールバック：最小解像度
        MIN_WIDTH, MIN_HEIGHT = 640, 480
        self.screen = pygame.display.set_mode((MIN_WIDTH, MIN_HEIGHT))
        self.resolution = (MIN_WIDTH, MIN_HEIGHT)
        self.logger.warning(f"Using minimum resolution: {MIN_WIDTH}x{MIN_HEIGHT}")
        return self.screen
    
    def get_info(self) -> Dict[str, Any]:
        """
        ディスプレイ情報を取得
        
        Returns:
            Dict[str, Any]: ディスプレイ情報
        """
        info = {
            'resolution': self.resolution,
            'fps': self.fps,
            'fullscreen': self.fullscreen,
            'dummy_mode': self.dummy_mode,
            'headless': self.headless,
            'driver': os.environ.get('SDL_VIDEODRIVER', 'default'),
            'pygame_version': pygame.version.ver if hasattr(pygame.version, 'ver') else 'unknown'
        }
        
        # 追加情報（利用可能な場合）
        if pygame.get_init():
            try:
                display_info = pygame.display.Info()
                info['desktop_size'] = (display_info.current_w, display_info.current_h)
            except Exception:
                pass
        
        return info
    
    def get_fps_stats(self) -> Dict[str, float]:
        """
        FPS統計情報を取得（TASK-101要件）
        
        Returns:
            Dict[str, float]: FPS統計
        """
        if not self.clock:
            return {'current_fps': 0.0, 'target_fps': float(self.fps)}
        
        return {
            'current_fps': self.clock.get_fps(),
            'target_fps': float(self.fps),
            'frame_time_ms': 1000.0 / max(self.clock.get_fps(), 1.0)
        }
    
    def tick(self) -> float:
        """
        FPS制御とフレーム時間取得（TASK-101要件）
        
        Returns:
            float: 前フレームからの経過時間（秒）
        """
        if not self.clock:
            return 0.0
        
        dt_ms = self.clock.tick(self.fps)
        return dt_ms / 1000.0
    
    def validate_display_requirements(self) -> Dict[str, bool]:
        """
        TASK-101要件の検証
        
        Returns:
            Dict[str, bool]: 要件チェック結果
        """
        requirements = {
            'pygame_initialized': pygame.get_init(),
            'screen_created': self.screen is not None,
            'target_resolution': self.resolution == (1024, 600),
            'fullscreen_capable': not self.dummy_mode and not self.headless,
            'cursor_hidden': not pygame.mouse.get_visible() if pygame.get_init() else False,
            'fps_control': self.clock is not None,
            'kmsdrm_driver': os.environ.get('SDL_VIDEODRIVER') == 'kmsdrm'
        }
        
        return requirements
    
    def get_initialization_report(self) -> str:
        """
        初期化レポートを生成（TASK-101デバッグ用）
        
        Returns:
            str: 初期化状況レポート
        """
        requirements = self.validate_display_requirements()
        fps_stats = self.get_fps_stats()
        info = self.get_info()
        
        report = [
            "=== TASK-101 Display Initialization Report ===",
            f"Environment: {'Raspberry Pi' if EnvironmentDetector.is_raspberry_pi() else 'Development'}",
            f"Resolution: {info['resolution']} (Target: 1024x600)",
            f"Video Driver: {info['driver']}",
            f"Fullscreen: {info['fullscreen']}",
            f"FPS Target: {fps_stats['target_fps']} (Current: {fps_stats['current_fps']:.1f})",
            "",
            "Requirements Check:",
        ]
        
        for requirement, status in requirements.items():
            status_icon = "✅" if status else "❌"
            report.append(f"  {status_icon} {requirement}: {status}")
        
        return "\n".join(report)