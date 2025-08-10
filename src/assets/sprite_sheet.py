"""
スプライトシート管理
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
import pygame

logger = logging.getLogger(__name__)


class SpriteSheet:
    """スプライトシートからフレームを抽出"""
    
    def __init__(self, surface: pygame.Surface, frame_size: Tuple[int, int],
                 metadata: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            surface: スプライトシート画像
            frame_size: 1フレームのサイズ (幅, 高さ)
            metadata: アニメーション情報等のメタデータ
        """
        self.surface = surface
        self.frame_size = frame_size
        self.metadata = metadata or {}
        
        # フレーム数を計算
        sheet_size = surface.get_size()
        self.cols = sheet_size[0] // frame_size[0]
        self.rows = sheet_size[1] // frame_size[1]
        self.frame_count = self.cols * self.rows
        
        # アニメーション情報
        self.animations = self.metadata.get('animations', {})
        
        # フレームキャッシュ
        self._frame_cache: Dict[int, pygame.Surface] = {}
    
    def get_frame(self, index: int) -> Optional[pygame.Surface]:
        """
        指定インデックスのフレームを取得
        
        Args:
            index: フレームインデックス
            
        Returns:
            フレーム画像
        """
        if index < 0 or index >= self.frame_count:
            logger.error(f"Frame index {index} out of range (0-{self.frame_count-1})")
            return None
        
        # キャッシュチェック
        if index in self._frame_cache:
            return self._frame_cache[index]
        
        try:
            # フレーム位置を計算
            col = index % self.cols
            row = index // self.cols
            x = col * self.frame_size[0]
            y = row * self.frame_size[1]
            
            # フレームを切り出し
            rect = pygame.Rect(x, y, self.frame_size[0], self.frame_size[1])
            frame = self.surface.subsurface(rect).copy()
            
            # キャッシュに保存
            self._frame_cache[index] = frame
            
            return frame
            
        except Exception as e:
            logger.error(f"Failed to extract frame {index}: {e}")
            return None
    
    def get_frames(self, indices: List[int]) -> List[pygame.Surface]:
        """
        複数フレームを取得
        
        Args:
            indices: フレームインデックスのリスト
            
        Returns:
            フレーム画像のリスト
        """
        frames = []
        for index in indices:
            frame = self.get_frame(index)
            if frame:
                frames.append(frame)
        return frames
    
    def get_animation(self, start: int, end: int) -> List[pygame.Surface]:
        """
        アニメーション用の連続フレームを取得
        
        Args:
            start: 開始インデックス
            end: 終了インデックス（含む）
            
        Returns:
            フレーム画像のリスト
        """
        indices = list(range(start, end + 1))
        return self.get_frames(indices)
    
    def get_animation_by_name(self, name: str) -> List[pygame.Surface]:
        """
        名前でアニメーションを取得
        
        Args:
            name: アニメーション名
            
        Returns:
            フレーム画像のリスト
        """
        if name not in self.animations:
            logger.error(f"Animation '{name}' not found")
            return []
        
        anim_data = self.animations[name]
        if isinstance(anim_data, list) and len(anim_data) >= 2:
            return self.get_animation(anim_data[0], anim_data[1])
        else:
            logger.error(f"Invalid animation data for '{name}'")
            return []
    
    def clear_cache(self) -> None:
        """フレームキャッシュをクリア"""
        self._frame_cache.clear()
    
    def get_frame_position(self, index: int) -> Tuple[int, int]:
        """
        フレームの位置を取得
        
        Args:
            index: フレームインデックス
            
        Returns:
            (x, y) 座標のタプル
        """
        if index < 0 or index >= self.frame_count:
            return (0, 0)
        
        col = index % self.cols
        row = index // self.cols
        x = col * self.frame_size[0]
        y = row * self.frame_size[1]
        
        return (x, y)