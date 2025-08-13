# PiCalendar 設定ガイド

## 📋 設定ファイルの概要

PiCalendarは`settings.yaml`ファイルで動作をカスタマイズできます。YAMLフォーマットで記述され、起動時に読み込まれます。

## 🔧 基本設定

### 画面設定 (screen)

```yaml
screen:
  width: 1024          # 画面幅（ピクセル）
  height: 600          # 画面高さ（ピクセル）
  fps: 30              # フレームレート（15-30推奨）
  fullscreen: true     # フルスクリーン表示
  hide_cursor: true    # マウスカーソルを隠す
```

**推奨設定：**
- Raspberry Pi Zero 2 W: `fps: 15`（CPU負荷軽減）
- Raspberry Pi 3/4: `fps: 30`（スムーズな表示）

### UI設定 (ui)

```yaml
ui:
  margins:
    x: 24              # 左右マージン
    y: 16              # 上下マージン
  clock_font_px: 130   # 時計のフォントサイズ
  date_font_px: 36     # 日付のフォントサイズ
  cal_font_px: 22      # カレンダーのフォントサイズ
  weather_font_px: 22  # 天気のフォントサイズ
```

**フォントサイズの目安：**
- 通常表示: 上記デフォルト値
- コンパクト表示: 各値を20-30%縮小
- 大画面: 各値を20-50%拡大

### 色設定 (colors)

```yaml
ui:
  colors:
    text: [255, 255, 255]        # 通常テキスト（白）
    sunday: [255, 100, 100]      # 日曜日（赤系）
    saturday: [100, 100, 255]    # 土曜日（青系）
    weekday: [255, 255, 255]     # 平日（白）
    background: [0, 0, 0]        # 背景（黒）
    weather_panel: [40, 40, 40]  # 天気パネル背景
    weather_panel_alpha: 200     # 天気パネル透明度（0-255）
```

**色の指定方法：**
- RGB形式: `[赤, 緑, 青]`（各値0-255）
- 透明度: `alpha`値（0=透明、255=不透明）

## 🗓️ カレンダー設定

```yaml
calendar:
  first_weekday: "SUNDAY"  # 週の始まり（SUNDAY または MONDAY）
```

## 🌤️ 天気設定

```yaml
weather:
  provider: "openmeteo"    # 天気プロバイダー
  refresh_sec: 1800        # 更新間隔（秒）= 30分
  timeout_sec: 10          # タイムアウト（秒）
  location:
    lat: 35.681236         # 緯度
    lon: 139.767125        # 経度
```

**主要都市の座標：**
- 東京: lat: 35.681236, lon: 139.767125
- 大阪: lat: 34.693725, lon: 135.502254
- 名古屋: lat: 35.181446, lon: 136.906398
- 札幌: lat: 43.064301, lon: 141.346874
- 福岡: lat: 33.590355, lon: 130.401716

**更新間隔の推奨値：**
- 通常: 1800（30分）
- 省エネ: 3600（1時間）
- 頻繁: 900（15分）

## 🖼️ 壁紙設定

```yaml
background:
  dir: "./wallpapers"      # 壁紙ディレクトリ
  mode: "fit"              # 表示モード（fit または fill）
  rescan_sec: 300          # 切替間隔（秒）= 5分
```

**表示モード：**
- `fit`: アスペクト比を保持して全体表示（レターボックス）
- `fill`: 画面全体を埋める（トリミングあり）

**切替間隔の推奨値：**
- 短い: 180（3分）
- 標準: 300（5分）
- 長い: 600（10分）
- 固定: 0（切替なし）

## 🎭 キャラクター設定（オプション）

```yaml
character:
  enabled: false           # キャラクター表示のON/OFF
  sprite: "./assets/sprites/char_idle.png"
  frame_width: 128         # フレーム幅
  frame_height: 128        # フレーム高さ
  fps: 8                   # アニメーションFPS
```

**注意：** キャラクター表示はCPU負荷が高いため、Raspberry Pi Zero 2 Wでは無効推奨

## 🔤 フォント設定

```yaml
fonts:
  main:
    path: "./assets/fonts/NotoSansCJK-Regular.otf"
    fallback: "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf"
```

**対応フォント形式：**
- TrueType (.ttf)
- OpenType (.otf)

## 📝 ログ設定

```yaml
logging:
  level: "INFO"            # ログレベル
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

**ログレベル：**
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 通常の動作情報
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージのみ

## 🎨 テーマ機能

テーマを使用すると、複数の設定を一括で切り替えられます。

### テーマの適用

```bash
# 利用可能なテーマを表示
python3 theme_manager.py list

# テーマを適用
python3 theme_manager.py apply night

# 現在のテーマを確認
python3 theme_manager.py current
```

### プリセットテーマ

1. **default** - 標準設定
2. **compact** - 小型画面向け
3. **night** - 夜間モード
4. **colorful** - カラフル表示
5. **minimal** - 最小限表示

### カスタムテーマの作成

```bash
# 現在の設定をテーマとして保存
python3 theme_manager.py create my_theme -d "説明文"
```

## ⚡ パフォーマンス最適化

### Raspberry Pi Zero 2 W向け

```yaml
# 低負荷設定
screen:
  fps: 15                  # FPSを下げる

weather:
  refresh_sec: 3600        # 更新頻度を下げる

background:
  rescan_sec: 600          # 切替頻度を下げる

character:
  enabled: false           # キャラクターを無効化
```

### メモリ節約設定

```yaml
# キャッシュを制限
cache:
  max_items: 10
  max_memory_mb: 50
```

## 🔄 設定の反映

設定変更後は再起動が必要です：

```bash
# クイック再起動
./quick_restart.sh

# または手動で
pkill -f main.py
python3 main.py
```

## 💡 設定のヒント

### 場所に応じた設定

**リビング・居間**
- 明るく大きな表示
- 頻繁な壁紙切替
- カラフルテーマ

**寝室**
- 暗めの表示
- 低FPS（省電力）
- ナイトテーマ

**オフィス・作業場**
- コンパクト表示
- 情報重視
- ミニマルテーマ

### 時間帯による調整

朝・昼・夜で異なるテーマを使い分けることも可能です（手動切替）。

## 📋 設定のバックアップ

```bash
# バックアップ作成
cp settings.yaml settings.yaml.backup

# バックアップから復元
cp settings.yaml.backup settings.yaml
```

## ❓ よくある質問

**Q: 設定が反映されない**
A: アプリケーションの再起動が必要です。`./quick_restart.sh`を実行してください。

**Q: YAMLエラーが出る**
A: インデント（スペース）が正しいか確認してください。タブは使用できません。

**Q: デフォルトに戻したい**
A: `cp settings.example.yaml settings.yaml`でサンプル設定に戻せます。

## 📚 関連ドキュメント

- [THEME_GUIDE.md](THEME_GUIDE.md) - テーマ機能の詳細
- [WALLPAPER_GUIDE.md](WALLPAPER_GUIDE.md) - 壁紙設定の詳細
- [WEATHER_SETUP.md](WEATHER_SETUP.md) - 天気設定の詳細