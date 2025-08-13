# settings.yaml 機能状況

## ✅ 実装済みの設定項目

### screen（画面設定）
- ✅ `width`: 画面幅（デフォルト: 1024）
- ✅ `height`: 画面高さ（デフォルト: 600）
- ✅ `fps`: フレームレート（デフォルト: 30）
- ✅ `fullscreen`: フルスクリーン表示（デフォルト: true）

### ui（UI設定）
- ✅ `clock_font_px`: 時計のフォントサイズ（デフォルト: 130）
- ✅ `date_font_px`: 日付のフォントサイズ（デフォルト: 36）
- ✅ `calendar_font_px`: カレンダーのフォントサイズ（デフォルト: 22）
- ✅ `weather_font_px`: 天気のフォントサイズ（デフォルト: 20）
- ❌ `margins.x`: 左右マージン（未実装）
- ❌ `margins.y`: 上下マージン（未実装）

### wallpaper（壁紙設定）
- ✅ `rotation_seconds`: 切り替え間隔（デフォルト: 300秒）
- ✅ `fit_mode`: 表示モード（fit/fill/stretch、デフォルト: fill）
- ❌ `directory`: 壁紙ディレクトリ（ハードコード: ./wallpapers）

### weather（天気設定）
- ✅ `location.lat`: 緯度（デフォルト: 35.681236 東京）
- ✅ `location.lon`: 経度（デフォルト: 139.767125 東京）
- ✅ `refresh_sec`: 更新間隔（デフォルト: 1800秒）
- ❌ `provider`: プロバイダ選択（ハードコード: openmeteo）
- ❌ `cache.*`: キャッシュ設定（自動管理）

### その他の未実装項目
- ❌ `calendar.first_weekday`: 週の始まり（ハードコード: SUNDAY）
- ❌ `character.*`: キャラクター表示（未実装）
- ❌ `fonts.*`: フォント設定（システムフォント使用）
- ❌ `logging.*`: ログ設定（標準出力のみ）
- ❌ `performance.*`: パフォーマンス設定（未実装）
- ❌ `error_recovery.*`: エラーリカバリ（未実装）

## 📝 settings.yaml の使い方

### 1. サンプルファイルをコピー

```bash
cd ~/picalender
cp settings.example.yaml settings.yaml
```

### 2. 設定を編集

```bash
nano settings.yaml
```

### 3. よく使う設定例

#### 地域を変更（天気予報）

```yaml
weather:
  location:
    lat: 34.693725   # 大阪の緯度
    lon: 135.502254  # 大阪の経度
```

#### フォントサイズ調整

```yaml
ui:
  clock_font_px: 100      # 時計を小さく
  date_font_px: 30        # 日付を小さく
  calendar_font_px: 18    # カレンダーを小さく
  weather_font_px: 18     # 天気を小さく
```

#### 壁紙の切り替え速度

```yaml
wallpaper:
  rotation_seconds: 60    # 1分ごとに切り替え
  fit_mode: 'fit'        # アスペクト比保持（黒帯あり）
```

#### フルスクリーン無効化

```yaml
screen:
  fullscreen: false       # ウィンドウモード
```

## 🔄 設定反映方法

設定を変更したら、PiCalendarを再起動：

```bash
cd ~/picalender
./scripts/quick_restart.sh
```

## ⚠️ 注意事項

1. **YAMLの構文に注意**
   - インデントはスペース2個または4個で統一
   - コロン（:）の後にスペースが必要
   - 文字列は引用符で囲む（省略可能な場合もある）

2. **無効な設定は無視される**
   - 認識されない設定項目は無視されます
   - エラーがあるとデフォルト設定が使用されます

3. **優先順位**
   1. 環境変数（PICALENDER_FULLSCREEN など）
   2. settings.yaml
   3. デフォルト値

## 🎯 今後の実装予定

優先度の高い順：

1. **フォント設定**: カスタムフォントのパス指定
2. **カレンダー設定**: 月曜始まりオプション
3. **ログ設定**: ファイル出力とローテーション
4. **マージン設定**: UI要素の配置調整
5. **パフォーマンス設定**: 自動品質調整

## 📱 設定テンプレート（最小限）

必要最小限の設定だけを含むシンプルな例：

```yaml
# 場所の設定（天気予報用）
weather:
  location:
    lat: 35.681236    # あなたの地域の緯度
    lon: 139.767125   # あなたの地域の経度

# 壁紙の設定
wallpaper:
  rotation_seconds: 300  # 5分ごと
  fit_mode: 'fill'      # 画面を埋める
```