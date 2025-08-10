# TASK-102: レンダリングループ実装 - 実装ドキュメント

## 概要
メインレンダリングループとレイヤー管理システムの実装詳細。

## 実装されたモジュール

### 1. RenderLoop (`src/rendering/render_loop.py`)

#### 責務
- メインレンダリングループの管理
- FPS制御
- イベント処理
- レイヤー管理
- 統計情報収集

#### 主要メソッド

| メソッド | 説明 | 引数 | 戻り値 |
|---------|------|------|--------|
| `__init__()` | 初期化 | display_manager, target_fps | None |
| `start()` | ループ開始 | duration: Optional[float] | None |
| `stop()` | ループ停止 | None | None |
| `pause()` | 一時停止 | None | None |
| `resume()` | 再開 | None | None |
| `add_layer()` | レイヤー追加 | layer, priority | None |
| `remove_layer()` | レイヤー削除 | layer | None |
| `add_event_handler()` | イベントハンドラー登録 | event_type, handler | None |
| `get_fps()` | 現在のFPS取得 | None | float |
| `get_stats()` | 統計情報取得 | None | Dict[str, Any] |

#### 内部メソッド

| メソッド | 説明 |
|---------|------|
| `_process_events()` | イベントキューを処理 |
| `_update_frame()` | フレーム更新処理 |
| `_render_frame()` | フレーム描画処理 |
| `_update_stats()` | 統計情報更新 |
| `_cleanup()` | 終了処理 |
| `_handle_memory_shortage()` | メモリ不足対応 |

#### プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `state` | LoopState | ループの状態 |
| `target_fps` | int | 目標FPS |
| `layers` | List[Tuple[Layer, int]] | レイヤーと優先順位 |
| `event_handlers` | Dict[int, List[Callable]] | イベントハンドラー |
| `stats` | Dict | 統計情報 |
| `reduced_quality` | bool | 品質低下モード |

### 2. Layer (`src/rendering/layer.py`)

#### 責務
- 描画オブジェクトの管理
- レイヤー単位の更新と描画
- 表示/非表示制御

#### 主要メソッド

| メソッド | 説明 | 引数 | 戻り値 |
|---------|------|------|--------|
| `__init__()` | 初期化 | name: str | None |
| `add_renderable()` | オブジェクト追加 | renderable | None |
| `remove_renderable()` | オブジェクト削除 | renderable | None |
| `update()` | 更新処理 | dt: float | None |
| `render()` | 描画処理 | surface | List[pygame.Rect] |
| `set_visible()` | 表示設定 | visible: bool | None |
| `is_visible()` | 表示状態取得 | None | bool |
| `is_dirty()` | 更新必要判定 | None | bool |
| `clear()` | 全オブジェクトクリア | None | None |

### 3. Renderable (`src/rendering/renderable.py`)

#### 責務
- 描画可能オブジェクトのインターフェース定義

#### 抽象メソッド

| メソッド | 説明 | 引数 | 戻り値 |
|---------|------|------|--------|
| `update()` | 更新処理 | dt: float | None |
| `render()` | 描画処理 | surface | Optional[pygame.Rect] |
| `get_bounds()` | 境界取得 | None | pygame.Rect |
| `is_dirty()` | 更新必要判定 | None | bool |

### 4. DirtyRegionManager (`src/rendering/dirty_region.py`)

#### 責務
- 更新が必要な画面領域の管理
- 領域の最適化と結合

#### 主要メソッド

| メソッド | 説明 | 引数 | 戻り値 |
|---------|------|------|--------|
| `add_rect()` | 領域追加 | rect | None |
| `get_dirty_rects()` | 領域リスト取得 | None | List[pygame.Rect] |
| `clear()` | クリア | None | None |
| `union_rects()` | 領域結合 | None | Optional[pygame.Rect] |
| `optimize()` | 最適化 | threshold | None |
| `is_empty()` | 空判定 | None | bool |

## アーキテクチャ

### レイヤー構造

```
RenderLoop
  ├── Layer (priority: 0) - 背景
  │     └── Renderable[] - 背景オブジェクト
  ├── Layer (priority: 10) - UI要素
  │     └── Renderable[] - 時計、カレンダー等
  └── Layer (priority: 20) - 前景
        └── Renderable[] - アニメーション等
```

### メインループフロー

```python
while running:
    1. イベント処理
       - pygame.event.get()
       - ハンドラー実行
    
    2. 更新処理
       - デルタタイム計算
       - 各レイヤーのupdate()
    
    3. 描画判定
       - フレームスキップチェック
       - ダーティリージョン収集
    
    4. 描画処理
       - レイヤー順に描画
       - 部分更新 or 全画面更新
    
    5. FPS制御
       - clock.tick(30)
       - 統計更新
```

### スレッドモデル

- メインループ: シングルスレッド
- イベント処理: メインスレッド内
- 描画: メインスレッド内
- 統計: メインスレッド内

## パフォーマンス最適化

### 実装された最適化

1. **ダーティリージョン管理**
   - 変更部分のみ再描画
   - 領域の自動結合

2. **フレームスキップ**
   - 処理遅延時に描画スキップ
   - 更新処理は継続

3. **レイヤーキャッシュ**
   - 非表示レイヤーはスキップ
   - dirtyフラグによる判定

4. **統計情報の軽量化**
   - 最新100フレームのみ保持
   - 移動平均によるFPS計算

## エラーハンドリング

### 実装されたエラー処理

1. **レンダリングエラー**
   - 個別オブジェクトの例外を隔離
   - エラーカウント記録
   - 処理継続

2. **イベントハンドラーエラー**
   - ハンドラー例外をキャッチ
   - 他のハンドラーは継続実行

3. **pygame未初期化対策**
   - pygame.get_init()チェック
   - 未初期化時は処理スキップ

4. **メモリ不足対応**
   - 品質低下モード
   - ガベージコレクション実行

## 統計情報

### 収集される統計

| 項目 | 説明 |
|------|------|
| `frames_rendered` | 描画されたフレーム数 |
| `frames_skipped` | スキップされたフレーム数 |
| `total_time` | 総実行時間 |
| `errors` | エラー発生数 |
| `current_fps` | 現在のFPS |
| `average_fps` | 平均FPS |
| `average_frame_time` | 平均フレーム時間 |

## テスト結果

- 総テスト数: 29
- 成功: 21
- 失敗: 6（環境依存）
- スキップ: 2

### 成功したテスト
- 基本的なループ制御
- レイヤー管理
- Renderableインターフェース
- ダーティリージョン管理
- エラーハンドリング
- メモリ管理

### 環境依存で失敗/スキップ
- FPS精密測定（タイミング依存）
- CPU使用率測定（環境依存）
- 長時間動作テスト（時間がかかる）

## 使用例

```python
from src.display import DisplayManager
from src.rendering import RenderLoop, Layer
from src.core import ConfigManager

# 初期化
config = ConfigManager("settings.yaml")
display = DisplayManager(config)
display.initialize()
display.create_screen()

# レンダリングループ作成
render_loop = RenderLoop(display, target_fps=30)

# レイヤー追加
background_layer = Layer("background")
ui_layer = Layer("ui")
render_loop.add_layer(background_layer, priority=0)
render_loop.add_layer(ui_layer, priority=10)

# イベントハンドラー登録
def on_key_press(event):
    if event.key == pygame.K_ESCAPE:
        render_loop.stop()

render_loop.add_event_handler(pygame.KEYDOWN, on_key_press)

# メインループ開始
render_loop.start()
```

## 既知の制限事項

1. **シングルスレッド**
   - すべての処理がメインスレッドで実行
   - 重い処理でブロッキング発生

2. **pygame依存**
   - イベントシステムがpygameに依存
   - 初期化が必要

3. **メモリ管理**
   - 手動でのガベージコレクション
   - psutil依存（オプション）

## 今後の改善案

1. **マルチスレッド化**
   - 更新と描画の分離
   - 非同期イベント処理

2. **最適化**
   - より効率的なダーティリージョン
   - GPUアクセラレーション活用

3. **機能拡張**
   - エフェクトシステム
   - トランジション
   - アニメーション管理