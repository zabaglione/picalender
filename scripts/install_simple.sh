#!/bin/bash

# PiCalendar シンプル版インストールスクリプト

set -e

echo "========================================="
echo "  PiCalendar Simple インストールスクリプト"
echo "========================================="
echo ""

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 現在のユーザー名を取得
CURRENT_USER=${SUDO_USER:-$USER}
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

echo -e "${GREEN}ユーザー名:${NC} $CURRENT_USER"
echo -e "${GREEN}インストールディレクトリ:${NC} $INSTALL_DIR"
echo ""

# 既存のサービスを停止
echo -e "${YELLOW}1. 既存のサービスを停止...${NC}"
sudo systemctl stop picalender 2>/dev/null || true
sudo systemctl disable picalender 2>/dev/null || true

# サービスファイルの作成
echo -e "${YELLOW}2. サービスファイルを作成...${NC}"

cat > /tmp/picalender.service <<EOF
[Unit]
Description=PiCalendar Simple Display Application
After=multi-user.target network.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR

# SDL/pygame設定
Environment="SDL_VIDEODRIVER=kmsdrm"
Environment="SDL_FBDEV=/dev/fb0"
Environment="SDL_KMSDRM_DEVICE_INDEX=0"
Environment="SDL_RENDER_DRIVER=software"
Environment="PYTHONUNBUFFERED=1"

# 起動前の待機時間（ネットワークとディスプレイの準備）
ExecStartPre=/bin/sleep 5

# メインアプリケーションを起動
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py

# 再起動設定
Restart=always
RestartSec=10
StartLimitBurst=5

# ログ設定
StandardOutput=journal
StandardError=journal

# プロセス管理
KillMode=control-group
TimeoutStopSec=10

# リソース制限（Raspberry Pi Zero 2 W向け）
MemoryMax=256M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# サービスファイルをインストール
echo -e "${YELLOW}3. サービスファイルをインストール...${NC}"
sudo mv /tmp/picalender.service /etc/systemd/system/
sudo systemctl daemon-reload
echo -e "${GREEN}✓ サービスファイルをインストールしました${NC}"

# ユーザーの権限確認
echo -e "${YELLOW}4. ユーザー権限の確認...${NC}"

# videoグループへの追加
if ! groups $CURRENT_USER | grep -q video; then
    sudo usermod -a -G video $CURRENT_USER
    echo -e "${GREEN}✓ $CURRENT_USER をvideoグループに追加しました${NC}"
else
    echo -e "${GREEN}✓ $CURRENT_USER は既にvideoグループに所属しています${NC}"
fi

# inputグループへの追加
if ! groups $CURRENT_USER | grep -q input; then
    sudo usermod -a -G input $CURRENT_USER
    echo -e "${GREEN}✓ $CURRENT_USER をinputグループに追加しました${NC}"
else
    echo -e "${GREEN}✓ $CURRENT_USER は既にinputグループに所属しています${NC}"
fi

# デバイスファイルの権限確認
echo -e "${YELLOW}5. デバイスファイルの権限確認...${NC}"
if [ -e /dev/fb0 ]; then
    sudo chmod 666 /dev/fb0 2>/dev/null || true
    echo -e "${GREEN}✓ /dev/fb0 の権限を設定しました${NC}"
fi

if [ -e /dev/dri/card0 ]; then
    sudo chmod 666 /dev/dri/card0 2>/dev/null || true
    echo -e "${GREEN}✓ /dev/dri/card0 の権限を設定しました${NC}"
fi

# ディレクトリの作成
echo -e "${YELLOW}6. 必要なディレクトリの作成...${NC}"
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/cache/weather
mkdir -p $INSTALL_DIR/wallpapers
echo -e "${GREEN}✓ ディレクトリを作成しました${NC}"

# サービスの有効化
echo -e "${YELLOW}7. サービスを有効化...${NC}"
sudo systemctl enable picalender
echo -e "${GREEN}✓ サービスを有効化しました${NC}"

# サービスの開始
read -p "今すぐサービスを開始しますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start picalender
    sleep 3
    
    # 状態確認
    if systemctl is-active --quiet picalender; then
        echo -e "${GREEN}✓ サービスが正常に起動しました${NC}"
    else
        echo -e "${RED}✗ サービスの起動に失敗しました${NC}"
        echo -e "${YELLOW}ログを確認してください:${NC}"
        sudo journalctl -u picalender -n 20 --no-pager
    fi
fi

echo ""
echo "========================================="
echo -e "${GREEN}インストールが完了しました！${NC}"
echo "========================================="
echo ""
echo "サービス管理コマンド:"
echo "  sudo systemctl start picalender    # 開始"
echo "  sudo systemctl stop picalender     # 停止"
echo "  sudo systemctl restart picalender  # 再起動"
echo "  sudo systemctl status picalender   # 状態確認"
echo ""
echo "ログ確認:"
echo "  sudo journalctl -u picalender -f   # リアルタイムログ"
echo "  sudo journalctl -u picalender -n 50 # 最新50行"
echo ""
echo "手動実行（デバッグ用）:"
echo "  cd $INSTALL_DIR"
echo "  python3 main_simple.py"
echo ""

# グループ変更の注意
if [ "$CURRENT_USER" != "root" ]; then
    echo -e "${YELLOW}注意: グループ設定を反映するには再ログインが必要な場合があります${NC}"
fi