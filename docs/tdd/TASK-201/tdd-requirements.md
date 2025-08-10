# TASK-201: 時計レンダラー実装 - 要件定義

## 概要

PiCalendarアプリケーションにおけるデジタル時計表示機能を実装する。画面上部中央に現在時刻を大きく表示し、毎秒更新を行う。

## 機能要件

### FR-201-01: 時計表示機能
- 現在時刻をHH:MM:SS形式で表示
- 24時間表記を使用
- 毎秒自動更新
- リアルタイム表示（NTP同期はOS任せ）

### FR-201-02: 表示位置・サイズ
- 画面上部中央に配置
- フォントサイズ: 130px（`settings.yaml`で設定可能）
- 位置: 上部中央、マージンを考慮
- 色: 白色（背景に応じて調整可能）

### FR-201-03: レンダリング最適化
- テキスト再レンダリングの間引き（毎秒のみ更新）
- pygame.font.Fontを使用した高品質レンダリング
- アンチエイリアシング適用

## 非機能要件

### NFR-201-01: パフォーマンス
- CPU使用率への影響を最小限に抑制
- メモリ使用量の効率化（フォントキャッシュ活用）
- 描画処理の最適化

### NFR-201-02: 設定可能性
- `settings.yaml`でフォントサイズ設定可能
- フォントファイルの指定可能
- 表示色の設定可能

### NFR-201-03: 拡張性
- 12時間表記への対応準備
- タイムゾーン対応への拡張性
- フォーマット変更への対応

## 技術要件

### TR-201-01: 依存関係
- AssetManager（TASK-103）のフォントローダー使用
- pygame.font.Font使用
- Python標準datetime利用

### TR-201-02: アーキテクチャ
- ClockRendererクラスとして実装
- レンダラーインターフェース準拠
- 状態管理の分離

### TR-201-03: 設定管理
```yaml
ui:
  clock_font_px: 130
  clock_color: [255, 255, 255]  # RGB
fonts:
  main: "./assets/fonts/NotoSansCJK-Regular.otf"
```

## 受け入れ基準

### AC-201-01: 基本表示
- 画面起動時に現在時刻が正しく表示される
- HH:MM:SS形式で24時間表記
- 時刻が毎秒更新される

### AC-201-02: 配置・見た目
- 画面上部中央に配置される
- 指定されたフォントサイズで表示される
- 視認性の高い色で表示される

### AC-201-03: パフォーマンス
- 時計更新によるCPU使用率が3%以下
- メモリリークが発生しない
- フォントキャッシュが正常に動作

### AC-201-04: 設定変更
- `settings.yaml`のフォントサイズ変更が反映される
- フォントファイル変更が反映される
- 色設定変更が反映される

## データフロー

```
Time Source (OS) → ClockRenderer → Asset Manager → Font Cache → Rendered Surface → Main Display
```

## エラー処理

### EH-201-01: フォント読み込み失敗
- システムデフォルトフォントへフォールバック
- エラーログ出力
- 処理継続

### EH-201-02: 時刻取得失敗
- 前回の時刻を表示
- エラーログ出力
- 再取得試行

## 実装クラス設計

### ClockRenderer
```python
class ClockRenderer:
    def __init__(self, asset_manager: AssetManager, settings: dict)
    def update(self) -> None  # 時刻更新
    def render(self, surface: pygame.Surface) -> None  # 描画
    def get_current_time(self) -> str  # 現在時刻取得
    def _format_time(self, dt: datetime) -> str  # 時刻フォーマット
```

## テスト戦略

### 単体テスト
- 時刻フォーマット機能
- レンダリング機能
- 設定変更対応

### 統合テスト  
- AssetManagerとの連携
- メイン描画ループとの統合

### 性能テスト
- 描画パフォーマンス測定
- メモリ使用量測定

## 実装優先度

1. **High**: 基本的な時刻表示機能
2. **High**: 毎秒更新機能
3. **Medium**: 設定変更対応
4. **Low**: エラーハンドリング強化

## 関連ドキュメント

- [TASK-103: アセット管理システム](../TASK-103/)
- [設定管理仕様](../../specs/settings.md)
- [レンダリング仕様](../../specs/rendering.md)