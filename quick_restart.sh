#!/bin/bash

# PiCalendar クイック再起動スクリプト（シンプル版）

echo "🔄 PiCalendarを再起動中..."

# 停止
pkill -f "python.*main_x11" 2>/dev/null
sleep 2

# 更新
cd ~/picalender
git pull

# 起動
export DISPLAY=:0
export PICALENDER_FULLSCREEN=true
python3 main_x11.py > logs/restart.log 2>&1 &

echo "✅ 完了！(PID: $!)"
echo "📝 ログ: tail -f ~/picalender/logs/restart.log"