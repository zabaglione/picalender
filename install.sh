#!/bin/bash

# PiCalendar インストールスクリプト
# Raspberry Pi OS (Bookworm以降) 対応

set -e

echo "========================================="
echo "  PiCalendar インストールスクリプト"
echo "========================================="
echo ""

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 実行ユーザーとディレクトリの確認
INSTALL_USER=${SUDO_USER:-$USER}
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}インストールディレクトリ:${NC} $INSTALL_DIR"
echo -e "${GREEN}インストールユーザー:${NC} $INSTALL_USER"
echo ""

# システムパッケージの更新
echo -e "${YELLOW}1. システムパッケージの更新...${NC}"
sudo apt update
sudo apt upgrade -y

# 必要なシステムパッケージのインストール
echo -e "${YELLOW}2. 必要なシステムパッケージのインストール...${NC}"
sudo apt install -y \
    python3-full \
    python3-pip \
    python3-venv \
    python3-pygame \
    python3-yaml \
    python3-requests \
    python3-pillow \
    fonts-noto-cjk \
    git

# 仮想環境の作成
echo -e "${YELLOW}3. Python仮想環境の作成...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 仮想環境を作成しました${NC}"
else
    echo -e "${GREEN}✓ 仮想環境は既に存在します${NC}"
fi

# 仮想環境の有効化とパッケージインストール
echo -e "${YELLOW}4. Pythonパッケージのインストール...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Pythonパッケージをインストールしました${NC}"

# 設定ファイルのセットアップ
echo -e "${YELLOW}5. 設定ファイルのセットアップ...${NC}"
if [ ! -f "settings.yaml" ]; then
    if [ -f "settings.example.yaml" ]; then
        cp settings.example.yaml settings.yaml
        echo -e "${GREEN}✓ 設定ファイルをコピーしました${NC}"
    else
        echo -e "${YELLOW}⚠ settings.example.yamlが見つかりません。既存のsettings.yamlを使用します${NC}"
    fi
else
    echo -e "${GREEN}✓ 設定ファイルは既に存在します${NC}"
fi

# ディレクトリの作成
echo -e "${YELLOW}6. 必要なディレクトリの作成...${NC}"
mkdir -p wallpapers
mkdir -p cache/weather
mkdir -p cache/images
mkdir -p logs
echo -e "${GREEN}✓ ディレクトリを作成しました${NC}"

# systemdサービスのインストール
echo -e "${YELLOW}7. systemdサービスの設定...${NC}"
read -p "systemdサービスとして自動起動を設定しますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # サービスファイルの生成
    cat > /tmp/picalender.service <<EOF
[Unit]
Description=PiCalendar Display Application
After=multi-user.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="SDL_VIDEODRIVER=kmsdrm"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/picalender.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable picalender
    echo -e "${GREEN}✓ systemdサービスを設定しました${NC}"
    
    read -p "今すぐサービスを開始しますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start picalender
        echo -e "${GREEN}✓ サービスを開始しました${NC}"
    fi
fi

# テスト実行
echo ""
echo -e "${YELLOW}8. インストールの確認...${NC}"
source venv/bin/activate
python -c "import pygame; import yaml; import requests; print('✓ すべてのパッケージが正常にインポートできました')"

echo ""
echo "========================================="
echo -e "${GREEN}インストールが完了しました！${NC}"
echo "========================================="
echo ""
echo "次のコマンドで起動できます:"
echo ""
echo "  手動起動:"
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
echo "  サービス管理:"
echo "    sudo systemctl start picalender   # 開始"
echo "    sudo systemctl stop picalender    # 停止"
echo "    sudo systemctl status picalender  # 状態確認"
echo "    sudo journalctl -u picalender -f  # ログ確認"
echo ""
echo "設定ファイル: $INSTALL_DIR/settings.yaml"
echo ""