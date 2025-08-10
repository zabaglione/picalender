#!/usr/bin/env python3
"""
PiCalendar - メインエントリーポイント
"""

import sys
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("PiCalendar starting...")
    
    # TODO: アプリケーション初期化
    # TODO: 設定読み込み
    # TODO: pygame初期化
    # TODO: メインループ開始
    
    logger.info("PiCalendar ready for implementation")
    return 0

if __name__ == "__main__":
    sys.exit(main())