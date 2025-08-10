# TASK-301: 天気プロバイダ基底クラス実装 - 要件定義

## 概要

PiCalendar天気機能の基盤となる抽象基底クラス（ABC）を実装する。複数の天気サービスプロバイダ（Open-Meteo、Yahoo天気など）を統一的に扱うためのインターフェースと共通機能を提供する。

## 基本要件

### 1. 抽象基底クラス仕様
- **クラス名**: `WeatherProvider`
- **継承**: `abc.ABC`を継承
- **主要抽象メソッド**: `fetch()`メソッド
- **共通メソッド**: HTTPクライアント、アイコンマッピング
- **設定管理**: プロバイダ固有設定の管理

### 2. インターフェース統一
- **戻り値形式**: 標準化されたJSON形式
- **エラーハンドリング**: 共通例外クラス
- **タイムアウト処理**: 10秒制限
- **レスポンス検証**: データ形式の妥当性チェック

### 3. HTTP通信基盤
- **プロトコル**: HTTPS必須
- **タイムアウト**: 10秒
- **リトライ機能**: なし（上位レイヤーで制御）
- **証明書検証**: 有効
- **User-Agent**: 適切な識別子設定

### 4. アイコンマッピング
- **内部アイコン**: 5種類（sunny, cloudy, rain, thunder, fog）
- **マッピング機能**: プロバイダ固有コード → 内部アイコン
- **デフォルト**: 不明な場合は "cloudy"
- **拡張性**: 新アイコンの追加に対応

## 技術要件

### 1. データフォーマット

#### 標準レスポンス形式
```python
{
    "updated": 1699999999,  # UNIX タイムスタンプ
    "location": {
        "latitude": 35.681236,
        "longitude": 139.767125,
        "name": "Tokyo"  # オプション
    },
    "forecasts": [
        {
            "date": "2025-01-11",
            "icon": "sunny",          # 内部アイコン名
            "temperature": {
                "min": 5,             # 最低気温（摂氏）
                "max": 12             # 最高気温（摂氏）
            },
            "precipitation_probability": 30,  # 降水確率（%）
            "description": "晴れ"     # オプション：日本語説明
        },
        # 3日分のデータ
    ]
}
```

#### エラーレスポンス形式
```python
{
    "error": {
        "code": "NETWORK_ERROR",
        "message": "API接続に失敗しました",
        "details": "Connection timeout"
    }
}
```

### 2. 例外クラス設計

```python
class WeatherProviderError(Exception):
    """天気プロバイダ基底例外"""
    pass

class NetworkError(WeatherProviderError):
    """ネットワーク関連エラー"""
    pass

class APIError(WeatherProviderError):
    """API関連エラー"""
    pass

class DataFormatError(WeatherProviderError):
    """データ形式エラー"""
    pass

class AuthenticationError(WeatherProviderError):
    """認証エラー"""
    pass
```

### 3. 設定管理仕様

```yaml
weather:
  provider: "openmeteo"           # openmeteo|yahoo
  location:
    latitude: 35.681236
    longitude: 139.767125
  timeout: 10                     # 秒
  openmeteo:
    base_url: "https://api.open-meteo.com/v1/forecast"
  yahoo:
    base_url: "https://weather.yahoo.co.jp/weather/api/"
    app_id: ""
    client_id: ""
    client_secret: ""
```

## 機能仕様

### 1. WeatherProvider基底クラス

```python
class WeatherProvider(ABC):
    """天気プロバイダ基底クラス"""
    
    def __init__(self, settings: Dict[str, Any]):
        """
        初期化
        
        Args:
            settings: 設定辞書
        """
        pass
    
    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """
        天気データ取得（抽象メソッド）
        
        Returns:
            標準形式の天気データ
            
        Raises:
            WeatherProviderError: 各種エラー
        """
        pass
    
    def validate_response(self, data: Dict[str, Any]) -> bool:
        """レスポンスデータの妥当性検証"""
        pass
    
    def map_to_internal_icon(self, provider_code: str) -> str:
        """プロバイダ固有アイコン → 内部アイコンマッピング"""
        pass
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """HTTP リクエスト実行（共通処理）"""
        pass
    
    def _handle_http_error(self, response) -> None:
        """HTTPエラーハンドリング"""
        pass
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        pass
```

### 2. HTTPクライアント機能
- **requests**ライブラリ使用
- **SSL/TLS**検証有効
- **タイムアウト**設定（接続・読み取り）
- **リダイレクト**対応
- **エラーハンドリング**（4XX、5XX）

### 3. アイコンマッピング機能
- **デフォルトマップ**提供
- **カスタマイズ**可能な設計
- **フォールバック**処理
- **ログ出力**（不明コード検出時）

### 4. 設定バリデーション
- **必須項目**チェック
- **データ型**検証
- **値範囲**検証（緯度経度など）
- **URL形式**検証

## セキュリティ要件

### 1. 通信セキュリティ
- **HTTPS必須**: HTTP通信を禁止
- **証明書検証**: SSL証明書の有効性確認
- **APIキー保護**: ログ出力でマスク処理
- **タイムアウト制御**: DoS攻撃対策

### 2. データ検証
- **入力検証**: ユーザー入力の検証
- **レスポンス検証**: APIレスポンスの妥当性
- **型安全性**: 型ヒントとランタイムチェック
- **例外処理**: 適切なエラーメッセージ

## パフォーマンス要件

### 1. レスポンス時間
- **通常時**: 3秒以内
- **タイムアウト**: 10秒
- **キャッシュ利用時**: 100ms以内
- **エラー応答**: 1秒以内

### 2. リソース使用量
- **メモリ使用**: 10MB以下
- **ネットワーク**: 100KB以下のレスポンス
- **CPU使用**: 解析処理で5%以下
- **ディスクI/O**: 設定読み込み時のみ

## エラーハンドリング

### 1. ネットワークエラー
- **接続タイムアウト**: NetworkError例外
- **読み取りタイムアウト**: NetworkError例外
- **DNS解決失敗**: NetworkError例外
- **SSL証明書エラー**: NetworkError例外

### 2. APIエラー
- **HTTP 4XX**: APIError例外
- **HTTP 5XX**: APIError例外
- **不正なJSON**: DataFormatError例外
- **認証失敗**: AuthenticationError例外

### 3. データエラー
- **必須フィールド欠如**: DataFormatError例外
- **不正な値範囲**: DataFormatError例外
- **型不整合**: DataFormatError例外
- **日付形式不正**: DataFormatError例外

## 受け入れ基準

### ✅ 基本機能確認
- [ ] WeatherProvider抽象クラスが正しく定義される
- [ ] 継承クラスでfetch()メソッドが強制実装される
- [ ] 標準レスポンス形式でデータが返される
- [ ] HTTPSクライアントが正しく動作する

### ✅ エラーハンドリング確認
- [ ] タイムアウト時に適切な例外が発生する
- [ ] HTTP4XX/5XXエラーが適切に処理される
- [ ] 不正なJSONレスポンスでDataFormatError例外
- [ ] SSL証明書エラーが適切に処理される

### ✅ セキュリティ確認
- [ ] HTTP通信が拒否される
- [ ] SSL証明書検証が有効である
- [ ] APIキーがログに出力されない
- [ ] タイムアウトが10秒で制限される

### ✅ アイコンマッピング確認
- [ ] 基本5アイコンのマッピングが動作する
- [ ] 不明コードでデフォルト"cloudy"が返される
- [ ] カスタムマッピングの追加が可能である
- [ ] プロバイダ固有の拡張に対応する

### ✅ 設定管理確認
- [ ] YAML設定から正しく値が読み込まれる
- [ ] 必須設定が欠如時に例外が発生する
- [ ] デフォルト値が適切に適用される
- [ ] 緯度経度の範囲チェックが動作する

## 実装ファイル構成

```
src/weather/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py          # WeatherProvider基底クラス
│   └── exceptions.py    # 例外クラス定義
└── utils/
    ├── __init__.py
    ├── http_client.py   # HTTP クライアント
    ├── icon_mapper.py   # アイコンマッピング
    └── validators.py    # バリデーター
```

## テスト要件

### 1. 単体テスト
- **抽象メソッド**: 継承時の強制実装確認
- **HTTPクライアント**: モック使用の通信テスト
- **アイコンマッピング**: 全パターンのマッピング確認
- **バリデーション**: 正常/異常データの検証

### 2. 統合テスト
- **実際のHTTPS通信**: テスト用エンドポイント使用
- **タイムアウト処理**: 実際の遅延で動作確認
- **SSL証明書**: 有効/無効な証明書でテスト
- **例外処理**: 各種エラー状況の再現

### 3. セキュリティテスト
- **HTTP通信拒否**: HTTP URLでの接続確認
- **APIキーマスク**: ログ出力内容の確認
- **証明書検証**: 自己署名証明書での確認
- **タイムアウト制限**: 長時間応答での確認

## 拡張性

### 1. 新プロバイダ追加
- **基底クラス継承**: WeatherProviderを継承
- **fetch()実装**: プロバイダ固有のロジック
- **設定追加**: provider_settings追加
- **テスト追加**: プロバイダ固有テスト

### 2. 機能拡張
- **新アイコン追加**: アイコンマップ更新
- **新データフィールド**: レスポンス形式拡張
- **認証方式追加**: 基底クラス拡張
- **リトライ機能**: オプション実装

## ログ設計

### 1. ログレベル
- **INFO**: 正常な天気データ取得
- **WARNING**: タイムアウト、リトライ
- **ERROR**: API接続失敗、データ形式エラー
- **DEBUG**: HTTPリクエスト詳細、レスポンス内容

### 2. ログフォーマット
```
[TIMESTAMP] [LEVEL] [weather.provider] MESSAGE
```

### 3. 機密情報保護
- **APIキー**: マスク処理（先頭3文字のみ表示）
- **レスポンス**: 個人情報除去
- **エラー詳細**: スタックトレースは DEBUG レベル

この要件定義に基づき、拡張可能で安全な天気プロバイダ基底システムを実装する。