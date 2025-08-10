# PiCalendar systemdサービス設定

このディレクトリには、PiCalendarをRaspberry Piで自動起動するためのsystemdサービス設定とセットアップスクリプトが含まれています。

## ファイル一覧

| ファイル | 説明 |
|---------|------|
| `picalender.service` | systemdサービス定義ファイル |
| `install_service.sh` | サービスインストールスクリプト |
| `uninstall_service.sh` | サービスアンインストールスクリプト |
| `setup_display.sh` | ディスプレイ設定スクリプト（1024x600用） |
| `check_system.sh` | システム診断スクリプト |

## セットアップ手順

### 1. システム診断

まず、システムの状態を確認します：

```bash
cd /home/pi/picalender/scripts
chmod +x check_system.sh
./check_system.sh
```

### 2. ディスプレイ設定

1024x600のディスプレイを使用する場合：

```bash
sudo chmod +x setup_display.sh
sudo ./setup_display.sh
sudo reboot
```

### 3. サービスインストール

システムが正常に設定されていることを確認後：

```bash
sudo chmod +x install_service.sh
sudo ./install_service.sh
```

### 4. サービス起動

```bash
# サービス開始
sudo systemctl start picalender

# ステータス確認
sudo systemctl status picalender

# ログ確認（リアルタイム）
sudo journalctl -u picalender -f
```

## サービス管理コマンド

### 基本操作

```bash
# サービス開始
sudo systemctl start picalender

# サービス停止
sudo systemctl stop picalender

# サービス再起動
sudo systemctl restart picalender

# ステータス確認
sudo systemctl status picalender
```

### 自動起動設定

```bash
# 自動起動有効化（インストール時に設定済み）
sudo systemctl enable picalender

# 自動起動無効化
sudo systemctl disable picalender
```

### ログ確認

```bash
# 最新のログを表示
sudo journalctl -u picalender -n 50

# リアルタイムでログを監視
sudo journalctl -u picalender -f

# 特定期間のログを表示
sudo journalctl -u picalender --since "1 hour ago"
sudo journalctl -u picalender --since today
```

## トラブルシューティング

### サービスが起動しない場合

1. システム診断を実行：
   ```bash
   ./check_system.sh
   ```

2. 詳細なログを確認：
   ```bash
   sudo journalctl -u picalender -n 100 --no-pager
   ```

3. 手動で起動してエラーを確認：
   ```bash
   cd /home/pi/picalender
   SDL_VIDEODRIVER=kmsdrm python3 main.py
   ```

### ディスプレイが表示されない場合

1. HDMI接続を確認：
   ```bash
   tvservice -s
   ```

2. フレームバッファを確認：
   ```bash
   ls -la /dev/fb*
   cat /sys/class/graphics/fb0/virtual_size
   ```

3. SDL環境変数を確認：
   ```bash
   echo $SDL_VIDEODRIVER
   echo $SDL_FBDEV
   ```

### パフォーマンス問題

1. CPU使用率を確認：
   ```bash
   top -p $(pgrep -f "python3.*main.py")
   ```

2. メモリ使用量を確認：
   ```bash
   free -h
   ```

3. サービスのリソース制限を調整（必要に応じて）：
   ```bash
   sudo nano /etc/systemd/system/picalender.service
   # MemoryMaxとCPUQuotaの値を調整
   sudo systemctl daemon-reload
   sudo systemctl restart picalender
   ```

## アンインストール

サービスを完全に削除する場合：

```bash
sudo chmod +x uninstall_service.sh
sudo ./uninstall_service.sh
```

アプリケーションファイルも削除する場合（注意！）：

```bash
sudo rm -rf /home/pi/picalender
```

## 設定のカスタマイズ

### サービス設定の変更

`picalender.service`を編集して、以下の設定を調整できます：

- `User`: 実行ユーザー（デフォルト: pi）
- `WorkingDirectory`: アプリケーションディレクトリ
- `Environment`: 環境変数
- `RestartSec`: 再起動間隔
- `MemoryMax`: メモリ上限
- `CPUQuota`: CPU使用率上限

変更後は必ず以下を実行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart picalender
```

### ディスプレイ設定の変更

異なる解像度のディスプレイを使用する場合は、`/boot/config.txt`を編集：

```bash
sudo nano /boot/config.txt
# hdmi_cvtの値を変更
# 例: 800x480の場合
# hdmi_cvt=800 480 60 3 0 0 0
```

## よくある質問

### Q: 起動時に自動的に全画面表示にならない

A: SDL_VIDEODRIVERがkmsdrmに設定されていることを確認してください。サービスファイルで設定されています。

### Q: 天気情報が表示されない

A: インターネット接続を確認し、Open-Meteo APIへのアクセスをテストしてください：

```bash
curl "https://api.open-meteo.com/v1/forecast?latitude=35.681&longitude=139.767&current_weather=true"
```

### Q: フォントが表示されない/文字化けする

A: 日本語フォントがインストールされているか確認：

```bash
fc-list | grep -i noto
```

インストールされていない場合：

```bash
sudo apt-get install fonts-noto-cjk
```

## サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. `check_system.sh`の出力
2. `sudo journalctl -u picalender -n 100`の出力
3. `settings.yaml`の内容（APIキーは除く）
4. 使用しているディスプレイの型番