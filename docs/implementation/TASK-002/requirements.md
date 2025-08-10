# TASK-002: 設定管理システム実装 - 要件定義

## 概要
PiCalendarアプリケーションの設定管理システムを実装する。YAMLファイルから設定を読み込み、デフォルト値の管理、環境変数によるオーバーライド、バリデーション機能を提供する。

## 機能要件

### 1. YAML設定ファイルの読み込み
- `settings.yaml`ファイルから設定を読み込む
- ネストされた構造をサポート
- 文字列、数値、リスト、辞書型をサポート

### 2. デフォルト値管理
- 設定ファイルが存在しない場合、デフォルト値で動作
- 部分的な設定のみ存在する場合、不足分はデフォルト値を使用
- デフォルト値は内部で定義

### 3. 環境変数オーバーライド
- 環境変数による設定値の上書きをサポート
- 命名規則: `PICALENDAR_<SECTION>_<KEY>`
- 例: `PICALENDAR_WEATHER_PROVIDER=yahoo`

### 4. 設定バリデーション
- 型チェック（int, float, str, list, dict）
- 範囲チェック（FPS: 1-60, 解像度: 正の整数）
- 必須項目の存在確認
- 不正な値の場合は警告を出してデフォルト値を使用

### 5. 設定アクセスインターフェース
- ドット記法でのアクセス: `config.screen.width`
- 辞書記法でのアクセス: `config['screen']['width']`
- get()メソッドでのデフォルト値付きアクセス

## 技術仕様

### クラス設計

```python
class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "settings.yaml"):
        """初期化"""
        
    def load(self) -> None:
        """設定ファイルを読み込む"""
        
    def validate(self) -> bool:
        """設定値を検証する"""
        
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        
    def set(self, key: str, value: Any) -> None:
        """設定値を更新（実行時のみ）"""
        
    def reload(self) -> None:
        """設定を再読み込み"""
        
    def to_dict(self) -> dict:
        """設定を辞書として取得"""
```

### デフォルト設定構造

```python
DEFAULT_CONFIG = {
    'screen': {
        'width': 1024,
        'height': 600,
        'fps': 30,
        'fullscreen': True,
        'hide_cursor': True
    },
    'ui': {
        'margins': {'x': 24, 'y': 16},
        'clock_font_px': 130,
        'date_font_px': 36,
        'cal_font_px': 22,
        'weather_font_px': 22,
        'colors': {
            'text': [255, 255, 255],
            'sunday': [255, 100, 100],
            'saturday': [100, 100, 255],
            'weekday': [255, 255, 255]
        }
    },
    'calendar': {
        'first_weekday': 'SUNDAY'
    },
    'weather': {
        'provider': 'openmeteo',
        'refresh_sec': 1800,
        'timeout_sec': 10,
        'location': {
            'lat': 35.681236,
            'lon': 139.767125
        }
    },
    'character': {
        'enabled': False,
        'fps': 8
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    }
}
```

## エラー処理

### 設定ファイル不在
- 警告ログを出力
- デフォルト設定で継続

### 不正なYAML形式
- エラーログを出力
- パースエラーの詳細を記録
- デフォルト設定で継続

### 型不整合
- 警告ログを出力
- 該当項目のみデフォルト値を使用
- 他の設定は維持

### バリデーションエラー
- 警告ログを出力
- 不正な値の詳細を記録
- デフォルト値または有効な範囲内の値を使用

## 受け入れ基準

1. ✅ `settings.yaml`から設定を正しく読み込める
2. ✅ 設定ファイルが存在しない場合、デフォルト値で動作する
3. ✅ 部分的な設定のみの場合、不足分はデフォルト値が適用される
4. ✅ 環境変数による設定の上書きが機能する
5. ✅ 不正な型の値が検出され、警告が出力される
6. ✅ 範囲外の値が検出され、適切な値に修正される
7. ✅ ドット記法と辞書記法の両方でアクセスできる
8. ✅ 設定の再読み込みが可能

## 非機能要件

- 設定読み込みは100ms以内に完了
- メモリ使用量は1MB以内
- スレッドセーフな実装
- 単体テストカバレッジ90%以上