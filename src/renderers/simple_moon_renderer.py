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
                
            elif self.moon_phase_format == "graphic":
                # グラフィック形式（円を描画）
                self._draw_moon_graphic(screen, moon_info, self.x, self.y)
                
                # 月齢を表示（背景付きで見やすく）
                age_text = f"月齢 {moon_info['age']}"
                age_surface = self.small_font.render(age_text, True, (255, 255, 200))
                age_rect = age_surface.get_rect(center=(self.x, self.y + 45))
                
                # 背景を描画（半透明の黒）
                padding = 4
                bg_rect = age_rect.inflate(padding * 2, padding)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 180))
                screen.blit(bg_surface, bg_rect)
                
                # テキストを描画
                screen.blit(age_surface, age_rect)
                
                # 月相名も表示
                phase_text = moon_info["phase_name"]
                phase_surface = self.small_font.render(phase_text, True, (255, 255, 200))
                phase_rect = phase_surface.get_rect(center=(self.x, self.y + 65))
                
                # 背景を描画
                bg_rect2 = phase_rect.inflate(padding * 2, padding)
                bg_surface2 = pygame.Surface((bg_rect2.width, bg_rect2.height), pygame.SRCALPHA)
                bg_surface2.fill((0, 0, 0, 180))
                screen.blit(bg_surface2, bg_rect2)
                
                # テキストを描画
                screen.blit(phase_surface, phase_rect)
                
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
    
    def _draw_moon_graphic(self, screen: pygame.Surface, moon_info: Dict, x: int, y: int) -> None:
        """
        月をグラフィカルに描画
        
        Args:
            screen: 描画対象のサーフェース
            moon_info: 月情報
            x: X座標
            y: Y座標
        """
        import math
        
        radius = 30  # 月の半径
        moon_age = moon_info["age"]
        
        # 月の色
        moon_color = (255, 255, 200)  # 薄い黄色
        shadow_color = (40, 40, 50)   # 暗い影の色
        
        # 作業用サーフェースを作成（透明背景）
        surface_size = radius * 2 + 4
        moon_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        
        # 月齢を0-1の範囲に正規化
        phase = moon_age / 29.53
        
        # ピクセル単位で月を描画
        for py in range(-radius, radius + 1):
            for px in range(-radius, radius + 1):
                # 円の内側かチェック
                distance_sq = px * px + py * py
                if distance_sq <= radius * radius:
                    # 画面座標
                    screen_x = center_x + px
                    screen_y = center_y + py
                    
                    # 月の位相に基づいて明暗を決定
                    # x座標を-1から1に正規化
                    norm_x = px / radius
                    
                    # 各ピクセルが明るいか暗いかを決定
                    is_bright = False
                    
                    if phase < 0.03 or phase > 0.97:  # 新月
                        is_bright = False
                    elif phase < 0.5:  # 新月から満月へ
                        # 右側が徐々に明るくなる
                        illumination = phase * 2  # 0から1へ
                        
                        if illumination < 0.5:
                            # 三日月形状（右側だけ明るい）
                            # 楕円の境界を計算
                            terminator_x = 1 - illumination * 2  # 1から0へ
                            # y座標での楕円の幅
                            y_factor = math.sqrt(1 - (py / radius) ** 2) if abs(py) <= radius else 0
                            boundary = -1 + (1 - terminator_x) * (1 + y_factor)
                            is_bright = norm_x > boundary
                        else:
                            # 上弦から満月へ（左側の影が減る）
                            shadow_amount = 1 - illumination  # 0.5から0へ
                            # y座標での楕円の幅
                            y_factor = math.sqrt(1 - (py / radius) ** 2) if abs(py) <= radius else 0
                            boundary = -1 + shadow_amount * 2 * y_factor
                            is_bright = norm_x > boundary
                    
                    elif phase < 0.53:  # 満月
                        is_bright = True
                    
                    else:  # 満月から新月へ
                        waning = (phase - 0.5) * 2  # 0から1へ
                        
                        if waning < 0.5:
                            # 満月直後から下弦（左側に影が増える）
                            shadow_amount = waning * 2  # 0から1へ
                            # y座標での楕円の幅
                            y_factor = math.sqrt(1 - (py / radius) ** 2) if abs(py) <= radius else 0
                            boundary = -1 + shadow_amount * 2 * y_factor
                            is_bright = norm_x > boundary
                        else:
                            # 下弦から新月（右側だけ明るい三日月）
                            illumination = 2 - waning * 2  # 1から0へ
                            # y座標での楕円の幅
                            y_factor = math.sqrt(1 - (py / radius) ** 2) if abs(py) <= radius else 0
                            boundary = 1 - illumination * (1 + y_factor)
                            is_bright = norm_x > boundary
                    
                    # ピクセルの色を設定
                    if is_bright:
                        # 縁に近いほど少し暗くする（リアリズム向上）
                        edge_factor = 1.0 - (distance_sq / (radius * radius)) * 0.2
                        color = (
                            int(moon_color[0] * edge_factor),
                            int(moon_color[1] * edge_factor),
                            int(moon_color[2] * edge_factor)
                        )
                        moon_surface.set_at((screen_x, screen_y), color + (255,))
                    else:
                        moon_surface.set_at((screen_x, screen_y), shadow_color + (255,))
        
        # 輪郭線を描画
        pygame.draw.circle(moon_surface, (200, 200, 180), (center_x, center_y), radius, 1)
        
        # 満月の場合はハイライトを追加
        if 0.47 < phase < 0.53:
            pygame.draw.circle(moon_surface, (255, 255, 220), 
                             (center_x - radius // 3, center_y - radius // 3), 
                             radius // 5)
        
        # 完成した月を画面に描画
        screen.blit(moon_surface, (x - center_x, y - center_y))
    
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