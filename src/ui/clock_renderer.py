"""
時計表示コンポーネント

デジタル時計をHH:MM:SS形式で表示するレンダラー。
効率的なテキストレンダリングのためにキャッシュ機構を実装。
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import pygame

from src.rendering.renderable import Renderable

logger = logging.getLogger(__name__)


class ClockRenderer(Renderable):
    """
    時計表示レンダラー
    
    Attributes:
        MAX_CACHE_SIZE (int): テキストキャッシュの最大サイズ
        DEFAULT_FONT_SIZE (int): デフォルトのフォントサイズ
        DEFAULT_COLOR (Tuple[int, int, int]): デフォルトのテキスト色
    """
    
    MAX_CACHE_SIZE: int = 60  # 最大60秒分のキャッシュ
    DEFAULT_FONT_SIZE: int = 130
    DEFAULT_COLOR: Tuple[int, int, int] = (255, 255, 255)
    
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
        self.font_size: int = config.get('ui.clock_font_px', self.DEFAULT_FONT_SIZE)
        self.color: Tuple[int, int, int] = config.get('ui.clock_color', self.DEFAULT_COLOR)
        self.position: str = config.get('ui.clock_position', 'top_center')
        self.margin_x: int = config.get('ui.margins.x', 24)
        self.margin_y: int = config.get('ui.margins.y', 16)
        self.screen_width: int = config.get('screen.width', 1024)
        self.screen_height: int = config.get('screen.height', 600)
        
        # フォント読み込み
        self.font = None
        self._load_font()
        
        # 状態管理
        self.visible = True
        self._dirty = True
        self._last_time_str = ""
        self._rendered_surface: Optional[pygame.Surface] = None
        self._text_cache: Dict[str, pygame.Surface] = {}
        self._position: Optional[Tuple[int, int]] = None
        self._dirty_rect: Optional[pygame.Rect] = None
    
    def _load_font(self) -> None:
        """フォントを読み込み"""
        try:
            # デフォルトフォント名を設定から取得
            font_name = self.config.get('fonts.clock', 'NotoSansCJK-Regular')
            self.font = self.asset_manager.load_font(font_name, self.font_size)
            
            if not self.font:
                logger.warning("Failed to load custom font, using pygame default")
                self.font = pygame.font.Font(None, self.font_size)
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            self.font = pygame.font.Font(None, self.font_size)
    
    def get_current_time(self) -> str:
        """
        現在時刻を取得
        
        Returns:
            HH:MM:SS形式の時刻文字列
        """
        return datetime.now().strftime("%H:%M:%S")
    
    def update(self, dt: float) -> None:
        """
        更新処理
        
        Args:
            dt: 前フレームからの経過時間（秒）
        """
        if not self.visible:
            return
        
        # 現在時刻を取得
        current_time = self.get_current_time()
        
        # 時刻が変わった場合のみdirtyフラグを立てる
        if current_time != self._last_time_str:
            self._last_time_str = current_time
            self._dirty = True
    
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
        
        # 時刻文字列が空の場合は現在時刻を取得
        if not self._last_time_str:
            self._last_time_str = self.get_current_time()
        
        dirty_rects = []
        
        try:
            # テキストのレンダリング（キャッシュチェック）
            if self._last_time_str not in self._text_cache:
                # 古いキャッシュをクリア
                if len(self._text_cache) >= self.MAX_CACHE_SIZE:
                    # 最も古いエントリを削除（dictは3.7+で順序保持）
                    oldest_key = next(iter(self._text_cache))
                    del self._text_cache[oldest_key]
                
                # 新しいテキストをレンダリング
                rendered = self.font.render(self._last_time_str, True, self.color)
                self._text_cache[self._last_time_str] = rendered
            
            self._rendered_surface = self._text_cache[self._last_time_str]
            
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
            
            # dirtyフラグをクリア（成功時のみ）
            self._dirty = False
            
        except Exception as e:
            logger.error(f"Error rendering clock: {e}")
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
            text_width, text_height = self.font.size(self._last_time_str or "00:00:00")
        else:
            text_width = self._rendered_surface.get_width()
            text_height = self._rendered_surface.get_height()
        
        # position設定に基づいて位置を決定
        if self.position == 'top_center':
            x = (self.screen_width - text_width) // 2
            y = self.margin_y
        elif self.position == 'top_left':
            x = self.margin_x
            y = self.margin_y
        elif self.position == 'top_right':
            x = self.screen_width - text_width - self.margin_x
            y = self.margin_y
        elif self.position == 'center':
            x = (self.screen_width - text_width) // 2
            y = (self.screen_height - text_height) // 2
        else:
            # デフォルト: top_center
            x = (self.screen_width - text_width) // 2
            y = self.margin_y
        
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
        if self.font and self._last_time_str:
            text_size = self.font.size(self._last_time_str)
            if self._position:
                return pygame.Rect(self._position[0], self._position[1], 
                                  text_size[0], text_size[1])
        
        return None
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self.visible != visible:
            self.visible = visible
            self._dirty = True
            # 表示に戻った時は強制的に時刻を更新
            if visible:
                self._last_time_str = ""  # 強制的に次のupdateで更新させる
    
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
            text = self._last_time_str or "00:00:00"
            size = self.font.size(text)
            pos = self.calculate_position()
            return pygame.Rect(pos[0], pos[1], size[0], size[1])
        
        # フォントもない場合はデフォルト
        return pygame.Rect(0, 0, 300, 130)