# 天気表示機能について

## 🌤️ 天気表示の仕組み

PiCalendarには天気予報を表示する機能があります：

- **3日分の天気予報**（今日・明日・明後日）
- **最高/最低気温**
- **降水確率**
- **天気アイコン**（晴れ、曇り、雨など）

## 📍 表示位置の設定

デフォルトでは東京の天気を表示します。お住まいの地域に変更するには：

### 1. 現在地の緯度・経度を調べる

Google Mapsなどで調べることができます：
1. [Google Maps](https://maps.google.com)を開く
2. 表示したい地域を右クリック
3. 表示される座標をメモ（例：35.681236, 139.767125）

### 2. 設定ファイルを編集

```bash
nano ~/picalender/settings.yaml
```

以下の部分を編集：

```yaml
weather:
  location:
    lat: 35.681236   # あなたの地域の緯度
    lon: 139.767125  # あなたの地域の経度
```

主要都市の座標例：

| 都市 | 緯度 | 経度 |
|------|------|------|
| 東京 | 35.681236 | 139.767125 |
| 大阪 | 34.693725 | 135.502254 |
| 名古屋 | 35.180344 | 136.906632 |
| 札幌 | 43.064171 | 141.346939 |
| 福岡 | 33.590184 | 130.401689 |
| 仙台 | 38.268215 | 140.869356 |
| 広島 | 34.396033 | 132.459622 |
| 京都 | 35.011635 | 135.768036 |

## 🔄 更新頻度

- デフォルトで**30分ごと**に自動更新
- インターネット接続が必要
- オフラインの場合は最後に取得したデータを表示

## 🌐 使用するAPI

無料の[Open-Meteo](https://open-meteo.com/)を使用：
- 認証不要
- 無料で利用可能
- 世界中の天気データ

## ✅ 動作確認

### 手動で天気表示を確認

```bash
cd ~/picalender
python3 -c "
from src.renderers.simple_weather_renderer import SimpleWeatherRenderer
import json

settings = {
    'weather': {
        'location': {
            'lat': 35.681236,
            'lon': 139.767125
        }
    }
}

renderer = SimpleWeatherRenderer(settings)
renderer._fetch_weather()

if renderer.weather_data:
    print('天気データ取得成功！')
    for day in renderer.weather_data:
        print(f\"  {day['date']}: {day['temp_max']}°/{day['temp_min']}° 降水確率{day.get('precip_prob', 0)}%\")
else:
    print('天気データを取得できませんでした')
"
```

### キャッシュファイルの確認

```bash
# キャッシュが作成されているか確認
ls -la ~/picalender/cache/
cat ~/picalender/cache/weather_cache.json | python3 -m json.tool
```

## 🚨 トラブルシューティング

### 天気が表示されない場合

1. **インターネット接続を確認**
   ```bash
   ping -c 3 api.open-meteo.com
   ```

2. **手動でAPIをテスト**
   ```bash
   curl "https://api.open-meteo.com/v1/forecast?latitude=35.681236&longitude=139.767125&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo&forecast_days=3"
   ```

3. **ログを確認**
   ```bash
   # アプリケーション実行中のログ
   tail -f ~/picalender/logs/autostart.log
   ```

4. **Pythonパッケージの確認**
   ```bash
   python3 -c "import requests; print('requests OK')"
   ```

### エラー別の対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| Connection Error | ネット未接続 | Wi-Fi設定を確認 |
| Timeout | API応答なし | しばらく待って再試行 |
| 取得中... が続く | 初回取得中 | 1-2分待つ |
| ImportError | requests未インストール | `pip3 install requests` |

## 📝 注意事項

- 初回起動時は天気データの取得に少し時間がかかります
- オフライン時も時計とカレンダーは正常に表示されます
- 天気データは最大24時間キャッシュされます

## 🎨 表示内容

画面左下に天気パネルが表示されます：

```
┌─────────────────────────┐
│      天気予報           │
├────────┬────────┬───────┤
│  今日  │  明日  │ 明後日 │
│   ☀️   │   🌤️   │   🌧️   │
│ 28°/20°│ 26°/19°│ 24°/18°│
│  ☔0%  │  ☔20% │  ☔80% │
└────────┴────────┴───────┘
```

## 🔧 カスタマイズ

表示をカスタマイズしたい場合は、`src/renderers/simple_weather_renderer.py`を編集してください。