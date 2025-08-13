"""
シンプルな時計レンダラー
AssetManagerに依存しない実装
等幅表示対応版
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
        
        # フォント初期化（デフォルトフォントを使用）
        try:
            self.font = pygame.font.Font(None, self.font_size)
            logger.info("Using default font")
        except:
            logger.warning(f"Failed to create font with size {self.font_size}, using fallback")
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
        
        # 各文字の幅を事前計算（固定位置表示用）
        self._calculate_char_widths()
    
    def _calculate_char_widths(self):
        """数字とコロンの幅を計算"""
        self.digit_widths = {}
        self.colon_width = 0
        
        # 各数字の幅を測定
        for i in range(10):
            text_surface = self.font.render(str(i), True, self.color)
            self.digit_widths[str(i)] = text_surface.get_width()
        
        # コロンの幅を測定
        colon_surface = self.font.render(":", True, self.color)
        self.colon_width = colon_surface.get_width()
        
        # 最大幅を取得（固定幅として使用）
        self.max_digit_width = max(self.digit_widths.values())
    
    def render(self, screen: pygame.Surface) -> None:
        """
        時計を描画（固定位置方式）
        
        Args:
            screen: 描画対象のサーフェース
        """
        try:
            # 現在時刻を取得
            current_time = time.localtime()
            hours = f"{current_time.tm_hour:02d}"
            minutes = f"{current_time.tm_min:02d}"
            seconds = f"{current_time.tm_sec:02d}"
            
            # 全体の幅を計算（固定幅使用）
            total_width = (self.max_digit_width * 6 +  # 6桁の数字
                          self.colon_width * 2)         # 2つのコロン
            
            # 開始位置
            start_x = (self.screen_width - total_width) // 2
            y_pos = 100
            
            # 現在のX位置
            x_pos = start_x
            
            # 時間の各桁を描画
            for i, char in enumerate(hours):
                # 文字を描画
                text_surface = self.font.render(char, True, self.color)
                shadow_surface = self.font.render(char, True, self.shadow_color)
                
                # 中央揃えで配置
                char_rect = text_surface.get_rect()
                char_rect.centerx = x_pos + self.max_digit_width // 2
                char_rect.centery = y_pos
                
                # 影を描画
                shadow_rect = char_rect.copy()
                shadow_rect.x += 3
                shadow_rect.y += 3
                screen.blit(shadow_surface, shadow_rect)
                
                # 文字を描画
                screen.blit(text_surface, char_rect)
                
                x_pos += self.max_digit_width
            
            # コロンを描画
            colon_surface = self.font.render(":", True, self.color)
            colon_shadow = self.font.render(":", True, self.shadow_color)
            colon_rect = colon_surface.get_rect()
            colon_rect.centerx = x_pos + self.colon_width // 2
            colon_rect.centery = y_pos
            
            shadow_rect = colon_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            screen.blit(colon_shadow, shadow_rect)
            screen.blit(colon_surface, colon_rect)
            x_pos += self.colon_width
            
            # 分の各桁を描画
            for i, char in enumerate(minutes):
                text_surface = self.font.render(char, True, self.color)
                shadow_surface = self.font.render(char, True, self.shadow_color)
                
                char_rect = text_surface.get_rect()
                char_rect.centerx = x_pos + self.max_digit_width // 2
                char_rect.centery = y_pos
                
                shadow_rect = char_rect.copy()
                shadow_rect.x += 3
                shadow_rect.y += 3
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, char_rect)
                
                x_pos += self.max_digit_width
            
            # 2つ目のコロンを描画
            colon_rect = colon_surface.get_rect()
            colon_rect.centerx = x_pos + self.colon_width // 2
            colon_rect.centery = y_pos
            
            shadow_rect = colon_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            screen.blit(colon_shadow, shadow_rect)
            screen.blit(colon_surface, colon_rect)
            x_pos += self.colon_width
            
            # 秒の各桁を描画
            for i, char in enumerate(seconds):
                text_surface = self.font.render(char, True, self.color)
                shadow_surface = self.font.render(char, True, self.shadow_color)
                
                char_rect = text_surface.get_rect()
                char_rect.centerx = x_pos + self.max_digit_width // 2
                char_rect.centery = y_pos
                
                shadow_rect = char_rect.copy()
                shadow_rect.x += 3
                shadow_rect.y += 3
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, char_rect)
                
                x_pos += self.max_digit_width
            
        except Exception as e:
            logger.error(f"Failed to render clock: {e}")
            # フォールバック：通常の描画
            self._render_fallback(screen)
    
    def _render_fallback(self, screen: pygame.Surface) -> None:
        """フォールバック描画（従来の方式）"""
        try:
            time_str = time.strftime("%H:%M:%S")
            text_surface = self.font.render(time_str, True, self.color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, 100))
            
            shadow_surface = self.font.render(time_str, True, self.shadow_color)
            shadow_rect = text_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            
            screen.blit(shadow_surface, shadow_rect)
            screen.blit(text_surface, text_rect)
        except Exception as e:
            logger.error(f"Fallback render also failed: {e}")
    
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