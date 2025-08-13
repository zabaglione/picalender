# PiCalendar インストールガイド

## 📋 前提条件

### ハードウェア
- Raspberry Pi Zero 2 W 以上
- 1024×600 解像度のディスプレイ
- microSDカード（8GB以上）
- 安定した電源供給（5V 2.5A以上推奨）
- Wi-Fi接続（天気情報取得用）

### ソフトウェア
- Raspberry Pi OS (64-bit推奨)
- Python 3.11以上
- インターネット接続

## 🚀 クイックインストール

最も簡単な方法：

```bash
# リポジトリをクローン
git clone https://github.com/zabaglione/picalender.git
cd picalender

# インストールスクリプトを実行
./scripts/install.sh
```

## 📝 詳細インストール手順

### 1. システムの準備

```bash
# システムを最新状態に更新
sudo apt update && sudo apt upgrade -y

# 基本的なパッケージをインストール
sudo apt install -y python3 python3-pip python3-venv git

# 日本語フォントをインストール
sudo apt install -y fonts-noto-cjk

# Pygameの依存関係をインストール
sudo apt install -y python3-pygame libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

### 2. アプリケーションのダウンロード

```bash
# ホームディレクトリに移動
cd ~

# GitHubからクローン
git clone https://github.com/zabaglione/picalender.git
cd picalender
```

### 3. 仮想環境のセットアップ（推奨）

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 4. 設定ファイルの準備

```bash
# サンプル設定ファイルをコピー
cp settings.example.yaml settings.yaml

# 設定を編集（任意）
nano settings.yaml
```

#### 重要な設定項目：

```yaml
# 天気情報の場所を設定（東京の例）
weather:
  location:
    lat: 35.681236    # 緯度
    lon: 139.767125   # 経度
```

### 5. 動作確認

```bash
# テスト起動（Ctrl+Cで終了）
python3 main.py

# X Window環境の場合
python3 main_x11.py
```

## 🔧 自動起動の設定

### systemdサービスとして登録

```bash
# サービスファイルをインストール
sudo ./scripts/install_service.sh

# サービスを有効化
sudo systemctl enable picalender

# サービスを開始
sudo systemctl start picalender

# 状態を確認
sudo systemctl status picalender
```

### X Window環境での自動起動

```bash
# X11用の自動起動設定
./scripts/setup_autostart_fullscreen.sh
```

## 🎨 初期設定

### 壁紙の追加

```bash
# サンプル壁紙を生成
python3 scripts/generate_sample_wallpapers.py

# 独自の壁紙を追加
cp your_image.jpg wallpapers/
```

### テーマの適用

```bash
# 利用可能なテーマを確認
python3 theme_manager.py list

# ナイトモードを適用
python3 theme_manager.py apply night

# 再起動して反映
./scripts/quick_restart.sh
```

## ⚠️ トラブルシューティング

### PEP 668エラーが出る場合

```bash
# 仮想環境を使用
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# または --break-system-packages オプションを使用（非推奨）
pip3 install -r requirements.txt --break-system-packages
```

### 画面が表示されない場合

```bash
# KMSドライバを有効化
echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
sudo reboot
```

### ALSAエラーが出る場合

音声は使用しないため、エラーは無視して構いません。

### メモリ不足の場合

```bash
# スワップサイズを増やす
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=512 に変更
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 📱 リモートアクセス

### SSH経由でファイル転送

```bash
# 壁紙を転送
scp wallpaper.jpg pi@raspberrypi.local:~/picalender/wallpapers/

# 複数ファイルを転送
scp *.jpg pi@raspberrypi.local:~/picalender/wallpapers/
```

### VNC設定（オプション）

```bash
# VNCサーバーをインストール
sudo apt install -y realvnc-vnc-server
sudo systemctl enable vncserver-x11-serviced
```

## ✅ インストール完了の確認

以下が正常に動作すれば成功です：

1. ✅ 時計が表示される
2. ✅ カレンダーが正しい曜日で表示される
3. ✅ 天気情報が取得できる（要インターネット）
4. ✅ 壁紙が表示される
5. ✅ 自動起動が設定されている

## 🆘 サポート

問題が解決しない場合：

1. ログを確認：
   ```bash
   sudo journalctl -u picalender -n 50
   tail -f ~/picalender/logs/restart.log
   ```

2. 診断スクリプトを実行：
   ```bash
   ./scripts/diagnose.sh
   ```

3. GitHubでIssueを作成：
   https://github.com/zabaglione/picalender/issues

## 📚 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [QUICK_START.md](QUICK_START.md) - クイックスタート
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - 設定ガイド
- [THEME_GUIDE.md](THEME_GUIDE.md) - テーマガイド
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - トラブルシューティング