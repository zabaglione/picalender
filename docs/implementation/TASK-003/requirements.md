# TASK-003: ログシステム実装 - 要件定義

## 概要
PiCalendarアプリケーションのログシステムを実装する。設定管理システムと連携し、レベル別ログ出力、journald連携、ファイル出力オプション、モジュール別ログ制御を提供する。

## 機能要件

### 1. ログフォーマッター設定
- タイムスタンプ付きログ出力
- カスタマイズ可能なフォーマット文字列
- デフォルト: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- 日時形式: ISO 8601形式（YYYY-MM-DD HH:MM:SS）

### 2. レベル別ログ出力
- ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 設定ファイルからレベル設定を読み込み
- 実行時のレベル変更が可能
- レベルに応じたフィルタリング

### 3. journald連携
- systemd-journaldへの出力サポート
- 構造化ログの送信
- プライオリティマッピング
- journalctlでの検索可能なフィールド

### 4. ファイル出力オプション
- ファイルへのログ出力（オプション）
- ログローテーション機能
- サイズベースのローテーション（デフォルト: 10MB）
- 保持ファイル数の設定（デフォルト: 5個）
- 非同期書き込みによるパフォーマンス最適化

### 5. モジュール別ログ制御
- モジュールごとに異なるログレベル設定
- 例: `weather`モジュールはDEBUG、`renderer`モジュールはINFO
- 動的なレベル変更

### 6. 出力先制御
- 複数の出力先を同時サポート
  - コンソール（stdout/stderr）
  - ファイル
  - journald
- 出力先ごとの有効/無効切り替え

## 技術仕様

### クラス設計

```python
class LogManager:
    """ログ管理クラス"""
    
    def __init__(self, config: ConfigManager):
        """初期化"""
        
    def setup(self) -> None:
        """ログシステムをセットアップ"""
        
    def get_logger(self, name: str) -> logging.Logger:
        """指定された名前のロガーを取得"""
        
    def set_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """ログレベルを設定"""
        
    def add_file_handler(self, filepath: str, level: Optional[str] = None) -> None:
        """ファイルハンドラーを追加"""
        
    def remove_file_handler(self, filepath: str) -> None:
        """ファイルハンドラーを削除"""
        
    def flush(self) -> None:
        """バッファをフラッシュ"""
        
    def close(self) -> None:
        """ログシステムをクローズ"""

class JournaldHandler(logging.Handler):
    """systemd-journald用ハンドラー"""
    
    def emit(self, record: logging.LogRecord) -> None:
        """ログレコードをjournaldに送信"""

class ColoredConsoleHandler(logging.StreamHandler):
    """カラー出力対応コンソールハンドラー"""
    
    def format(self, record: logging.LogRecord) -> str:
        """レベルに応じて色付けしたメッセージを返す"""
```

### ログレベルマッピング

| Python Level | journald Priority | Console Color |
|-------------|------------------|---------------|
| DEBUG       | 7 (DEBUG)        | Cyan          |
| INFO        | 6 (INFO)         | Green         |
| WARNING     | 4 (WARNING)      | Yellow        |
| ERROR       | 3 (ERR)          | Red           |
| CRITICAL    | 2 (CRIT)         | Magenta       |

### 設定構造（ConfigManagerから読み込み）

```python
{
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        'output': {
            'console': True,
            'file': False,
            'journald': True
        },
        'file': {
            'path': './logs/picalendar.log',
            'rotate_size_mb': 10,
            'rotate_count': 5
        },
        'modules': {
            'weather': 'DEBUG',
            'renderer': 'INFO',
            'asset': 'WARNING'
        }
    }
}
```

## エラー処理

### ファイル書き込みエラー
- エラーログをコンソールに出力
- ファイルハンドラーを無効化
- アプリケーションは継続動作

### journald接続エラー
- フォールバックとしてコンソール出力
- 警告ログを出力
- 定期的な再接続試行

### 設定エラー
- 不正なログレベル → デフォルト（INFO）を使用
- 不正なフォーマット文字列 → デフォルトフォーマットを使用
- ファイルパス作成失敗 → ファイル出力を無効化

## パフォーマンス要件

- ログ出力によるメインループへの影響を最小化
- ファイル書き込みは非同期またはバッファリング
- ログレベルチェックの高速化（事前フィルタリング）
- メモリ使用量: 5MB以内

## 受け入れ基準

1. ✅ 設定ファイルからログ設定を読み込める
2. ✅ INFO/ERROR/DEBUGレベルの出力が正しく制御される
3. ✅ タイムスタンプ付きでログが出力される
4. ✅ journaldにログが送信される（Linux環境）
5. ✅ ファイルローテーションが正しく動作する
6. ✅ モジュール別のログレベル設定が機能する
7. ✅ 複数の出力先に同時に出力できる
8. ✅ カラー出力が端末で正しく表示される
9. ✅ エラー発生時もアプリケーションが継続動作する

## 非機能要件

- スレッドセーフな実装
- ログ出力のレイテンシ: 1ms以内
- バッファサイズ: 8KB
- 単体テストカバレッジ: 85%以上