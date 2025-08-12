# PiCalendar 再起動ガイド

## 🔄 SSH経由での再起動方法

### 現在の状態を確認

```bash
# PiCalendarのプロセスを確認
ps aux | grep -E "python.*main_x11|picalender"

# 自動起動の状態を確認
ls ~/.config/autostart/picalender.desktop
```

### 方法1: プロセスを再起動（推奨）

```bash
# 1. 現在実行中のPiCalendarを停止
pkill -f "python.*main_x11"

# 2. 最新版を取得
cd ~/picalender
git pull

# 3. 手動で再起動
python3 main_x11.py &

# または、ログを確認しながら起動
python3 main_x11.py > ~/picalender/logs/manual.log 2>&1 &
```

### 方法2: システム全体を再起動

```bash
# 1. 最新版を取得
cd ~/picalender
git pull

# 2. システムを再起動（自動起動が設定済みの場合）
sudo reboot
```

### 方法3: スクリプトを使用して再起動

```bash
# 再起動スクリプトを作成
cd ~/picalender
cat > restart.sh << 'EOF'
#!/bin/bash

echo "PiCalendarを再起動します..."

# 既存プロセスを停止
pkill -f "python.*main_x11"
sleep 2

# 最新版を取得
git pull

# 環境変数設定
export DISPLAY=:0
export PICALENDER_FULLSCREEN=true

# 再起動
echo "起動中..."
python3 main_x11.py > logs/restart.log 2>&1 &

echo "PiCalendarが再起動されました"
echo "ログ: tail -f ~/picalender/logs/restart.log"
EOF

chmod +x restart.sh

# 実行
./restart.sh
```

## 📝 ログの確認方法

```bash
# 自動起動のログ
tail -f ~/picalender/logs/autostart.log

# 手動起動のログ
tail -f ~/picalender/logs/manual.log

# エラーだけを確認
grep ERROR ~/picalender/logs/*.log
```

## 🚨 トラブルシューティング

### "cannot connect to X server"エラーの場合

```bash
# X serverの権限を許可
export DISPLAY=:0
xhost +local:

# 再実行
cd ~/picalender
python3 main_x11.py
```

### プロセスが終了しない場合

```bash
# 強制終了
pkill -9 -f "python.*main_x11"

# プロセス確認
ps aux | grep python
```

### 画面が表示されない場合

```bash
# VNCやHDMI経由で確認するか、以下のコマンドでテスト
DISPLAY=:0 python3 ~/picalender/main_x11.py
```

## 🔧 便利なエイリアス設定

`.bashrc`に以下を追加すると便利です：

```bash
echo '
# PiCalendar shortcuts
alias picalender-stop="pkill -f python.*main_x11"
alias picalender-start="cd ~/picalender && DISPLAY=:0 python3 main_x11.py > logs/manual.log 2>&1 &"
alias picalender-restart="picalender-stop && sleep 2 && picalender-start"
alias picalender-log="tail -f ~/picalender/logs/autostart.log"
alias picalender-update="cd ~/picalender && git pull"
' >> ~/.bashrc

# 設定を反映
source ~/.bashrc
```

使用例：
```bash
picalender-update  # 最新版を取得
picalender-restart # 再起動
picalender-log     # ログ確認
```

## 📱 一括更新＆再起動コマンド

最も簡単な方法：

```bash
cd ~/picalender && \
git pull && \
pkill -f "python.*main_x11" && \
sleep 2 && \
DISPLAY=:0 python3 main_x11.py > logs/restart.log 2>&1 & \
echo "✅ PiCalendarを更新して再起動しました"
```