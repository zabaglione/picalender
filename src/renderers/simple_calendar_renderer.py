"""
シンプルなカレンダーレンダラー
AssetManagerに依存しない実装
"""

import pygame
import calendar
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

# 祝日ライブラリをオプショナルにインポート
try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

# 六曜計算モジュールをインポート
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / 'utils'))
    from rokuyou import get_rokuyou_name, get_rokuyou_color, get_rokuyou_info
    ROKUYOU_AVAILABLE = True
except ImportError:
    ROKUYOU_AVAILABLE = False

logger = logging.getLogger(__name__)


class SimpleCalendarRenderer:
    """シンプルなカレンダーレンダラー"""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            settings: 設定辞書
        """
        self.settings = settings or {}
        ui_settings = self.settings.get('ui', {})
        
        # フォントサイズ（旧名と新名の両方をサポート）
        self.font_size = ui_settings.get('cal_font_px', ui_settings.get('calendar_font_px', 22))
        self.small_font_size = max(self.font_size - 6, 12)
        self.tiny_font_size = 10  # 祝日名・六曜用の極小フォント
        
        # フォント初期化（settings.yamlの設定を使用）
        font_config = self.settings.get('fonts', {}).get('main', {})
        font_path = font_config.get('path', './assets/fonts/NotoSansCJK-Regular.otf')
        font_fallback = font_config.get('fallback', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf')
        
        # フォントファイルを探す（より多くの場所をチェック）
        self.font_file = None
        from pathlib import Path
        
        # チェックするフォントパスのリスト（優先順）
        font_paths = [
            font_path,
            font_fallback,
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf',
            '/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf',
        ]
        
        # 設定されたパスをチェック
        for path in font_paths:
            if Path(path).exists():
                self.font_file = path
                logger.info(f"Using font file: {path}")
                break
        
        # フォントを初期化
        try:
            if self.font_file:
                self.font = pygame.font.Font(self.font_file, self.font_size)
                self.small_font = pygame.font.Font(self.font_file, self.small_font_size)
                self.tiny_font = pygame.font.Font(self.font_file, self.tiny_font_size)
            else:
                # ファイルが見つからない場合はSysFontを使用
                logger.warning(f"No font files found in standard locations")
                logger.info("Falling back to system font")
                # 複数のシステムフォント名を試す
                for font_name in ['notosanscjkjp', 'notosansjp', 'noto', None]:
                    try:
                        self.font = pygame.font.SysFont(font_name, self.font_size)
                        self.small_font = pygame.font.SysFont(font_name, self.small_font_size)
                        self.tiny_font = pygame.font.SysFont(font_name, self.tiny_font_size)
                        logger.info(f"Using system font: {font_name}")
                        break
                    except:
                        continue
        except Exception as e:
            logger.warning(f"Failed to create font: {e}")
            # 最終的なフォールバック
            self.font = pygame.font.Font(None, self.font_size)
            self.small_font = pygame.font.Font(None, self.small_font_size)
            self.tiny_font = pygame.font.Font(None, self.tiny_font_size)
        
        # 位置設定
        screen_settings = self.settings.get('screen', {})
        self.screen_width = screen_settings.get('width', 1024)
        self.screen_height = screen_settings.get('height', 600)
        
        # レイアウト設定を読み込み
        layout_settings = self.settings.get('layout', {}).get('calendar', {})
        position = layout_settings.get('position', 'bottom-right')
        x_offset = layout_settings.get('x_offset', -30)
        y_offset = layout_settings.get('y_offset', -30)
        
        # カレンダーサイズ（初期値を設定）
        self.cal_width = 350
        self.cal_height = 300  # デフォルト値を設定（後で動的計算で上書き）
        
        # 位置の初期値を設定（後で計算で上書き）
        self.cal_x = 0
        self.cal_y = 0
        
        # 色設定
        colors = ui_settings.get('colors', {})
        self.bg_color = (20, 20, 30, 200)
        self.text_color = tuple(colors.get('text', [255, 255, 255]))
        self.sunday_color = tuple(colors.get('sunday', [255, 100, 100]))
        self.saturday_color = tuple(colors.get('saturday', [100, 100, 255]))
        self.today_color = (255, 255, 100)
        self.today_bg_color = (255, 255, 100)
        self.holiday_color = tuple(colors.get('holiday', [255, 80, 80]))  # 祝日の色
        
        # 更新間隔
        self.last_update = 0
        self.update_interval = 60.0  # 1分ごと
        
        # 祝日設定
        calendar_settings = self.settings.get('calendar', {})
        self.holidays_enabled = calendar_settings.get('holidays_enabled', True)
        self.holidays_country = calendar_settings.get('holidays_country', 'JP')
        self.show_holiday_names = calendar_settings.get('show_holiday_names', False)
        
        # 六曜設定
        self.rokuyou_enabled = calendar_settings.get('rokuyou_enabled', True)
        self.show_rokuyou_names = calendar_settings.get('show_rokuyou_names', True)
        self.rokuyou_format = calendar_settings.get('rokuyou_format', 'single')
        
        logger.info(f"Holiday settings: enabled={self.holidays_enabled}, country={self.holidays_country}, show_names={self.show_holiday_names}, holidays_available={HOLIDAYS_AVAILABLE}")
        logger.info(f"Rokuyou settings: enabled={self.rokuyou_enabled}, show_names={self.show_rokuyou_names}, format={self.rokuyou_format}, rokuyou_available={ROKUYOU_AVAILABLE}")
        
        # 祝日データの初期化
        self.jp_holidays = None
        if HOLIDAYS_AVAILABLE and self.holidays_enabled:
            try:
                if self.holidays_country == 'JP':
                    # 現在年と来年の祝日データを読み込み
                    from datetime import datetime
                    current_year = datetime.now().year
                    self.jp_holidays = holidays.Japan(years=[current_year, current_year + 1])
                    logger.info(f"Japanese holidays loaded successfully for {current_year}-{current_year + 1}")
                else:
                    logger.warning(f"Country {self.holidays_country} is not supported yet")
            except Exception as e:
                logger.warning(f"Failed to load holidays: {e}")
                self.jp_holidays = None
        else:
            if not HOLIDAYS_AVAILABLE:
                logger.warning("holidays library is not available")
            if not self.holidays_enabled:
                logger.info("holidays are disabled in settings")
        
        # 属性が初期化された後に高さと位置を計算
        try:
            self.cal_height = self._calculate_calendar_height()  # 動的に計算
        except Exception as e:
            logger.warning(f"Failed to calculate dynamic height: {e}, using default")
            self.cal_height = 300
        
        self._calculate_position(position, x_offset, y_offset)
    
    def _calculate_calendar_height(self):
        """現在の月に必要なカレンダー高さを動的計算"""
        import calendar as cal
        from datetime import datetime
        
        now = datetime.now()
        cal.setfirstweekday(cal.SUNDAY)
        cal_obj = cal.monthcalendar(now.year, now.month)
        num_weeks = len(cal_obj)
        
        # 基本サイズ計算（六曜・祝日名を考慮）
        base_height = 80   # ヘッダー部分（月名+曜日）
        row_height = 48    # 各行の高さ（日付＋六曜＋祝日名のスペース）- さらに広げる
        bottom_margin = 15  # 下部余白を上部と同じ15pxに統一
        
        # 高さ計算
        calculated_height = base_height + (num_weeks * row_height) + bottom_margin
        
        # 最小・最大制限
        min_height = 250
        max_height = 380  # 最大値を増やす（6週×48px対応）
        final_height = max(min_height, min(max_height, calculated_height))
        
        logger.info(f"Calendar dynamic sizing: {num_weeks} weeks, calculated={calculated_height}px, final={final_height}px")
        return final_height
    
    def _calculate_position(self, position: str, x_offset: int, y_offset: int):
        """位置を計算"""
        # 基本位置を決定（デフォルトマージンなし、オフセットで調整）
        if position == "top-left":
            base_x = 0
            base_y = 0
        elif position == "top-center":
            base_x = (self.screen_width - self.cal_width) // 2
            base_y = 0
        elif position == "top-right":
            base_x = self.screen_width - self.cal_width
            base_y = 0
        elif position == "center":
            base_x = (self.screen_width - self.cal_width) // 2
            base_y = (self.screen_height - self.cal_height) // 2
        elif position == "bottom-left":
            base_x = 0
            base_y = self.screen_height - self.cal_height
        elif position == "bottom-center":
            base_x = (self.screen_width - self.cal_width) // 2
            base_y = self.screen_height - self.cal_height
        elif position == "bottom-right":
            base_x = self.screen_width - self.cal_width
            base_y = self.screen_height - self.cal_height
        else:
            # デフォルト: 右下
            base_x = self.screen_width - self.cal_width
            base_y = self.screen_height - self.cal_height
        
        # オフセットを適用
        self.cal_x = base_x + x_offset
        self.cal_y = base_y + y_offset
    
    def render(self, screen: pygame.Surface) -> None:
        """
        カレンダーを描画
        
        Args:
            screen: 描画対象のサーフェース
        """
        # フォントが初期化されていない場合はスキップ
        if not hasattr(self, 'font') or self.font is None:
            logger.error("Calendar renderer: Font not initialized, skipping render")
            return
        
        # tiny_fontが初期化されていない場合は作成
        if not hasattr(self, 'tiny_font') or self.tiny_font is None:
            self.tiny_font = self.small_font  # フォールバック
        
        try:
            now = datetime.now()
            
            # カレンダー背景
            cal_surface = pygame.Surface((self.cal_width, self.cal_height), pygame.SRCALPHA)
            pygame.draw.rect(cal_surface, self.bg_color, (0, 0, self.cal_width, self.cal_height), border_radius=10)
            screen.blit(cal_surface, (self.cal_x, self.cal_y))
            
            # カレンダーヘッダー（月年）
            month_year = now.strftime("%B %Y")
            month_text = self.font.render(month_year, True, self.text_color)
            month_rect = month_text.get_rect(center=(self.cal_x + self.cal_width // 2, self.cal_y + 15))
            screen.blit(month_text, month_rect)
            
            # 曜日ヘッダー
            weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            day_width = self.cal_width // 7
            
            for i, day in enumerate(weekdays):
                if i == 0:
                    color = self.sunday_color
                elif i == 6:
                    color = self.saturday_color
                else:
                    color = self.text_color
                
                day_text = self.small_font.render(day, True, color)
                day_x = self.cal_x + i * day_width + day_width // 2
                day_rect = day_text.get_rect(center=(day_x, self.cal_y + 40))
                screen.blit(day_text, day_rect)
            
            # カレンダー日付（日曜日始まりに設定）
            # calendarモジュールを日曜日始まりに設定
            calendar.setfirstweekday(calendar.SUNDAY)
            cal_obj = calendar.monthcalendar(now.year, now.month)
            day_y = self.cal_y + 65  # カレンダー開始位置（よりコンパクトに）
            
            for week in cal_obj:
                for i, day in enumerate(week):
                    if day > 0:
                        # 色の決定（優先順位：今日 > 祝日 > 曜日）
                        current_date = date(now.year, now.month, day)
                        
                        # 今日をハイライト
                        if day == now.day:
                            pygame.draw.circle(screen, self.today_bg_color,
                                             (self.cal_x + i * day_width + day_width // 2, day_y),
                                             15)
                            color = (0, 0, 0)  # 黒
                        # 祝日判定（曜日より優先）
                        elif self.jp_holidays and current_date in self.jp_holidays:
                            color = self.holiday_color
                            logger.debug(f"Holiday detected: {current_date} ({self.jp_holidays[current_date]}) - color: {color}")
                        # 曜日判定
                        elif i == 0:  # 日曜日
                            color = self.sunday_color
                        elif i == 6:  # 土曜日
                            color = self.saturday_color
                        else:  # 平日
                            color = self.text_color
                        
                        day_text = self.small_font.render(str(day), True, color)
                        day_x = self.cal_x + i * day_width + day_width // 2
                        day_rect = day_text.get_rect(center=(day_x, day_y))
                        screen.blit(day_text, day_rect)
                        
                        # 補助情報の表示（今日は位置を調整）
                        if day == now.day:
                            # 今日の場合は黄色い円を避けて少し下に表示
                            sub_info_y = day_y + 22  # 黄色い円（半径15px）を避けるため
                        else:
                            # 通常の日付の場合
                            sub_info_y = day_y + 16  # 日付の下の位置をさらに下げる（フォント高さを考慮）
                        
                        # 六曜名を小さく表示（すべての日に対して）
                        if self.rokuyou_enabled and ROKUYOU_AVAILABLE and self.show_rokuyou_names:
                            try:
                                rokuyou_name = get_rokuyou_name(current_date, self.rokuyou_format)
                                rokuyou_color = get_rokuyou_color(current_date)
                                rokuyou_text = self.tiny_font.render(rokuyou_name, True, rokuyou_color)
                                rokuyou_rect = rokuyou_text.get_rect(center=(day_x, sub_info_y))
                                screen.blit(rokuyou_text, rokuyou_rect)
                                sub_info_y += 12  # 次の情報のために位置を下げる（間隔をさらに広げる）
                            except Exception as e:
                                logger.debug(f"Failed to render rokuyou for {current_date}: {e}")
                        
                        # 祝日名を小さく表示（オプション）- 六曜の後に表示
                        if self.show_holiday_names and self.jp_holidays and current_date in self.jp_holidays:
                            holiday_name = self.jp_holidays[current_date]
                            # 短縮表示（最初の2文字）
                            if len(holiday_name) > 2:
                                holiday_name = holiday_name[:2]
                            
                            try:
                                holiday_text = self.tiny_font.render(holiday_name, True, self.holiday_color)
                                holiday_rect = holiday_text.get_rect(center=(day_x, sub_info_y))
                                screen.blit(holiday_text, holiday_rect)
                            except:
                                pass  # フォントエラーは無視
                
                day_y += 48  # 行間を広げて六曜・祝日名との重複を防ぐ（row_heightと同期）
            
        except Exception as e:
            logger.error(f"Failed to render calendar: {e}")
    
    def should_update(self) -> bool:
        """
        更新が必要か確認
        
        Returns:
            更新が必要な場合True
        """
        import time
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            return True
        return False