"""
フォントローダー実装

TASK-103: フォント管理システム
- TTF/OTF/CJKフォント対応
- サイズ別キャッシュ管理
- フォールバック機能
"""

import os
import logging
from typing import Optional, Dict, Any, List
import pygame
from ..cache.lru_cache import LRUCache

logger = logging.getLogger(__name__)


class FontLoader:
    """フォントローダークラス"""
    
    def __init__(self, cache_size: int = 50):
        """
        初期化
        
        Args:
            cache_size: キャッシュサイズ
        """
        self.cache = LRUCache(max_size=cache_size, max_memory=10 * 1024 * 1024)  # 10MB
        
        # システムフォントパスの候補
        self.system_font_paths = self._find_system_fonts()
        
        # フォールバック用デフォルトフォント
        self.default_font = None
        
    def load_font(self, font_path: Optional[str], size: int) -> pygame.font.Font:
        """
        フォントを読み込み
        
        Args:
            font_path: フォントファイルパス（Noneでシステムデフォルト）
            size: フォントサイズ
            
        Returns:
            pygame.font.Fontオブジェクト
        """
        # キャッシュキーを生成
        cache_key = f"{font_path or 'default'}:{size}"
        
        # キャッシュから取得を試行
        cached_font = self.cache.get(cache_key)
        if cached_font is not None:
            return cached_font
        
        # フォント読み込み
        try:
            font = self._load_font_impl(font_path, size)
            self.cache.put(cache_key, font)
            return font
        except Exception as e:
            logger.warning(f"Font loading failed for {font_path}: {e}")
            return self._get_fallback_font(size)
    
    def _load_font_impl(self, font_path: Optional[str], size: int) -> pygame.font.Font:
        """
        フォント読み込みの実装
        
        Args:
            font_path: フォントファイルパス
            size: フォントサイズ
            
        Returns:
            pygame.font.Fontオブジェクト
        """
        if font_path is None:
            # システムデフォルトフォント
            return pygame.font.Font(None, size)
        
        # ファイル存在チェック
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font file not found: {font_path}")
        
        # フォント読み込み
        try:
            return pygame.font.Font(font_path, size)
        except pygame.error as e:
            raise RuntimeError(f"Failed to load font: {e}")
    
    def _get_fallback_font(self, size: int) -> pygame.font.Font:
        """
        フォールバック用フォントを取得
        
        Args:
            size: フォントサイズ
            
        Returns:
            pygame.font.Fontオブジェクト
        """
        try:
            # システムデフォルトフォント
            if self.default_font is None:
                self.default_font = pygame.font.Font(None, 24)
            
            # サイズが異なる場合は新しく作成
            if size != 24:
                return pygame.font.Font(None, size)
            
            return self.default_font
            
        except Exception as e:
            logger.error(f"Failed to create fallback font: {e}")
            # 最後の手段：pygameデフォルト
            return pygame.font.Font(None, size)
    
    def _find_system_fonts(self) -> List[str]:
        """
        システムフォントパスを検索
        
        Returns:
            システムフォントパスのリスト
        """
        font_paths = []
        
        # 一般的なシステムフォントディレクトリ
        possible_dirs = [
            "/System/Library/Fonts",           # macOS
            "/usr/share/fonts",                # Linux
            "/usr/local/share/fonts",          # Linux
            "C:\\Windows\\Fonts",              # Windows
        ]
        
        for font_dir in possible_dirs:
            if os.path.exists(font_dir):
                try:
                    for font_file in os.listdir(font_dir):
                        if font_file.lower().endswith(('.ttf', '.otf')):
                            font_paths.append(os.path.join(font_dir, font_file))
                except (PermissionError, OSError):
                    continue
        
        return font_paths
    
    def find_cjk_font(self) -> Optional[str]:
        """
        CJK（日中韓）対応フォントを検索
        
        Returns:
            CJKフォントパス（見つからない場合None）
        """
        cjk_font_names = [
            'NotoSansCJK-Regular.ttc',
            'NotoSansCJK.ttc',
            'NotoSansJP-Regular.otf',
            'Hiragino Sans GB.ttc',
            'PingFang.ttc',
            'SimHei.ttf',
            'MS Gothic.ttf'
        ]
        
        for font_path in self.system_font_paths:
            font_name = os.path.basename(font_path)
            if any(cjk_name in font_name for cjk_name in cjk_font_names):
                return font_path
        
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            統計情報
        """
        return self.cache.get_statistics()
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
    
    def preload_common_fonts(self) -> None:
        """
        よく使用されるフォントサイズをプリロード
        """
        common_sizes = [12, 16, 18, 24, 32, 36, 48, 72, 96, 130]
        
        for size in common_sizes:
            try:
                self.load_font(None, size)  # システムデフォルト
                
                # CJKフォントがある場合はそれもプリロード
                cjk_font = self.find_cjk_font()
                if cjk_font:
                    self.load_font(cjk_font, size)
                    
            except Exception as e:
                logger.debug(f"Preload failed for size {size}: {e}")
        
        logger.info(f"Preloaded fonts for {len(common_sizes)} sizes")