# テーマ機能ガイド

## 🎨 テーマ機能について

PiCalendarのテーマ機能を使うと、表示設定を簡単に切り替えることができます。
フォントサイズ、色、壁紙設定などをまとめて変更できます。

## 📦 同梱テーマ

### 1. **default** - デフォルト
標準的な表示設定。バランスの取れた見やすい表示。

### 2. **compact** - コンパクト
小さいフォントで情報を詰めて表示。小型ディスプレイ向け。

### 3. **night** - ナイトモード
暗めの配色で夜間や暗い環境向け。目に優しい。

### 4. **colorful** - カラフル
明るく鮮やかな配色。楽しい雰囲気。

### 5. **minimal** - ミニマル
必要最小限の情報のみ。時計を大きく表示。

## 🚀 使い方

### テーマ一覧を表示

```bash
cd ~/picalender
python3 theme_manager.py list
```

### テーマを適用

```bash
# 例：ナイトモードを適用
python3 theme_manager.py apply night

# 再起動して反映
./quick_restart.sh
```

### 現在のテーマを確認

```bash
python3 theme_manager.py current
```

### 現在の設定をテーマとして保存

```bash
# カスタマイズした設定を保存
python3 theme_manager.py create my_theme -d "私のカスタムテーマ"
```

## ⚙️ テーマの内容

各テーマで設定される項目：

- **画面設定**: 解像度、FPS、フルスクリーン
- **フォントサイズ**: 時計、日付、カレンダー、天気
- **色設定**: 
  - 時計の文字色と影
  - 日付の文字色と影
  - カレンダーの背景、文字、曜日色
  - 天気の背景、文字、気温、降水確率
- **壁紙設定**: 切り替え間隔、表示モード

## 🛠️ カスタムテーマの作成

### 方法1: 既存テーマをコピーして編集

```bash
# テーマファイルをコピー
cp themes/default.yaml themes/my_custom.yaml

# 編集
nano themes/my_custom.yaml

# 適用
python3 theme_manager.py apply my_custom
```

### 方法2: 現在の設定から作成

1. settings.yamlで好みの設定に調整
2. テーマとして保存：
   ```bash
   python3 theme_manager.py create my_theme
   ```

## 📝 テーマファイルの構造

```yaml
# テーマ名と説明
name: "My Theme"
description: "カスタムテーマの説明"

# 画面設定
screen:
  width: 1024
  height: 600
  fps: 30
  fullscreen: true

# UI設定
ui:
  clock_font_px: 130
  date_font_px: 36
  calendar_font_px: 22
  weather_font_px: 20

# 色設定（RGB値）
colors:
  clock:
    text: [255, 255, 255]
    shadow: [10, 10, 20]
  # ... 他の色設定

# 壁紙設定
wallpaper:
  rotation_seconds: 300
  fit_mode: 'fill'
```

## 💡 活用例

### 時間帯による自動切り替え（手動）

朝・昼・夜でテーマを切り替える：

```bash
# 朝（6:00-）
python3 theme_manager.py apply default

# 夜（18:00-）
python3 theme_manager.py apply night
```

### 用途別テーマ

- **プレゼン用**: `colorful` - 目立つ表示
- **常設展示**: `minimal` - シンプルで飽きない
- **寝室用**: `night` - 暗めで目に優しい
- **作業机**: `compact` - 情報量重視

## 🔄 元に戻す

テーマ適用前の設定に戻す：

```bash
# バックアップから復元
cp settings.yaml.backup settings.yaml
./quick_restart.sh
```

## 🎯 おすすめの使い方

1. **まず試す**: 各テーマを試して好みを見つける
2. **カスタマイズ**: 気に入ったテーマをベースに調整
3. **保存**: カスタマイズしたら新しいテーマとして保存
4. **共有**: 良いテーマができたらGitHubで共有！

## ⚠️ 注意事項

- テーマを適用すると現在の設定は上書きされます（バックアップは自動作成）
- 天気の位置情報（緯度・経度）はデフォルトで保持されます
- `--no-keep-location`オプションで位置情報も含めて完全に切り替え可能