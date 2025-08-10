"""
Renderableインターフェース

全てのUI要素が実装すべき基本インターフェース
"""

from abc import ABC, abstractmethod
from typing import Tuple
import pygame


class Renderable(ABC):
    """
    描画可能なUI要素の基底クラス
    
    全てのレンダラーはこのインターフェースを実装する
    """
    
    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """
        画面に要素を描画
        
        Args:
            screen: 描画対象のサーフェス
        """
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        状態を更新
        
        Args:
            dt: 前回の更新からの経過時間（秒）
        """
        pass
    
    @abstractmethod
    def is_dirty(self) -> bool:
        """
        再描画が必要かどうかを返す
        
        Returns:
            再描画が必要な場合True
        """
        pass
    
    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        pass
    
    @abstractmethod
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """
        描画領域を返す
        
        Returns:
            (x, y, width, height)のタプル
        """
        pass