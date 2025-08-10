"""
描画可能オブジェクトの基底クラス
"""

from abc import ABC, abstractmethod
from typing import Optional
import pygame


class Renderable(ABC):
    """描画可能オブジェクトのインターフェース"""
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        更新処理
        
        Args:
            dt: デルタタイム（秒）
        """
        pass
    
    @abstractmethod
    def render(self, surface: pygame.Surface) -> Optional[pygame.Rect]:
        """
        描画処理
        
        Args:
            surface: 描画先サーフェス
            
        Returns:
            更新された領域（ダーティリージョン）
        """
        pass
    
    @abstractmethod
    def get_bounds(self) -> pygame.Rect:
        """
        境界矩形を取得
        
        Returns:
            オブジェクトの境界矩形
        """
        pass
    
    @abstractmethod
    def is_dirty(self) -> bool:
        """
        更新が必要かどうか
        
        Returns:
            更新が必要な場合True
        """
        pass