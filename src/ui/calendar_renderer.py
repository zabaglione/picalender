"""
カレンダー表示コンポーネント

月間カレンダーをグリッド形式で表示するレンダラー。
日曜始まりで、今日の日付をハイライト表示。
"""

import logging
import calendar
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any
import pygame

from src.rendering.renderable import Renderable

logger = logging.getLogger(__name__)


class CalendarRenderer(Renderable):
    """
    カレンダー表示レンダラー
    
    Attributes:
        WEEKDAYS_JP: 日本語の曜日名（短縮）
        WEEKDAYS_EN: 英語の曜日名（短縮）
        DEFAULT_FONT_SIZE: デフォルトのフォントサイズ
        HEADER_HEIGHT_RATIO: ヘッダー高さの比率
    """
    
    WEEKDAYS_JP: List[str] = ['日', '月', '火', '水', '木', '金', '土']
    WEEKDAYS_EN: List[str] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    DEFAULT_FONT_SIZE: int = 22
    HEADER_HEIGHT_RATIO: float = 0.15  # ヘッダーは全体の15%
    MAX_WEEKS: int = 6  # カレンダー表示の最大週数
    DAYS_IN_WEEK: int = 7  # 1週間の日数
    CELL_PADDING: int = 2  # セル内のパディング
    
    def __init__(self, asset_manager: Any, config: Any) -> None:
        """
        初期化
        
        Args:
            asset_manager: アセット管理オブジェクト
            config: 設定管理オブジェクト
        """
        self.asset_manager = asset_manager
        self.config = config
        
        # 設定値の取得
        self.font_size: int = config.get('ui.cal_font_px', self.DEFAULT_FONT_SIZE)
        self.weekday_color: Tuple[int, int, int] = config.get('ui.cal_weekday_color', (200, 200, 200))
        self.sunday_color: Tuple[int, int, int] = config.get('ui.cal_sunday_color', (255, 128, 128))
        self.saturday_color: Tuple[int, int, int] = config.get('ui.cal_saturday_color', (128, 128, 255))
        self.today_bg_color: Tuple[int, int, int] = config.get('ui.cal_today_bg_color', (64, 64, 128))
        self.position_type: str = config.get('ui.cal_position', 'bottom_right')
        self.width: int = config.get('ui.cal_width', 420)
        self.height: int = config.get('ui.cal_height', 280)
        self.weekday_lang: str = config.get('ui.cal_weekday_lang', 'jp')
        self.margin_x: int = config.get('ui.margins.x', 24)
        self.margin_y: int = config.get('ui.margins.y', 16)
        self.screen_width: int = config.get('screen.width', 1024)
        self.screen_height: int = config.get('screen.height', 600)
        
        # フォント読み込み
        self.font: Optional[pygame.font.Font] = None
        self._load_font()
        
        # カレンダー設定（日曜始まり）
        calendar.setfirstweekday(calendar.SUNDAY)
        
        # 状態管理
        self.visible: bool = True
        self._dirty: bool = True
        self._current_month: int = 0
        self._current_year: int = 0
        self._current_day: int = 0
        self._calendar_surface: Optional[pygame.Surface] = None
        self._position: Optional[Tuple[int, int]] = None
        self._dirty_rect: Optional[pygame.Rect] = None
    
    def _load_font(self) -> None:
        """フォントを読み込み"""
        try:
            font_name = self.config.get('fonts.calendar', 'NotoSansCJK-Regular')
            self.font = self.asset_manager.load_font(font_name, self.font_size)
            
            if not self.font:
                logger.warning("Failed to load custom font, using pygame default")
                self.font = pygame.font.Font(None, self.font_size)
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            self.font = pygame.font.Font(None, self.font_size)
    
    def get_calendar_data(self, year: int, month: int) -> List[List[int]]:
        """
        指定月のカレンダーデータを取得
        
        Args:
            year: 年
            month: 月
            
        Returns:
            週ごとの日付リスト（0は空白日）
        """
        cal = calendar.monthcalendar(year, month)
        # 6週分を確保（表示を統一するため）
        while len(cal) < self.MAX_WEEKS:
            cal.append([0] * self.DAYS_IN_WEEK)
        return cal
    
    def get_weekday_headers(self) -> List[str]:
        """
        曜日ヘッダーを取得
        
        Returns:
            曜日名のリスト
        """
        if self.weekday_lang == 'en':
            return self.WEEKDAYS_EN
        else:
            return self.WEEKDAYS_JP
    
    def get_today(self) -> int:
        """
        今日の日付を取得
        
        Returns:
            今日の日（1-31）
        """
        return datetime.now().day
    
    def is_today(self, day: int) -> bool:
        """
        指定日が今日かどうか
        
        Args:
            day: 日（1-31）
            
        Returns:
            今日の場合True
        """
        now = datetime.now()
        # 初回の場合は現在の月と年を設定
        if self._current_month == 0:
            self._current_month = now.month
            self._current_year = now.year
        
        return (day == now.day and 
                self._current_month == now.month and 
                self._current_year == now.year)
    
    def get_day_color(self, col_index: int, day: int, is_today: bool) -> Tuple[int, int, int]:
        """
        日付の表示色を取得
        
        Args:
            col_index: 列インデックス（0=日曜、6=土曜）
            day: 日付
            is_today: 今日かどうか
            
        Returns:
            RGB色
        """
        if col_index == 0:  # 日曜日
            return self.sunday_color
        elif col_index == 6:  # 土曜日
            return self.saturday_color
        else:
            return self.weekday_color
    
    def calculate_position(self) -> Tuple[int, int]:
        """
        表示位置を計算
        
        Returns:
            (x, y) 座標のタプル
        """
        if self.position_type == 'bottom_right':
            x = self.screen_width - self.width - self.margin_x
            y = self.screen_height - self.height - self.margin_y
        elif self.position_type == 'bottom_left':
            x = self.margin_x
            y = self.screen_height - self.height - self.margin_y
        elif self.position_type == 'top_right':
            x = self.screen_width - self.width - self.margin_x
            y = self.margin_y
        elif self.position_type == 'top_left':
            x = self.margin_x
            y = self.margin_y
        else:
            # デフォルト: bottom_right
            x = self.screen_width - self.width - self.margin_x
            y = self.screen_height - self.height - self.margin_y
        
        return (x, y)
    
    def calculate_cell_size(self) -> Tuple[int, int]:
        """
        セルサイズを計算
        
        Returns:
            (幅, 高さ) のタプル
        """
        cell_width = self.width // self.DAYS_IN_WEEK
        header_height = int(self.height * self.HEADER_HEIGHT_RATIO)
        cell_height = (self.height - header_height) // self.MAX_WEEKS
        return (cell_width, cell_height)
    
    def _render_calendar_grid(self) -> pygame.Surface:
        """
        カレンダーグリッドをレンダリング
        
        Returns:
            レンダリングされたサーフェス
        """
        # 透明な背景のサーフェスを作成
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # 完全透明
        
        if not self.font:
            return surface
        
        cell_width, cell_height = self.calculate_cell_size()
        header_height = int(self.height * self.HEADER_HEIGHT_RATIO)
        
        # 曜日ヘッダーを描画
        headers = self.get_weekday_headers()
        for i, header in enumerate(headers):
            x = i * cell_width + cell_width // 2
            y = header_height // 2
            
            # 曜日の色
            if i == 0:
                color = self.sunday_color
            elif i == 6:
                color = self.saturday_color
            else:
                color = self.weekday_color
            
            text_surface = self.font.render(header, True, color)
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)
        
        # カレンダーデータを取得
        cal_data = self.get_calendar_data(self._current_year, self._current_month)
        today = self.get_today()
        
        # 日付を描画
        for week_idx, week in enumerate(cal_data):
            for day_idx, day in enumerate(week):
                if day == 0:
                    continue
                
                x = day_idx * cell_width + cell_width // 2
                y = header_height + week_idx * cell_height + cell_height // 2
                
                # 今日の背景を描画
                if self.is_today(day):
                    bg_rect = pygame.Rect(
                        day_idx * cell_width + self.CELL_PADDING,
                        header_height + week_idx * cell_height + self.CELL_PADDING,
                        cell_width - self.CELL_PADDING * 2,
                        cell_height - self.CELL_PADDING * 2
                    )
                    pygame.draw.rect(surface, self.today_bg_color, bg_rect)
                    pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1)  # 白い枠線
                
                # 日付の色を取得
                color = self.get_day_color(day_idx, day, self.is_today(day))
                
                # 日付を描画
                text_surface = self.font.render(str(day), True, color)
                text_rect = text_surface.get_rect(center=(x, y))
                surface.blit(text_surface, text_rect)
        
        return surface
    
    def update(self, dt: float) -> None:
        """
        更新処理
        
        Args:
            dt: 前フレームからの経過時間（秒）
        """
        if not self.visible:
            return
        
        now = datetime.now()
        
        # 月または日が変わった場合にdirtyフラグを立てる
        if (now.month != self._current_month or 
            now.year != self._current_year or
            now.day != self._current_day):
            
            self._current_month = now.month
            self._current_year = now.year
            self._current_day = now.day
            self._dirty = True
            self._calendar_surface = None  # キャッシュをクリア
    
    def render(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """
        描画処理
        
        Args:
            surface: 描画対象のサーフェス
            
        Returns:
            更新された領域のリスト
        """
        if not self.visible:
            return []
        
        if not self._dirty:
            return []
        
        if not self.font:
            return []
        
        # 初回または月が変わった場合
        if self._current_month == 0:
            now = datetime.now()
            self._current_month = now.month
            self._current_year = now.year
            self._current_day = now.day
        
        dirty_rects = []
        
        try:
            # カレンダーグリッドをレンダリング（キャッシュチェック）
            if self._calendar_surface is None:
                self._calendar_surface = self._render_calendar_grid()
            
            # 位置の計算
            if self._position is None:
                self._position = self.calculate_position()
            
            # dirtyレクトの作成
            rect = pygame.Rect(
                self._position[0],
                self._position[1],
                self.width,
                self.height
            )
            dirty_rects.append(rect)
            self._dirty_rect = rect
            
            # 描画（pygameのSurfaceかどうかチェック）
            if isinstance(surface, pygame.Surface):
                surface.blit(self._calendar_surface, self._position)
            
            # dirtyフラグをクリア
            self._dirty = False
            
        except Exception as e:
            logger.error(f"Error rendering calendar: {e}")
            self._dirty = False
        
        return dirty_rects
    
    def is_dirty(self) -> bool:
        """
        更新が必要かどうか
        
        Returns:
            更新が必要な場合True
        """
        return self._dirty
    
    def get_dirty_rect(self) -> Optional[pygame.Rect]:
        """
        更新領域を取得
        
        Returns:
            更新領域のRect、なければNone
        """
        if self._dirty_rect:
            return self._dirty_rect
        
        # 推定サイズで返す
        if self._position:
            return pygame.Rect(self._position[0], self._position[1], 
                              self.width, self.height)
        
        return None
    
    def get_bounds(self) -> pygame.Rect:
        """
        境界矩形を取得
        
        Returns:
            オブジェクトの境界矩形
        """
        if self._position:
            return pygame.Rect(
                self._position[0],
                self._position[1],
                self.width,
                self.height
            )
        
        # まだ位置が決まっていない場合
        pos = self.calculate_position()
        return pygame.Rect(pos[0], pos[1], self.width, self.height)
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self.visible != visible:
            self.visible = visible
            self._dirty = True
    
    def set_weekday_language(self, lang: str) -> None:
        """
        曜日表示言語を設定
        
        Args:
            lang: 言語コード ('jp' または 'en')
        """
        if self.weekday_lang != lang:
            self.weekday_lang = lang
            self._calendar_surface = None  # キャッシュをクリア
            self._dirty = True