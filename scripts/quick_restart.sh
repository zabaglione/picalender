#!/bin/bash

# PiCalendar クイック再起動スクリプト（シンプル版）

echo "🔄 PiCalendarを再起動中..."

# 停止
pkill -f "python.*main" 2>/dev/null
sleep 2

# 更新
cd ~/picalender
git pull

# 仮想環境のアクティベート（存在する場合）
if [ -d "venv" ]; then
    echo "📦 仮想環境を使用..."
    source venv/bin/activate
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3"
fi

# 起動
export DISPLAY=:0
export PICALENDER_FULLSCREEN=true
$PYTHON_CMD main.py > logs/restart.log 2>&1 &

echo "✅ 完了！(PID: $!)"
echo "📝 ログ: tail -f ~/picalender/logs/restart.log"