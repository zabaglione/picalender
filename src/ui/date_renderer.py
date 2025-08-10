"""
日付表示コンポーネント

YYYY-MM-DD (曜)形式で日付を表示するレンダラー。
日本語と英語の曜日表示に対応。
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import pygame

from src.rendering.renderable import Renderable

logger = logging.getLogger(__name__)


class DateRenderer(Renderable):
    """
    日付表示レンダラー
    
    Attributes:
        WEEKDAYS_JP: 日本語の曜日名
        WEEKDAYS_EN: 英語の曜日名
        DEFAULT_FONT_SIZE: デフォルトのフォントサイズ
        DEFAULT_COLOR: デフォルトのテキスト色
    """
    
    WEEKDAYS_JP: List[str] = ['月', '火', '水', '木', '金', '土', '日']
    WEEKDAYS_EN: List[str] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    DEFAULT_FONT_SIZE: int = 36
    DEFAULT_COLOR: Tuple[int, int, int] = (255, 255, 255)
    SUNDAY_COLOR: Tuple[int, int, int] = (255, 128, 128)  # 赤系
    SATURDAY_COLOR: Tuple[int, int, int] = (128, 128, 255)  # 青系
    MAX_CACHE_SIZE: int = 7  # 最大7日分のキャッシュ（1週間）
    
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
        self.font_size: int = config.get('ui.date_font_px', self.DEFAULT_FONT_SIZE)
        self.color: Tuple[int, int, int] = config.get('ui.date_color', self.DEFAULT_COLOR)
        self.position_type: str = config.get('ui.date_position', 'below_clock')
        self.weekday_lang: str = config.get('ui.date_weekday_lang', 'jp')
        self.margin_x: int = config.get('ui.margins.x', 24)
        self.margin_y: int = config.get('ui.margins.y', 16)
        self.screen_width: int = config.get('screen.width', 1024)
        self.screen_height: int = config.get('screen.height', 600)
        self.clock_font_px: int = config.get('ui.clock_font_px', 130)
        
        # フォント読み込み
        self.font: Optional[pygame.font.Font] = None
        self._load_font()
        
        # 状態管理
        self.visible: bool = True
        self._dirty: bool = True
        self._last_date_str: str = ""
        self._rendered_surface: Optional[pygame.Surface] = None
        self._text_cache: Dict[str, pygame.Surface] = {}
        self._position: Optional[Tuple[int, int]] = None
        self._dirty_rect: Optional[pygame.Rect] = None
    
    def _load_font(self) -> None:
        """フォントを読み込み"""
        try:
            # デフォルトフォント名を設定から取得
            font_name = self.config.get('fonts.date', 'NotoSansCJK-Regular')
            self.font = self.asset_manager.load_font(font_name, self.font_size)
            
            if not self.font:
                logger.warning("Failed to load custom font, using pygame default")
                self.font = pygame.font.Font(None, self.font_size)
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            self.font = pygame.font.Font(None, self.font_size)
    
    def get_current_date(self) -> str:
        """
        現在日付を取得
        
        Returns:
            YYYY-MM-DD (曜)形式の日付文字列
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        # 曜日を取得 (月曜=0, 日曜=6)
        weekday_idx = now.weekday()
        
        # 曜日名を選択
        if self.weekday_lang == 'en':
            weekday = self.WEEKDAYS_EN[weekday_idx]
        else:
            weekday = self.WEEKDAYS_JP[weekday_idx]
        
        return f"{date_str} ({weekday})"
    
    def get_weekday_color(self, weekday_idx: int) -> Tuple[int, int, int]:
        """
        曜日に応じた色を取得
        
        Args:
            weekday_idx: 曜日インデックス (月曜=0, 日曜=6)
            
        Returns:
            RGB色
        """
        if weekday_idx == 6:  # 日曜日
            return self.SUNDAY_COLOR
        elif weekday_idx == 5:  # 土曜日
            return self.SATURDAY_COLOR
        else:
            return self.color
    
    def update(self, dt: float) -> None:
        """
        更新処理
        
        Args:
            dt: 前フレームからの経過時間（秒）
        """
        if not self.visible:
            return
        
        # 現在日付を取得
        current_date = self.get_current_date()
        
        # 日付が変わった場合のみdirtyフラグを立てる
        if current_date != self._last_date_str:
            self._last_date_str = current_date
            self._dirty = True
            # 位置の再計算が必要
            self._position = None
    
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
        
        # 日付文字列が空の場合は現在日付を取得
        if not self._last_date_str:
            self._last_date_str = self.get_current_date()
        
        dirty_rects = []
        
        try:
            # テキストのレンダリング（キャッシュチェック）
            if self._last_date_str not in self._text_cache:
                # 古いキャッシュをクリア
                if len(self._text_cache) >= self.MAX_CACHE_SIZE:
                    oldest_key = next(iter(self._text_cache))
                    del self._text_cache[oldest_key]
                
                # 曜日に応じた色を取得
                weekday_idx = datetime.now().weekday()
                text_color = self.get_weekday_color(weekday_idx)
                
                # 新しいテキストをレンダリング
                rendered = self.font.render(self._last_date_str, True, text_color)
                self._text_cache[self._last_date_str] = rendered
            
            self._rendered_surface = self._text_cache[self._last_date_str]
            
            # 位置の計算
            if self._position is None:
                self._position = self.calculate_position()
            
            # dirtyレクトの作成
            rect = pygame.Rect(
                self._position[0],
                self._position[1],
                self._rendered_surface.get_width(),
                self._rendered_surface.get_height()
            )
            dirty_rects.append(rect)
            self._dirty_rect = rect
            
            # 描画（pygameのSurfaceかどうかチェック）
            if isinstance(surface, pygame.Surface):
                surface.blit(self._rendered_surface, self._position)
            
            # dirtyフラグをクリア
            self._dirty = False
            
        except Exception as e:
            logger.error(f"Error rendering date: {e}")
            # エラー時でもdirtyフラグをクリア（無限ループ防止）
            self._dirty = False
        
        return dirty_rects
    
    def calculate_position(self) -> Tuple[int, int]:
        """
        表示位置を計算
        
        Returns:
            (x, y) 座標のタプル
        """
        if not self._rendered_surface:
            # デフォルトサイズで仮計算
            text_width, text_height = self.font.size(self._last_date_str or "2024-01-01 (月)")
        else:
            text_width = self._rendered_surface.get_width()
            text_height = self._rendered_surface.get_height()
        
        # position設定に基づいて位置を決定
        if self.position_type == 'below_clock':
            # 時計の下に配置
            x = (self.screen_width - text_width) // 2
            # 時計の高さ + マージン + 間隔
            y = self.margin_y + self.clock_font_px + 10
        elif self.position_type == 'top_left':
            x = self.margin_x
            y = self.margin_y
        elif self.position_type == 'top_right':
            x = self.screen_width - text_width - self.margin_x
            y = self.margin_y
        elif self.position_type == 'center':
            x = (self.screen_width - text_width) // 2
            y = (self.screen_height - text_height) // 2
        else:
            # デフォルト: below_clock
            x = (self.screen_width - text_width) // 2
            y = self.margin_y + self.clock_font_px + 10
        
        return (x, y)
    
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
        if self.font and self._last_date_str:
            text_size = self.font.size(self._last_date_str)
            if self._position:
                return pygame.Rect(self._position[0], self._position[1], 
                                  text_size[0], text_size[1])
        
        return None
    
    def get_bounds(self) -> pygame.Rect:
        """
        境界矩形を取得
        
        Returns:
            オブジェクトの境界矩形
        """
        # 現在の位置とサイズから境界を計算
        if self._position and self._rendered_surface:
            return pygame.Rect(
                self._position[0],
                self._position[1],
                self._rendered_surface.get_width(),
                self._rendered_surface.get_height()
            )
        
        # まだレンダリングされていない場合は推定サイズ
        if self.font:
            text = self._last_date_str or "2024-01-01 (月)"
            size = self.font.size(text)
            pos = self.calculate_position()
            return pygame.Rect(pos[0], pos[1], size[0], size[1])
        
        # フォントもない場合はデフォルト
        return pygame.Rect(0, 0, 250, 36)
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self.visible != visible:
            self.visible = visible
            self._dirty = True
            # 表示に戻った時は強制的に日付を更新
            if visible:
                self._last_date_str = ""  # 強制的に次のupdateで更新させる
    
    def set_color(self, color: Tuple[int, int, int]) -> None:
        """
        文字色を設定
        
        Args:
            color: RGB色 (R, G, B)
        """
        if self.color != color:
            self.color = color
            self._text_cache.clear()  # キャッシュをクリア
            self._dirty = True
    
    def set_font_size(self, size: int) -> None:
        """
        フォントサイズを設定
        
        Args:
            size: フォントサイズ
        """
        if self.font_size != size:
            self.font_size = size
            self._load_font()
            self._text_cache.clear()  # キャッシュをクリア
            self._position = None  # 位置を再計算
            self._dirty = True
    
    def set_weekday_language(self, lang: str) -> None:
        """
        曜日表示言語を設定
        
        Args:
            lang: 言語コード ('jp' または 'en')
        """
        if self.weekday_lang != lang:
            self.weekday_lang = lang
            self._last_date_str = ""  # 強制的に再レンダリング
            self._text_cache.clear()  # キャッシュをクリア
            self._dirty = True