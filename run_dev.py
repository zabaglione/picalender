#!/usr/bin/env python3
"""
開発環境での実行スクリプト（Mac/デスクトップ用）
"""

import sys
import os
from pathlib import Path

# SDL環境変数をデスクトップ用に設定
os.environ['SDL_VIDEODRIVER'] = ''  # デフォルトドライバを使用

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 開発用設定ファイルを指定
os.environ['PICALENDER_CONFIG'] = 'settings_dev.yaml'

# main.pyをインポートして実行
from main import main

if __name__ == "__main__":
    print("="*50)
    print("PiCalendar - Development Mode")
    print("="*50)
    print("Controls:")
    print("  ESC    : Exit application")
    print("  F11    : Toggle fullscreen")
    print("="*50)
    print()
    
    sys.exit(main())