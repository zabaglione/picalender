"""
レイヤー管理クラス
"""

from typing import List, Optional
import pygame
from .renderable import Renderable


class Layer:
    """描画レイヤー"""
    
    def __init__(self, name: str):
        """
        初期化
        
        Args:
            name: レイヤー名
        """
        self.name = name
        self.renderables: List[Renderable] = []
        self._visible = True
        self._dirty = False
    
    def add_renderable(self, renderable: Renderable) -> None:
        """
        描画オブジェクトを追加
        
        Args:
            renderable: 追加するオブジェクト
        """
        if renderable not in self.renderables:
            self.renderables.append(renderable)
            self._dirty = True
    
    def remove_renderable(self, renderable: Renderable) -> None:
        """
        描画オブジェクトを削除
        
        Args:
            renderable: 削除するオブジェクト
        """
        if renderable in self.renderables:
            self.renderables.remove(renderable)
            self._dirty = True
    
    def update(self, dt: float) -> None:
        """
        レイヤー内のすべてのオブジェクトを更新
        
        Args:
            dt: デルタタイム（秒）
        """
        for renderable in self.renderables:
            try:
                renderable.update(dt)
            except Exception as e:
                # エラーをログに記録（実際の実装ではログマネージャーを使用）
                print(f"Error updating renderable in layer {self.name}: {e}")
    
    def render(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """
        レイヤー内のすべてのオブジェクトを描画
        
        Args:
            surface: 描画先サーフェス
            
        Returns:
            更新された領域のリスト
        """
        dirty_rects = []
        
        if not self._visible:
            return dirty_rects
        
        for renderable in self.renderables:
            try:
                if renderable.is_dirty():
                    rect = renderable.render(surface)
                    if rect:
                        dirty_rects.append(rect)
            except Exception as e:
                # エラーをログに記録
                print(f"Error rendering object in layer {self.name}: {e}")
        
        self._dirty = False
        return dirty_rects
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self._visible != visible:
            self._visible = visible
            self._dirty = True
    
    def is_visible(self) -> bool:
        """
        表示状態を取得
        
        Returns:
            表示中の場合True
        """
        return self._visible
    
    def is_dirty(self) -> bool:
        """
        レイヤーが更新必要かどうか
        
        Returns:
            更新が必要な場合True
        """
        if self._dirty:
            return True
        
        # いずれかのオブジェクトがdirtyならTrue
        return any(r.is_dirty() for r in self.renderables)
    
    def clear(self) -> None:
        """すべての描画オブジェクトをクリア"""
        self.renderables.clear()
        self._dirty = True