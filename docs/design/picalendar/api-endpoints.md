# PiCalendar API エンドポイント仕様

## 概要

PiCalendarは主にスタンドアロンアプリケーションですが、天気情報の取得やオプションの管理インターフェースのために外部APIと通信します。
また、将来的な拡張のために内部APIエンドポイントの設計も含みます。

## 外部API仕様

### 1. Open-Meteo Weather API

#### エンドポイント
```
GET https://api.open-meteo.com/v1/forecast
```

#### リクエストパラメータ
```json
{
  "latitude": 35.681236,
  "longitude": 139.767125,
  "daily": [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "weathercode"
  ],
  "timezone": "Asia/Tokyo",
  "forecast_days": 3
}
```

#### レスポンス
```json
{
  "latitude": 35.681236,
  "longitude": 139.767125,
  "generationtime_ms": 0.5,
  "utc_offset_seconds": 32400,
  "timezone": "Asia/Tokyo",
  "timezone_abbreviation": "JST",
  "daily": {
    "time": ["2025-01-10", "2025-01-11", "2025-01-12"],
    "temperature_2m_max": [12.5, 14.2, 11.8],
    "temperature_2m_min": [5.2, 6.8, 4.5],
    "precipitation_probability_max": [20, 45, 10],
    "weathercode": [1, 3, 0]
  },
  "daily_units": {
    "temperature_2m_max": "°C",
    "temperature_2m_min": "°C",
    "precipitation_probability_max": "%",
    "weathercode": "wmo code"
  }
}
```

#### Weather Code マッピング
| Code | Description | Icon |
|------|------------|------|
| 0 | Clear sky | sunny |
| 1-3 | Mainly clear to overcast | cloudy |
| 45-48 | Fog | fog |
| 51-67 | Drizzle/Rain | rain |
| 71-77 | Snow | snow |
| 80-82 | Rain showers | rain |
| 85-86 | Snow showers | snow |
| 95-99 | Thunderstorm | thunder |

#### エラーハンドリング
```json
{
  "error": true,
  "reason": "Invalid coordinates"
}
```

### 2. Yahoo! 天気 API（非公式）

#### エンドポイント
```
GET https://weather.tsukumijima.net/api/forecast/city/{city_code}
```

#### リクエスト例
```
GET https://weather.tsukumijima.net/api/forecast/city/130010
```

#### レスポンス
```json
{
  "publicTime": "2025-01-10T11:00:00+09:00",
  "publicTimeFormatted": "2025/01/10 11:00:00",
  "title": "東京都 東京 の天気",
  "link": "https://weather.yahoo.co.jp/weather/jp/13/4410.html",
  "description": {
    "publicTime": "2025年01月10日 11時00分",
    "text": "日本付近は冬型の気圧配置となっています..."
  },
  "forecasts": [
    {
      "date": "2025-01-10",
      "dateLabel": "今日",
      "telop": "晴れ",
      "detail": {
        "weather": "晴れ",
        "wind": "北の風",
        "wave": "0.5メートル"
      },
      "temperature": {
        "min": {
          "celsius": "5",
          "fahrenheit": "41"
        },
        "max": {
          "celsius": "12",
          "fahrenheit": "53.6"
        }
      },
      "chanceOfRain": {
        "T00_06": "--%",
        "T06_12": "0%",
        "T12_18": "0%",
        "T18_24": "10%"
      },
      "image": {
        "title": "晴れ",
        "url": "https://weather.yahoo.co.jp/weather/img/100.gif"
      }
    }
  ],
  "location": {
    "area": "関東",
    "prefecture": "東京都",
    "district": "東京",
    "city": "千代田区"
  },
  "copyright": {
    "title": "(C) Yahoo Japan Corporation.",
    "link": "https://weather.yahoo.co.jp/weather/",
    "image": {
      "title": "Yahoo!天気",
      "url": "https://weather.yahoo.co.jp/img/logo.gif"
    }
  }
}
```

#### 天気テロップマッピング
| テロップ | Icon |
|---------|------|
| 晴れ、快晴 | sunny |
| 曇り、くもり | cloudy |
| 雨、小雨、大雨 | rain |
| 雷雨、雷 | thunder |
| 雪、小雪、大雪 | snow |
| 霧 | fog |

## 内部API仕様（将来拡張用）

### 管理インターフェース API

#### 基本仕様
- プロトコル: HTTP/HTTPS
- ポート: 8080（設定可能）
- 認証: Basic認証またはトークンベース
- フォーマット: JSON

#### 1. システム状態取得
```
GET /api/v1/status
```

**レスポンス:**
```json
{
  "status": "running",
  "uptime": 86400,
  "version": "1.0.0",
  "cpu_usage": 25.5,
  "memory_usage": 145.2,
  "last_weather_update": "2025-01-10T12:00:00Z",
  "errors": []
}
```

#### 2. 設定取得
```
GET /api/v1/config
```

**レスポンス:**
```json
{
  "screen": {
    "width": 1024,
    "height": 600,
    "fps": 30
  },
  "weather": {
    "provider": "openmeteo",
    "refresh_sec": 1800
  }
  // ... 完全な設定オブジェクト
}
```

#### 3. 設定更新
```
PUT /api/v1/config
Content-Type: application/json
```

**リクエスト:**
```json
{
  "weather": {
    "refresh_sec": 900
  }
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Configuration updated",
  "restart_required": false
}
```

#### 4. 天気データ取得
```
GET /api/v1/weather
```

**レスポンス:**
```json
{
  "updated": "2025-01-10T12:00:00Z",
  "provider": "openmeteo",
  "location": {
    "lat": 35.681236,
    "lon": 139.767125
  },
  "forecasts": [
    {
      "date": "2025-01-10",
      "icon": "sunny",
      "temp_min": 5.2,
      "temp_max": 12.5,
      "pop": 20
    }
  ]
}
```

#### 5. 天気データ強制更新
```
POST /api/v1/weather/refresh
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Weather update initiated",
  "next_update": "2025-01-10T12:30:00Z"
}
```

#### 6. スクリーンショット取得
```
GET /api/v1/screenshot
```

**レスポンス:**
```
Content-Type: image/png
[PNG画像データ]
```

#### 7. ログ取得
```
GET /api/v1/logs?level=ERROR&limit=100
```

**レスポンス:**
```json
{
  "logs": [
    {
      "timestamp": "2025-01-10T11:45:00Z",
      "level": "ERROR",
      "module": "weather",
      "message": "Failed to fetch weather data: timeout"
    }
  ],
  "total": 15,
  "limit": 100
}
```

#### 8. システム再起動
```
POST /api/v1/system/restart
```

**レスポンス:**
```json
{
  "success": true,
  "message": "System restart scheduled",
  "restart_in": 5
}
```

#### 9. キャッシュクリア
```
DELETE /api/v1/cache
```

**レスポンス:**
```json
{
  "success": true,
  "message": "Cache cleared",
  "freed_bytes": 524288
}
```

## WebSocket API（将来拡張用）

### リアルタイム更新用WebSocket

#### エンドポイント
```
ws://localhost:8080/ws
```

#### メッセージフォーマット

**サーバー → クライアント:**
```json
{
  "type": "weather_update",
  "timestamp": "2025-01-10T12:00:00Z",
  "data": {
    "forecasts": [...]
  }
}
```

```json
{
  "type": "status_update",
  "timestamp": "2025-01-10T12:00:00Z",
  "data": {
    "cpu_usage": 28.3,
    "memory_usage": 152.1
  }
}
```

**クライアント → サーバー:**
```json
{
  "type": "subscribe",
  "events": ["weather_update", "status_update"]
}
```

```json
{
  "type": "command",
  "action": "refresh_weather"
}
```

## エラーレスポンス形式

### 標準エラーレスポンス
```json
{
  "error": {
    "code": "WEATHER_FETCH_ERROR",
    "message": "Failed to fetch weather data",
    "details": {
      "provider": "openmeteo",
      "reason": "Network timeout",
      "retry_after": 60
    }
  },
  "timestamp": "2025-01-10T12:00:00Z"
}
```

### HTTPステータスコード

| Code | Description | Usage |
|------|------------|-------|
| 200 | OK | 正常なレスポンス |
| 201 | Created | リソース作成成功 |
| 400 | Bad Request | 不正なリクエスト |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | アクセス拒否 |
| 404 | Not Found | リソース不在 |
| 429 | Too Many Requests | レート制限 |
| 500 | Internal Server Error | サーバーエラー |
| 503 | Service Unavailable | サービス停止中 |

## レート制限

### 外部API
- Open-Meteo: 10,000 リクエスト/日（商用版は無制限）
- Yahoo天気（非公式）: 制限なし（ただし良識的な使用を推奨）

### 内部API
- デフォルト: 60 リクエスト/分
- 認証済み: 600 リクエスト/分

## セキュリティ考慮事項

1. **HTTPS通信**
   - 外部API通信は必ずHTTPS使用
   - 証明書検証を有効化

2. **認証情報管理**
   - APIキーは環境変数または暗号化ファイルで管理
   - ログに認証情報を出力しない

3. **入力検証**
   - すべての入力パラメータを検証
   - SQLインジェクション対策（将来のDB実装時）

4. **CORS設定**
   - 管理APIは同一オリジンのみ許可
   - 必要に応じてホワイトリスト設定

5. **レート制限**
   - DoS攻撃防止のためレート制限実装
   - IPアドレスベースの制限

## 今後の拡張計画

1. **GraphQL API**
   - より柔軟なデータ取得
   - リアルタイムサブスクリプション

2. **gRPC サポート**
   - 高性能な内部通信
   - マイクロサービス化対応

3. **OAuth 2.0 認証**
   - より安全な認証機構
   - サードパーティ連携

4. **Webhook通知**
   - イベント駆動型通知
   - 外部システム連携

5. **メトリクスAPI**
   - Prometheus形式のメトリクス
   - Grafana連携