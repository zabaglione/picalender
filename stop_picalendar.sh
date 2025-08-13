#!/bin/bash

# PiCalendar 緊急停止スクリプト

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PiCalendarを停止しています...${NC}"

# 実行中のプロセスを確認
PIDS=$(pgrep -f "python.*main")
if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}PiCalendarは実行されていません${NC}"
    exit 0
fi

echo -e "${GREEN}実行中のプロセス:${NC}"
ps aux | grep -E "python.*main" | grep -v grep

echo ""
echo -e "${YELLOW}プロセスを終了します...${NC}"

# 段階的に停止
echo "1. 通常終了シグナル (SIGTERM) を送信..."
pkill -f "python.*main"
sleep 3

# まだ実行中か確認
if pgrep -f "python.*main" > /dev/null; then
    echo "2. 強制終了シグナル (SIGKILL) を送信..."
    pkill -9 -f "python.*main"
    sleep 2
fi

# 最終確認
if pgrep -f "python.*main" > /dev/null; then
    echo -e "${RED}✗ プロセスがまだ実行中です${NC}"
    echo ""
    echo "手動で以下のコマンドを実行してください："
    echo -e "${YELLOW}  sudo pkill -9 -f 'python.*main'${NC}"
    echo ""
    echo "または個別にPIDを指定して停止："
    pgrep -f "python.*main" | while read pid; do
        echo -e "${YELLOW}  sudo kill -9 $pid${NC}"
    done
    exit 1
else
    echo -e "${GREEN}✓ PiCalendarを停止しました${NC}"
fi