# settings.yaml の対応状況

2026-10-01に `main.py` と使用中のレンダラーを照合しました。モジュールが存在することと、現在の起動経路で設定が使われることを区別します。設定は起動時に読み込み、変更後に再起動が必要です。

| 設定 | Field Notes（標準） | classic（旧画面） |
| --- | --- | --- |
| `ui.style` | `field_notes` | `classic` |
| `screen.width` / `height` | ウィンドウ寸法。1024×600基準の画面を縦横比保持で拡縮 | 各描画寸法に使用 |
| `screen.fps` / `fullscreen` | 対応。サンプルは5fps | 対応 |
| `weather.location.lat` / `lon` | 天気と日月の出入に使用 | 天気に使用 |
| `weather.timezone` | 時刻・月切替・天気に使用。既定 `Asia/Tokyo` | 使用しない。OS時刻を使用 |
| `weather.refresh_sec` | 対応。既定1800秒、最低60秒 | 設定を読まず取得側で固定 |
| `weather.provider` / `timeout_sec` | 選択・調整には使用しない | 選択・調整には使用しない |
| `calendar.first_weekday` | `SUNDAY` / `MONDAY` | 日曜固定 |
| `calendar.holidays_enabled` / `holidays_country` / `show_holiday_names` | 対応 | 対応 |
| `calendar.rokuyou_enabled` / `show_rokuyou_names` | 対応 | 対応 |
| `calendar.rokuyou_format` | 常に六曜名を表示。形式設定は使用しない | 対応 |
| `calendar.moon_phase_enabled` | 対応 | 対応 |
| `calendar.moon_phase_format` | 図形と英日ラベル固定 | 対応 |
| `daily_art.enabled` | 最新キャッシュ画像の表示を有効化 | 使用しない |
| その他 `daily_art.*` | 別の同期スクリプトが使用 | 使用しない |
| `ui.clock_font_px` / `date_font_px` / `weather_font_px` | 同梱フォント・サイズ固定 | 対応 |
| `ui.cal_font_px` / `calendar_font_px` | サイズ固定 | 前者優先で対応 |
| `ui.colors.*` | 月別配色固定 | 主にカレンダーが使用 |
| `layout.*` | 配置固定 | カレンダー配置・天気オフセット等に一部対応 |
| `fonts.main.path` / `fallback` | 同梱3フォント固定 | カレンダーと月相が使用 |
| `wallpaper.rotation_seconds` / `fit_mode` | 使用しない | 対応。`fit` / `fill` / `stretch` |
| `background.*` | 使用しない | 現行のSimpleWallpaperRendererでは使用しない |
| `ui.margins` / `character.*` / `performance.*` / `cache.*` / `error_recovery.*` / `logging.*` | 現行起動経路では使用しない | 現行起動経路では使用しない |

`screen.hide_cursor` は設定値を読みません。フルスクリーン処理でカーソルを隠します。ログレベルは `main.py` でINFOに固定されています。

`main.py` の既定値とサンプルは同一ではありません。たとえば設定なしでは30fps、`show_holiday_names: false`、サンプルでは5fps、祝日名表示ありです。使用する値は明示してください。

環境変数 `PICALENDER_WINDOWED=true` / `PICALENDER_FULLSCREEN=true` は画面モードを上書きします。両方を指定すると後者が優先されます。`PICALENDER_CONFIG` で別の設定ファイルを指定する機能は現行の `main.py` にはありません。

設定例と反映手順は[設定ガイド](SETTINGS_GUIDE.md)、生成・同期設定は[日替わりイラスト](DAILY_ARTWORK.md)を参照してください。
