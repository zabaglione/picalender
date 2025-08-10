"""
時計レンダラー実装

TASK-201: デジタル時計表示
- HH:MM:SS形式
- 毎秒更新
- 画面上部中央配置
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import pygame
from ..assets.asset_manager import AssetManager

logger = logging.getLogger(__name__)

# デフォルト設定値
DEFAULT_FONT_SIZE = 130
DEFAULT_FONT_COLOR = [255, 255, 255]
DEFAULT_TOP_MARGIN = 50


class ClockRenderer:
    """デジタル時計レンダラークラス"""
    
    def __init__(self, asset_manager: AssetManager, settings: Dict[str, Any]):
        """
        初期化
        
        Args:
            asset_manager: アセット管理インスタンス
            settings: 設定辞書
        """
        self.asset_manager = asset_manager
        self.settings = settings
        self.current_time = ""
        
        # 設定値を取得（デフォルト値あり）
        self.font_size = self._get_setting('ui.clock_font_px', DEFAULT_FONT_SIZE)
        self.font_color = self._get_setting('ui.clock_color', DEFAULT_FONT_COLOR)
        self.font_path = self._get_setting('fonts.main', None)
        self.top_margin = self._get_setting('ui.margins.y', DEFAULT_TOP_MARGIN)
        
        # フォントをロード
        self.font = None
        self._load_font()
        
        # レンダリング用サーフェス
        self.text_surface = None
        self.text_rect = None
        
        # キャッシュされた描画位置（画面サイズ変更時に再計算）
        self.cached_screen_size = None
        self.cached_position = None
        
        logger.info(f"ClockRenderer initialized: font_size={self.font_size}, color={self.font_color}")
    
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
        """時刻更新"""
        # 現在時刻を取得してフォーマット
        current_dt = datetime.now()
        new_time = self._format_time(current_dt)
        
        # 時刻が変わった場合のみテキストサーフェスを更新
        if new_time != self.current_time:
            self.current_time = new_time
            self._render_text()
    
    def get_current_time(self) -> str:
        """
        現在時刻を取得
        
        Returns:
            HH:MM:SS形式の現在時刻
        """
        current_dt = datetime.now()
        return self._format_time(current_dt)
    
    def _format_time(self, dt: datetime) -> str:
        """
        時刻をフォーマット
        
        Args:
            dt: datetimeオブジェクト
            
        Returns:
            HH:MM:SS形式の文字列
        """
        return dt.strftime("%H:%M:%S")
    
    def _render_text(self) -> None:
        """テキストをレンダリング"""
        if self.font is None:
            return
            
        try:
            # テキストサーフェスを作成
            self.text_surface = self.font.render(
                self.current_time, 
                True,  # アンチエイリアシング
                tuple(self.font_color)
            )
            
            # 描画位置を計算（中央配置）
            self.text_rect = self.text_surface.get_rect()
            
        except Exception as e:
            logger.error(f"Text rendering failed: {e}")
            self.text_surface = None
    
    def _calculate_position(self, surface: pygame.Surface) -> Tuple[int, int]:
        """描画位置を計算"""
        screen_size = surface.get_size()
        
        # 画面サイズが変わった場合のみ再計算
        if self.cached_screen_size != screen_size or self.cached_position is None:
            screen_width, screen_height = screen_size
            
            if self.text_rect:
                x = (screen_width - self.text_rect.width) // 2
                y = self.top_margin
                self.cached_position = (x, y)
                self.cached_screen_size = screen_size
        
        return self.cached_position or (0, self.top_margin)
    
    def _draw_to_surface(self, surface: pygame.Surface) -> None:
        """サーフェスに時計を描画"""
        if not (self.text_surface and self.text_rect):
            return
            
        x, y = self._calculate_position(surface)
        draw_rect = pygame.Rect(x, y, self.text_rect.width, self.text_rect.height)
        surface.blit(self.text_surface, draw_rect)
    
    def render(self, surface: pygame.Surface) -> None:
        """
        時計を描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 時刻が未更新の場合は更新
        if not self.current_time:
            self.update()
        
        # テキストサーフェスが存在しない場合は作成
        if self.text_surface is None:
            self._render_text()
        
        # 描画実行
        self._draw_to_surface(surface)
    
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
    
    def set_font_size(self, size: int) -> None:
        """
        フォントサイズを変更
        
        Args:
            size: 新しいフォントサイズ
        """
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
        if list(color) != self.font_color:
            self.font_color = list(color)
            self._invalidate_cache()
            logger.info(f"Font color changed to: {color}")
    
    def _invalidate_cache(self) -> None:
        """キャッシュを無効化"""
        self.text_surface = None
        self.text_rect = None
        self.cached_position = None
        self.cached_screen_size = None
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        self._invalidate_cache()
        self.font = None
        logger.info("ClockRenderer cleanup completed")