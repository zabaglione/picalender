# TASK-203: カレンダーレンダラー実装 - Red Phase

## Red Phase実行結果

### テスト実行サマリー
- **総テスト数**: 25ケース
- **失敗**: 20ケース ✅（期待通り）
- **成功**: 5ケース（ダミーカラスのシンプル実装により成功）
- **実行時間**: 5.42秒

### 失敗テスト詳細

期待通りCalendarRendererクラスが存在しないため、以下のテストが失敗しました：

#### 1. 基本機能テスト (4/4失敗)
- `test_calendar_renderer_initialization` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'asset_manager'`
- `test_generate_calendar_data` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_generate_calendar_data'`
- `test_is_today_function` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_is_today'`

#### 2. レイアウト・描画テスト (4/4失敗)
- `test_calculate_cell_positions` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_calculate_cell_positions'`
- `test_basic_rendering` ❌
  - pygame関連メソッドが存在しない
- `test_render_header` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_render_header'`
- `test_render_date_cells` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_render_date_cells'`

#### 3. 色分け・ハイライトテスト (3/3失敗)
- `test_get_cell_color_weekdays` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_get_cell_color'`
- `test_today_highlight_colors` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_get_today_bg_color'`
- `test_color_override_for_today` ❌
  - 今日色優先ロジックが存在しない

#### 4. 更新・変更検知テスト (4/4失敗)
- `test_update_method` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'current_month'`
- `test_month_change_detection` ❌
  - 月変更検知ロジックが存在しない
- `test_day_change_highlight_update` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_get_today_date'`
- `test_same_month_optimization` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'calendar_data'`

#### 5. 設定・カスタマイズテスト (5/5失敗)
- `test_set_first_weekday_sunday` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute '_get_weekday_headers'`
- `test_set_first_weekday_monday` ❌
  - 週開始曜日変更機能が存在しない
- `test_font_size_configuration` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'font_size'`
- `test_position_setting` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'position_x'`
- `test_size_configuration` ❌
  - `AttributeError: 'CalendarRenderer' object has no attribute 'width'`

#### 6. エラーハンドリングテスト (1/3失敗)
- `test_invalid_settings_default_values` ❌
  - バリデーション機能が存在しない
- `test_empty_settings_handling` ✅（ダミークラスで成功）
- `test_invalid_font_path_fallback` ✅（ダミークラスで成功）

### 成功したテスト（5ケース）
これらはダミークラスの単純な実装により偶然成功しました：

1. `test_get_current_month` ✅
   - ダミー実装が固定値(2024, 8)を返すため成功
2. `test_empty_settings_handling` ✅
   - ダミークラスは例外を投げないため
3. `test_invalid_font_path_fallback` ✅
   - ダミークラスは例外を投げないため
4. `test_asset_manager_integration` ✅
   - ダミークラスは例外を投げないため
5. `test_full_workflow` ✅
   - ダミークラスは例外を投げないため

## 必要な実装項目（失敗から導出）

### 1. クラス基本構造
```python
class CalendarRenderer:
    def __init__(self, asset_manager: AssetManager, settings: Dict[str, Any])
    # 必要属性：
    # - self.asset_manager
    # - self.settings
    # - self.current_month, self.current_year
    # - self.calendar_data
    # - self.font_size, self.header_font_size
    # - self.position_x, self.position_y
    # - self.width, self.height
```

### 2. 内部メソッド群
```python
# カレンダーデータ生成
def _generate_calendar_data(self, year: int, month: int) -> List[List[int]]

# 今日判定
def _is_today(self, year: int, month: int, day: int) -> bool
def _get_today_date(self) -> int

# レイアウト計算
def _calculate_cell_positions(self) -> List[List[Tuple[int, int]]]

# 描画メソッド群
def _render_header(self, surface: pygame.Surface) -> None
def _render_date_cells(self, surface: pygame.Surface, calendar_data: List[List[int]]) -> None

# 色管理
def _get_cell_color(self, weekday: int, is_today: bool) -> List[int]
def _get_today_bg_color(self) -> List[int]
def _get_today_text_color(self) -> List[int]

# 曜日管理
def _get_weekday_headers(self) -> List[str]
```

### 3. パブリックメソッド
```python
def update(self) -> None
def render(self, surface: pygame.Surface) -> None
def get_current_month(self) -> Tuple[int, int]
def set_first_weekday(self, weekday: str) -> None
def set_position(self, x: int, y: int) -> None
def cleanup(self) -> None
```

## Red Phase成功確認

✅ **期待されたテスト失敗**: 20/25ケース
✅ **エラーメッセージの明確性**: AttributeError によりメソッド不足が明確
✅ **テストの網羅性**: 主要機能すべてをカバー

## 次ステップ（Green Phase）準備

1. **CalendarRenderer クラス実装**
   - 基本的なクラス構造
   - 必要な属性の初期化
   - ダミー実装から実際の機能実装への変更

2. **最小実装方針**
   - テストが通る最小限の実装
   - まずは基本的なカレンダー生成機能
   - 描画は後回し（テストが通る程度）

3. **実装優先順序**
   - 基本機能（カレンダーデータ生成、今日判定）
   - 設定管理（初期化、属性設定）
   - レイアウト計算（セル位置計算）
   - 描画基本（ヘッダ、日付セル）
   - 色分け機能
   - 更新・最適化機能

## TDD Red Phase完了

Red Phaseが期待通り完了しました。20件のテスト失敗により、CalendarRenderer実装に必要な機能が明確になりました。

Green Phaseで最小実装を行い、テストを通過させる段階に進みます。