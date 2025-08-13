# 壁紙機能ガイド

## 🖼️ 壁紙自動更新機能

PiCalendarには壁紙を自動的に切り替える機能があります。

### 機能概要

- **自動切り替え**: 5分ごとに次の壁紙に切り替え（設定可能）
- **自動スキャン**: 1分ごとに新しい壁紙をチェック
- **複数の表示モード**: fit（収める）、fill（埋める）、stretch（引き伸ばす）
- **対応形式**: JPG、PNG、BMP、GIF

## 📁 壁紙の追加方法

### 1. 壁紙ディレクトリに画像を配置

```bash
# 壁紙ディレクトリを確認
ls ~/picalender/wallpapers/

# 画像を追加
cp your_image.jpg ~/picalender/wallpapers/
```

### 2. サンプル壁紙の生成

既にサンプル壁紙が含まれています：

```bash
cd ~/picalender
python3 scripts/generate_sample_wallpapers.py
```

生成される壁紙：
- 01_morning.jpg - 朝のグラデーション
- 02_noon.jpg - 昼のグラデーション  
- 03_evening.jpg - 夕方のグラデーション
- 04_night.jpg - 夜のグラデーション
- 05_pattern_blue.jpg - 青いパターン
- 06_pattern_green.jpg - 緑のパターン

## ⚙️ 設定方法

`settings.yaml`で設定を変更できます：

```yaml
wallpaper:
  rotation_seconds: 300  # 切り替え間隔（秒）
  fit_mode: 'fill'      # 表示モード
```

### 切り替え間隔の設定

| 設定値 | 説明 |
|--------|------|
| 60 | 1分ごと |
| 300 | 5分ごと（デフォルト） |
| 600 | 10分ごと |
| 1800 | 30分ごと |
| 3600 | 1時間ごと |
| 0 | 自動切り替えなし |

### 表示モードの設定

| モード | 説明 |
|--------|------|
| fit | アスペクト比を保持して画面に収める（黒帯あり） |
| fill | アスペクト比を保持して画面を埋める（一部カット） |
| stretch | 画面サイズに引き伸ばす（歪む可能性あり） |

## 🎨 推奨画像サイズ

- **Raspberry Pi (1024×600)**: 1024×600ピクセル以上
- **フルHD (1920×1080)**: 1920×1080ピクセル以上

## 📝 使用例

### 時間帯で壁紙を変える（手動）

朝・昼・夕・夜の壁紙を用意して、時間帯ごとに雰囲気を変えることができます。

### スライドショー

お気に入りの写真を複数入れて、デジタルフォトフレームとして使用。

### 季節の壁紙

季節ごとの風景写真を入れて、季節感を演出。

## 🚨 トラブルシューティング

### 壁紙が表示されない

```bash
# 壁紙ディレクトリを確認
ls -la ~/picalender/wallpapers/

# 権限を確認
chmod 644 ~/picalender/wallpapers/*.jpg
```

### メモリ不足エラー

大きすぎる画像はメモリ不足の原因になります。推奨：
- 最大サイズ: 1920×1080
- ファイルサイズ: 5MB以下

### 切り替わらない

```bash
# ログを確認
tail -f ~/picalender/logs/restart.log | grep -i wallpaper
```

## 🎯 パフォーマンスのヒント

1. **画像の最適化**
   ```bash
   # ImageMagickで最適化（要インストール）
   convert input.jpg -resize 1024x600 -quality 85 output.jpg
   ```

2. **適切な枚数**
   - 推奨: 10枚以下
   - 最大: 50枚程度

3. **形式の選択**
   - JPG: 写真向け（ファイルサイズ小）
   - PNG: イラスト向け（透明度対応）

## 📱 Raspberry Piでの確認

```bash
# 最新版を取得して再起動
cd ~/picalender && git pull && ./scripts/quick_restart.sh
```

壁紙が自動的に切り替わることを確認してください。