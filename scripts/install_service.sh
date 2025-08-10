#!/bin/bash

# PiCalendar systemdサービスインストールスクリプト

set -e

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ルート権限チェック
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: このスクリプトはroot権限で実行する必要があります${NC}"
   echo "使用方法: sudo ./install_service.sh"
   exit 1
fi

echo -e "${GREEN}=== PiCalendar systemdサービスのインストール ===${NC}"

# 変数設定
SERVICE_NAME="picalender"
SERVICE_FILE="${SERVICE_NAME}.service"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_SERVICE="${SCRIPT_DIR}/${SERVICE_FILE}"
TARGET_SERVICE="/etc/systemd/system/${SERVICE_FILE}"
APP_DIR="/home/pi/picalender"
APP_USER="pi"

# ディレクトリ存在チェック
if [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}警告: アプリケーションディレクトリが存在しません: $APP_DIR${NC}"
    echo "アプリケーションを $APP_DIR にインストールしてください"
    exit 1
fi

# main.pyの存在チェック
if [ ! -f "$APP_DIR/main.py" ]; then
    echo -e "${RED}Error: main.pyが見つかりません: $APP_DIR/main.py${NC}"
    exit 1
fi

# 既存サービスの停止
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "既存のサービスを停止中..."
    systemctl stop $SERVICE_NAME
fi

# サービスファイルのコピー
echo "サービスファイルをインストール中..."
cp "$SOURCE_SERVICE" "$TARGET_SERVICE"

# 権限設定
chmod 644 "$TARGET_SERVICE"

# systemdのリロード
echo "systemdをリロード中..."
systemctl daemon-reload

# サービスの有効化
echo "サービスを有効化中..."
systemctl enable $SERVICE_NAME

# 必要なディレクトリの作成
echo "必要なディレクトリを作成中..."
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/cache"
mkdir -p "$APP_DIR/assets/fonts"
mkdir -p "$APP_DIR/assets/icons/weather"
mkdir -p "$APP_DIR/assets/sprites"
mkdir -p "$APP_DIR/wallpapers"

# 権限設定
chown -R $APP_USER:$APP_USER "$APP_DIR"

echo -e "${GREEN}=== インストール完了 ===${NC}"
echo
echo "使用可能なコマンド:"
echo "  サービス開始: sudo systemctl start $SERVICE_NAME"
echo "  サービス停止: sudo systemctl stop $SERVICE_NAME"
echo "  サービス再起動: sudo systemctl restart $SERVICE_NAME"
echo "  ステータス確認: sudo systemctl status $SERVICE_NAME"
echo "  ログ確認: sudo journalctl -u $SERVICE_NAME -f"
echo "  サービス無効化: sudo systemctl disable $SERVICE_NAME"
echo
echo -e "${YELLOW}注意: アプリケーションを起動する前に、settings.yamlを適切に設定してください${NC}"