#!/bin/bash

# PiCalendar systemdサービスアンインストールスクリプト

set -e

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ルート権限チェック
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: このスクリプトはroot権限で実行する必要があります${NC}"
   echo "使用方法: sudo ./uninstall_service.sh"
   exit 1
fi

echo -e "${YELLOW}=== PiCalendar systemdサービスのアンインストール ===${NC}"

# 変数設定
SERVICE_NAME="picalender"
SERVICE_FILE="${SERVICE_NAME}.service"
TARGET_SERVICE="/etc/systemd/system/${SERVICE_FILE}"

# サービスの状態確認
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "サービスを停止中..."
    systemctl stop $SERVICE_NAME
fi

# サービスの無効化
if systemctl is-enabled --quiet $SERVICE_NAME; then
    echo "サービスを無効化中..."
    systemctl disable $SERVICE_NAME
fi

# サービスファイルの削除
if [ -f "$TARGET_SERVICE" ]; then
    echo "サービスファイルを削除中..."
    rm "$TARGET_SERVICE"
fi

# systemdのリロード
echo "systemdをリロード中..."
systemctl daemon-reload

echo -e "${GREEN}=== アンインストール完了 ===${NC}"
echo
echo "注意: アプリケーションファイルは削除されていません。"
echo "アプリケーションを完全に削除する場合は、以下のディレクトリを手動で削除してください:"
echo "  /home/pi/picalender"