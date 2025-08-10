"""
PiCalendar インターフェース定義
Python 3.11+ 向けの型定義とプロトコル
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypedDict, Union
import pygame


# ====================
# Enum定義
# ====================

class WeekDay(Enum):
    """曜日定義"""
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


class WeatherIcon(Enum):
    """天気アイコン種別"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAIN = "rain"
    THUNDER = "thunder"
    SNOW = "snow"
    FOG = "fog"
    UNKNOWN = "unknown"


class ImageScaleMode(Enum):
    """画像スケーリングモード"""
    FIT = "fit"      # アスペクト比維持、レターボックス
    SCALE = "scale"  # 画面全体に拡大
    TILE = "tile"    # タイル表示
    CENTER = "center"  # 中央配置


class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ====================
# 設定関連の型定義
# ====================

@dataclass
class ScreenConfig:
    """画面設定"""
    width: int = 1024
    height: int = 600
    fps: int = 30
    fullscreen: bool = True
    hide_cursor: bool = True


@dataclass
class UIMargins:
    """UI余白設定"""
    x: int = 24
    y: int = 16


@dataclass
class UIConfig:
    """UI設定"""
    margins: UIMargins = field(default_factory=lambda: UIMargins())
    clock_font_px: int = 130
    date_font_px: int = 36
    cal_font_px: int = 22
    weather_font_px: int = 22
    
    # 色設定
    text_color: Tuple[int, int, int] = (255, 255, 255)
    sunday_color: Tuple[int, int, int] = (255, 100, 100)
    saturday_color: Tuple[int, int, int] = (100, 100, 255)
    weekday_color: Tuple[int, int, int] = (255, 255, 255)
    
    # レイアウト位置
    clock_position: Tuple[int, int] = (512, 100)  # 中央上部
    date_position: Tuple[int, int] = (512, 180)   # 時計下
    calendar_position: Tuple[int, int] = (580, 320)  # 右下
    weather_position: Tuple[int, int] = (24, 320)    # 左下
    character_position: Tuple[int, int] = (50, 50)   # 左上


@dataclass
class CalendarConfig:
    """カレンダー設定"""
    first_weekday: WeekDay = WeekDay.SUNDAY
    show_holidays: bool = False  # 将来拡張
    show_lunar: bool = False     # 将来拡張（六曜）


@dataclass
class BackgroundConfig:
    """背景設定"""
    dir: Path = Path("./wallpapers")
    mode: ImageScaleMode = ImageScaleMode.FIT
    rescan_sec: int = 300
    rotation_enabled: bool = False  # 将来拡張
    rotation_interval: int = 3600   # 将来拡張


@dataclass
class WeatherLocation:
    """天気取得位置"""
    lat: float = 35.681236
    lon: float = 139.767125
    city_code: Optional[str] = None  # Yahoo天気用


@dataclass
class WeatherConfig:
    """天気設定"""
    provider: str = "openmeteo"
    refresh_sec: int = 1800
    location: WeatherLocation = field(default_factory=WeatherLocation)
    timeout_sec: int = 10
    show_credit: bool = False  # Yahoo天気用
    
    # プロバイダ固有設定
    openmeteo_options: Dict[str, Any] = field(default_factory=dict)
    yahoo_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CharacterConfig:
    """2Dキャラクター設定"""
    enabled: bool = False
    sprite: Path = Path("./assets/sprites/char_idle.png")
    frame_w: int = 128
    frame_h: int = 128
    fps: int = 8
    scale: float = 1.0


@dataclass
class FontConfig:
    """フォント設定"""
    main: Path = Path("./assets/fonts/NotoSansCJK-Regular.otf")
    fallback: Optional[Path] = None


@dataclass
class LoggingConfig:
    """ログ設定"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    output: str = "stdout"  # stdout, file, journald
    file_path: Optional[Path] = None
    rotate_size_mb: int = 10
    rotate_count: int = 5


@dataclass
class AppConfig:
    """アプリケーション全体設定"""
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    character: CharacterConfig = field(default_factory=CharacterConfig)
    fonts: FontConfig = field(default_factory=FontConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


# ====================
# データモデル
# ====================

@dataclass
class WeatherForecast:
    """天気予報データ"""
    date: str  # YYYY-MM-DD
    icon: WeatherIcon
    temp_min: float
    temp_max: float
    pop: int  # 降水確率(%)
    description: Optional[str] = None


@dataclass
class WeatherData:
    """天気データセット"""
    updated: datetime
    forecasts: List[WeatherForecast]
    provider: str
    location: WeatherLocation
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class CalendarDay:
    """カレンダーの1日"""
    day: int
    weekday: WeekDay
    is_current_month: bool
    is_today: bool
    is_holiday: bool = False
    holiday_name: Optional[str] = None


@dataclass
class CalendarData:
    """カレンダーデータ"""
    year: int
    month: int
    days: List[List[Optional[CalendarDay]]]  # 6週 x 7日


@dataclass
class SpriteAnimation:
    """スプライトアニメーション"""
    frames: List[pygame.Surface]
    current_frame: int = 0
    frame_duration: float = 0.125  # 8fps = 1/8秒
    elapsed_time: float = 0.0


# ====================
# プロトコル定義（インターフェース）
# ====================

class WeatherProvider(Protocol):
    """天気情報プロバイダインターフェース"""
    
    def fetch(self) -> Optional[WeatherData]:
        """天気情報を取得"""
        ...
    
    def parse_response(self, response: Dict[str, Any]) -> WeatherData:
        """APIレスポンスを解析"""
        ...
    
    def get_cache_key(self) -> str:
        """キャッシュキーを生成"""
        ...


class Renderer(Protocol):
    """レンダラーインターフェース"""
    
    def render(self, surface: pygame.Surface) -> None:
        """サーフェスに描画"""
        ...
    
    def update(self, dt: float) -> None:
        """状態更新"""
        ...
    
    def is_dirty(self) -> bool:
        """再描画が必要か"""
        ...


class AssetLoader(Protocol):
    """アセットローダーインターフェース"""
    
    def load_image(self, path: Path) -> pygame.Surface:
        """画像読み込み"""
        ...
    
    def load_font(self, path: Path, size: int) -> pygame.font.Font:
        """フォント読み込み"""
        ...
    
    def load_sprite_sheet(self, path: Path, frame_size: Tuple[int, int]) -> List[pygame.Surface]:
        """スプライトシート読み込み"""
        ...


class CacheStorage(Protocol):
    """キャッシュストレージインターフェース"""
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュ保存"""
        ...
    
    def delete(self, key: str) -> None:
        """キャッシュ削除"""
        ...
    
    def clear(self) -> None:
        """全キャッシュクリア"""
        ...


# ====================
# 抽象基底クラス
# ====================

class BaseWeatherProvider(ABC):
    """天気プロバイダ基底クラス"""
    
    def __init__(self, config: WeatherConfig):
        self.config = config
        self._cache: Optional[WeatherData] = None
    
    @abstractmethod
    def fetch(self) -> Optional[WeatherData]:
        """天気情報を取得（実装必須）"""
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> WeatherData:
        """レスポンス解析（実装必須）"""
        pass
    
    def get_cache_key(self) -> str:
        """キャッシュキー生成"""
        loc = self.config.location
        return f"weather_{self.__class__.__name__}_{loc.lat}_{loc.lon}"
    
    def map_icon(self, condition: str) -> WeatherIcon:
        """天気条件をアイコンにマップ"""
        # デフォルト実装、プロバイダごとにオーバーライド可能
        mapping = {
            "clear": WeatherIcon.SUNNY,
            "sunny": WeatherIcon.SUNNY,
            "cloudy": WeatherIcon.CLOUDY,
            "rain": WeatherIcon.RAIN,
            "thunder": WeatherIcon.THUNDER,
            "snow": WeatherIcon.SNOW,
            "fog": WeatherIcon.FOG,
        }
        for key, icon in mapping.items():
            if key in condition.lower():
                return icon
        return WeatherIcon.UNKNOWN


class BaseRenderer(ABC):
    """レンダラー基底クラス"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._dirty = True
        self._last_update = datetime.now()
    
    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """描画処理（実装必須）"""
        pass
    
    def update(self, dt: float) -> None:
        """更新処理（オーバーライド可能）"""
        pass
    
    def is_dirty(self) -> bool:
        """再描画必要性チェック"""
        return self._dirty
    
    def mark_dirty(self) -> None:
        """再描画フラグ設定"""
        self._dirty = True
    
    def mark_clean(self) -> None:
        """再描画フラグクリア"""
        self._dirty = False


# ====================
# イベント型定義
# ====================

class EventType(Enum):
    """イベント種別"""
    QUIT = "quit"
    WEATHER_UPDATE = "weather_update"
    CONFIG_RELOAD = "config_reload"
    ASSET_CHANGE = "asset_change"
    ERROR = "error"


@dataclass
class AppEvent:
    """アプリケーションイベント"""
    type: EventType
    data: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


# ====================
# エラー定義
# ====================

class PiCalendarError(Exception):
    """基底エラークラス"""
    pass


class ConfigError(PiCalendarError):
    """設定エラー"""
    pass


class RenderError(PiCalendarError):
    """描画エラー"""
    pass


class WeatherFetchError(PiCalendarError):
    """天気取得エラー"""
    pass


class AssetLoadError(PiCalendarError):
    """アセット読み込みエラー"""
    pass