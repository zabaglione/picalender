#!/bin/bash

# PiCalendar 再起動スクリプト
# 使い方: ./restart.sh

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ヘッダー表示
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    PiCalendar 再起動スクリプト${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 1. 現在の状態を確認
echo -e "${YELLOW}[1/5] 現在の状態を確認...${NC}"
PICALENDER_PID=$(pgrep -f "python.*main_x11")
if [ ! -z "$PICALENDER_PID" ]; then
    echo -e "${GREEN}✓ PiCalendarが実行中 (PID: $PICALENDER_PID)${NC}"
else
    echo -e "${YELLOW}! PiCalendarは実行されていません${NC}"
fi

# 2. 既存プロセスを停止
if [ ! -z "$PICALENDER_PID" ]; then
    echo -e "${YELLOW}[2/5] PiCalendarを停止...${NC}"
    pkill -f "python.*main_x11"
    sleep 2
    
    # 停止確認
    if pgrep -f "python.*main_x11" > /dev/null; then
        echo -e "${RED}✗ 停止に失敗しました。強制終了します...${NC}"
        pkill -9 -f "python.*main_x11"
        sleep 1
    fi
    echo -e "${GREEN}✓ PiCalendarを停止しました${NC}"
else
    echo -e "${YELLOW}[2/5] スキップ（停止するプロセスなし）${NC}"
fi

# 3. 最新版を取得
echo -e "${YELLOW}[3/5] 最新版を取得...${NC}"
cd ~/picalender

# Git pull の結果を確認
git_output=$(git pull 2>&1)
if echo "$git_output" | grep -q "Already up to date"; then
    echo -e "${GREEN}✓ 既に最新版です${NC}"
elif echo "$git_output" | grep -q "error"; then
    echo -e "${RED}✗ 更新エラー:${NC}"
    echo "$git_output"
    echo -e "${YELLOW}! ローカルの変更をリセットしますか? (y/n)${NC}"
    read -t 10 -n 1 reset_choice
    if [[ $reset_choice == "y" ]]; then
        echo ""
        git reset --hard origin/main
        git pull
        echo -e "${GREEN}✓ リセットして更新しました${NC}"
    fi
else
    echo -e "${GREEN}✓ 更新完了${NC}"
    echo "$git_output" | grep -E "files? changed|insertions?|deletions?" || true
fi

# 4. ログディレクトリを確認
echo -e "${YELLOW}[4/5] ログディレクトリを準備...${NC}"
mkdir -p ~/picalender/logs
LOG_FILE=~/picalender/logs/restart_$(date +%Y%m%d_%H%M%S).log
echo -e "${GREEN}✓ ログファイル: $LOG_FILE${NC}"

# 5. PiCalendarを起動
echo -e "${YELLOW}[5/5] PiCalendarを起動...${NC}"

# 仮想環境のアクティベート（存在する場合）
# 既にcd ~/picalenderしているので、カレントディレクトリをまずチェック
if [ -d "venv" ]; then
    echo -e "${YELLOW}仮想環境をアクティベート...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✓ 仮想環境をアクティベートしました${NC}"
    PYTHON_CMD="python3"
    # アクティベート確認
    which python3
elif [ -d "/home/$CURRENT_USER/picalender/venv" ]; then
    echo -e "${YELLOW}仮想環境をアクティベート（フルパス）...${NC}"
    source "/home/$CURRENT_USER/picalender/venv/bin/activate"
    echo -e "${GREEN}✓ 仮想環境をアクティベートしました${NC}"
    PYTHON_CMD="python3"
else
    echo -e "${YELLOW}! 仮想環境が見つかりません。システムPythonを使用${NC}"
    echo -e "${YELLOW}  検索パス: $(pwd)/venv${NC}"
    echo -e "${YELLOW}  検索パス: /home/$CURRENT_USER/picalender/venv${NC}"
    PYTHON_CMD="python3"
fi

# 環境変数設定
export DISPLAY=:0
export PICALENDER_FULLSCREEN=true

# 起動
nohup $PYTHON_CMD ~/picalender/main_x11.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!

# 起動確認（3秒待機）
sleep 3

if ps -p $NEW_PID > /dev/null; then
    echo -e "${GREEN}✓ PiCalendarが起動しました (PID: $NEW_PID)${NC}"
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${GREEN}✅ 再起動完了！${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "📝 ログを確認:"
    echo "   tail -f $LOG_FILE"
    echo ""
    echo "🔍 プロセス確認:"
    echo "   ps aux | grep main_x11"
    echo ""
    
    # 最初の数行のログを表示
    echo -e "${YELLOW}起動ログ（最初の10行）:${NC}"
    head -n 10 "$LOG_FILE" 2>/dev/null || echo "（ログはまだ生成されていません）"
else
    echo -e "${RED}✗ 起動に失敗しました${NC}"
    echo -e "${YELLOW}ログを確認してください:${NC}"
    echo "tail -f $LOG_FILE"
    exit 1
fi

# オプション: 自動的にログを表示
echo ""
echo -e "${YELLOW}ログをリアルタイムで表示しますか? (y/n)${NC}"
read -t 5 -n 1 show_log
if [[ $show_log == "y" ]]; then
    echo ""
    echo -e "${BLUE}ログ表示中... (Ctrl+Cで終了)${NC}"
    tail -f "$LOG_FILE"
fi