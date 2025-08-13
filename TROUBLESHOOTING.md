# PiCalendar トラブルシューティングガイド

## 🚨 よくある問題と解決方法

### 起動関連の問題

#### 画面に何も表示されない

**症状：** アプリケーションは起動しているが、画面が真っ黒

**解決方法：**

1. ディスプレイドライバを確認：
```bash
# フレームバッファデバイスを確認
ls /dev/fb*

# KMSドライバを有効化
echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
sudo reboot
```

2. X Window環境で実行：
```bash
# X11版を使用
python3 main_x11.py
```

3. ログを確認：
```bash
tail -f ~/picalender/logs/restart.log
sudo journalctl -u picalender -n 50
```

#### PEP 668エラー

**症状：** `error: externally-managed-environment`

**解決方法：**

```bash
# 仮想環境を使用（推奨）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# または、システムパッケージを使用
sudo apt install -y python3-pygame python3-yaml python3-requests python3-pillow
```

#### ModuleNotFoundError

**症状：** `No module named 'pygame'` など

**解決方法：**

```bash
# 仮想環境を確認
which python3

# 仮想環境を有効化し忘れていないか確認
source venv/bin/activate

# 依存関係を再インストール
pip install -r requirements.txt
```

### 表示関連の問題

#### 時計がズレる・ちらつく

**症状：** 秒が更新されるたびに時計全体が左右に動く

**解決方法：**

最新版では固定位置描画で解決済み。更新してください：
```bash
git pull
./quick_restart.sh
```

#### 文字が重なって表示される

**症状：** 天気情報の気温と降水確率が重なる

**解決方法：**

設定ファイルでフォントサイズを調整：
```yaml
ui:
  weather_font_px: 18  # 小さくする
```

#### カレンダーの曜日がずれている

**症状：** 日付と曜日が一致しない

**解決方法：**

1. システム時刻を確認：
```bash
date
```

2. NTPで時刻を同期：
```bash
sudo timedatectl set-ntp true
```

3. タイムゾーンを設定：
```bash
sudo timedatectl set-timezone Asia/Tokyo
```

### 天気関連の問題

#### 天気が取得できない

**症状：** 天気欄に「取得不可」と表示される

**解決方法：**

1. ネットワーク接続を確認：
```bash
ping -c 4 api.open-meteo.com
```

2. DNS設定を確認：
```bash
cat /etc/resolv.conf
# nameserverが正しく設定されているか確認
```

3. プロキシ設定が必要な場合：
```bash
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080
```

#### 天気アイコンが「?」で表示される

**症状：** 天気アイコンが正しく表示されない

**解決方法：**

アイコンファイルを確認：
```bash
ls ~/picalender/assets/icons/weather/
# sunny_48.png, cloudy_48.png などが存在するか確認
```

存在しない場合は生成：
```bash
python3 scripts/generate_weather_icons.py
```

### パフォーマンス関連の問題

#### CPU使用率が高い

**症状：** topコマンドでCPU使用率が50%以上

**解決方法：**

1. FPSを下げる：
```yaml
screen:
  fps: 15  # 30から15に変更
```

2. キャラクター表示を無効化：
```yaml
character:
  enabled: false
```

3. 壁紙切替を遅くする：
```yaml
background:
  rescan_sec: 600  # 10分に変更
```

#### メモリ不足

**症状：** `MemoryError`やシステムが重い

**解決方法：**

1. スワップを増やす：
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=512 に変更
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

2. 不要なサービスを停止：
```bash
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

### 音声関連の問題

#### ALSAエラーが表示される

**症状：** `ALSA lib pcm.c:8568:(snd_pcm_recover) underrun occurred`

**解決方法：**

音声は使用しないため、エラーは無視して構いません。
最新版では音声が無効化されています。

### 自動起動の問題

#### 起動時に自動実行されない

**症状：** 再起動してもPiCalendarが起動しない

**解決方法：**

1. サービス状態を確認：
```bash
sudo systemctl status picalender
```

2. サービスを有効化：
```bash
sudo systemctl enable picalender
sudo systemctl start picalender
```

3. ログを確認：
```bash
sudo journalctl -u picalender -b
```

#### サービスが繰り返し再起動する

**症状：** `Start request repeated too quickly`

**解決方法：**

1. 設定ファイルのエラーを確認：
```bash
python3 -c "import yaml; yaml.safe_load(open('settings.yaml'))"
```

2. 依存関係を確認：
```bash
source venv/bin/activate
python3 -c "import pygame, yaml, requests"
```

### 壁紙関連の問題

#### 壁紙が表示されない

**症状：** 背景が黒いまま

**解決方法：**

1. 壁紙ディレクトリを確認：
```bash
ls ~/picalender/wallpapers/
```

2. サンプル壁紙を生成：
```bash
python3 scripts/generate_sample_wallpapers.py
```

#### 壁紙が切り替わらない

**症状：** 同じ壁紙が表示され続ける

**解決方法：**

設定を確認：
```yaml
background:
  rescan_sec: 300  # 0だと切り替わらない
```

### その他の問題

#### YAMLエラー

**症状：** `yaml.scanner.ScannerError`

**解決方法：**

1. インデントを確認（スペースのみ使用、タブ禁止）
2. コロンの後にスペースが必要
3. 文字列に特殊文字がある場合は引用符で囲む

#### 設定が反映されない

**症状：** settings.yamlを変更しても変わらない

**解決方法：**

アプリケーションを再起動：
```bash
./quick_restart.sh
```

## 🔍 診断ツール

### システム診断スクリプト

```bash
# 診断スクリプトを実行
./diagnose.sh
```

### 手動診断コマンド

```bash
# Python環境確認
python3 --version
pip list

# ディスプレイ確認
echo $DISPLAY
xrandr

# ネットワーク確認
ip addr
ping -c 1 google.com

# システムリソース確認
free -h
df -h
top
```

## 📝 ログファイルの場所

- アプリケーションログ: `~/picalender/logs/restart.log`
- systemdログ: `sudo journalctl -u picalender`
- Xorgログ: `/var/log/Xorg.0.log`

## 🆘 それでも解決しない場合

1. **最新版に更新**
```bash
cd ~/picalender
git pull
pip install -r requirements.txt --upgrade
```

2. **クリーンインストール**
```bash
cd ~
mv picalender picalender.bak
git clone https://github.com/zabaglione/picalender.git
cd picalender
./install.sh
```

3. **Issueを作成**

GitHubで問題を報告：
https://github.com/zabaglione/picalender/issues

以下の情報を含めてください：
- Raspberry Piのモデル
- OSバージョン（`cat /etc/os-release`）
- Pythonバージョン（`python3 --version`）
- エラーメッセージ全文
- `diagnose.sh`の出力

## 💡 予防的メンテナンス

### 定期的な更新

```bash
# 月1回程度実行
cd ~/picalender
git pull
pip install -r requirements.txt --upgrade
```

### バックアップ

```bash
# 設定のバックアップ
cp settings.yaml settings.yaml.$(date +%Y%m%d)
```

### システムの健全性チェック

```bash
# ディスク容量確認
df -h

# メモリ使用状況
free -h

# ログサイズ確認
du -sh /var/log/*
```

## 📚 関連ドキュメント

- [INSTALL_GUIDE.md](INSTALL_GUIDE.md) - インストール手順
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - 設定方法
- [QUICK_START.md](QUICK_START.md) - クイックスタート
- [README.md](README.md) - プロジェクト概要