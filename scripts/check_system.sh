#!/bin/bash

# システム診断スクリプト

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== PiCalendar システム診断 ===${NC}"
echo

# システム情報
echo -e "${YELLOW}[システム情報]${NC}"
echo "ホスト名: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "カーネル: $(uname -r)"
echo "アーキテクチャ: $(uname -m)"
echo

# ハードウェア情報
echo -e "${YELLOW}[ハードウェア情報]${NC}"
echo "モデル: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
echo "CPU: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "メモリ: $(free -h | awk 'NR==2{print $2}') (合計) / $(free -h | awk 'NR==2{print $3}') (使用中)"
echo "ディスク: $(df -h / | awk 'NR==2{print $2}') (合計) / $(df -h / | awk 'NR==2{print $3}') (使用中)"
echo

# ディスプレイ情報
echo -e "${YELLOW}[ディスプレイ情報]${NC}"
if command -v tvservice &> /dev/null; then
    echo "HDMI状態: $(tvservice -s 2>/dev/null || echo 'tvservice not available')"
else
    echo "HDMI状態: tvservice コマンドが利用できません"
fi

if [ -f /sys/class/graphics/fb0/virtual_size ]; then
    echo "フレームバッファ: $(cat /sys/class/graphics/fb0/virtual_size)"
else
    echo "フレームバッファ: 情報を取得できません"
fi
echo

# Python環境
echo -e "${YELLOW}[Python環境]${NC}"
echo "Python: $(python3 --version 2>&1)"
echo "pip: $(pip3 --version 2>&1 | cut -d' ' -f2)"

# 必要なPythonパッケージのチェック
echo "必要なパッケージ:"
for package in pygame pyyaml requests pillow; do
    if pip3 show $package &> /dev/null; then
        version=$(pip3 show $package | grep Version | cut -d' ' -f2)
        echo -e "  $package: ${GREEN}✓${NC} (v$version)"
    else
        echo -e "  $package: ${RED}✗${NC} (未インストール)"
    fi
done
echo

# SDL環境
echo -e "${YELLOW}[SDL環境]${NC}"
if command -v sdl2-config &> /dev/null; then
    echo "SDL2: $(sdl2-config --version)"
else
    echo "SDL2: sdl2-config が見つかりません"
fi

# SDL環境変数
echo "SDL_VIDEODRIVER: ${SDL_VIDEODRIVER:-未設定}"
echo "SDL_FBDEV: ${SDL_FBDEV:-未設定}"
echo

# systemdサービス状態
echo -e "${YELLOW}[systemdサービス]${NC}"
SERVICE_NAME="picalender"
if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "サービス登録: ${GREEN}✓${NC}"
    
    # サービス状態
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "サービス状態: ${GREEN}稼働中${NC}"
    else
        echo -e "サービス状態: ${YELLOW}停止中${NC}"
    fi
    
    # 自動起動設定
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        echo -e "自動起動: ${GREEN}有効${NC}"
    else
        echo -e "自動起動: ${YELLOW}無効${NC}"
    fi
else
    echo -e "サービス登録: ${RED}未登録${NC}"
fi
echo

# アプリケーションファイル
echo -e "${YELLOW}[アプリケーションファイル]${NC}"
APP_DIR="/home/pi/picalender"
if [ -d "$APP_DIR" ]; then
    echo -e "アプリケーションディレクトリ: ${GREEN}✓${NC}"
    
    # 重要ファイルのチェック
    for file in main.py settings.yaml; do
        if [ -f "$APP_DIR/$file" ]; then
            echo -e "  $file: ${GREEN}✓${NC}"
        else
            echo -e "  $file: ${RED}✗${NC}"
        fi
    done
    
    # ディレクトリ構造
    for dir in src assets wallpapers logs cache; do
        if [ -d "$APP_DIR/$dir" ]; then
            echo -e "  $dir/: ${GREEN}✓${NC}"
        else
            echo -e "  $dir/: ${YELLOW}✗${NC} (作成が必要)"
        fi
    done
else
    echo -e "アプリケーションディレクトリ: ${RED}✗${NC} ($APP_DIR が存在しません)"
fi
echo

# ネットワーク状態
echo -e "${YELLOW}[ネットワーク]${NC}"
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    echo -e "インターネット接続: ${GREEN}✓${NC}"
    
    # Open-Meteo APIテスト
    if curl -s --max-time 5 "https://api.open-meteo.com/v1/forecast?latitude=35.681&longitude=139.767&current_weather=true" &> /dev/null; then
        echo -e "Open-Meteo API: ${GREEN}✓${NC}"
    else
        echo -e "Open-Meteo API: ${RED}✗${NC} (接続できません)"
    fi
else
    echo -e "インターネット接続: ${RED}✗${NC}"
fi
echo

# 推奨事項
echo -e "${BLUE}=== 診断結果 ===${NC}"

# 問題の検出と推奨事項
problems=0

# Pythonパッケージチェック
for package in pygame pyyaml requests pillow; do
    if ! pip3 show $package &> /dev/null; then
        echo -e "${YELLOW}推奨:${NC} $package をインストールしてください: pip3 install $package"
        ((problems++))
    fi
done

# SDL2チェック
if ! command -v sdl2-config &> /dev/null; then
    echo -e "${YELLOW}推奨:${NC} SDL2をインストールしてください: sudo apt-get install libsdl2-dev"
    ((problems++))
fi

# サービスチェック
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo -e "${YELLOW}推奨:${NC} systemdサービスをインストールしてください: sudo ./scripts/install_service.sh"
    ((problems++))
fi

# アプリケーションディレクトリチェック
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}エラー:${NC} アプリケーションを /home/pi/picalender にインストールしてください"
    ((problems++))
fi

if [ $problems -eq 0 ]; then
    echo -e "${GREEN}システムは正常に設定されています！${NC}"
else
    echo -e "${YELLOW}$problems 個の問題が見つかりました。上記の推奨事項を確認してください。${NC}"
fi