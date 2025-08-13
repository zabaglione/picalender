# ファイル転送ガイド

## 📤 SCPでRaspberry Piに壁紙を転送する方法

### 基本的なSCPコマンド

```bash
# 単一ファイルの転送
scp your_image.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/

# 複数のJPGファイルを一括転送
scp *.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/

# ディレクトリごと転送
scp -r wallpapers/* zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/
```

### よくあるエラーと解決方法

#### 1. Permission denied エラー

**原因**: ディレクトリが存在しないか、権限がない

**解決方法**:
```bash
# まずSSHでログインしてディレクトリを作成
ssh zabaglione@192.168.0.27
mkdir -p ~/picalender/wallpapers
chmod 755 ~/picalender/wallpapers
exit

# その後SCPを実行
scp *.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/
```

#### 2. ssh_askpass エラー

**原因**: パスワード入力ができない環境

**解決方法1**: ターミナルから直接実行
```bash
# ターミナルアプリから実行（VSCodeのターミナルではなく）
scp *.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/
```

**解決方法2**: SSH鍵認証を設定
```bash
# SSH鍵を生成（まだない場合）
ssh-keygen -t rsa

# 公開鍵をRaspberry Piに転送
ssh-copy-id zabaglione@192.168.0.27
```

#### 3. ディレクトリが存在しないエラー

```bash
# SSHで先にディレクトリ作成
ssh zabaglione@192.168.0.27 "mkdir -p ~/picalender/wallpapers"

# その後転送
scp *.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/
```

## 🎯 推奨手順（確実な方法）

### 方法1: 段階的に転送

```bash
# 1. SSHでログインして準備
ssh zabaglione@192.168.0.27

# 2. ディレクトリ確認・作成
cd ~/picalender
ls -la
mkdir -p wallpapers
cd wallpapers
pwd  # /home/zabaglione/picalender/wallpapers を確認

# 3. 別のターミナルから転送
scp ~/Desktop/wallpapers/*.jpg zabaglione@192.168.0.27:/home/zabaglione/picalender/wallpapers/

# 4. 転送確認
ls -la ~/picalender/wallpapers/
```

### 方法2: Raspberry Pi側でダウンロード

GitHubから直接ダウンロードする方が簡単な場合：

```bash
# Raspberry Pi上で実行
cd ~/picalender

# 最新版を取得（壁紙も含まれる）
git pull

# サンプル壁紙を生成
python3 scripts/generate_sample_wallpapers.py

# 確認
ls wallpapers/
```

### 方法3: USB経由で転送

1. USBメモリに壁紙をコピー
2. Raspberry PiにUSBを接続
3. マウント＆コピー：

```bash
# USBをマウント（通常は自動マウント）
ls /media/zabaglione/

# 壁紙をコピー
cp /media/zabaglione/USB_NAME/*.jpg ~/picalender/wallpapers/
```

## 🌐 Web経由でダウンロード

インターネット上の画像を直接ダウンロード：

```bash
# Raspberry Pi上で実行
cd ~/picalender/wallpapers

# wgetでダウンロード
wget https://example.com/image.jpg

# curlでダウンロード
curl -O https://example.com/image.jpg
```

## 📱 転送後の確認

```bash
# 壁紙が転送されたか確認
ls -la ~/picalender/wallpapers/

# PiCalendarを再起動して確認
cd ~/picalender
./scripts/quick_restart.sh
```

## 💡 ヒント

1. **ファイル名に日本語は避ける**: 文字化けの原因になる
2. **ファイルサイズ**: 5MB以下推奨
3. **画像形式**: JPG推奨（PNG、BMPも可）
4. **解像度**: 1024×600以上推奨

## 🚨 それでもうまくいかない場合

最も簡単な解決方法：

```bash
# Raspberry Pi上でサンプル壁紙を生成
ssh zabaglione@192.168.0.27
cd ~/picalender
python3 scripts/generate_sample_wallpapers.py
ls wallpapers/  # 6つの壁紙が生成される
./scripts/quick_restart.sh
```

これでまず動作確認してから、お好みの壁紙を追加してください。