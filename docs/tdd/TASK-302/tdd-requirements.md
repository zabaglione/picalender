# TASK-302: Open-Meteoプロバイダ実装 - 要件定義

## 概要

WeatherProvider基底クラスを継承し、Open-Meteo APIから天気データを取得するプロバイダを実装する。無料・認証不要の天気APIサービスとして、開発・テスト環境での利用を想定。

## 基本要件

### 1. Open-Meteo API仕様
- **エンドポイント**: `https://api.open-meteo.com/v1/forecast`
- **認証**: 不要（無料公開API）
- **リクエスト形式**: GET
- **レート制限**: 10,000リクエスト/日（IPベース）
- **データ範囲**: 16日間の予報データ

### 2. データ取得仕様
- **取得期間**: 今日から3日分
- **取得項目**: 
  - 日次最高・最低気温
  - 天気コード（WMO Weather Code）
  - 降水確率
- **座標ベース**: 緯度経度で地点指定
- **タイムゾーン**: Asia/Tokyo

### 3. レスポンス変換
- **Open-Meteo形式 → 標準形式**: JSONレスポンスの変換
- **天気コード → アイコン**: WMOコードの内部アイコンマッピング
- **温度単位**: 摂氏（°C）
- **日付形式**: YYYY-MM-DD

### 4. エラーハンドリング
- **接続エラー**: NetworkError例外
- **APIエラー**: APIError例外（400, 500番台）
- **データ不正**: DataFormatError例外
- **タイムアウト**: 10秒制限（基底クラス継承）

## 技術要件

### 1. APIリクエスト仕様

#### リクエストパラメータ
```python
{
    "latitude": 35.681236,        # 緯度
    "longitude": 139.767125,      # 経度
    "daily": [                    # 日次データ項目
        "temperature_2m_max",     # 最高気温
        "temperature_2m_min",     # 最低気温
        "weathercode",            # 天気コード
        "precipitation_probability_max"  # 最大降水確率
    ],
    "timezone": "Asia/Tokyo",     # タイムゾーン
    "forecast_days": 3           # 予報日数
}
```

#### レスポンス形式（Open-Meteo）
```json
{
    "latitude": 35.6812,
    "longitude": 139.7671,
    "timezone": "Asia/Tokyo",
    "daily": {
        "time": ["2025-01-11", "2025-01-12", "2025-01-13"],
        "temperature_2m_max": [12.5, 8.3, 7.1],
        "temperature_2m_min": [5.2, 3.1, 4.0],
        "weathercode": [1, 3, 61],
        "precipitation_probability_max": [30, 60, 90]
    }
}
```

### 2. 天気コードマッピング

#### WMO Weather Code → 内部アイコン
```python
WMO_ICON_MAPPING = {
    # Clear/Sunny (0-1)
    0: "sunny",      # Clear sky
    1: "sunny",      # Mainly clear
    
    # Cloudy (2-3)
    2: "cloudy",     # Partly cloudy
    3: "cloudy",     # Overcast
    
    # Fog (45, 48)
    45: "fog",       # Foggy
    48: "fog",       # Depositing rime fog
    
    # Rain (51-67, 80-82)
    51: "rain",      # Light drizzle
    53: "rain",      # Moderate drizzle
    55: "rain",      # Dense drizzle
    61: "rain",      # Slight rain
    63: "rain",      # Moderate rain
    65: "rain",      # Heavy rain
    66: "rain",      # Light freezing rain
    67: "rain",      # Heavy freezing rain
    80: "rain",      # Slight rain showers
    81: "rain",      # Moderate rain showers
    82: "rain",      # Violent rain showers
    
    # Thunder (95, 96, 99)
    95: "thunder",   # Thunderstorm
    96: "thunder",   # Thunderstorm with hail
    99: "thunder",   # Thunderstorm with heavy hail
    
    # Snow (71-77, 85-86) -> rain として扱う
    71: "rain",      # Light snow
    73: "rain",      # Moderate snow
    75: "rain",      # Heavy snow
    77: "rain",      # Snow grains
    85: "rain",      # Light snow showers
    86: "rain",      # Heavy snow showers
}
```

### 3. 標準レスポンス変換

```python
# Open-Meteo形式から標準形式への変換
{
    "updated": 1705123200,  # 現在のUNIXタイムスタンプ
    "location": {
        "latitude": 35.681236,
        "longitude": 139.767125,
        "name": None  # Open-Meteoは地名を返さない
    },
    "forecasts": [
        {
            "date": "2025-01-11",
            "icon": "sunny",
            "temperature": {
                "min": 5,
                "max": 13
            },
            "precipitation_probability": 30,
            "description": None  # Open-Meteoは説明文を返さない
        },
        # ... 3日分
    ]
}
```

## 機能仕様

### 1. OpenMeteoProviderクラス

```python
class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo天気プロバイダ"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self, settings: Dict[str, Any]):
        """初期化"""
        super().__init__(settings)
        self._init_wmo_mapping()
    
    def fetch(self) -> Dict[str, Any]:
        """
        天気データ取得（実装必須）
        
        Returns:
            標準形式の天気データ
            
        Raises:
            WeatherProviderError: 各種エラー
        """
        pass
    
    def _build_request_params(self) -> Dict[str, Any]:
        """Open-Meteo APIリクエストパラメータ構築"""
        pass
    
    def _parse_openmeteo_response(self, data: Dict) -> Dict[str, Any]:
        """Open-Meteoレスポンスを標準形式に変換"""
        pass
    
    def _convert_daily_data(self, daily_data: Dict, index: int) -> Dict[str, Any]:
        """日次データを標準形式の予報データに変換"""
        pass
    
    def _map_wmo_code_to_icon(self, wmo_code: int) -> str:
        """WMO天気コードを内部アイコンにマッピング"""
        pass
```

### 2. データ取得フロー
1. 設定から緯度経度を取得
2. APIリクエストパラメータ構築
3. HTTPSリクエスト実行（基底クラスの_make_request使用）
4. レスポンス検証
5. 標準形式への変換
6. データ返却

### 3. エラー処理
- **API接続失敗**: 基底クラスのNetworkError
- **不正レスポンス**: DataFormatError（必須フィールド欠如等）
- **変換エラー**: DataFormatError（データ型不整合等）
- **タイムアウト**: 基底クラスの10秒制限

### 4. キャッシュ考慮
- このクラスではキャッシュ実装なし
- TASK-303で別途キャッシュレイヤー実装予定
- 毎回APIリクエストを実行

## セキュリティ要件

### 1. 通信セキュリティ
- **HTTPS必須**: 基底クラスで強制
- **証明書検証**: 有効（基底クラス設定）
- **認証不要**: Open-Meteoは公開API
- **レート制限対応**: 呼び出し側で制御

### 2. データ検証
- **レスポンス検証**: 基底クラスのvalidate_response使用
- **型チェック**: 数値・文字列の妥当性確認
- **範囲チェック**: 温度・降水確率の妥当性
- **日付形式**: ISO 8601形式の確認

## パフォーマンス要件

### 1. レスポンス時間
- **通常時**: 1-2秒（Open-Meteo APIレスポンス）
- **タイムアウト**: 10秒（基底クラス設定）
- **解析時間**: 100ms以内
- **変換処理**: 50ms以内

### 2. リソース使用量
- **メモリ**: 1MB以下（レスポンスサイズ）
- **CPU**: 解析で1%以下
- **ネットワーク**: 10KB以下のレスポンス
- **並行処理**: スレッドセーフ

## 受け入れ基準

### ✅ 基本機能確認
- [ ] WeatherProviderを正しく継承している
- [ ] fetch()メソッドが実装されている
- [ ] Open-Meteo APIと通信できる
- [ ] 3日分の天気データが取得できる

### ✅ データ変換確認
- [ ] WMO天気コードが正しくアイコンにマッピングされる
- [ ] 温度データが摂氏で取得される
- [ ] 降水確率が0-100%の範囲で取得される
- [ ] 日付がYYYY-MM-DD形式で返される

### ✅ エラーハンドリング確認
- [ ] ネットワークエラー時にNetworkError例外
- [ ] 不正レスポンス時にDataFormatError例外
- [ ] タイムアウト時に適切な処理
- [ ] エラー時も基底クラスのcleanup()が呼ばれる

### ✅ 統合確認
- [ ] 基底クラスの設定管理が機能する
- [ ] 基底クラスのHTTPクライアントが使用される
- [ ] 基底クラスのログ出力が動作する
- [ ] 基底クラスのセキュリティ機能が有効

## 実装ファイル構成

```
src/weather/providers/
├── __init__.py          # 更新（OpenMeteoProviderを追加）
├── base.py              # 既存
├── exceptions.py        # 既存
└── openmeteo.py        # 新規作成
```

## テスト要件

### 1. 単体テスト
- **fetch()実装**: 正常系・異常系のテスト
- **APIパラメータ構築**: 正しいパラメータ生成
- **レスポンス変換**: Open-Meteo→標準形式
- **WMOコードマッピング**: 全天気コードのテスト

### 2. 統合テスト
- **実際のAPI通信**: モックとスタブでのテスト
- **エラー状況**: ネットワーク断・不正レスポンス
- **設定変更**: 異なる緯度経度での動作
- **基底クラス連携**: 設定・ログ・例外の統合

### 3. パフォーマンステスト
- **レスポンス時間**: 3秒以内の確認
- **メモリ使用量**: 1MB以下の確認
- **並行実行**: 複数インスタンスの同時実行

## 制限事項

### 1. Open-Meteo API制限
- **地名なし**: 緯度経度のみ、地名は返されない
- **説明文なし**: 天気の日本語説明はない
- **レート制限**: 1日10,000リクエストまで
- **データ精度**: 無料版のため精度は限定的

### 2. 実装制限
- **キャッシュなし**: この実装ではキャッシュ機能なし
- **リトライなし**: エラー時の自動リトライなし
- **バッチ取得なし**: 複数地点の同時取得非対応

## 今後の拡張

### Phase 1: 基本実装（本タスク）
- Open-Meteo API連携
- WMOコードマッピング
- 標準形式変換

### Phase 2: 機能拡張
- 時間別予報対応
- 週間予報（7日間）対応
- UV指数・風速等の追加データ

### Phase 3: 最適化
- レスポンスキャッシュ
- バッチリクエスト対応
- エラーリトライ機構

この要件定義に基づき、無料で利用可能な Open-Meteo 天気プロバイダを実装する。