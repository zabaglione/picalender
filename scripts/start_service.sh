#!/bin/bash
# PiCalendarサービス起動スクリプト

# 作業ディレクトリに移動
cd /home/pi/picalender

# ログディレクトリ作成
mkdir -p logs

# 起動時刻を記録
echo "Starting PiCalendar at $(date)" >> logs/service.log

# 仮想環境が存在するか確認
if [ -d "venv" ]; then
    echo "Using virtual environment" >> logs/service.log
    source venv/bin/activate
    
    # 依存関係の確認
    python -c "import pygame; import yaml; print('Dependencies OK')" >> logs/service.log 2>&1
    if [ $? -ne 0 ]; then
        echo "Missing dependencies, installing..." >> logs/service.log
        pip install -r requirements.txt >> logs/service.log 2>&1
    fi
    
    # メインアプリケーション起動
    exec python main.py >> logs/service.log 2>&1
else
    echo "Virtual environment not found, using system Python" >> logs/service.log
    exec python3 main.py >> logs/service.log 2>&1
fi