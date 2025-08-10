# TASK-101: pygame/SDL2初期化 - 要件定義

## 概要
PiCalendarアプリケーションの描画基盤となるpygame/SDL2の初期化システムを実装する。
Raspberry Pi Zero 2 W環境でKMSDRMバックエンドを使用し、フルスクリーン表示、マウスカーソル非表示、FPS制御を実現する。

## 機能要件

### 1. pygame初期化
- pygameモジュールの初期化
- 必要なサブシステムの起動
- エラーハンドリング
- 環境変数の設定（SDL_VIDEODRIVER）

### 2. KMSDRM設定
- Raspberry Pi環境でのKMSDRMバックエンド使用
- X Window System非依存での直接描画
- フォールバック機構（開発環境用）
- パフォーマンス最適化設定

### 3. フルスクリーン設定
- 1024×600解像度でのフルスクリーン表示
- 解像度の自動検出オプション
- ウィンドウモードとの切り替え（開発用）
- アスペクト比の維持

### 4. マウスカーソル非表示
- マウスカーソルの完全非表示
- タッチスクリーン対応考慮
- 開発モードでの表示オプション

### 5. FPS制御
- 30FPSでの安定動作
- Clockオブジェクトによる制御
- CPU使用率の最適化
- フレームスキップ機能

### 6. 描画サーフェス管理
- メインサーフェスの取得と管理
- ダブルバッファリング
- ハードウェアアクセラレーション（可能な場合）
- サーフェス情報の取得

## 技術仕様

### クラス設計

```python
class DisplayManager:
    """ディスプレイ管理クラス"""
    
    def __init__(self, config: ConfigManager):
        """初期化"""
        
    def initialize(self) -> bool:
        """pygame/SDL2を初期化"""
        
    def create_screen(self) -> pygame.Surface:
        """スクリーンサーフェスを作成"""
        
    def set_fullscreen(self, fullscreen: bool) -> None:
        """フルスクリーンモードを設定"""
        
    def hide_cursor(self, hide: bool) -> None:
        """マウスカーソルの表示/非表示"""
        
    def get_screen(self) -> pygame.Surface:
        """現在のスクリーンサーフェスを取得"""
        
    def get_clock(self) -> pygame.time.Clock:
        """FPS制御用のClockオブジェクトを取得"""
        
    def flip(self) -> None:
        """画面を更新（ダブルバッファリング）"""
        
    def clear(self, color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """画面をクリア"""
        
    def quit(self) -> None:
        """pygameを終了"""
        
    def get_info(self) -> Dict[str, Any]:
        """ディスプレイ情報を取得"""

class EnvironmentDetector:
    """実行環境検出クラス"""
    
    @staticmethod
    def is_raspberry_pi() -> bool:
        """Raspberry Pi環境かどうかを判定"""
        
    @staticmethod
    def has_display() -> bool:
        """ディスプレイが接続されているか確認"""
        
    @staticmethod
    def get_video_driver() -> str:
        """使用するビデオドライバーを決定"""
```

### 環境別設定

| 環境 | ビデオドライバー | フルスクリーン | カーソル |
|-----|-----------------|--------------|---------|
| Raspberry Pi (本番) | kmsdrm | 有効 | 非表示 |
| Linux (開発) | x11 | 無効 | 表示 |
| macOS (開発) | default | 無効 | 表示 |
| Windows (開発) | windib | 無効 | 表示 |
| ヘッドレス | dummy | - | - |

### 初期化シーケンス

1. 環境検出
2. SDL環境変数設定
3. pygame.init()
4. ビデオモード設定
5. スクリーン作成
6. カーソル設定
7. FPS制御初期化

### エラー処理

#### SDL初期化失敗
- フォールバックドライバーを試行
- ダミードライバーで起動（ヘッドレスモード）
- エラーログを出力
- グレースフルな終了

#### ディスプレイ未接続
- ヘッドレスモードで起動
- ダミーサーフェスを作成
- 警告ログを出力
- 描画処理は継続（出力なし）

#### 解像度不一致
- 利用可能な解像度にフォールバック
- スケーリング処理を有効化
- 警告ログを出力

## パフォーマンス要件

- 初期化時間: 2秒以内
- メモリ使用量: 50MB以内（pygame関連）
- CPU使用率: アイドル時5%以下
- フレームレート: 30FPS±1FPS

## 受け入れ基準

1. ✅ pygame が正常に初期化される
2. ✅ 1024×600の解像度で画面が作成される
3. ✅ フルスクリーンモードが有効になる
4. ✅ マウスカーソルが非表示になる
5. ✅ 30FPSで安定動作する
6. ✅ Raspberry Pi環境でKMSDRMが使用される
7. ✅ 開発環境では適切なドライバーが選択される
8. ✅ エラー時にクラッシュしない
9. ✅ ディスプレイ情報が取得できる
10. ✅ 正常に終了処理ができる

## 非機能要件

- スレッドセーフな実装（将来の拡張用）
- 環境変数による設定のオーバーライド
- デバッグモードでの詳細情報出力
- 単体テストカバレッジ: 80%以上

## 依存関係

- pygame >= 2.5.0
- SDL2（pygameに含まれる）
- ConfigManager（設定読み込み）
- LogManager（ログ出力）

## 制約事項

- X Window Systemを使用しない（本番環境）
- GPU使用は限定的（Pi Zero 2 Wの制約）
- メモリ使用量を最小限に抑える
- 電源投入から10秒以内に表示開始