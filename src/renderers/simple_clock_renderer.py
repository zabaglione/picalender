"""
シンプルな時計レンダラー
AssetManagerに依存しない実装
"""

import pygame
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleClockRenderer:
    """シンプルな時計レンダラー"""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            settings: 設定辞書
        """
        self.settings = settings or {}
        ui_settings = self.settings.get('ui', {})
        
        # フォントサイズ
        self.font_size = ui_settings.get('clock_font_px', 130)
        
        # フォント初期化
        try:
            self.font = pygame.font.Font(None, self.font_size)
        except:
            logger.warning(f"Failed to create font with size {self.font_size}, using default")
            self.font = pygame.font.Font(None, 72)
        
        # 位置設定
        screen_settings = self.settings.get('screen', {})
        self.screen_width = screen_settings.get('width', 1024)
        self.screen_height = screen_settings.get('height', 600)
        
        # 色設定
        self.color = (255, 255, 255)  # 白
        self.shadow_color = (10, 10, 20)  # 影の色
        
        # 更新間隔
        self.last_update = 0
        self.update_interval = 1.0  # 1秒ごと
    
    def render(self, screen: pygame.Surface) -> None:
        """
        時計を描画
        
        Args:
            screen: 描画対象のサーフェース
        """
        try:
            # 現在時刻を取得
            time_str = time.strftime("%H:%M:%S")
            
            # テキストレンダリング
            text_surface = self.font.render(time_str, True, self.color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, 100))
            
            # ドロップシャドウ
            shadow_surface = self.font.render(time_str, True, self.shadow_color)
            shadow_rect = text_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            
            # 描画
            screen.blit(shadow_surface, shadow_rect)
            screen.blit(text_surface, text_rect)
            
        except Exception as e:
            logger.error(f"Failed to render clock: {e}")
    
    def should_update(self) -> bool:
        """
        更新が必要か確認
        
        Returns:
            更新が必要な場合True
        """
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            return True
        return False