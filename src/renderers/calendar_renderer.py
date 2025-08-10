"""
カレンダーレンダラー実装

TASK-203: 今月カレンダー表示
- 日曜始まり（設定可能）
- 約420×280px領域
- 曜日色分け・今日ハイライト
- 毎分更新
"""

import logging
import calendar
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional
import pygame
from ..assets.asset_manager import AssetManager

logger = logging.getLogger(__name__)

# 設定キー定数
class SettingKeys:
    """YAML設定キーの定数"""
    UI_FONT_SIZE = 'ui.calendar_font_px'
    UI_HEADER_FONT_SIZE = 'ui.calendar_header_font_px'
    UI_POSITION_X = 'ui.calendar_position_x'
    UI_POSITION_Y = 'ui.calendar_position_y'
    UI_WIDTH = 'ui.calendar_width'
    UI_HEIGHT = 'ui.calendar_height'
    UI_CELL_MARGIN = 'ui.calendar_cell_margin'
    
    CAL_FIRST_WEEKDAY = 'calendar.first_weekday'
    CAL_TODAY_HIGHLIGHT = 'calendar.today_highlight'
    
    COLOR_SUNDAY = 'calendar.color_sunday'
    COLOR_SATURDAY = 'calendar.color_saturday'
    COLOR_WEEKDAY = 'calendar.color_weekday'
    COLOR_TODAY_BG = 'calendar.color_today_bg'
    COLOR_TODAY_TEXT = 'calendar.color_today_text'
    COLOR_HEADER = 'calendar.color_header'
    
    FONT_MAIN = 'fonts.main'

# デフォルト設定値
class DefaultSettings:
    """YAML設定のデフォルト値"""
    FONT_SIZE = 22
    HEADER_FONT_SIZE = 22
    POSITION_X = 580
    POSITION_Y = 300
    WIDTH = 420
    HEIGHT = 280
    CELL_MARGIN = 4
    FIRST_WEEKDAY = "SUNDAY"

# 色パレット定義
class ColorPalette:
    """CALENDAR色パレット定義"""
    SUNDAY = [255, 107, 107]     # #FF6B6B 赤系
    SATURDAY = [77, 171, 247]    # #4DABF7 青系
    WEEKDAY = [255, 255, 255]    # #FFFFFF 白系
    TODAY_BG = [255, 217, 61]    # #FFD93D 黄系
    TODAY_TEXT = [0, 0, 0]       # #000000 黒系
    HEADER = [200, 200, 200]     # #C8C8C8 グレー系

# バリデーション範囲
class ValidationRanges:
    """SETTINGバリデーション範囲"""
    FONT_SIZE_MIN, FONT_SIZE_MAX = 8, 200
    POSITION_MIN, POSITION_MAX = 0, 10000
    SIZE_MIN, SIZE_MAX = 50, 2000
    MARGIN_MIN, MARGIN_MAX = 0, 50
    COLOR_MIN, COLOR_MAX = 0, 255

# 曜日ヘッダ定義
WEEKDAY_HEADERS = {
    'SUNDAY': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    'MONDAY': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
}


class CalendarRenderer:
    """カレンダーレンダラークラス"""
    
    def __init__(self, asset_manager: AssetManager, settings: Dict[str, Any]):
        """
        初期化
        
        Args:
            asset_manager: アセット管理インスタンス
            settings: 設定辞書
        """
        self.asset_manager = asset_manager
        self.settings = settings
        
        # UI設定値を取得（バリデーション付き）
        self.font_size = self._validate_font_size(
            self._get_setting(SettingKeys.UI_FONT_SIZE, DefaultSettings.FONT_SIZE))
        self.header_font_size = self._validate_font_size(
            self._get_setting(SettingKeys.UI_HEADER_FONT_SIZE, DefaultSettings.HEADER_FONT_SIZE))
        self.position_x = self._validate_position(
            self._get_setting(SettingKeys.UI_POSITION_X, DefaultSettings.POSITION_X))
        self.position_y = self._validate_position(
            self._get_setting(SettingKeys.UI_POSITION_Y, DefaultSettings.POSITION_Y))
        self.width = self._validate_size(
            self._get_setting(SettingKeys.UI_WIDTH, DefaultSettings.WIDTH))
        self.height = self._validate_size(
            self._get_setting(SettingKeys.UI_HEIGHT, DefaultSettings.HEIGHT))
        self.cell_margin = self._validate_margin(
            self._get_setting(SettingKeys.UI_CELL_MARGIN, DefaultSettings.CELL_MARGIN))
        
        # カレンダー設定値を取得
        self.first_weekday = self._get_setting(SettingKeys.CAL_FIRST_WEEKDAY, DefaultSettings.FIRST_WEEKDAY).upper()
        self.today_highlight = self._get_setting(SettingKeys.CAL_TODAY_HIGHLIGHT, True)
        
        # 色設定（パレットから取得）
        self.color_sunday = self._get_setting(SettingKeys.COLOR_SUNDAY, ColorPalette.SUNDAY)
        self.color_saturday = self._get_setting(SettingKeys.COLOR_SATURDAY, ColorPalette.SATURDAY)
        self.color_weekday = self._get_setting(SettingKeys.COLOR_WEEKDAY, ColorPalette.WEEKDAY)
        self.color_today_bg = self._get_setting(SettingKeys.COLOR_TODAY_BG, ColorPalette.TODAY_BG)
        self.color_today_text = self._get_setting(SettingKeys.COLOR_TODAY_TEXT, ColorPalette.TODAY_TEXT)
        self.color_header = self._get_setting(SettingKeys.COLOR_HEADER, ColorPalette.HEADER)
        
        # フォント設定
        self.font_path = self._get_setting(SettingKeys.FONT_MAIN, None)
        
        # カレンダーデータ
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.calendar_data = []
        
        # フォントを読み込み
        self.font = None
        self.header_font = None
        self._load_fonts()
        
        # キャッシュ用変数
        self.cell_positions = []
        self.cached_month = None
        
        # 初期化完了処理
        self._finalize_initialization()
    
    def _finalize_initialization(self) -> None:
        """初期化の最終処理"""
        # 週開始曜日を設定
        self._set_calendar_first_weekday()
        
        # 初期状態のログ出力
        logger.info(f"CalendarRenderer initialized: {self.width}x{self.height} at ({self.position_x}, {self.position_y})")
        logger.debug(f"Settings: weekday={self.first_weekday}, highlight={self.today_highlight}")
        logger.debug(f"Colors: sunday={self.color_sunday}, saturday={self.color_saturday}")
    
    def _get_setting(self, path: str, default=None):
        """設定値を安全に取得"""
        keys = path.split('.')
        current = self.settings
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def _validate_font_size(self, size):
        """フォントサイズのバリデーション"""
        if isinstance(size, int) and ValidationRanges.FONT_SIZE_MIN <= size <= ValidationRanges.FONT_SIZE_MAX:
            return size
        return DefaultSettings.FONT_SIZE
    
    def _validate_position(self, pos):
        """位置のバリデーション"""
        if isinstance(pos, int) and ValidationRanges.POSITION_MIN <= pos <= ValidationRanges.POSITION_MAX:
            return pos
        return 0
    
    def _validate_size(self, size):
        """サイズのバリデーション"""
        if isinstance(size, int) and ValidationRanges.SIZE_MIN <= size <= ValidationRanges.SIZE_MAX:
            return size
        return DefaultSettings.WIDTH  # 統一されたデフォルト
    
    def _validate_margin(self, margin):
        """マージンのバリデーション"""
        if isinstance(margin, int) and ValidationRanges.MARGIN_MIN <= margin <= ValidationRanges.MARGIN_MAX:
            return margin
        return DefaultSettings.CELL_MARGIN
    
    def _load_fonts(self) -> None:
        """フォントを読み込み"""
        font_strategies = [
            (self.font_path, "specified font"),
            (None, "system default font"),
            ('pygame_fallback', "pygame fallback")
        ]
        
        # 通常フォント
        for font_path, description in font_strategies:
            try:
                if font_path == 'pygame_fallback':
                    self.font = pygame.font.Font(None, self.font_size)
                else:
                    self.font = self.asset_manager.load_font(font_path, self.font_size)
                logger.info(f"Calendar font loaded successfully: {description}")
                break
            except Exception as e:
                logger.warning(f"Failed to load calendar font {description}: {e}")
                continue
        
        # ヘッダフォント
        for font_path, description in font_strategies:
            try:
                if font_path == 'pygame_fallback':
                    self.header_font = pygame.font.Font(None, self.header_font_size)
                else:
                    self.header_font = self.asset_manager.load_font(font_path, self.header_font_size)
                logger.info(f"Calendar header font loaded successfully: {description}")
                break
            except Exception as e:
                logger.warning(f"Failed to load calendar header font {description}: {e}")
                continue
        
        if self.font is None or self.header_font is None:
            logger.error("All font loading strategies failed for calendar")
            raise RuntimeError("Cannot initialize calendar fonts")
    
    def _set_calendar_first_weekday(self) -> None:
        """calendar モジュールの週開始曜日を設定"""
        if self.first_weekday == 'SUNDAY':
            calendar.setfirstweekday(6)  # 日曜日 = 6
        elif self.first_weekday == 'MONDAY':
            calendar.setfirstweekday(0)  # 月曜日 = 0
        else:
            # デフォルトは日曜始まり
            calendar.setfirstweekday(6)
            self.first_weekday = 'SUNDAY'
    
    def get_current_month(self) -> Tuple[int, int]:
        """
        現在月を取得
        
        Returns:
            (年, 月)のタプル
        """
        now = datetime.now()
        return (now.year, now.month)
    
    def _generate_calendar_data(self, year: int, month: int) -> List[List[int]]:
        """
        カレンダーデータを生成
        
        Args:
            year: 年
            month: 月
            
        Returns:
            週ごとの日付配列
        """
        return calendar.monthcalendar(year, month)
    
    def _is_today(self, year: int, month: int, day: int) -> bool:
        """
        指定日が今日かどうか判定
        
        Args:
            year: 年
            month: 月
            day: 日
            
        Returns:
            今日の場合True
        """
        if day == 0:  # 空セル
            return False
        
        # テストでモックされることを考慮してdate.today()を直接使用
        today = date.today()
        return (year, month, day) == (today.year, today.month, today.day)
    
    def _get_today_date(self) -> int:
        """今日の日付を取得"""
        return date.today().day
    
    def _calculate_cell_positions(self) -> List[List[Tuple[int, int]]]:
        """
        各セルの描画位置を計算
        
        Returns:
            各セルの(x, y)座標の配列
        """
        positions = []
        
        # セルサイズ計算（7列×7行分のグリッド）
        cell_width = (self.width - self.cell_margin * 6) // 7
        cell_height = (self.height - self.cell_margin * 6) // 7
        
        for row in range(7):  # ヘッダ + 6週
            row_positions = []
            for col in range(7):  # 7曜日
                x = self.position_x + col * (cell_width + self.cell_margin)
                y = self.position_y + row * (cell_height + self.cell_margin)
                row_positions.append((x, y))
            positions.append(row_positions)
        
        return positions
    
    def _get_weekday_headers(self) -> List[str]:
        """
        曜日ヘッダを取得
        
        Returns:
            曜日名のリスト
        """
        if self.first_weekday in WEEKDAY_HEADERS:
            return WEEKDAY_HEADERS[self.first_weekday]
        else:
            return WEEKDAY_HEADERS['SUNDAY']
    
    def _get_cell_color(self, weekday: int, is_today: bool) -> List[int]:
        """
        セルの色を取得
        
        Args:
            weekday: 曜日インデックス（0=日曜, 6=土曜）
            is_today: 今日フラグ
            
        Returns:
            RGB色のリスト
        """
        if is_today and self.today_highlight:
            return self.color_today_bg
        
        # 週開始曜日に応じてインデックスを調整
        if self.first_weekday == 'MONDAY':
            # 月曜始まりの場合：0=月曜, 6=日曜
            if weekday == 5:  # 土曜日
                return self.color_saturday
            elif weekday == 6:  # 日曜日
                return self.color_sunday
            else:  # 平日
                return self.color_weekday
        else:
            # 日曜始まりの場合：0=日曜, 6=土曜
            if weekday == 0:  # 日曜日
                return self.color_sunday
            elif weekday == 6:  # 土曜日
                return self.color_saturday
            else:  # 平日
                return self.color_weekday
    
    def _get_today_bg_color(self) -> List[int]:
        """今日背景色を取得"""
        return self.color_today_bg
    
    def _get_today_text_color(self) -> List[int]:
        """今日文字色を取得"""
        return self.color_today_text
    
    def _render_header(self, surface: pygame.Surface) -> None:
        """
        曜日ヘッダを描画
        
        Args:
            surface: 描画対象サーフェス
        """
        if not self.header_font:
            return
        
        weekday_headers = self._get_weekday_headers()
        
        if not self.cell_positions:
            self.cell_positions = self._calculate_cell_positions()
        
        # ヘッダ行（最初の行）に曜日名を描画
        for col, weekday_name in enumerate(weekday_headers):
            if col < len(self.cell_positions[0]):
                x, y = self.cell_positions[0][col]
                
                # テキストをレンダリング
                text_surface = self.header_font.render(
                    weekday_name, 
                    True, 
                    tuple(self.color_header)
                )
                
                # 中央揃えで配置
                text_rect = text_surface.get_rect()
                text_rect.centerx = x + (self.width // 7) // 2
                text_rect.centery = y + (self.height // 7) // 2
                
                surface.blit(text_surface, text_rect)
    
    def _render_date_cells(self, surface: pygame.Surface, calendar_data: List[List[int]]) -> None:
        """
        日付セルを描画
        
        Args:
            surface: 描画対象サーフェス
            calendar_data: カレンダーデータ
        """
        if not self.font or not self.cell_positions:
            return
        
        # セルサイズの事前計算
        cell_width = self.width // 7
        cell_height = self.height // 7
        
        # データ行（ヘッダの次の行から）に日付を描画
        for week_idx, week in enumerate(calendar_data):
            if week_idx + 1 >= len(self.cell_positions):
                break
                
            for day_idx, day in enumerate(week):
                if day == 0 or day_idx >= len(self.cell_positions[week_idx + 1]):
                    continue  # 空セルはスキップ
                
                # セル情報の取得
                cell_info = self._get_cell_render_info(week_idx + 1, day_idx, day, cell_width, cell_height)
                if not cell_info:
                    continue
                
                # セル描画実行
                self._render_single_cell(surface, cell_info)
    
    def _get_cell_render_info(self, row: int, col: int, day: int, cell_width: int, cell_height: int) -> Optional[Dict]:
        """セル描画情報を取得"""
        x, y = self.cell_positions[row][col]
        is_today = self._is_today(self.current_year, self.current_month, day)
        
        # 色決定
        text_color = self.color_today_text if (is_today and self.today_highlight) else self._get_cell_color(col, is_today)
        
        return {
            'day': day,
            'x': x,
            'y': y,
            'width': cell_width,
            'height': cell_height,
            'text_color': text_color,
            'is_today': is_today
        }
    
    def _render_single_cell(self, surface: pygame.Surface, cell_info: Dict) -> None:
        """単一セルの描画"""
        # 今日の場合は背景描画
        if cell_info['is_today'] and self.today_highlight:
            bg_rect = pygame.Rect(cell_info['x'], cell_info['y'], cell_info['width'], cell_info['height'])
            pygame.draw.rect(surface, tuple(self.color_today_bg), bg_rect)
        
        # テキスト描画
        text_surface = self.font.render(str(cell_info['day']), True, tuple(cell_info['text_color']))
        
        # 中央揃え配置
        text_rect = text_surface.get_rect()
        text_rect.centerx = cell_info['x'] + cell_info['width'] // 2
        text_rect.centery = cell_info['y'] + cell_info['height'] // 2
        
        surface.blit(text_surface, text_rect)
    
    def update(self) -> None:
        """カレンダー更新"""
        current_year, current_month = self.get_current_month()
        
        # 月が変わった場合のみカレンダーデータを再生成
        if (current_year, current_month) != (self.current_year, self.current_month):
            self.current_year = current_year
            self.current_month = current_month
            self.calendar_data = self._generate_calendar_data(current_year, current_month)
            self.cell_positions = []  # 位置も再計算
            logger.info(f"Calendar updated to {current_year}-{current_month:02d}")
        
        # 既にデータがない場合は生成
        if not self.calendar_data:
            self.calendar_data = self._generate_calendar_data(self.current_year, self.current_month)
    
    def render(self, surface: pygame.Surface) -> None:
        """
        カレンダーを描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 描画前節備
        if not self._prepare_for_rendering():
            return
        
        # 描画パイプライン実行
        self._execute_render_pipeline(surface)
    
    def _prepare_for_rendering(self) -> bool:
        """描画前の準備処理"""
        # カレンダーデータの確認・更新
        if not self.calendar_data:
            self.update()
            if not self.calendar_data:
                logger.error("Failed to generate calendar data")
                return False
        
        # セル位置の確認・計算
        if not self.cell_positions:
            self.cell_positions = self._calculate_cell_positions()
            if not self.cell_positions:
                logger.error("Failed to calculate cell positions")
                return False
        
        # フォントの確認
        if not self.font or not self.header_font:
            logger.error("Fonts not loaded properly")
            return False
        
        return True
    
    def _execute_render_pipeline(self, surface: pygame.Surface) -> None:
        """描画パイプラインの実行"""
        # 1. ヘッダ描画
        self._render_header(surface)
        
        # 2. 日付セル描画
        self._render_date_cells(surface, self.calendar_data)
    
    def set_first_weekday(self, weekday: str) -> None:
        """
        週開始曜日を変更
        
        Args:
            weekday: "SUNDAY" または "MONDAY"
        """
        weekday = weekday.upper()
        if weekday in ['SUNDAY', 'MONDAY'] and weekday != self.first_weekday:
            self.first_weekday = weekday
            self._set_calendar_first_weekday()
            # カレンダーデータを再生成
            self.calendar_data = self._generate_calendar_data(self.current_year, self.current_month)
            self.cell_positions = []
            logger.info(f"First weekday changed to: {weekday}")
    
    def set_position(self, x: int, y: int) -> None:
        """
        描画位置を変更
        
        Args:
            x: X座標
            y: Y座標
        """
        self.position_x = x
        self.position_y = y
        self.cell_positions = []  # 位置再計算が必要
        logger.info(f"Calendar position changed to: ({x}, {y})")
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        self.font = None
        self.header_font = None
        self.calendar_data = []
        self.cell_positions = []
        logger.info("CalendarRenderer cleanup completed")