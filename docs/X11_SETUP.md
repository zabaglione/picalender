# PiCalendar - X Window環境での設定

## X Windowが起動している場合の対処法

Raspberry Pi OSでデスクトップ環境（X Window）が起動している場合、通常のKMSDRMモードでは表示されません。
この場合はX11モードで実行する必要があります。

## 確認方法

X Windowが起動しているか確認：

```bash
# プロセス確認
ps aux | grep -E "Xorg|lightdm|lxde"

# または環境変数確認
echo $DISPLAY
```

`DISPLAY=:0`などが表示される場合、X Windowが起動しています。

## X Window環境での実行方法

### 方法1: 手動実行（推奨）

```bash
# スクリプトを使用
cd ~/picalender
./scripts/run_on_x11.sh

# または直接実行
cd ~/picalender
python3 main_x11.py
```

### 方法2: SSH経由での実行

SSH経由で実行する場合は、DISPLAYを指定：

```bash
# SSH接続後
export DISPLAY=:0
cd ~/picalender
python3 main_x11.py
```

### 方法3: 自動起動設定

X Window起動時に自動的にPiCalendarを起動：

```bash
# 自動起動設定
cd ~/picalender
./scripts/autostart_x11.sh

# 設定後、再起動またはログアウト→ログイン
```

## systemdサービスとの関係

- **X Windowあり**: systemdサービスは機能しません。X11版を使用してください
- **X Windowなし（コンソール）**: systemdサービスが正常に動作します

現在のサービス状態を確認：

```bash
# サービス状態確認
sudo systemctl status picalender

# X Window環境では停止推奨
sudo systemctl stop picalender
sudo systemctl disable picalender
```

## 操作方法

X11版での操作：

- **ESC / Q**: アプリケーション終了
- **F11 / F**: フルスクリーン切り替え
- **Alt+F4**: ウィンドウを閉じる（ウィンドウモード時）

## トラブルシューティング

### 画面が表示されない

```bash
# X11権限を許可
xhost +local:

# 環境変数を設定して実行
DISPLAY=:0 python3 ~/picalender/main_x11.py
```

### パフォーマンスが低い

X Window環境では描画性能が低下する場合があります：

1. 他のアプリケーションを終了
2. ウィンドウモードで実行（フルスクリーンより軽い場合がある）
3. FPSを下げる（設定ファイルで調整）

### エラー: "cannot connect to X server"

```bash
# X serverが起動しているか確認
ps aux | grep Xorg

# startxで手動起動（コンソールから）
startx
```

## コンソールモードへの切り替え

X Windowを無効にしてコンソールモードで起動したい場合：

```bash
# raspi-configで設定
sudo raspi-config
# → 1 System Options
# → S5 Boot / Auto Login
# → B2 Console Autologin

# 再起動
sudo reboot

# その後、systemdサービスを有効化
sudo systemctl enable picalender
sudo systemctl start picalender
```

## 推奨環境

最高のパフォーマンスを得るには：

1. **コンソールモード** + **systemdサービス**（最速）
2. **X Window** + **X11版手動起動**（GUI環境が必要な場合）

用途に応じて選択してください。