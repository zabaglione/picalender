"""
環境検出モジュール
実行環境を判定し、適切な設定を提供する
"""

import os
import platform
from pathlib import Path


class EnvironmentDetector:
    """実行環境検出クラス"""
    
    # 定数
    RPI_CPU_MARKERS = ['Raspberry Pi', 'BCM2']
    RPI_MODEL_PATH = '/proc/device-tree/model'
    CPU_INFO_PATH = '/proc/cpuinfo'
    FRAMEBUFFER_PATH = '/dev/fb0'
    
    @staticmethod
    def is_raspberry_pi() -> bool:
        """
        Raspberry Pi環境かどうかを判定
        
        Returns:
            bool: Raspberry Pi環境の場合True
        """
        # 複数の方法で判定
        # 1. /proc/cpuinfoをチェック
        if EnvironmentDetector._check_file_contains(
            EnvironmentDetector.CPU_INFO_PATH, 
            EnvironmentDetector.RPI_CPU_MARKERS
        ):
            return True
        
        # 2. /proc/device-treeをチェック
        if EnvironmentDetector._check_file_contains(
            EnvironmentDetector.RPI_MODEL_PATH,
            ['Raspberry Pi']
        ):
            return True
        
        # 3. ホスト名をチェック（raspberrypiがデフォルト）
        hostname = platform.node()
        if 'raspberry' in hostname.lower():
            return True
        
        # 4. 環境変数でのオーバーライド（テスト用）
        if os.environ.get('PICALENDAR_DEVICE') == 'raspberry_pi':
            return True
        
        return False
    
    @staticmethod
    def _check_file_contains(file_path: str, markers: list) -> bool:
        """
        ファイルに特定のマーカー文字列が含まれるかチェック
        
        Args:
            file_path: チェックするファイルパス
            markers: 検索するマーカー文字列のリスト
            
        Returns:
            bool: マーカーが含まれる場合True
        """
        if not Path(file_path).exists():
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                return any(marker in content for marker in markers)
        except Exception:
            return False
    
    @staticmethod
    def has_display() -> bool:
        """
        ディスプレイが接続されているか確認
        
        Returns:
            bool: ディスプレイが利用可能な場合True
        """
        # 1. DISPLAY環境変数のチェック（X11）
        if os.environ.get('DISPLAY'):
            return True
        
        # 2. Waylandセッションのチェック
        if os.environ.get('WAYLAND_DISPLAY'):
            return True
        
        # 3. フレームバッファのチェック（Linux）
        if platform.system() == 'Linux':
            if Path('/dev/fb0').exists():
                return True
        
        # 4. Windows/macOSは通常ディスプレイがある
        if platform.system() in ['Windows', 'Darwin']:
            return True
        
        # 5. SSH経由の場合はヘッドレスと判定
        if os.environ.get('SSH_CONNECTION'):
            return False
        
        # 6. 環境変数でのオーバーライド
        if os.environ.get('PICALENDAR_HEADLESS') == 'true':
            return False
        
        # デフォルトはディスプレイありと仮定
        return True
    
    @staticmethod
    def get_video_driver() -> str | None:
        """
        使用するビデオドライバーを決定
        
        Returns:
            str | None: ビデオドライバー名（Noneはデフォルト使用）
        """
        # 環境変数でのオーバーライド
        if os.environ.get('SDL_VIDEODRIVER'):
            return os.environ.get('SDL_VIDEODRIVER')
        
        system = platform.system()
        
        # Raspberry Pi
        if EnvironmentDetector.is_raspberry_pi():
            # KMSDRMを優先的に使用
            if not os.environ.get('DISPLAY'):  # X11が動いていない場合
                return 'kmsdrm'
            else:
                return 'x11'  # X11が動いている場合
        
        # macOS
        if system == 'Darwin':
            return None  # pygameのデフォルトを使用
        
        # Windows
        if system == 'Windows':
            return 'windib'
        
        # Linux (non-RPi)
        if system == 'Linux':
            # Waylandセッション
            if os.environ.get('WAYLAND_DISPLAY'):
                return 'wayland'
            # X11セッション
            if os.environ.get('DISPLAY'):
                return 'x11'
            # フレームバッファ
            if Path('/dev/fb0').exists():
                return 'fbcon'
            # ヘッドレス
            return 'dummy'
        
        # その他のOSはデフォルト
        return None