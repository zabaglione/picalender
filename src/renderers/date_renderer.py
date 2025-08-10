"""
日付レンダラー実装

TASK-202: 日付表示
- YYYY-MM-DD (曜日)形式
- 時計直下配置
- 毎分更新
- 日本語・英語曜日対応
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import pygame
from ..assets.asset_manager import AssetManager

logger = logging.getLogger(__name__)

# デフォルト設定値
DEFAULT_FONT_SIZE = 36
DEFAULT_FONT_COLOR = [255, 255, 255]
DEFAULT_WEEKDAY_FORMAT = "japanese"
DEFAULT_DATE_MARGIN = 10  # 時計との間隔

# 曜日フォーマット定義（グローバル定数）
WEEKDAY_FORMATS = {
    'japanese': ['(月)', '(火)', '(水)', '(木)', '(金)', '(土)', '(日)'],
    'english': ['(Mon)', '(Tue)', '(Wed)', '(Thu)', '(Fri)', '(Sat)', '(Sun)']
}


class DateRenderer:
    """日付レンダラークラス"""
    
    def __init__(self, asset_manager: AssetManager, settings: Dict[str, Any]):
        """
        初期化
        
        Args:
            asset_manager: アセット管理インスタンス
            settings: 設定辞書
        """
        self.asset_manager = asset_manager
        self.settings = settings
        self.current_date = ""
        
        # 設定値を取得（デフォルト値あり）
        self.font_size = self._get_setting('ui.date_font_px', DEFAULT_FONT_SIZE)
        self.font_color = self._get_setting('ui.date_color', DEFAULT_FONT_COLOR)
        self.weekday_format = self._get_setting('ui.weekday_format', DEFAULT_WEEKDAY_FORMAT)
        self.font_path = self._get_setting('fonts.main', None)
        self.date_margin = self._get_setting('ui.date_margin', DEFAULT_DATE_MARGIN)
        
        # フォントをロード
        self.font = None
        self._load_font()
        
        # レンダリング用サーフェス
        self.text_surface = None
        self.text_rect = None
        
        # キャッシュされた位置情報
        self.cached_position = None
        self.cached_clock_rect = None
        
        # 曜日フォーマットはグローバル定義を使用
        self.weekday_formats = WEEKDAY_FORMATS
        
        logger.info(f"DateRenderer initialized: font_size={self.font_size}, weekday_format={self.weekday_format}")
    
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
    
    def _load_font(self) -> None:
        """フォントを読み込み"""
        font_strategies = [
            (self.font_path, "specified font"),
            (None, "system default font"),
            ('pygame_fallback', "pygame fallback")
        ]
        
        for font_path, description in font_strategies:
            try:
                if font_path == 'pygame_fallback':
                    self.font = pygame.font.Font(None, self.font_size)
                else:
                    self.font = self.asset_manager.load_font(font_path, self.font_size)
                logger.info(f"Font loaded successfully: {description}")
                return
            except Exception as e:
                logger.warning(f"Failed to load {description}: {e}")
                continue
        
        # 全ての戦略が失敗した場合
        logger.error("All font loading strategies failed")
        raise RuntimeError("Cannot initialize font")
    
    def update(self) -> None:
        """日付更新"""
        # 現在日付を取得してフォーマット
        current_dt = datetime.now()
        new_date = self._format_date(current_dt)
        
        # 日付が変わった場合のみテキストサーフェスを更新
        if new_date != self.current_date:
            self.current_date = new_date
            self._render_text()
    
    def get_current_date(self) -> str:
        """
        現在日付を取得
        
        Returns:
            YYYY-MM-DD (曜日)形式の現在日付
        """
        current_dt = datetime.now()
        return self._format_date(current_dt)
    
    def _format_date(self, dt: datetime) -> str:
        """
        日付をフォーマット
        
        Args:
            dt: datetimeオブジェクト
            
        Returns:
            YYYY-MM-DD (曜日)形式の文字列
        """
        date_part = dt.strftime("%Y-%m-%d")
        weekday_part = self._format_weekday(dt)
        return f"{date_part} {weekday_part}"
    
    def _format_weekday(self, dt: datetime) -> str:
        """
        曜日をフォーマット
        
        Args:
            dt: datetimeオブジェクト
            
        Returns:
            フォーマットされた曜日文字列
        """
        # 週の曜日を取得（月曜=0, 日曜=6）
        weekday_index = dt.weekday()
        
        # 現在の曜日フォーマット設定を使用
        format_type = self.weekday_format.lower()
        if format_type not in self.weekday_formats:
            format_type = DEFAULT_WEEKDAY_FORMAT
            
        weekday_list = self.weekday_formats[format_type]
        return weekday_list[weekday_index]
    
    def _render_text(self) -> None:
        """テキストをレンダリング"""
        if self.font is None:
            return
            
        try:
            # テキストサーフェスを作成
            self.text_surface = self.font.render(
                self.current_date, 
                True,  # アンチエイリアシング
                tuple(self.font_color)
            )
            
            # 描画位置を計算
            self.text_rect = self.text_surface.get_rect()
            
        except Exception as e:
            logger.error(f"Text rendering failed: {e}")
            self.text_surface = None
    
    def _should_recalculate_position(self, clock_rect: pygame.Rect) -> bool:
        """位置再計算が必要かどうかを判断"""
        return (self.cached_clock_rect != clock_rect or 
                self.cached_position is None or 
                self.text_rect is None)
    
    def _calculate_center_x_position(self, clock_rect: pygame.Rect) -> int:
        """X座標（中央配置）を計算"""
        clock_center_x = clock_rect.centerx
        return clock_center_x - self.text_rect.width // 2
    
    def _calculate_y_position(self, clock_rect: pygame.Rect) -> int:
        """Y座標（時計直下）を計算"""
        return clock_rect.bottom + self.date_margin
    
    def _calculate_position(self, clock_rect: pygame.Rect) -> Tuple[int, int]:
        """時計相対位置を計算"""
        if not self._should_recalculate_position(clock_rect):
            return self.cached_position or (0, 0)
        
        if self.text_rect:
            date_x = self._calculate_center_x_position(clock_rect)
            date_y = self._calculate_y_position(clock_rect)
            
            self.cached_position = (date_x, date_y)
            self.cached_clock_rect = clock_rect
        
        return self.cached_position or (0, 0)
    
    def render(self, surface: pygame.Surface, clock_rect: pygame.Rect) -> None:
        """
        日付を描画
        
        Args:
            surface: 描画対象のサーフェス
            clock_rect: 時計の描画領域
        """
        # 日付が未更新の場合は更新
        if not self.current_date:
            self.update()
        
        # テキストサーフェスが存在しない場合は作成
        if self.text_surface is None:
            self._render_text()
        
        # 描画実行
        if self.text_surface and self.text_rect:
            x, y = self._calculate_position(clock_rect)
            draw_rect = pygame.Rect(x, y, self.text_rect.width, self.text_rect.height)
            surface.blit(self.text_surface, draw_rect)
    
    def set_weekday_format(self, format_type: str) -> None:
        """
        曜日フォーマットを変更
        
        Args:
            format_type: "japanese" または "english"
        """
        format_type = format_type.lower()
        
        # バリデーション
        if not self._validate_weekday_format(format_type):
            logger.warning(f"Invalid weekday format: {format_type}, using default")
            format_type = DEFAULT_WEEKDAY_FORMAT
        
        if format_type != self.weekday_format:
            self.weekday_format = format_type
            self._clear_text_cache()
            self._force_text_update()
            logger.info(f"Weekday format changed to: {format_type}")
    
    def set_font_size(self, size: int) -> None:
        """
        フォントサイズを変更
        
        Args:
            size: 新しいフォントサイズ
        """
        if not self._validate_font_size(size):
            logger.warning(f"Invalid font size: {size}, using default")
            size = DEFAULT_FONT_SIZE
        
        if size != self.font_size:
            self.font_size = size
            self._load_font()
            self._invalidate_cache()
            logger.info(f"Font size changed to: {size}")
    
    def set_font_color(self, color: Tuple[int, int, int]) -> None:
        """
        フォント色を変更
        
        Args:
            color: RGB色タプル
        """
        if not self._validate_font_color(color):
            logger.warning(f"Invalid font color: {color}, using default")
            color = tuple(DEFAULT_FONT_COLOR)
        
        if list(color) != self.font_color:
            self.font_color = list(color)
            self._clear_text_cache()
            self._force_text_update()
            logger.info(f"Font color changed to: {color}")
    
    def _clear_text_cache(self) -> None:
        """テキスト関連キャッシュを無効化"""
        self.text_surface = None
        self.text_rect = None
    
    def _clear_position_cache(self) -> None:
        """位置関連キャッシュを無効化"""
        self.cached_position = None
        self.cached_clock_rect = None
    
    def _force_text_update(self) -> None:
        """テキスト強制更新"""
        # 現在の日付を強制的にクリアして再レンダを促す
        self.current_date = ""
        self.update()
    
    def _invalidate_cache(self) -> None:
        """全キャッシュを無効化"""
        self._clear_text_cache()
        self._clear_position_cache()
        self._force_text_update()
    
    def get_font_metrics(self) -> Dict[str, int]:
        """
        フォントメトリクス情報を取得
        
        Returns:
            フォント情報辞書
        """
        if self.font is None:
            return {}
            
        return {
            'height': self.font.get_height(),
            'ascent': self.font.get_ascent(), 
            'descent': self.font.get_descent(),
            'linesize': self.font.get_linesize()
        }
    
    def get_rendered_size(self) -> Tuple[int, int]:
        """
        レンダリング済みテキストのサイズを取得
        
        Returns:
            (width, height)のタプル
        """
        if self.text_rect:
            return (self.text_rect.width, self.text_rect.height)
        return (0, 0)
    
    def _validate_weekday_format(self, format_type: str) -> bool:
        """曜日フォーマットのバリデーション"""
        return format_type.lower() in WEEKDAY_FORMATS
    
    def _validate_font_size(self, size: int) -> bool:
        """フォントサイズのバリデーション"""
        return isinstance(size, int) and 8 <= size <= 200
    
    def _validate_font_color(self, color: Tuple[int, int, int]) -> bool:
        """フォント色のバリデーション"""
        try:
            return (len(color) == 3 and 
                   all(isinstance(c, int) and 0 <= c <= 255 for c in color))
        except (TypeError, ValueError):
            return False
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        self._invalidate_cache()
        self.font = None
        logger.info("DateRenderer cleanup completed")