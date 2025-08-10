# TASK-202: 日付レンダラー実装 - 要件定義

## 概要

PiCalendarアプリケーションにおける日付表示機能を実装する。時計表示の直下に現在日付を表示し、毎分更新を行う。

## 機能要件

### FR-202-01: 日付表示機能
- 現在日付をYYYY-MM-DD (曜日)形式で表示
- 例: "2024-08-10 (土)" または "2024-08-10 (Sat)"  
- 毎分自動更新（秒単位の更新は不要）
- ローカル日付を使用（タイムゾーンはOS任せ）

### FR-202-02: 表示位置・サイズ
- 時計表示の直下に配置
- フォントサイズ: 36px（`settings.yaml`で設定可能）
- 位置: 時計の中央に合わせて配置
- 色: 白色（背景に応じて調整可能）

### FR-202-03: 曜日表示オプション
- 曜日表記の切替（日本語/英語）
- 日本語: (月), (火), (水), (木), (金), (土), (日)
- 英語: (Mon), (Tue), (Wed), (Thu), (Fri), (Sat), (Sun)
- `settings.yaml`で設定可能

### FR-202-04: レンダリング最適化
- テキスト再レンダリングの間引き（毎分のみ更新）
- pygame.font.Fontを使用した高品質レンダリング
- アンチエイリアシング適用

## 非機能要件

### NFR-202-01: パフォーマンス
- CPU使用率への影響を最小限に抑制
- メモリ使用量の効率化（フォントキャッシュ活用）
- 描画処理の最適化（日付変更時のみ再描画）

### NFR-202-02: 設定可能性
- `settings.yaml`でフォントサイズ・色・曜日表記設定可能
- フォントファイルの指定可能（時計レンダラーと共通）
- 表示フォーマットの拡張性

### NFR-202-03: 拡張性
- 日付フォーマット変更への対応準備
- 多言語対応への拡張性
- カスタム日付表示への対応

## 技術要件

### TR-202-01: 依存関係
- AssetManager（TASK-103）のフォントローダー使用
- pygame.font.Font使用
- Python標準datetime利用

### TR-202-02: アーキテクチャ
- DateRendererクラスとして実装
- レンダラーインターフェース準拠（ClockRendererと統一）
- 状態管理の分離

### TR-202-03: 設定管理
```yaml
ui:
  date_font_px: 36
  date_color: [255, 255, 255]  # RGB
  weekday_format: "japanese"   # japanese|english
fonts:
  main: "./assets/fonts/NotoSansCJK-Regular.otf"
```

## 受け入れ基準

### AC-202-01: 基本表示
- 画面起動時に現在日付が正しく表示される
- YYYY-MM-DD (曜日)形式で表示される
- 日付が毎分更新される（秒更新は不要）

### AC-202-02: 配置・見た目
- 時計表示の直下に配置される
- 指定されたフォントサイズで表示される
- 視認性の高い色で表示される
- 時計と水平中央が揃っている

### AC-202-03: 曜日表示
- 日本語設定時: "(月)", "(火)"等で表示
- 英語設定時: "(Mon)", "(Tue)"等で表示
- 設定変更が即座に反映される

### AC-202-04: パフォーマンス
- 日付更新によるCPU使用率が2%以下
- メモリリークが発生しない
- フォントキャッシュが正常に動作

### AC-202-05: 設定変更
- `settings.yaml`のフォントサイズ変更が反映される
- フォントファイル変更が反映される
- 色設定変更が反映される
- 曜日表記設定変更が反映される

## データフロー

```
Date Source (OS) → DateRenderer → Asset Manager → Font Cache → Rendered Surface → Main Display
                     ↓
                 Weekday Formatter (JP/EN)
```

## エラー処理

### EH-202-01: フォント読み込み失敗
- システムデフォルトフォントへフォールバック
- エラーログ出力
- 処理継続

### EH-202-02: 日付取得失敗
- 前回の日付を表示
- エラーログ出力
- 再取得試行

### EH-202-03: 設定値異常
- 不正な曜日フォーマット設定時はデフォルト値使用
- 不正なフォントサイズは範囲内にクランプ

## 実装クラス設計

### DateRenderer
```python
class DateRenderer:
    def __init__(self, asset_manager: AssetManager, settings: dict)
    def update(self) -> None  # 日付更新
    def render(self, surface: pygame.Surface, clock_rect: pygame.Rect) -> None  # 描画
    def get_current_date(self) -> str  # 現在日付取得
    def _format_date(self, dt: datetime) -> str  # 日付フォーマット
    def _format_weekday(self, dt: datetime) -> str  # 曜日フォーマット
    def set_weekday_format(self, format: str) -> None  # 曜日表記変更
```

## テスト戦略

### 単体テスト
- 日付フォーマット機能
- 曜日フォーマット機能（日/英切替）
- レンダリング機能
- 設定変更対応

### 統合テスト  
- AssetManagerとの連携
- ClockRendererとの位置関係
- メイン描画ループとの統合

### 性能テスト
- 描画パフォーマンス測定
- メモリ使用量測定

## 実装優先度

1. **High**: 基本的な日付表示機能
2. **High**: 曜日表示機能（日本語優先）
3. **Medium**: 設定変更対応
4. **Medium**: 英語曜日対応
5. **Low**: エラーハンドリング強化

## 連携要件

### CR-202-01: ClockRendererとの連携
- 時計の表示領域（pygame.Rect）を受け取り位置調整
- フォント設定の共有可能
- 同一のAssetManagerインスタンス使用

### CR-202-02: レイアウト調整
- 時計とのマージン調整（設定可能）
- 画面解像度変更への対応
- 複数レンダラーの垂直配置管理

## 関連ドキュメント

- [TASK-201: 時計レンダラー実装](../TASK-201/)
- [TASK-103: アセット管理システム](../TASK-103/)
- [設定管理仕様](../../specs/settings.md)
- [レンダリング仕様](../../specs/rendering.md)