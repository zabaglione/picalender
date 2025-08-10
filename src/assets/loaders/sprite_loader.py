"""
スプライトローダー実装

TASK-103: スプライト管理システム
- 横並びスプライトシートの分割処理
- フレーム定義ファイル読み込み
- アニメーション情報の管理
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import pygame
from ..cache.lru_cache import LRUCache

logger = logging.getLogger(__name__)


class SpriteLoader:
    """スプライトローダークラス"""
    
    def __init__(self, cache_size: int = 50):
        """
        初期化
        
        Args:
            cache_size: キャッシュサイズ
        """
        self.cache = LRUCache(max_size=cache_size, max_memory=20 * 1024 * 1024)  # 20MB
    
    def load_sprite_sheet(self, sprite_path: str, frame_width: int, frame_height: int, 
                         frame_count: int) -> List[pygame.Surface]:
        """
        スプライトシートを分割してフレームリストを取得
        
        Args:
            sprite_path: スプライトシートパス
            frame_width: フレーム幅
            frame_height: フレーム高さ
            frame_count: フレーム数
            
        Returns:
            フレームサーフェスのリスト
        """
        # キャッシュキーを生成
        cache_key = f"sprite:{sprite_path}:{frame_width}x{frame_height}x{frame_count}"
        
        # キャッシュから取得を試行
        cached_frames = self.cache.get(cache_key)
        if cached_frames is not None:
            return cached_frames
        
        # スプライト読み込み・分割
        try:
            frames = self._load_sprite_impl(sprite_path, frame_width, frame_height, frame_count)
            self.cache.put(cache_key, frames)
            return frames
        except Exception as e:
            logger.error(f"Sprite loading failed for {sprite_path}: {e}")
            return self._get_default_frames(frame_width, frame_height, frame_count)
    
    def _load_sprite_impl(self, sprite_path: str, frame_width: int, frame_height: int, 
                         frame_count: int) -> List[pygame.Surface]:
        """
        スプライト読み込みの実装
        
        Args:
            sprite_path: スプライトシートパス
            frame_width: フレーム幅
            frame_height: フレーム高さ
            frame_count: フレーム数
            
        Returns:
            フレームサーフェスのリスト
        """
        # ファイル存在チェック
        if not os.path.exists(sprite_path):
            raise FileNotFoundError(f"Sprite file not found: {sprite_path}")
        
        # スプライトシート読み込み
        try:
            sprite_sheet = pygame.image.load(sprite_path)
        except pygame.error as e:
            raise RuntimeError(f"Failed to load sprite sheet: {e}")
        
        # アルファチャンネル処理
        sprite_sheet = sprite_sheet.convert_alpha()
        
        # フレーム分割
        frames = []
        for i in range(frame_count):
            x = i * frame_width
            y = 0
            
            # フレーム領域をチェック
            if x + frame_width > sprite_sheet.get_width():
                logger.warning(f"Frame {i} exceeds sprite sheet width")
                break
            
            # フレームを切り出し
            frame_rect = pygame.Rect(x, y, frame_width, frame_height)
            frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame_surface.blit(sprite_sheet, (0, 0), frame_rect)
            frames.append(frame_surface)
        
        return frames
    
    def load_frame_definition(self, definition_path: str) -> Dict[str, Any]:
        """
        フレーム定義ファイルを読み込み
        
        Args:
            definition_path: 定義ファイルパス
            
        Returns:
            フレーム定義情報
        """
        # キャッシュキーを生成
        cache_key = f"definition:{definition_path}"
        
        # キャッシュから取得を試行
        cached_def = self.cache.get(cache_key)
        if cached_def is not None:
            return cached_def
        
        # 定義ファイル読み込み
        try:
            frame_def = self._load_definition_impl(definition_path)
            self.cache.put(cache_key, frame_def)
            return frame_def
        except Exception as e:
            logger.error(f"Frame definition loading failed for {definition_path}: {e}")
            return self._get_default_definition()
    
    def _load_definition_impl(self, definition_path: str) -> Dict[str, Any]:
        """
        フレーム定義読み込みの実装
        
        Args:
            definition_path: 定義ファイルパス
            
        Returns:
            フレーム定義情報
        """
        # ファイル存在チェック
        if not os.path.exists(definition_path):
            raise FileNotFoundError(f"Definition file not found: {definition_path}")
        
        # JSON読み込み
        try:
            with open(definition_path, 'r', encoding='utf-8') as f:
                definition = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Failed to load frame definition: {e}")
        
        # 必要なフィールドの検証
        required_fields = ['frame_width', 'frame_height', 'frame_count']
        for field in required_fields:
            if field not in definition:
                raise ValueError(f"Missing required field: {field}")
        
        return definition
    
    def load_animation(self, sprite_path: str, frame_def_path: str) -> Dict[str, Any]:
        """
        アニメーション情報を読み込み
        
        Args:
            sprite_path: スプライトシートパス
            frame_def_path: フレーム定義パス
            
        Returns:
            アニメーション情報
        """
        # フレーム定義を読み込み
        frame_def = self.load_frame_definition(frame_def_path)
        
        # スプライトフレームを読み込み
        frames = self.load_sprite_sheet(
            sprite_path,
            frame_def['frame_width'],
            frame_def['frame_height'],
            frame_def['frame_count']
        )
        
        # アニメーション情報を構築
        animation = {
            'frames': frames,
            'frame_count': len(frames),
            'frame_width': frame_def['frame_width'],
            'frame_height': frame_def['frame_height'],
            'fps': frame_def.get('animation', {}).get('fps', 8),
            'loop': frame_def.get('animation', {}).get('loop', True),
            'duration': len(frames) / frame_def.get('animation', {}).get('fps', 8)
        }
        
        return animation
    
    def _get_default_frames(self, frame_width: int, frame_height: int, 
                           frame_count: int) -> List[pygame.Surface]:
        """
        デフォルトフレームを生成
        
        Args:
            frame_width: フレーム幅
            frame_height: フレーム高さ
            frame_count: フレーム数
            
        Returns:
            デフォルトフレームのリスト
        """
        frames = []
        
        for i in range(frame_count):
            # 単色フレームを生成（色を変えて識別可能にする）
            surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            color_intensity = min(255, 50 + i * 30)
            surface.fill((color_intensity, 50, 50, 255))
            frames.append(surface)
        
        return frames
    
    def _get_default_definition(self) -> Dict[str, Any]:
        """
        デフォルトフレーム定義を取得
        
        Returns:
            デフォルト定義
        """
        return {
            'frame_width': 64,
            'frame_height': 64,
            'frame_count': 1,
            'animation': {
                'fps': 8,
                'loop': True
            }
        }
    
    def create_sprite_animation(self, frames: List[pygame.Surface], fps: int = 8, 
                              loop: bool = True) -> Dict[str, Any]:
        """
        スプライトアニメーション情報を作成
        
        Args:
            frames: フレームリスト
            fps: フレームレート
            loop: ループするか
            
        Returns:
            アニメーション情報
        """
        return {
            'frames': frames,
            'frame_count': len(frames),
            'fps': fps,
            'loop': loop,
            'duration': len(frames) / fps if fps > 0 else 0,
            'frame_duration': 1.0 / fps if fps > 0 else 0
        }
    
    def extract_single_frame(self, sprite_path: str, frame_index: int, 
                           frame_width: int, frame_height: int) -> pygame.Surface:
        """
        スプライトシートから単一フレームを抽出
        
        Args:
            sprite_path: スプライトシートパス
            frame_index: フレームインデックス
            frame_width: フレーム幅
            frame_height: フレーム高さ
            
        Returns:
            フレームサーフェス
        """
        # キャッシュキーを生成
        cache_key = f"frame:{sprite_path}:{frame_index}:{frame_width}x{frame_height}"
        
        # キャッシュから取得
        cached_frame = self.cache.get(cache_key)
        if cached_frame is not None:
            return cached_frame
        
        try:
            # スプライトシート全体を一旦取得
            frames = self.load_sprite_sheet(sprite_path, frame_width, frame_height, frame_index + 1)
            
            if frame_index < len(frames):
                frame = frames[frame_index]
                self.cache.put(cache_key, frame)
                return frame
            else:
                raise IndexError(f"Frame index {frame_index} out of range")
                
        except Exception as e:
            logger.error(f"Single frame extraction failed: {e}")
            return self._get_default_frames(frame_width, frame_height, 1)[0]
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            統計情報
        """
        return self.cache.get_statistics()