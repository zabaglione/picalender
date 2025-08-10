"""
ダーティリージョン管理
"""

from typing import List, Optional
import pygame


class DirtyRegionManager:
    """ダーティリージョン（更新が必要な領域）を管理"""
    
    def __init__(self):
        """初期化"""
        self.dirty_rects: List[pygame.Rect] = []
        self._union_cache: Optional[pygame.Rect] = None
    
    def add_rect(self, rect: pygame.Rect) -> None:
        """
        更新領域を追加
        
        Args:
            rect: 追加する矩形領域
        """
        if rect and rect.width > 0 and rect.height > 0:
            self.dirty_rects.append(rect.copy())
            self._union_cache = None  # キャッシュ無効化
    
    def get_dirty_rects(self) -> List[pygame.Rect]:
        """
        更新領域リストを取得
        
        Returns:
            ダーティリージョンのリスト
        """
        return self.dirty_rects.copy()
    
    def clear(self) -> None:
        """すべての更新領域をクリア"""
        self.dirty_rects.clear()
        self._union_cache = None
    
    def union_rects(self) -> Optional[pygame.Rect]:
        """
        すべての領域を結合した最小包含矩形を取得
        
        Returns:
            結合された矩形、領域がない場合はNone
        """
        if self._union_cache is not None:
            return self._union_cache
        
        if not self.dirty_rects:
            return None
        
        # 最初の矩形から開始
        union = self.dirty_rects[0].copy()
        
        # 残りの矩形を結合
        for rect in self.dirty_rects[1:]:
            union.union_ip(rect)
        
        self._union_cache = union
        return union
    
    def optimize(self, threshold: int = 10) -> None:
        """
        重なりの多い領域を結合して最適化
        
        Args:
            threshold: 結合する最小重複面積
        """
        if len(self.dirty_rects) < 2:
            return
        
        optimized = []
        processed = set()
        
        for i, rect1 in enumerate(self.dirty_rects):
            if i in processed:
                continue
            
            current = rect1.copy()
            merged = False
            
            for j, rect2 in enumerate(self.dirty_rects[i+1:], i+1):
                if j in processed:
                    continue
                
                # 重なりをチェック
                if current.colliderect(rect2):
                    # 結合
                    current.union_ip(rect2)
                    processed.add(j)
                    merged = True
            
            optimized.append(current)
            processed.add(i)
        
        self.dirty_rects = optimized
        self._union_cache = None
    
    def is_empty(self) -> bool:
        """
        更新領域が空かどうか
        
        Returns:
            空の場合True
        """
        return len(self.dirty_rects) == 0