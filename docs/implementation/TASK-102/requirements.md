# TASK-102: レンダリングループ実装 - 要件定義

## 概要
PiCalendarアプリケーションのメインレンダリングループを実装する。
30FPSで安定動作し、効率的なイベント処理とレイヤー管理を実現する。

## 機能要件

### 1. メインループ構造
- アプリケーションのメインループ実装
- 起動・停止・一時停止の制御
- グレースフルシャットダウン
- 例外ハンドリング

### 2. FPS制御
- 30FPS（33.33ms/フレーム）の維持
- フレームスキップ機能
- FPS計測と統計
- 適応的なFPS調整

### 3. イベント処理
- pygameイベントキューの処理
- イベントハンドラーの登録と実行
- キーボード・マウスイベント対応
- カスタムイベントのサポート

### 4. ダーティリージョン管理
- 更新が必要な領域の追跡
- 部分的な再描画
- 効率的な更新領域の結合
- フルスクリーン更新の最小化

### 5. レイヤー管理
- 複数レイヤーの管理（背景、UI要素、前景）
- レイヤーの優先順位制御
- レイヤーごとの表示/非表示
- ブレンドモードのサポート

### 6. レンダラブルインターフェース
- 描画可能オブジェクトの共通インターフェース
- update()とrender()メソッドの分離
- 描画順序の制御
- 条件付き描画

## 技術仕様

### クラス設計

```python
class RenderLoop:
    """メインレンダリングループ"""
    
    def __init__(self, display_manager: DisplayManager, target_fps: int = 30):
        """初期化"""
        
    def start(self) -> None:
        """ループ開始"""
        
    def stop(self) -> None:
        """ループ停止"""
        
    def pause(self) -> None:
        """一時停止"""
        
    def resume(self) -> None:
        """再開"""
        
    def add_layer(self, layer: Layer, priority: int = 0) -> None:
        """レイヤー追加"""
        
    def remove_layer(self, layer: Layer) -> None:
        """レイヤー削除"""
        
    def add_event_handler(self, event_type: int, handler: Callable) -> None:
        """イベントハンドラー登録"""
        
    def get_fps(self) -> float:
        """現在のFPS取得"""
        
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""

class Layer:
    """レイヤー基底クラス"""
    
    def __init__(self, name: str):
        """初期化"""
        
    def add_renderable(self, renderable: Renderable) -> None:
        """描画オブジェクト追加"""
        
    def remove_renderable(self, renderable: Renderable) -> None:
        """描画オブジェクト削除"""
        
    def update(self, dt: float) -> None:
        """更新処理"""
        
    def render(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """描画処理"""
        
    def set_visible(self, visible: bool) -> None:
        """表示/非表示設定"""
        
    def is_visible(self) -> bool:
        """表示状態取得"""

class Renderable(ABC):
    """描画可能オブジェクトインターフェース"""
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """更新処理"""
        
    @abstractmethod
    def render(self, surface: pygame.Surface) -> Optional[pygame.Rect]:
        """描画処理"""
        
    @abstractmethod
    def get_bounds(self) -> pygame.Rect:
        """境界矩形取得"""
        
    @abstractmethod
    def is_dirty(self) -> bool:
        """更新必要判定"""

class DirtyRegionManager:
    """ダーティリージョン管理"""
    
    def __init__(self):
        """初期化"""
        
    def add_rect(self, rect: pygame.Rect) -> None:
        """更新領域追加"""
        
    def get_dirty_rects(self) -> List[pygame.Rect]:
        """更新領域取得"""
        
    def clear(self) -> None:
        """クリア"""
        
    def union_rects(self) -> pygame.Rect:
        """領域結合"""
```

### メインループフロー

```
1. イベント処理
   - pygameイベントキューから取得
   - 登録ハンドラーの実行
   - システムイベント処理（QUIT等）

2. 更新処理
   - デルタタイム計算
   - 全レイヤーのupdate()呼び出し
   - ダーティリージョン収集

3. 描画処理
   - ダーティリージョンのクリア
   - レイヤー優先順に描画
   - 画面更新（flip/update）

4. FPS制御
   - フレーム時間計測
   - 必要に応じてsleep
   - フレームスキップ判定
```

### パフォーマンス最適化

| 手法 | 説明 | 効果 |
|------|------|------|
| ダーティリージョン | 変更部分のみ再描画 | CPU負荷削減 |
| レイヤーキャッシュ | 静的レイヤーをキャッシュ | 描画時間短縮 |
| イベントバッチング | 複数イベントをまとめて処理 | 処理効率向上 |
| フレームスキップ | 遅延時に描画スキップ | FPS安定化 |

## パフォーマンス要件

- FPS: 30±1 FPS
- CPU使用率: 30%未満（Pi Zero 2 W）
- メモリ使用量: 追加50MB以内
- フレームドロップ率: 1%未満
- 最大フレーム時間: 50ms

## 受け入れ基準

1. ✅ メインループが30FPSで安定動作する
2. ✅ CPU使用率が30%未満に収まる
3. ✅ メモリ使用量が仕様内に収まる
4. ✅ イベント処理が正常に動作する
5. ✅ レイヤー管理が正しく機能する
6. ✅ ダーティリージョン管理が機能する
7. ✅ 一時停止・再開が正常動作する
8. ✅ グレースフルシャットダウンができる
9. ✅ FPS統計が取得できる
10. ✅ 長時間動作で安定している

## 非機能要件

- スレッドセーフな実装
- 拡張可能なアーキテクチャ
- デバッグモードでの詳細ログ
- プロファイリング機能
- 単体テストカバレッジ: 80%以上

## 依存関係

- pygame >= 2.5.0
- DisplayManager（TASK-101で実装済み）
- ConfigManager（設定読み込み）
- LogManager（ログ出力）

## 制約事項

- シングルスレッドでの実装（メインループ）
- pygame依存のイベントシステム
- 最大レイヤー数: 10
- 最大同時イベントハンドラー: 100

## エラーハンドリング

### レンダリングエラー
- 個別オブジェクトの描画失敗を隔離
- エラーログ出力後、継続動作
- フォールバック描画の実行

### イベント処理エラー
- ハンドラーエラーを捕捉
- エラーログ出力
- 他のハンドラーは継続実行

### パフォーマンス劣化
- FPS低下を検出
- 自動的な品質調整
- 警告ログ出力