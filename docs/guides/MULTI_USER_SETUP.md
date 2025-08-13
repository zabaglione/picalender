# 複数ユーザー環境でのPiCalendarセットアップ

PiCalendarは標準の`pi`ユーザー以外でも動作します。

## 任意のユーザーでのセットアップ手順

### 1. アプリケーションのクローン

```bash
# 任意のユーザーでログイン（例: zabaglione）
cd ~
git clone https://github.com/zabaglione/picalender.git
cd picalender
```

### 2. 依存関係のインストール

```bash
# 通常のインストール手順
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-pygame fonts-noto-cjk git
pip3 install -r requirements.txt
```

### 3. systemdサービスのインストール（任意のユーザー対応）

```bash
# 自動的に現在のユーザーを検出してサービスファイルを生成
sudo ./scripts/install_service.sh
```

このスクリプトは：
- `sudo`で実行された場合、元のユーザー（`$SUDO_USER`）を検出
- 直接rootで実行された場合、ユーザー名の入力を求める
- サービスファイルを自動的にカスタマイズ

### 4. 実行確認

```bash
# 手動実行でテスト
python3 main.py

# サービス起動でテスト
sudo systemctl start picalender
sudo systemctl status picalender
```

## 生成されるサービスファイル

`install_service.sh`実行後、以下の内容で`/etc/systemd/system/picalender.service`が生成されます：

```ini
[Unit]
Description=PiCalendar Clock Kiosk (pygame KMSDRM)
After=multi-user.target network.target

[Service]
Type=simple
User=zabaglione          # ← 実際のユーザー名に置換
Group=zabaglione         # ← 実際のユーザー名に置換
WorkingDirectory=/home/zabaglione/picalender  # ← 実際のパスに置換
Environment="SDL_VIDEODRIVER=kmsdrm"
ExecStart=/usr/bin/python3 /home/zabaglione/picalender/main.py  # ← 実際のパスに置換
Restart=always

[Install]
WantedBy=multi-user.target
```

## 注意点

### ユーザー権限
- PiCalendarは通常ユーザーで実行されます
- KMSDRMを使用する場合、ユーザーが`video`グループに所属している必要があります：

```bash
# 現在のユーザーをvideoグループに追加
sudo usermod -a -G video $USER
# ログアウト・ログインで反映
```

### ホームディレクトリの場所
- `/home/username/picalender`が標準パス
- 異なる場所にインストールした場合、手動でサービスファイルを編集

### 複数ユーザーでの同時実行
- 同じRaspberry Pi上で複数ユーザーがPiCalendarを同時実行することは想定されていません
- ディスプレイとGPUリソースが競合する可能性があります

## トラブルシューティング

### サービスファイル確認
```bash
# 生成されたサービスファイルの内容確認
sudo systemctl cat picalender

# サービス状態の確認
sudo systemctl status picalender
```

### ログ確認
```bash
# systemdログ
sudo journalctl -u picalender -f

# アプリケーションログ
tail -f ~/picalender/logs/restart_*.log
```

### 権限問題の解決
```bash
# ファイル権限を現在のユーザーに設定
sudo chown -R $USER:$USER ~/picalender

# video群への追加確認
groups $USER | grep video
```