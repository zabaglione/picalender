"""
フォント管理
"""

import os
import logging
from typing import Dict, Optional, Tuple
import pygame

logger = logging.getLogger(__name__)


class FontManager:
    """フォントの読み込みと管理"""
    
    def __init__(self, base_path: str):
        """
        初期化
        
        Args:
            base_path: ベースディレクトリパス
        """
        self.base_path = base_path
        self.fonts: Dict[str, pygame.font.Font] = {}
        
        # pygame.fontの初期化
        if not pygame.font.get_init():
            pygame.font.init()
    
    def load(self, font_path: str, size: int) -> pygame.font.Font:
        """
        フォントを読み込み
        
        Args:
            font_path: フォントファイルパス
            size: フォントサイズ
            
        Returns:
            pygame.font.Font オブジェクト
        """
        cache_key = f"{font_path}_{size}"
        
        # キャッシュチェック
        if cache_key in self.fonts:
            return self.fonts[cache_key]
        
        try:
            # 絶対パスでない場合はベースパスと結合
            if not os.path.isabs(font_path):
                font_path = os.path.join(self.base_path, font_path)
            
            # フォント読み込み
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, size)
            else:
                # ファイルが存在しない場合はシステムフォントにフォールバック
                logger.warning(f"Font file not found: {font_path}, using system font")
                font = self.get_system_font(None, size)
            
            self.fonts[cache_key] = font
            return font
            
        except Exception as e:
            logger.error(f"Failed to load font {font_path}: {e}")
            # エラー時はシステムフォントを返す
            return self.get_system_font(None, size)
    
    def get_system_font(self, name: Optional[str], size: int) -> pygame.font.Font:
        """
        システムフォントを取得
        
        Args:
            name: フォント名（Noneでデフォルト）
            size: フォントサイズ
            
        Returns:
            pygame.font.Font オブジェクト
        """
        try:
            # 日本語対応のシステムフォントを試す
            japanese_fonts = [
                'notosanscjkjp',
                'hiraginosans',
                'meiryo',
                'yugothic',
                'msgothic'
            ]
            
            if name:
                return pygame.font.SysFont(name, size)
            
            # 日本語フォントを順に試す
            for font_name in japanese_fonts:
                if font_name in pygame.font.get_fonts():
                    return pygame.font.SysFont(font_name, size)
            
            # デフォルトフォント
            return pygame.font.SysFont(None, size)
            
        except Exception as e:
            logger.error(f"Failed to get system font: {e}")
            # 最終フォールバック
            return pygame.font.Font(None, size)
    
    def render_text(self, font: pygame.font.Font, text: str, 
                   color: Tuple[int, int, int], 
                   antialias: bool = True) -> pygame.Surface:
        """
        テキストをレンダリング
        
        Args:
            font: フォントオブジェクト
            text: レンダリングするテキスト
            color: テキスト色 (R, G, B)
            antialias: アンチエイリアスを適用するか
            
        Returns:
            レンダリングされたサーフェス
        """
        try:
            return font.render(text, antialias, color)
        except Exception as e:
            logger.error(f"Failed to render text: {e}")
            # エラー時は空のサーフェスを返す
            return pygame.Surface((1, 1))
    
    def get_text_size(self, font: pygame.font.Font, text: str) -> Tuple[int, int]:
        """
        テキストのサイズを取得
        
        Args:
            font: フォントオブジェクト
            text: 測定するテキスト
            
        Returns:
            (幅, 高さ) のタプル
        """
        try:
            return font.size(text)
        except Exception as e:
            logger.error(f"Failed to get text size: {e}")
            return (0, 0)