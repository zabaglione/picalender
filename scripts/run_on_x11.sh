#!/bin/bash

# PiCalendarをX Window上で実行するスクリプト

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  PiCalendar X11 起動スクリプト"
echo "========================================="
echo ""

# X Windowの確認
if [ -z "$DISPLAY" ]; then
    echo -e "${YELLOW}DISPLAYが設定されていません。設定します...${NC}"
    export DISPLAY=:0
fi

echo -e "${GREEN}DISPLAY:${NC} $DISPLAY"

# 既存のsystemdサービスを停止（競合を避けるため）
if systemctl is-active --quiet picalender; then
    echo -e "${YELLOW}systemdサービスが実行中です。停止します...${NC}"
    sudo systemctl stop picalender
    echo -e "${GREEN}✓ サービスを停止しました${NC}"
fi

# X11権限の設定
echo -e "${YELLOW}X11アクセス権限を設定...${NC}"
xhost +local: 2>/dev/null || true

# PiCalendarディレクトリに移動
cd /home/$USER/picalender

# 実行モードの選択
echo ""
echo "実行モードを選択してください:"
echo "1) ウィンドウモード（デフォルト）"
echo "2) フルスクリーンモード"
echo -n "選択 [1]: "
read -t 5 choice

case "$choice" in
    2)
        echo -e "${GREEN}フルスクリーンモードで起動します${NC}"
        export PICALENDER_FULLSCREEN=true
        ;;
    *)
        echo -e "${GREEN}ウィンドウモードで起動します${NC}"
        export PICALENDER_FULLSCREEN=false
        ;;
esac

echo ""
echo "起動中..."
echo "終了するには: ESC または Q キーを押してください"
echo "フルスクリーン切り替え: F11 または F キー"
echo ""

# 統合版を実行（X11環境は自動検出）
python3 main.py

echo ""
echo -e "${GREEN}PiCalendarを終了しました${NC}"