# 天気設定と確認

標準のField NotesはOpen-Meteoから今日・明日・明後日の予報を取得します。最高／最低気温、降水確率、天気アイコン、取得日時を表示します。認証情報の設定は不要です。`weather.provider` を変更しても現行画面のプロバイダは切り替わりません。

## 地点と時刻

プロジェクト直下の `settings.yaml` を編集します。

```yaml
weather:
  location:
    lat: 35.681236
    lon: 139.767125
  timezone: Asia/Tokyo
  refresh_sec: 1800
```

座標は設置地点へ変更してください。`timezone` は標準画面の時刻・月別背景の切替にも使用します。正常時は既定30分、失敗時は60秒後に再試行します。設定変更後は `sudo systemctl restart picalender` で反映します。

## 通信・表示確認

APIを直接確認する場合：

```bash
curl --fail --max-time 20 'https://api.open-meteo.com/v1/forecast?latitude=35.681236&longitude=139.767125&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Tokyo&forecast_days=3'
```

これは東京の例です。設定地点に置き換えます。API応答だけではアプリの描画確認にはなりません。

```bash
cd ~/picalender
venv/bin/python scripts/render_preview.py --offline
sudo journalctl -u picalender --since today
tail -n 40 logs/service.log
```

プレビューは既存キャッシュを使います。`--offline` を外すと取得を試みます。ネットワーク取得を確認する際は `DashboardWeather` と現行画面を使用し、旧レンダラーの内部メソッドを直接呼び出す必要はありません。

## キャッシュと古い予報

標準画面のキャッシュは `cache/field_notes_weather.json` です。設定地点とタイムゾーンが一致するものだけ読み込み、取得失敗時は直前のデータを保持します。表示日の予報がなければ値を補わず、取得時刻が古い場合は状態を区別します。24時間で一律に削除する仕様ではありません。

日替わりイラストの入力には、設定地点・対象日が一致し、取得2時間以内の予報だけを使います。画面で保持する予報とは条件が異なります。[日替わりイラスト](DAILY_ARTWORK.md)

旧 `classic` 画面は `SimpleWeatherRenderer` と `cache/weather_cache.json` を使用します。取得間隔は実装の1800秒固定で、`weather.refresh_sec` を読みません。地点は `weather.location` から読み込みます。
