# 現行実装の構成

2026-10-01時点。現在の起動経路は次のとおりです。

```text
install_service.sh版: scripts/start_service.sh → venv/bin/python main.py
旧install.sh版unitは起動パス不整合があり、導入には使用しない
  PiCalendarApp: settings.yaml読込、表示初期化、描画ループ
    field_notes（既定）→ FieldNotesRenderer
      DashboardWeather → Open-Meteo / cache/field_notes_weather.json
      wafu_theme_design → assets/field_notes/monthly/*.png
      moon_phase / lunisolar / rokuyou / sky_events → オフライン計算
      cache/daily_art/current.png → 同期済み画像の表示
    classic → SimpleClock / Date / Calendar / Weather / Wallpaper / Moon Renderer
```

別経路の `scripts/sync_daily_art.py` がSSHで `scripts/serve_daily_art.py` を呼び、サーバーで生成した画像をPiへ同期します。描画ループ自体は画像生成を実行しません。[運用と入力検証](guides/DAILY_ARTWORK.md)

`src/core/`、`src/ui/`、`src/rendering/`、`src/character/`、汎用天気プロバイダには過去の実装が残っています。現在の `main.py` はこれらの設定管理・イベント駆動・キャラクター機能を起動していません。クラスが存在しても標準画面の機能とは限りません。

## 現行のAPI

| 対象 | 入口・返却値 |
| --- | --- |
| `FieldNotesRenderer` | `FieldNotesRenderer(settings=None, weather=None, start_worker=True)`（後2引数はキーワード専用）、`render(screen, now=None)`、`cleanup()` |
| `DashboardWeather` | `DashboardWeather(settings, root, start_worker=True)`、`refresh()`、`snapshot()`、`cleanup()` |
| `WeatherSnapshot` | `forecasts`、`updated`、`error`、`revision`。予報は `Forecast(date, code, high, low, rain)` |
| `get_moon_info(date_or_datetime)` | 月齢、月相英日名、照明率、黄経差、直前／次の新月などの辞書 |
| `get_next_moon_phases(start_date, days=30)` | 期間内の朔弦望の `phase` とUTCの `time` を含む辞書のリスト |
| `lunar_date(day)` | 旧暦の日付 |
| `rise_set_times(day, latitude, longitude, timezone_name="Asia/Tokyo")` | `SkyTimes(sunrise, sunset, moonrise, moonset)`。現象がなければ該当値は `None` |

`get_moon_info(date)` はJST正午、`get_next_moon_phases(date)` は当日JST 00:00から検索します。naive datetimeはJST、timezone付きdatetimeは瞬間を意味します。主要月相名はJSTの現象日に従います。日月の出入は地形や建物による遮蔽を含みません。

現在の設定は[設定対応表](guides/SETTINGS_STATUS.md)、描画・テストの入口は[README](../README.md)を参照してください。[旧API資料](API_DOCUMENTATION.md)は過去のモジュール設計資料として保持しています。
