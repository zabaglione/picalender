"""
画像ローダー実装

TASK-103: 画像管理システム
- PNG/JPG/GIF対応
- 自動スケーリング機能
- 透明度処理
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
from enum import Enum
import pygame
from ..cache.lru_cache import LRUCache

logger = logging.getLogger(__name__)


class ScaleMode(Enum):
    """スケーリングモード"""
    FIT = "fit"           # アスペクト比保持してフィット
    SCALE = "scale"       # 指定サイズに強制スケール
    STRETCH = "stretch"   # 縦横比無視して伸縮


class ImageLoader:
    """画像ローダークラス"""
    
    def __init__(self, cache_size: int = 100):
        """
        初期化
        
        Args:
            cache_size: キャッシュサイズ
        """
        self.cache = LRUCache(max_size=cache_size, max_memory=30 * 1024 * 1024)  # 30MB
        
        # デフォルト画像（黒い正方形）
        self.default_image = None
        
    def load_image(self, image_path: str, target_size: Optional[Tuple[int, int]] = None, 
                  scale_mode: ScaleMode = ScaleMode.FIT) -> pygame.Surface:
        """
        画像を読み込み
        
        Args:
            image_path: 画像ファイルパス
            target_size: 目標サイズ（None で元サイズ）
            scale_mode: スケーリングモード
            
        Returns:
            pygame.Surfaceオブジェクト
        """
        # キャッシュキーを生成
        cache_key = f"{image_path}:{target_size}:{scale_mode.value}"
        
        # キャッシュから取得を試行
        cached_image = self.cache.get(cache_key)
        if cached_image is not None:
            return cached_image
        
        # 画像読み込み
        try:
            surface = self._load_image_impl(image_path, target_size, scale_mode)
            self.cache.put(cache_key, surface)
            return surface
        except Exception as e:
            logger.warning(f"Image loading failed for {image_path}: {e}")
            return self._get_default_image(target_size or (100, 100))
    
    def _load_image_impl(self, image_path: str, target_size: Optional[Tuple[int, int]], 
                        scale_mode: ScaleMode) -> pygame.Surface:
        """
        画像読み込みの実装
        
        Args:
            image_path: 画像ファイルパス
            target_size: 目標サイズ
            scale_mode: スケーリングモード
            
        Returns:
            pygame.Surfaceオブジェクト
        """
        # ファイル存在チェック
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # 画像読み込み
        try:
            surface = pygame.image.load(image_path)
        except pygame.error as e:
            raise RuntimeError(f"Failed to load image: {e}")
        
        # アルファチャンネル処理
        surface = self._process_alpha(surface)
        
        # スケーリング処理
        if target_size is not None:
            surface = self._scale_image(surface, target_size, scale_mode)
        
        return surface
    
    def _process_alpha(self, surface: pygame.Surface) -> pygame.Surface:
        """
        アルファチャンネル処理
        
        Args:
            surface: 元のサーフェス
            
        Returns:
            処理済みサーフェス
        """
        # PNGの場合、アルファチャンネルを保持
        if surface.get_flags() & pygame.SRCALPHA:
            return surface.convert_alpha()
        else:
            return surface.convert()
    
    def _scale_image(self, surface: pygame.Surface, target_size: Tuple[int, int], 
                    scale_mode: ScaleMode) -> pygame.Surface:
        """
        画像スケーリング
        
        Args:
            surface: 元のサーフェス
            target_size: 目標サイズ
            scale_mode: スケーリングモード
            
        Returns:
            スケーリング済みサーフェス
        """
        original_size = surface.get_size()
        
        if scale_mode == ScaleMode.FIT:
            # アスペクト比を保持してフィット
            scale_size = self._calculate_fit_size(original_size, target_size)
        elif scale_mode == ScaleMode.SCALE:
            # 指定サイズに強制スケール
            scale_size = target_size
        elif scale_mode == ScaleMode.STRETCH:
            # 縦横比無視（STRETCHもSCALEと同じ処理）
            scale_size = target_size
        else:
            scale_size = target_size
        
        # スケーリング実行
        if scale_size != original_size:
            try:
                return pygame.transform.smoothscale(surface, scale_size)
            except Exception:
                # smoothscaleが失敗した場合はscaleを使用
                return pygame.transform.scale(surface, scale_size)
        
        return surface
    
    def _calculate_fit_size(self, original_size: Tuple[int, int], 
                           target_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        FITモードのサイズを計算
        
        Args:
            original_size: 元のサイズ
            target_size: 目標サイズ
            
        Returns:
            フィットサイズ
        """
        orig_w, orig_h = original_size
        target_w, target_h = target_size
        
        # アスペクト比を計算
        orig_ratio = orig_w / orig_h
        target_ratio = target_w / target_h
        
        if orig_ratio > target_ratio:
            # 横長：幅を基準にスケール
            new_w = target_w
            new_h = int(target_w / orig_ratio)
        else:
            # 縦長：高さを基準にスケール
            new_h = target_h
            new_w = int(target_h * orig_ratio)
        
        return (new_w, new_h)
    
    def _get_default_image(self, size: Tuple[int, int]) -> pygame.Surface:
        """
        デフォルト画像を取得
        
        Args:
            size: サイズ
            
        Returns:
            デフォルト画像サーフェス
        """
        try:
            # 単色のサーフェスを作成
            surface = pygame.Surface(size)
            surface.fill((50, 50, 50))  # ダークグレー
            return surface
        except Exception as e:
            logger.error(f"Failed to create default image: {e}")
            # 最小限のフォールバック
            return pygame.Surface((1, 1))
    
    def get_supported_formats(self) -> list:
        """
        サポートされている画像フォーマットを取得
        
        Returns:
            サポートフォーマットのリスト
        """
        return ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tga']
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        サポートされているフォーマットかチェック
        
        Args:
            file_path: ファイルパス
            
        Returns:
            サポート有無
        """
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.get_supported_formats()
    
    def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        画像情報を取得（メタデータ）
        
        Args:
            image_path: 画像パス
            
        Returns:
            画像情報（読み込み失敗時None）
        """
        try:
            surface = pygame.image.load(image_path)
            width, height = surface.get_size()
            bitsize = surface.get_bitsize()
            flags = surface.get_flags()
            
            return {
                'path': image_path,
                'size': (width, height),
                'width': width,
                'height': height,
                'bitsize': bitsize,
                'has_alpha': bool(flags & pygame.SRCALPHA),
                'format': os.path.splitext(image_path)[1].lower(),
                'file_size': os.path.getsize(image_path)
            }
        except Exception as e:
            logger.warning(f"Failed to get image info for {image_path}: {e}")
            return None
    
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