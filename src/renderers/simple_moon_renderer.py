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
        outline_color = (180, 180, 160)  # 輪郭線の色
        
        # 作業用サーフェースを作成（透明背景、アンチエイリアシング用に大きめ）
        surface_size = radius * 2 + 6
        moon_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        
        # 月齢を0-1の範囲に正規化
        phase = moon_age / 29.53
        
        # アンチエイリアシングされた月を描画
        if phase < 0.03 or phase > 0.97:  # 新月（月齢0-1, 28.5-29.53）
            # 全体を暗く
            pygame.draw.circle(moon_surface, shadow_color, (center_x, center_y), radius)
            pygame.draw.circle(moon_surface, (50, 50, 55), (center_x, center_y), radius, 1)
            
        elif phase < 0.5:  # 新月から満月へ（月齢1-14.75）
            # 右側が明るく、左側が暗い
            # まず全体を暗くする
            pygame.draw.circle(moon_surface, shadow_color, (center_x, center_y), radius)
            
            # 右側に明るい部分を描画
            # phaseが増えるほど明るい部分が増える
            illumination = phase * 2  # 0から1へ
            
            if illumination < 0.5:
                # 三日月〜上弦前（細い明るい弧）
                ellipse_width = int(radius * 2 * illumination)
                if ellipse_width > 0:
                    # 右側だけ明るくする
                    for i in range(radius):
                        x_pos = center_x + i
                        # 楕円の方程式で高さを計算
                        if illumination > 0:
                            height = int(radius * math.sqrt(1 - (i / radius) ** 2))
                            # 楕円の幅に応じた明るい部分の幅
                            bright_width = int(ellipse_width * math.sqrt(1 - (i / radius) ** 2) / radius)
                            if bright_width > 0:
                                pygame.draw.line(moon_surface, moon_color,
                                               (x_pos, center_y - height),
                                               (x_pos, center_y + height))
            else:
                # 上弦〜満月前（ほぼ全体が明るい）
                pygame.draw.circle(moon_surface, moon_color, (center_x, center_y), radius)
                # 左側に影を描画
                shadow_width = int(radius * 2 * (1 - illumination))
                if shadow_width > 0:
                    for i in range(radius):
                        x_pos = center_x - i
                        height = int(radius * math.sqrt(1 - (i / radius) ** 2))
                        shadow_x_width = int(shadow_width * math.sqrt(1 - (i / radius) ** 2) / radius)
                        if shadow_x_width > 0:
                            pygame.draw.line(moon_surface, shadow_color,
                                           (x_pos, center_y - height),
                                           (x_pos, center_y + height))
                             
        elif phase < 0.53:  # 満月（月齢14.75-15.5）
            # 全体を明るく
            pygame.draw.circle(moon_surface, moon_color, (center_x, center_y), radius)
            # ハイライトを追加
            highlight_radius = radius // 4
            highlight_x = center_x - radius // 3
            highlight_y = center_y - radius // 3
            for i in range(highlight_radius):
                alpha = 1 - (i / highlight_radius)
                color = (
                    min(255, int(255 + 20 * alpha)),
                    min(255, int(255 + 20 * alpha)),
                    min(255, int(220 + 35 * alpha))
                )
                pygame.draw.circle(moon_surface, color,
                                 (highlight_x, highlight_y),
                                 highlight_radius - i)
                             
        else:  # 満月から新月へ（月齢15.5-29.53）
            # 左側が暗く、右側が明るい
            shadow_ratio = (phase - 0.5) * 2  # 0から1へ
            
            if shadow_ratio < 0.5:  # 寝待月〜下弦（月齢15.5-22）
                # 基本は明るく、左側に影を増やす
                pygame.draw.circle(moon_surface, moon_color, (center_x, center_y), radius)
                # 左側に影を描画
                shadow_width = int(radius * 2 * shadow_ratio)
                if shadow_width > 0:
                    for i in range(radius):
                        x_pos = center_x - i
                        height = int(radius * math.sqrt(1 - (i / radius) ** 2))
                        shadow_x_width = int(shadow_width * math.sqrt(1 - (i / radius) ** 2) / radius)
                        if shadow_x_width > 0:
                            pygame.draw.line(moon_surface, shadow_color,
                                           (x_pos, center_y - height),
                                           (x_pos, center_y + height))
                    
            else:  # 下弦から新月へ（月齢22-29.53）
                # 全体を暗くして、右側だけ明るい三日月
                pygame.draw.circle(moon_surface, shadow_color, (center_x, center_y), radius)
                
                # 右側に明るい部分を描画
                light_ratio = 1 - shadow_ratio  # 1から0へ
                bright_width = int(radius * 2 * light_ratio)
                if bright_width > 0:
                    for i in range(radius):
                        x_pos = center_x + i
                        height = int(radius * math.sqrt(1 - (i / radius) ** 2))
                        bright_x_width = int(bright_width * math.sqrt(1 - (i / radius) ** 2) / radius)
                        if bright_x_width > 0:
                            pygame.draw.line(moon_surface, moon_color,
                                           (x_pos, center_y - height),
                                           (x_pos, center_y + height))
        
        # 輪郭線を描画（アンチエイリアシング効果）
        pygame.draw.circle(moon_surface, outline_color, (center_x, center_y), radius, 1)
        
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