"""
画像読み込みと処理
"""

import os
import logging
from typing import Optional, Tuple
import pygame

logger = logging.getLogger(__name__)


class ImageLoader:
    """画像の読み込みと基本的な処理"""
    
    def __init__(self, base_path: str):
        """
        初期化
        
        Args:
            base_path: ベースディレクトリパス
        """
        self.base_path = base_path
    
    def load(self, path: str, alpha: bool = True) -> Optional[pygame.Surface]:
        """
        画像を読み込み
        
        Args:
            path: 画像ファイルパス
            alpha: アルファチャンネルを有効にするか
            
        Returns:
            pygame.Surface オブジェクト、失敗時はNone
        """
        try:
            # 絶対パスでない場合はベースパスと結合
            if not os.path.isabs(path):
                path = os.path.join(self.base_path, path)
            
            if not os.path.exists(path):
                logger.error(f"Image file not found: {path}")
                return None
            
            # 画像読み込み
            surface = pygame.image.load(path)
            
            # アルファチャンネル処理
            if alpha:
                surface = surface.convert_alpha()
            else:
                surface = surface.convert()
            
            return surface
            
        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            return None
    
    def scale(self, surface: pygame.Surface, size: Tuple[int, int],
             smooth: bool = True) -> pygame.Surface:
        """
        画像をスケーリング
        
        Args:
            surface: スケーリングする画像
            size: 目標サイズ (幅, 高さ)
            smooth: スムーズスケーリングを使用するか
            
        Returns:
            スケーリングされた画像
        """
        try:
            if smooth:
                return pygame.transform.smoothscale(surface, size)
            else:
                return pygame.transform.scale(surface, size)
        except Exception as e:
            logger.error(f"Failed to scale image: {e}")
            return surface
    
    def rotate(self, surface: pygame.Surface, angle: float) -> pygame.Surface:
        """
        画像を回転
        
        Args:
            surface: 回転する画像
            angle: 回転角度（度）
            
        Returns:
            回転された画像
        """
        try:
            return pygame.transform.rotate(surface, angle)
        except Exception as e:
            logger.error(f"Failed to rotate image: {e}")
            return surface
    
    def flip(self, surface: pygame.Surface, x: bool, y: bool) -> pygame.Surface:
        """
        画像を反転
        
        Args:
            surface: 反転する画像
            x: 水平反転するか
            y: 垂直反転するか
            
        Returns:
            反転された画像
        """
        try:
            return pygame.transform.flip(surface, x, y)
        except Exception as e:
            logger.error(f"Failed to flip image: {e}")
            return surface
    
    def set_alpha(self, surface: pygame.Surface, alpha: int) -> pygame.Surface:
        """
        画像の透明度を設定
        
        Args:
            surface: 対象画像
            alpha: 透明度 (0-255)
            
        Returns:
            透明度が設定された画像
        """
        try:
            surface = surface.copy()
            surface.set_alpha(alpha)
            return surface
        except Exception as e:
            logger.error(f"Failed to set alpha: {e}")
            return surface
    
    def crop(self, surface: pygame.Surface, rect: pygame.Rect) -> pygame.Surface:
        """
        画像を切り抜き
        
        Args:
            surface: 切り抜く画像
            rect: 切り抜き領域
            
        Returns:
            切り抜かれた画像
        """
        try:
            return surface.subsurface(rect).copy()
        except Exception as e:
            logger.error(f"Failed to crop image: {e}")
            return surface