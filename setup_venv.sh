#!/bin/bash

# 仮想環境セットアップスクリプト

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    PiCalendar 仮想環境セットアップ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Python3とvenvの確認
echo -e "${YELLOW}1. Python環境を確認...${NC}"
python3 --version

# venvモジュールの確認
python3 -c "import venv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ python3-venvがインストールされていません${NC}"
    echo -e "${YELLOW}インストール方法:${NC}"
    echo "  sudo apt install python3-venv"
    exit 1
fi
echo -e "${GREEN}✓ python3-venv is available${NC}"

# 既存の仮想環境を確認
if [ -d "venv" ]; then
    echo -e "${YELLOW}! 既存の仮想環境が見つかりました${NC}"
    echo -n "削除して再作成しますか? (y/n): "
    read -n 1 recreate
    echo ""
    if [[ $recreate == "y" ]]; then
        rm -rf venv
        echo -e "${GREEN}✓ 既存の仮想環境を削除しました${NC}"
    else
        echo -e "${YELLOW}既存の仮想環境を使用します${NC}"
        source venv/bin/activate
        echo -e "${GREEN}✓ 仮想環境をアクティベートしました${NC}"
        pip3 list
        exit 0
    fi
fi

# 仮想環境を作成
echo -e "${YELLOW}2. 仮想環境を作成...${NC}"
python3 -m venv venv

# アクティベート
source venv/bin/activate
echo -e "${GREEN}✓ 仮想環境を作成してアクティベートしました${NC}"

# pipをアップグレード
echo -e "${YELLOW}3. pipをアップグレード...${NC}"
pip3 install --upgrade pip
echo -e "${GREEN}✓ pipをアップグレードしました${NC}"

# 必要なパッケージをインストール
echo -e "${YELLOW}4. 必要なパッケージをインストール...${NC}"

# requirements.txtが存在する場合はそれを使用
if [ -f "requirements.txt" ]; then
    echo "  Installing packages from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo -e "${YELLOW}! requirements.txtが見つかりません。個別にインストールします${NC}"
    
    # 必須パッケージ
    echo "  Installing pygame..."
    pip3 install pygame
    
    echo "  Installing requests..."
    pip3 install requests
    
    # オプションパッケージ
    echo "  Installing PyYAML..."
    pip3 install pyyaml || echo -e "${YELLOW}! PyYAMLのインストールに失敗しました${NC}"
    
    echo "  Installing Pillow..."
    pip3 install Pillow || echo -e "${YELLOW}! Pillowのインストールに失敗しました${NC}"
    
    echo "  Installing holidays..."
    pip3 install holidays || echo -e "${YELLOW}! holidaysのインストールに失敗しました${NC}"
fi

# インストール状況を確認
echo ""
echo -e "${YELLOW}5. インストール済みパッケージ:${NC}"
pip3 list | grep -E "pygame|requests|PyYAML|Pillow|holidays"

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "仮想環境の使い方:"
echo ""
echo "  アクティベート:"
echo "    source venv/bin/activate"
echo ""
echo "  無効化:"
echo "    deactivate"
echo ""
echo "PiCalendarの起動:"
echo "    source venv/bin/activate"
echo "    python3 main_x11.py"
echo ""
echo "または:"
echo "    ./quick_restart.sh  # 自動的に仮想環境を使用"
echo ""