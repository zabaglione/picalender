#!/usr/bin/env python3
"""
簡易壁紙レンダラー
画像ファイルの自動切り替え対応
"""

import pygame
import time
import random
from pathlib import Path
import logging


class SimpleWallpaperRenderer:
    """簡易壁紙レンダラー"""
    
    def __init__(self, settings):
        """初期化"""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 壁紙ディレクトリ
        self.wallpaper_dir = Path("wallpapers")
        if not self.wallpaper_dir.exists():
            self.wallpaper_dir.mkdir(exist_ok=True)
            self.logger.info(f"Created wallpaper directory: {self.wallpaper_dir}")
        
        # 画面サイズ
        screen_settings = self.settings.get('screen', {})
        self.screen_width = screen_settings.get('width', 1024)
        self.screen_height = screen_settings.get('height', 600)
        
        # 壁紙設定
        wallpaper_settings = self.settings.get('wallpaper', {})
        self.rotation_interval = wallpaper_settings.get('rotation_seconds', 300)  # デフォルト5分
        self.fit_mode = wallpaper_settings.get('fit_mode', 'fit')  # fit, fill, stretch
        
        # 壁紙リストと現在の壁紙
        self.wallpapers = []
        self.current_wallpaper = None
        self.current_surface = None
        self.current_index = 0
        self.last_rotation = 0
        self.last_scan = 0
        self.scan_interval = 60  # 1分ごとに新しい壁紙をスキャン
        
        # デフォルト背景（壁紙がない場合）
        self.default_background = None
        self._create_default_background()
        
        # 初回スキャン
        self._scan_wallpapers()
        self._load_current_wallpaper()
    
    def _create_default_background(self):
        """デフォルトのグラデーション背景を作成"""
        self.default_background = pygame.Surface((self.screen_width, self.screen_height))
        
        # グラデーション描画
        for y in range(self.screen_height):
            ratio = y / self.screen_height
            color = (
                int(20 + (50 - 20) * ratio),
                int(30 + (80 - 30) * ratio),
                int(60 + (120 - 60) * ratio)
            )
            pygame.draw.line(self.default_background, color, 
                           (0, y), (self.screen_width, y))
    
    def _scan_wallpapers(self):
        """壁紙ディレクトリをスキャン"""
        # サポートする画像形式
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        # 壁紙ファイルを検索
        new_wallpapers = []
        for format in supported_formats:
            new_wallpapers.extend(self.wallpaper_dir.glob(f'*{format}'))
            new_wallpapers.extend(self.wallpaper_dir.glob(f'*{format.upper()}'))
        
        # ソートして保存
        new_wallpapers = sorted(new_wallpapers)
        
        if new_wallpapers != self.wallpapers:
            self.wallpapers = new_wallpapers
            self.logger.info(f"Found {len(self.wallpapers)} wallpaper(s)")
            
            # 壁紙が追加/削除された場合
            if self.wallpapers and not self.current_wallpaper:
                self.current_index = 0
                self._load_current_wallpaper()
    
    def _load_current_wallpaper(self):
        """現在の壁紙を読み込み"""
        if not self.wallpapers:
            self.current_surface = None
            self.current_wallpaper = None
            return
        
        # インデックスが範囲外の場合は修正
        if self.current_index >= len(self.wallpapers):
            self.current_index = 0
        
        wallpaper_path = self.wallpapers[self.current_index]
        
        try:
            # 画像を読み込み
            original = pygame.image.load(str(wallpaper_path))
            
            # フィットモードに応じてリサイズ
            if self.fit_mode == 'fit':
                # アスペクト比を保持して画面に収める
                self.current_surface = self._fit_image(original)
            elif self.fit_mode == 'fill':
                # アスペクト比を保持して画面を埋める
                self.current_surface = self._fill_image(original)
            else:  # stretch
                # 画面サイズに引き伸ばす
                self.current_surface = pygame.transform.smoothscale(
                    original, (self.screen_width, self.screen_height))
            
            self.current_wallpaper = wallpaper_path
            self.logger.info(f"Loaded wallpaper: {wallpaper_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load wallpaper {wallpaper_path}: {e}")
            self.current_surface = None
            self.current_wallpaper = None
    
    def _fit_image(self, image):
        """画像をアスペクト比を保持して画面に収める"""
        img_width, img_height = image.get_size()
        
        # スケール比を計算
        scale_x = self.screen_width / img_width
        scale_y = self.screen_height / img_height
        scale = min(scale_x, scale_y)
        
        # 新しいサイズ
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # リサイズ
        scaled = pygame.transform.smoothscale(image, (new_width, new_height))
        
        # 中央に配置するためのサーフェス
        result = pygame.Surface((self.screen_width, self.screen_height))
        result.fill((0, 0, 0))  # 黒で塗りつぶし
        
        # 中央に配置
        x = (self.screen_width - new_width) // 2
        y = (self.screen_height - new_height) // 2
        result.blit(scaled, (x, y))
        
        return result
    
    def _fill_image(self, image):
        """画像をアスペクト比を保持して画面を埋める"""
        img_width, img_height = image.get_size()
        
        # スケール比を計算（大きい方）
        scale_x = self.screen_width / img_width
        scale_y = self.screen_height / img_height
        scale = max(scale_x, scale_y)
        
        # 新しいサイズ
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # リサイズ
        scaled = pygame.transform.smoothscale(image, (new_width, new_height))
        
        # 中央部分を切り取る
        x = (new_width - self.screen_width) // 2
        y = (new_height - self.screen_height) // 2
        
        result = pygame.Surface((self.screen_width, self.screen_height))
        result.blit(scaled, (-x, -y))
        
        return result
    
    def _rotate_wallpaper(self):
        """次の壁紙に切り替え"""
        if len(self.wallpapers) <= 1:
            return
        
        self.current_index = (self.current_index + 1) % len(self.wallpapers)
        self._load_current_wallpaper()
        self.last_rotation = time.time()
    
    def render(self, screen):
        """壁紙を描画"""
        current_time = time.time()
        
        # 定期的に新しい壁紙をスキャン
        if current_time - self.last_scan > self.scan_interval:
            self._scan_wallpapers()
            self.last_scan = current_time
        
        # 自動切り替え
        if self.rotation_interval > 0 and len(self.wallpapers) > 1:
            if current_time - self.last_rotation > self.rotation_interval:
                self._rotate_wallpaper()
        
        # 背景描画
        if self.current_surface:
            screen.blit(self.current_surface, (0, 0))
        elif self.default_background:
            screen.blit(self.default_background, (0, 0))
        else:
            # フォールバック：単色背景
            screen.fill((30, 40, 60))