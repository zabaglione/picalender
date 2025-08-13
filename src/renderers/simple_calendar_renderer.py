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
        
        # フォント初期化
        try:
            self.font = pygame.font.Font(None, self.font_size)
            self.small_font = pygame.font.Font(None, self.small_font_size)
        except:
            logger.warning("Failed to create fonts, using defaults")
            self.font = pygame.font.Font(None, 20)
            self.small_font = pygame.font.Font(None, 16)
        
        # 位置設定
        screen_settings = self.settings.get('screen', {})
        self.screen_width = screen_settings.get('width', 1024)
        self.screen_height = screen_settings.get('height', 600)
        
        # カレンダー位置とサイズ
        self.cal_x = self.screen_width - 380
        self.cal_y = self.screen_height - 280
        self.cal_width = 350
        self.cal_height = 250
        
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
        
        logger.info(f"Holiday settings: enabled={self.holidays_enabled}, country={self.holidays_country}, show_names={self.show_holiday_names}, holidays_available={HOLIDAYS_AVAILABLE}")
        
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
    
    def render(self, screen: pygame.Surface) -> None:
        """
        カレンダーを描画
        
        Args:
            screen: 描画対象のサーフェース
        """
        try:
            now = datetime.now()
            
            # カレンダー背景
            cal_surface = pygame.Surface((self.cal_width, self.cal_height), pygame.SRCALPHA)
            pygame.draw.rect(cal_surface, self.bg_color, (0, 0, self.cal_width, self.cal_height), border_radius=10)
            screen.blit(cal_surface, (self.cal_x, self.cal_y))
            
            # カレンダーヘッダー（月年）
            month_year = now.strftime("%B %Y")
            month_text = self.font.render(month_year, True, self.text_color)
            month_rect = month_text.get_rect(center=(self.cal_x + self.cal_width // 2, self.cal_y + 20))
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
                day_rect = day_text.get_rect(center=(day_x, self.cal_y + 50))
                screen.blit(day_text, day_rect)
            
            # カレンダー日付（日曜日始まりに設定）
            # calendarモジュールを日曜日始まりに設定
            calendar.setfirstweekday(calendar.SUNDAY)
            cal_obj = calendar.monthcalendar(now.year, now.month)
            day_y = self.cal_y + 80
            
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
                        
                        # 祝日名を小さく表示（オプション）
                        if self.show_holiday_names and self.jp_holidays and current_date in self.jp_holidays:
                            holiday_name = self.jp_holidays[current_date]
                            # 短縮表示（最初の2文字）
                            if len(holiday_name) > 2:
                                holiday_name = holiday_name[:2]
                            
                            # さらに小さいフォントで祝日名を表示
                            try:
                                tiny_font = pygame.font.Font(None, 10)
                                holiday_text = tiny_font.render(holiday_name, True, self.holiday_color)
                                holiday_rect = holiday_text.get_rect(center=(day_x, day_y + 10))
                                screen.blit(holiday_text, holiday_rect)
                            except:
                                pass  # フォントエラーは無視
                
                day_y += 30
            
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