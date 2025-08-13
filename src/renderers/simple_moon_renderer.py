#!/usr/bin/env python3
"""
シンプルな月相レンダラー
"""

import pygame
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

# 月相計算モジュールをインポート
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / 'utils'))
    from moon_phase import get_moon_info, get_moon_display
    MOON_PHASE_AVAILABLE = True
except ImportError:
    MOON_PHASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SimpleMoonRenderer:
    """シンプルな月相レンダラー"""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            settings: 設定辞書
        """
        self.settings = settings or {}
        ui_settings = self.settings.get('ui', {})
        calendar_settings = self.settings.get('calendar', {})
        layout_settings = self.settings.get('layout', {}).get('moon_phase', {})
        
        # 月相表示設定
        self.moon_phase_enabled = calendar_settings.get('moon_phase_enabled', True)
        self.moon_phase_format = calendar_settings.get('moon_phase_format', 'emoji')
        
        # レイアウト設定
        self.position = layout_settings.get('position', 'top-right')
        self.x_offset = layout_settings.get('x_offset', -50)
        self.y_offset = layout_settings.get('y_offset', 50)
        
        # 画面設定
        screen_settings = self.settings.get('screen', {})
        self.screen_width = screen_settings.get('width', 1024)
        self.screen_height = screen_settings.get('height', 600)
        
        # フォント設定
        self.font_size = 48  # 月相表示用の大きめのフォントサイズ
        self.small_font_size = 16
        
        # フォント初期化（settings.yamlの設定を使用）
        font_config = self.settings.get('fonts', {}).get('main', {})
        font_path = font_config.get('path', './assets/fonts/NotoSansCJK-Regular.otf')
        font_fallback = font_config.get('fallback', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf')
        
        # フォントファイルを探す
        self.font_file = None
        from pathlib import Path
        
        for path in [font_path, font_fallback]:
            if Path(path).exists():
                self.font_file = path
                break
        
        # フォントを初期化
        try:
            if self.font_file:
                self.font = pygame.font.Font(self.font_file, self.font_size)
                self.small_font = pygame.font.Font(self.font_file, self.small_font_size)
            else:
                # ファイルが見つからない場合はSysFontを使用
                self.font = pygame.font.SysFont('notosanscjkjp', self.font_size)
                self.small_font = pygame.font.SysFont('notosanscjkjp', self.small_font_size)
        except Exception as e:
            logger.warning(f"Failed to create font: {e}")
            self.font = pygame.font.Font(None, self.font_size)
            self.small_font = pygame.font.Font(None, self.small_font_size)
        
        # 位置を計算
        self._calculate_position()
        
        # 更新間隔
        self.last_update = 0
        self.update_interval = 3600.0  # 1時間ごと
        
        logger.info(f"Moon phase settings: enabled={self.moon_phase_enabled}, format={self.moon_phase_format}, available={MOON_PHASE_AVAILABLE}")
    
    def _calculate_position(self):
        """位置を計算"""
        # 基本位置を決定
        if self.position == "top-left":
            base_x = 100
            base_y = 50
        elif self.position == "top-center":
            base_x = self.screen_width // 2
            base_y = 50
        elif self.position == "top-right":
            base_x = self.screen_width - 100
            base_y = 50
        elif self.position == "center":
            base_x = self.screen_width // 2
            base_y = self.screen_height // 2
        elif self.position == "bottom-left":
            base_x = 100
            base_y = self.screen_height - 100
        elif self.position == "bottom-center":
            base_x = self.screen_width // 2
            base_y = self.screen_height - 100
        elif self.position == "bottom-right":
            base_x = self.screen_width - 100
            base_y = self.screen_height - 100
        else:
            # デフォルト: 右上
            base_x = self.screen_width - 100
            base_y = 50
        
        # オフセットを適用
        self.x = base_x + self.x_offset
        self.y = base_y + self.y_offset
    
    def render(self, screen: pygame.Surface) -> None:
        """
        月相を描画
        
        Args:
            screen: 描画対象のサーフェース
        """
        if not self.moon_phase_enabled or not MOON_PHASE_AVAILABLE:
            return
        
        try:
            now = datetime.now()
            today = now.date()
            
            # 月相情報を取得
            moon_info = get_moon_info(today)
            
            # 表示形式に応じて描画
            if self.moon_phase_format == "emoji":
                # 絵文字形式
                moon_text = moon_info["emoji"]
                text_surface = self.font.render(moon_text, True, (255, 255, 200))
                text_rect = text_surface.get_rect(center=(self.x, self.y))
                screen.blit(text_surface, text_rect)
                
                # 月齢を小さく表示
                age_text = f"月齢 {moon_info['age']}"
                age_surface = self.small_font.render(age_text, True, (200, 200, 200))
                age_rect = age_surface.get_rect(center=(self.x, self.y + 35))
                screen.blit(age_surface, age_rect)
                
            elif self.moon_phase_format == "text":
                # テキスト形式
                moon_text = moon_info["phase_name"]
                text_surface = self.small_font.render(moon_text, True, (255, 255, 200))
                text_rect = text_surface.get_rect(center=(self.x, self.y))
                screen.blit(text_surface, text_rect)
                
                # 月齢を表示
                age_text = f"月齢 {moon_info['age']}"
                age_surface = self.small_font.render(age_text, True, (200, 200, 200))
                age_rect = age_surface.get_rect(center=(self.x, self.y + 20))
                screen.blit(age_surface, age_rect)
                
            elif self.moon_phase_format == "ascii":
                # ASCII形式
                moon_text = moon_info["ascii"]
                # ASCIIは大きめに表示
                ascii_font = pygame.font.Font(None, 64)
                text_surface = ascii_font.render(moon_text, True, (255, 255, 200))
                text_rect = text_surface.get_rect(center=(self.x, self.y))
                screen.blit(text_surface, text_rect)
                
                # 月相名を小さく表示
                phase_surface = self.small_font.render(moon_info["phase_name"], True, (200, 200, 200))
                phase_rect = phase_surface.get_rect(center=(self.x, self.y + 35))
                screen.blit(phase_surface, phase_rect)
            
        except Exception as e:
            logger.error(f"Failed to render moon phase: {e}")
    
    def should_update(self) -> bool:
        """
        更新が必要か確認
        
        Returns:
            更新が必要な場合True
        """
        import time
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            return True
        return False