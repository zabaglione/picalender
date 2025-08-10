# PiCalendar API Documentation

## 目次

1. [コアモジュール](#コアモジュール)
2. [ディスプレイシステム](#ディスプレイシステム)
3. [レンダラー](#レンダラー)
4. [天気システム](#天気システム)
5. [キャラクターシステム](#キャラクターシステム)
6. [ユーティリティ](#ユーティリティ)

## コアモジュール

### ConfigManager

設定ファイルの読み込みと管理を行うクラス。

```python
from src.core.config_manager import ConfigManager

# 初期化
config = ConfigManager("settings.yaml")

# 設定の取得
screen_width = config.get("screen.width")
weather_settings = config.get("weather")

# 設定の更新
config.set("screen.fps", 30)

# 設定の保存
config.save("settings.yaml")

# デフォルト値付き取得
fps = config.get("screen.fps", default=30)
```

**メソッド:**

| メソッド | 説明 | パラメータ | 戻り値 |
|---------|------|-----------|--------|
| `__init__(config_path)` | 設定ファイルを読み込む | `config_path: str` | None |
| `get(key, default=None)` | 設定値を取得 | `key: str`, `default: Any` | Any |
| `set(key, value)` | 設定値を更新 | `key: str`, `value: Any` | None |
| `save(path)` | 設定を保存 | `path: str` | None |
| `get_all()` | 全設定を取得 | None | Dict |

### LogManager

ログシステムの管理クラス。

```python
from src.core.log_manager import LogManager

# 初期化
log_manager = LogManager(settings)
logger = log_manager.logger

# ログ出力
logger.info("Application started")
logger.warning("Memory usage high")
logger.error("Failed to connect", exc_info=True)
```

**ログレベル:**

- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報
- `WARNING`: 警告メッセージ
- `ERROR`: エラー情報
- `CRITICAL`: 致命的なエラー

### ErrorRecoveryManager

エラーからの自動復旧を管理するクラス。

```python
from src.core.error_recovery import ErrorRecoveryManager

# 初期化
recovery = ErrorRecoveryManager(settings)

# 関数のラップ
@recovery.wrap_with_recovery
def risky_operation():
    # エラーが発生する可能性のある処理
    pass

# エラーハンドリング
try:
    operation()
except Exception as e:
    if recovery.handle_error(e):
        # リカバリ成功
        retry_operation()
    else:
        # リカバリ失敗
        raise

# 統計取得
stats = recovery.get_recovery_stats()
```

**リカバリ戦略:**

| エラータイプ | 戦略 | 説明 |
|-------------|------|------|
| NetworkError | リトライ+バックオフ | 指数バックオフでリトライ |
| FileSystemError | 代替パス使用 | 別の場所に保存/読み込み |
| MemoryError | メモリ解放 | キャッシュクリア、GC実行 |

### PerformanceOptimizer

パフォーマンスの最適化を行うクラス。

```python
from src.core.performance_optimizer import PerformanceOptimizer

# 初期化
optimizer = PerformanceOptimizer(settings)

# パフォーマンス監視
perf = optimizer.monitor_performance()
print(f"CPU: {perf['cpu_percent']}%, Memory: {perf['memory_mb']}MB")

# 品質自動調整
optimizer.auto_adjust_quality(current_fps=20)

# 最適化設定取得
settings = optimizer.get_optimized_settings()

# メモリ解放
optimizer.free_memory()

# Dirty Rectangle管理
optimizer.add_dirty_rect(pygame.Rect(0, 0, 100, 100))
dirty_rects = optimizer.get_dirty_rects()
```

**品質レベル:**

```python
QUALITY_LEVELS = {
    'ultra_low': {'fps': 10, 'cache_size': 10},
    'low': {'fps': 15, 'cache_size': 20},
    'medium': {'fps': 20, 'cache_size': 50},
    'high': {'fps': 30, 'cache_size': 100}
}
```

## ディスプレイシステム

### DisplayManager

画面表示を管理するクラス。

```python
from src.display.display_manager import DisplayManager

# 初期化
display = DisplayManager(settings)

# 画面取得
screen = display.screen

# 画面更新
display.flip()

# フルスクリーン切り替え
display.toggle_fullscreen()

# 画面クリア
display.clear(color=(0, 0, 0))
```

**プロパティ:**

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `screen` | pygame.Surface | 画面サーフェース |
| `width` | int | 画面幅 |
| `height` | int | 画面高さ |
| `fullscreen` | bool | フルスクリーン状態 |

### AssetManager

アセット（フォント、画像等）を管理するクラス。

```python
from src.assets.asset_manager import AssetManager

# 初期化
assets = AssetManager(settings)

# フォント取得
font = assets.get_font("main", size=48)

# 画像読み込み
image = assets.load_image("background.jpg")

# スプライトシート読み込み
sprite_sheet = assets.load_sprite_sheet("character.png", frame_width=128, frame_height=128)

# キャッシュクリア
assets.clear_cache()
```

## レンダラー

### ClockRenderer

時計を描画するレンダラー。

```python
from src.renderers.clock_renderer import ClockRenderer

# 初期化
clock = ClockRenderer(settings)

# 描画
clock.render(screen)

# 更新間隔確認
if clock.should_update():
    clock.update()
```

**設定オプション:**

```yaml
ui:
  clock_font_px: 130
  clock_color: [255, 255, 255]
  clock_position: "center"  # center, top-left, top-right, etc.
```

### DateRenderer

日付を描画するレンダラー。

```python
from src.renderers.date_renderer import DateRenderer

# 初期化
date = DateRenderer(settings)

# 描画
date.render(screen)

# フォーマット変更
date.set_format("%Y年%m月%d日 (%a)")
```

### CalendarRenderer

カレンダーを描画するレンダラー。

```python
from src.renderers.calendar_renderer import CalendarRenderer

# 初期化
calendar = CalendarRenderer(settings)

# 描画
calendar.render(screen)

# 月変更
calendar.set_month(2025, 1)

# 日付ハイライト
calendar.highlight_date(15)
```

**カスタマイズ:**

```yaml
calendar:
  first_weekday: "SUNDAY"  # SUNDAY or MONDAY
  colors:
    sunday: [255, 100, 100]
    saturday: [100, 100, 255]
    weekday: [255, 255, 255]
    today: [255, 255, 100]
```

### WeatherPanelRenderer

天気パネルを描画するレンダラー。

```python
from src.renderers.weather_panel_renderer import WeatherPanelRenderer

# 初期化
weather_panel = WeatherPanelRenderer(settings)

# 天気データ設定
weather_data = {
    "forecasts": [
        {"date": "2025-01-11", "icon": "sunny", "tmin": 5, "tmax": 15, "pop": 10},
        {"date": "2025-01-12", "icon": "cloudy", "tmin": 7, "tmax": 17, "pop": 20},
        {"date": "2025-01-13", "icon": "rain", "tmin": 8, "tmax": 16, "pop": 80}
    ]
}
weather_panel.set_weather_data(weather_data)

# 描画
weather_panel.render(screen)
```

## 天気システム

### WeatherProvider (基底クラス)

```python
from src.weather.providers.base import WeatherProvider

class CustomProvider(WeatherProvider):
    def fetch(self) -> Dict[str, Any]:
        # APIから天気データを取得
        return {
            "updated": time.time(),
            "forecasts": [...]
        }
```

### OpenMeteoProvider

Open-Meteo APIを使用する天気プロバイダ。

```python
from src.weather.providers.openmeteo import OpenMeteoProvider

# 初期化
provider = OpenMeteoProvider(settings)

# 天気取得
weather_data = provider.fetch()

# エラーハンドリング付き取得
try:
    weather_data = provider.fetch_with_retry(max_retries=3)
except WeatherFetchError as e:
    logger.error(f"Failed to fetch weather: {e}")
```

### WeatherCache

天気データのキャッシュシステム。

```python
from src.weather.cache.weather_cache import WeatherCache

# 初期化
cache = WeatherCache(settings)

# キャッシュ保存
cache.set("weather_data", weather_data)

# キャッシュ取得
data = cache.get("weather_data")
if data is None:
    # キャッシュミス - 新規取得が必要
    pass

# フォールバック付き取得
data = cache.get("weather_data", fallback=True)

# キャッシュクリア
cache.clear()
```

### WeatherThread

バックグラウンドで天気情報を取得するスレッド。

```python
from src.weather.thread.weather_thread import WeatherThread

# 初期化
thread = WeatherThread(provider, cache, settings)

# スレッド開始
thread.start()

# 最新データ取得
weather_data = thread.get_latest_data()

# スレッド停止
thread.stop(timeout=5)
```

## キャラクターシステム

### CharacterRenderer

2Dキャラクターを描画するレンダラー。

```python
from src.character.character_renderer import CharacterRenderer

# 初期化
character = CharacterRenderer(settings)

# アニメーション設定
character.set_animation("idle")

# 描画
character.render(screen)

# アニメーション更新
character.update(dt)

# 位置設定
character.set_position(100, 200)
```

### AnimationSystem

アニメーションを管理するシステム。

```python
from src.character.animation_system import AnimationSystem

# 初期化
anim_system = AnimationSystem()

# アニメーション追加
anim_system.add_animation("idle", frames=[0, 1, 2, 3], fps=8)
anim_system.add_animation("walk", frames=[4, 5, 6, 7], fps=12)

# アニメーション切り替え
anim_system.set_animation("walk")

# 更新
anim_system.update(dt)
current_frame = anim_system.get_current_frame()
```

### WeatherBehaviorSystem

天気に応じてキャラクターの動作を変更するシステム。

```python
from src.character.weather_behavior_system import WeatherBehaviorSystem

# 初期化
behavior = WeatherBehaviorSystem()

# 天気に応じた動作取得
weather_code = "sunny"
animation = behavior.get_animation_for_weather(weather_code)
# Returns: "happy"

# カスタム動作マッピング
behavior.register_behavior("rain", "umbrella")
behavior.register_behavior("snow", "cold")
```

## ユーティリティ

### Dirty Rectangle最適化

```python
from src.core.performance_optimizer import DirtyRectManager

# 初期化
dirty_manager = DirtyRectManager()

# 更新領域追加
dirty_manager.add(pygame.Rect(100, 100, 200, 200))

# 領域統合
merged_rects = dirty_manager.get_merged_rects()

# 部分更新
pygame.display.update(merged_rects)

# クリア
dirty_manager.clear()
```

### イベントシステム

```python
from src.core.event_system import EventSystem

# 初期化
events = EventSystem()

# イベントリスナー登録
def on_weather_update(data):
    print(f"Weather updated: {data}")

events.on("weather_update", on_weather_update)

# イベント発火
events.emit("weather_update", weather_data)

# リスナー削除
events.off("weather_update", on_weather_update)
```

### ファイル監視

```python
from src.assets.file_watcher import FileWatcher

# 初期化
watcher = FileWatcher()

# ディレクトリ監視
def on_file_change(path):
    print(f"File changed: {path}")

watcher.watch("wallpapers/", on_file_change)

# 監視開始
watcher.start()

# 監視停止
watcher.stop()
```

## エラーハンドリング

### カスタム例外

```python
# 天気システムの例外
from src.weather.providers.exceptions import (
    WeatherFetchError,
    WeatherAPIError,
    WeatherCacheError
)

# キャラクターシステムの例外
from src.character.exceptions import (
    AnimationNotFoundError,
    SpriteLoadError
)

# 使用例
try:
    weather_data = provider.fetch()
except WeatherAPIError as e:
    logger.error(f"API error: {e.status_code}")
except WeatherFetchError as e:
    logger.error(f"Fetch failed: {e}")
```

## テスト

### ユニットテスト例

```python
import unittest
from unittest.mock import Mock, patch
from src.renderers.clock_renderer import ClockRenderer

class TestClockRenderer(unittest.TestCase):
    def setUp(self):
        self.settings = {"ui": {"clock_font_px": 48}}
        self.renderer = ClockRenderer(self.settings)
    
    def test_format_time(self):
        with patch('time.strftime') as mock_time:
            mock_time.return_value = "12:34:56"
            time_str = self.renderer.get_time_string()
            self.assertEqual(time_str, "12:34:56")
    
    def test_should_update(self):
        self.assertTrue(self.renderer.should_update())
```

### 統合テスト例

```python
import pytest
from src.weather.providers.openmeteo import OpenMeteoProvider
from src.weather.cache.weather_cache import WeatherCache

@pytest.mark.integration
def test_weather_system():
    settings = {
        "weather": {
            "location": {"latitude": 35.681, "longitude": 139.767},
            "cache": {"directory": "/tmp/test_cache"}
        }
    }
    
    provider = OpenMeteoProvider(settings)
    cache = WeatherCache(settings)
    
    # 天気取得とキャッシュ
    weather_data = provider.fetch()
    cache.set("test_weather", weather_data)
    
    # キャッシュから取得
    cached_data = cache.get("test_weather")
    assert cached_data is not None
    assert cached_data["forecasts"] == weather_data["forecasts"]
```

## パフォーマンス最適化のベストプラクティス

### 1. 更新間隔の最適化

```python
class OptimizedRenderer:
    def __init__(self):
        self.last_update = 0
        self.update_interval = 1.0  # 1秒ごと
    
    def should_update(self):
        now = time.time()
        if now - self.last_update >= self.update_interval:
            self.last_update = now
            return True
        return False
    
    def render(self, screen):
        if self.should_update():
            self.update_content()
        self.draw(screen)
```

### 2. キャッシュの活用

```python
class CachedRenderer:
    def __init__(self):
        self.cache = {}
    
    def get_cached_surface(self, key, generator):
        if key not in self.cache:
            self.cache[key] = generator()
        return self.cache[key]
    
    def render(self, screen):
        surface = self.get_cached_surface(
            "content",
            lambda: self.generate_surface()
        )
        screen.blit(surface, self.position)
```

### 3. Dirty Rectangle最適化

```python
class DirtyRenderer:
    def __init__(self):
        self.dirty = False
        self.rect = pygame.Rect(0, 0, 100, 100)
    
    def update(self):
        # 内容を更新
        self.dirty = True
    
    def render(self, screen):
        if self.dirty:
            # 変更された部分のみ描画
            self.draw(screen)
            pygame.display.update(self.rect)
            self.dirty = False
```

## 設定ファイル完全リファレンス

```yaml
# 画面設定
screen:
  width: 1024              # 画面幅
  height: 600              # 画面高さ
  fps: 30                  # フレームレート
  fullscreen: true         # フルスクリーン
  vsync: false            # 垂直同期

# UI設定
ui:
  margins: 
    x: 24                 # 左右マージン
    y: 16                 # 上下マージン
  clock_font_px: 130      # 時計フォントサイズ
  date_font_px: 36        # 日付フォントサイズ
  calendar_font_px: 22    # カレンダーフォントサイズ
  weather_font_px: 22     # 天気フォントサイズ
  update_intervals:       # 更新間隔（秒）
    clock: 1
    date: 60
    calendar: 60
    weather: 300

# 天気設定
weather:
  provider: openmeteo     # プロバイダ選択
  location:
    latitude: 35.681236   # 緯度
    longitude: 139.767125 # 経度
  refresh_sec: 1800       # 更新間隔（秒）
  cache:
    enabled: true         # キャッシュ有効化
    directory: ./cache/weather
    ttl: 7200            # TTL（秒）
    max_size: 100        # 最大エントリ数
  thread:
    enabled: true        # バックグラウンド更新
    update_interval: 1800 # 更新間隔（秒）

# キャラクター設定
character:
  enabled: false         # 有効/無効
  sprite: ./assets/sprites/char_idle.png
  frame_w: 128          # フレーム幅
  frame_h: 128          # フレーム高さ
  fps: 8                # アニメーションFPS
  position:
    x: 50               # X座標
    y: 50               # Y座標
  weather_aware: true   # 天気連動

# 背景設定
background:
  directory: ./wallpapers
  mode: fit             # fit, scale, fill, tile
  rescan_sec: 300       # 再スキャン間隔
  cache_images: true    # 画像キャッシュ

# パフォーマンス設定
performance:
  auto_adjust: true     # 自動調整
  default_quality: medium # ultra_low, low, medium, high
  monitor_interval: 10  # 監視間隔（秒）
  thresholds:
    cpu_high: 50        # CPU使用率閾値（%）
    memory_high: 200    # メモリ使用量閾値（MB）
    fps_low: 15         # 低FPS閾値

# エラーリカバリ設定
error_recovery:
  enabled: true         # 有効/無効
  network:
    max_retries: 3      # 最大リトライ回数
    backoff_factor: 2.0 # バックオフ係数
    max_backoff: 60     # 最大バックオフ（秒）
  filesystem:
    fallback_paths:     # フォールバックパス
      - /tmp
      - /var/tmp
  memory:
    threshold_mb: 50    # メモリ不足閾値
    cleanup_aggressive: false

# フォント設定
fonts:
  main: ./assets/fonts/NotoSansCJK-Regular.otf
  fallback: /usr/share/fonts/truetype/noto/NotoSansCJK-Regular.otf

# ログ設定
logging:
  level: INFO          # DEBUG, INFO, WARNING, ERROR
  file: ./logs/picalender.log
  max_size: 10485760   # 10MB
  backup_count: 5      # バックアップ数
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

最終更新日: 2025年1月11日
バージョン: 1.0.0