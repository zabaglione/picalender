# PiCalendar 運用マニュアル

## 目次

1. [システム概要](#システム概要)
2. [初期セットアップ](#初期セットアップ)
3. [日常運用](#日常運用)
4. [メンテナンス](#メンテナンス)
5. [トラブルシューティング](#トラブルシューティング)
6. [パフォーマンスチューニング](#パフォーマンスチューニング)
7. [バックアップとリストア](#バックアップとリストア)
8. [セキュリティ](#セキュリティ)

## システム概要

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│              Main Application               │
├─────────────────────────────────────────────┤
│  Display Manager │ Config Manager │ Logger  │
├─────────────────────────────────────────────┤
│     Renderers    │   Weather API  │ Cache   │
├─────────────────────────────────────────────┤
│           pygame (SDL2/KMSDRM)              │
├─────────────────────────────────────────────┤
│         Raspberry Pi OS (Linux)             │
└─────────────────────────────────────────────┘
```

### 主要コンポーネント

| コンポーネント | 説明 | ファイルパス |
|---------------|------|-------------|
| Main Application | メインループとシステム制御 | `main.py` |
| Display Manager | 画面表示管理 | `src/display/display_manager.py` |
| Config Manager | 設定管理 | `src/core/config_manager.py` |
| Weather System | 天気情報取得と管理 | `src/weather/` |
| Renderers | 各要素の描画 | `src/renderers/` |
| Error Recovery | エラー復旧システム | `src/core/error_recovery.py` |
| Performance Optimizer | パフォーマンス最適化 | `src/core/performance_optimizer.py` |

## 初期セットアップ

### 1. Raspberry Pi OSの準備

```bash
# Raspberry Pi Imagerでイメージ書き込み
# 推奨: Raspberry Pi OS Lite (64-bit)

# 初回起動後の設定
sudo raspi-config
# - ネットワーク設定
# - タイムゾーン設定（Asia/Tokyo）
# - ロケール設定（ja_JP.UTF-8）
# - GPU メモリ分割（128MB推奨）
```

### 2. システムの最適化

```bash
# 不要なサービスの無効化
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable triggerhappy

# スワップの設定
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=256 に設定
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. ディスプレイの設定

```bash
# /boot/config.txt の編集
sudo nano /boot/config.txt

# 以下を追加または編集
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
dtoverlay=vc4-kms-v3d
max_framebuffers=2
```

### 4. 自動ログイン設定

```bash
# 自動ログインの有効化
sudo raspi-config
# 3 Boot Options -> B1 Desktop / CLI -> B2 Console Autologin
```

## 日常運用

### サービスの監視

```bash
# サービス状態の確認
sudo systemctl status picalender

# CPU/メモリ使用状況の確認
htop

# ログの監視
sudo journalctl -u picalender -f

# ディスク使用量の確認
df -h
```

### 定期メンテナンススケジュール

| 頻度 | タスク | コマンド/手順 |
|------|--------|--------------|
| 日次 | ログ確認 | `sudo journalctl -u picalender --since today` |
| 週次 | メモリ使用確認 | `free -h` |
| 週次 | ディスク容量確認 | `df -h` |
| 月次 | システムアップデート | `sudo apt update && sudo apt upgrade` |
| 月次 | ログローテーション | 自動（logrotate） |
| 四半期 | SDカード健全性チェック | `sudo badblocks -sv /dev/mmcblk0` |

### 設定変更手順

```bash
# 1. サービス停止
sudo systemctl stop picalender

# 2. 設定ファイル編集
nano settings.yaml

# 3. 設定検証
python3 -c "import yaml; yaml.safe_load(open('settings.yaml'))"

# 4. サービス再起動
sudo systemctl start picalender

# 5. 動作確認
sudo systemctl status picalender
```

## メンテナンス

### ログ管理

```bash
# ログローテーション設定
sudo nano /etc/logrotate.d/picalender

# 内容：
/home/pi/picalender/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
```

### キャッシュクリア

```bash
# 天気キャッシュのクリア
rm -rf cache/weather/*

# 画像キャッシュのクリア
rm -rf cache/images/*

# 全キャッシュクリア
rm -rf cache/*
```

### バックグラウンドジョブ

```bash
# cronジョブの設定
crontab -e

# 毎日午前3時にキャッシュクリア
0 3 * * * find /home/pi/picalender/cache -type f -mtime +7 -delete

# 毎週日曜日にシステム再起動
0 4 * * 0 sudo reboot
```

## トラブルシューティング

### 一般的な問題と対処法

#### 画面が真っ黒

1. ディスプレイ接続確認
```bash
tvservice -s
```

2. フレームバッファ確認
```bash
ls -l /dev/fb*
```

3. 権限確認
```bash
groups pi  # video グループに所属しているか確認
```

#### 天気が表示されない

1. ネットワーク接続確認
```bash
ping -c 4 8.8.8.8
ping -c 4 api.open-meteo.com
```

2. APIエンドポイント確認
```bash
curl -I https://api.open-meteo.com/v1/forecast
```

3. キャッシュ確認
```bash
ls -la cache/weather/
```

#### メモリ不足エラー

1. メモリ使用状況確認
```bash
free -h
ps aux --sort=-%mem | head
```

2. 品質設定を下げる
```yaml
# settings.yaml
performance:
  default_quality: ultra_low
```

3. 不要なプロセス停止
```bash
sudo systemctl stop unnecessary-service
```

#### フリーズ/応答なし

1. プロセス確認
```bash
ps aux | grep python
```

2. 強制終了と再起動
```bash
sudo systemctl restart picalender
```

3. ログ確認
```bash
sudo journalctl -u picalender -n 100
```

### エラーコード一覧

| コード | 説明 | 対処法 |
|--------|------|--------|
| E001 | 設定ファイル読み込みエラー | `settings.yaml`の構文確認 |
| E002 | ディスプレイ初期化失敗 | ディスプレイドライバ確認 |
| E003 | フォント読み込みエラー | フォントファイルの存在確認 |
| E004 | ネットワーク接続エラー | ネットワーク設定確認 |
| E005 | メモリ不足 | 品質設定を下げる |
| E006 | APIレート制限 | 更新間隔を長くする |

## パフォーマンスチューニング

### CPU使用率の最適化

```yaml
# settings.yaml - 低CPU使用設定
screen:
  fps: 10  # FPSを下げる

ui:
  update_intervals:
    clock: 1     # 1秒ごと
    date: 60     # 1分ごと
    calendar: 60 # 1分ごと
    weather: 300 # 5分ごと
```

### メモリ使用量の削減

```yaml
# settings.yaml - 低メモリ設定
performance:
  cache_size: 10  # キャッシュサイズ制限
  
character:
  enabled: false  # キャラクター無効化
  
background:
  cache_images: false  # 画像キャッシュ無効
```

### ネットワーク最適化

```yaml
# settings.yaml - ネットワーク負荷軽減
weather:
  refresh_sec: 3600  # 1時間ごと
  retry_count: 3
  timeout: 10
```

### 品質レベル別設定

| レベル | FPS | CPU使用率 | メモリ使用量 | 用途 |
|--------|-----|-----------|-------------|------|
| ultra_low | 10 | 15-20% | 100MB | 省電力・長時間稼働 |
| low | 15 | 20-30% | 150MB | 通常運用（推奨） |
| medium | 20 | 30-40% | 180MB | 滑らかな表示 |
| high | 30 | 40-50% | 220MB | 高品質表示 |

## バックアップとリストア

### 設定のバックアップ

```bash
# バックアップスクリプト
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/picalender_config_$DATE.tar.gz \
  settings.yaml \
  wallpapers/ \
  assets/sprites/

echo "Backup created: $BACKUP_DIR/picalender_config_$DATE.tar.gz"
```

### システム全体のバックアップ

```bash
# SDカードのイメージ作成
sudo dd if=/dev/mmcblk0 of=/backup/pi_backup.img bs=4M status=progress
```

### リストア手順

```bash
# 設定のリストア
tar -xzf picalender_config_20250111_120000.tar.gz

# システムイメージのリストア
sudo dd if=pi_backup.img of=/dev/mmcblk0 bs=4M status=progress
```

## セキュリティ

### 基本的なセキュリティ設定

```bash
# デフォルトパスワードの変更
passwd

# SSH設定の強化
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no （鍵認証のみにする場合）

# ファイアウォール設定
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### APIキーの管理

```bash
# 環境変数ファイル作成
nano .env

# 内容：
WEATHER_API_KEY=your_api_key_here

# 権限設定
chmod 600 .env
```

### 定期的なセキュリティアップデート

```bash
# 自動アップデートの設定
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## 監視とアラート

### システム監視スクリプト

```bash
#!/bin/bash
# monitor.sh

# CPU温度チェック
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
if (( $(echo "$TEMP > 70" | bc -l) )); then
    echo "WARNING: High temperature: $TEMP°C"
    # アラート送信処理
fi

# メモリ使用率チェック
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "WARNING: High memory usage: $MEM_USAGE%"
    # アラート送信処理
fi

# サービス状態チェック
if ! systemctl is-active --quiet picalender; then
    echo "ERROR: PiCalendar service is not running"
    sudo systemctl restart picalender
fi
```

### ログ監視

```bash
# エラーログの監視
sudo journalctl -u picalender -p err -f

# 特定のパターンを監視
sudo journalctl -u picalender -f | grep -E "ERROR|CRITICAL"
```

## 付録

### 環境変数一覧

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| SDL_VIDEODRIVER | ビデオドライバ | kmsdrm |
| PICALENDER_CONFIG | 設定ファイルパス | ./settings.yaml |
| PICALENDER_LOG_LEVEL | ログレベル | INFO |
| PICALENDER_DEBUG | デバッグモード | false |

### よく使うコマンド集

```bash
# サービス管理
sudo systemctl {start|stop|restart|status} picalender

# ログ確認
sudo journalctl -u picalender -f

# プロセス確認
ps aux | grep picalender

# リソース監視
htop

# ネットワーク確認
ip addr show
ping -c 4 google.com

# ディスク使用量
df -h
du -sh /home/pi/picalender/*

# 温度確認
vcgencmd measure_temp
```

### 関連リンク

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [pygame Documentation](https://www.pygame.org/docs/)
- [Open-Meteo API](https://open-meteo.com/en/docs)
- [systemd Manual](https://www.freedesktop.org/software/systemd/man/)

---

最終更新日: 2025年1月11日