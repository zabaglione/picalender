#!/usr/bin/env python3
"""
TASK-204: 背景画像レンダラー実装

PiCalendar表示システムの背景画像表示機能。
wallpapers/ディレクトリから画像を選択し、fit/scaleモードで1024×600解像度に描画する。
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pygame

from ..assets.asset_manager import AssetManager


class SettingKeys:
    """YAML設定キーの定数"""
    BACKGROUND_DIR = 'background.dir'
    BACKGROUND_MODE = 'background.mode'
    BACKGROUND_RESCAN_SEC = 'background.rescan_sec'
    BACKGROUND_FALLBACK_COLOR = 'background.fallback_color'
    BACKGROUND_SUPPORTED_FORMATS = 'background.supported_formats'
    UI_SCREEN_WIDTH = 'ui.screen_width'
    UI_SCREEN_HEIGHT = 'ui.screen_height'


class DefaultSettings:
    """デフォルト設定値"""
    WALLPAPER_DIR = './wallpapers'
    SCALE_MODE = 'fit'
    RESCAN_INTERVAL = 300
    FALLBACK_COLOR = [0, 0, 0]
    SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'gif']
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 600


class ValidationRanges:
    """バリデーション範囲"""
    MIN_RESCAN_INTERVAL = 30
    MAX_RESCAN_INTERVAL = 3600
    MIN_SCREEN_SIZE = 320
    MAX_SCREEN_SIZE = 4096
    VALID_SCALE_MODES = ['fit', 'scale']


class BackgroundImageRenderer:
    """背景画像レンダラークラス"""
    
    def __init__(self, asset_manager: AssetManager, settings: Dict[str, Any]):
        """
        BackgroundImageRenderer初期化
        
        Args:
            asset_manager: AssetManagerインスタンス
            settings: 設定辞書
        """
        self.logger = logging.getLogger(__name__)
        
        # 基本属性
        self.asset_manager = asset_manager
        self.settings = settings
        
        # 設定読み込み
        self._load_settings()
        
        # 内部状態
        self.current_image_path = None
        self.cached_surface = None
        self.last_scan_time = 0
        self.available_images = []
        
        # 初期化完了
        self.logger.info("BackgroundImageRenderer initialized")
    
    def _load_settings(self):
        """設定値読み込み"""
        background_config = self.settings.get('background', {})
        ui_config = self.settings.get('ui', {})
        
        # 基本設定 - バリデーション付き
        self.wallpaper_directory = self._validate_directory(
            background_config.get('dir', DefaultSettings.WALLPAPER_DIR)
        )
        self.scale_mode = self._validate_scale_mode(
            background_config.get('mode', DefaultSettings.SCALE_MODE)
        )
        self.rescan_interval = self._validate_rescan_interval(
            background_config.get('rescan_sec', DefaultSettings.RESCAN_INTERVAL)
        )
        self.fallback_color = self._validate_color(
            background_config.get('fallback_color', DefaultSettings.FALLBACK_COLOR)
        )
        
        # 対応形式
        self.supported_formats = background_config.get(
            'supported_formats', DefaultSettings.SUPPORTED_FORMATS
        )
        
        # 画面サイズ
        self.screen_width = self._validate_screen_size(
            ui_config.get('screen_width', DefaultSettings.SCREEN_WIDTH)
        )
        self.screen_height = self._validate_screen_size(
            ui_config.get('screen_height', DefaultSettings.SCREEN_HEIGHT)
        )
        
        self.logger.debug(f"Settings loaded - Dir: {self.wallpaper_directory}, "
                         f"Mode: {self.scale_mode}, Interval: {self.rescan_interval}")
    
    def _validate_directory(self, path: str) -> str:
        """ディレクトリパスのバリデーション"""
        if not isinstance(path, str) or not path:
            self.logger.warning(f"Invalid directory path: {path}, using default")
            return DefaultSettings.WALLPAPER_DIR
        return path
    
    def _validate_scale_mode(self, mode: str) -> str:
        """スケールモードのバリデーション"""
        if mode not in ValidationRanges.VALID_SCALE_MODES:
            self.logger.warning(f"Invalid scale mode: {mode}, using default")
            return DefaultSettings.SCALE_MODE
        return mode
    
    def _validate_rescan_interval(self, interval: int) -> int:
        """再スキャン間隔のバリデーション"""
        if not isinstance(interval, int) or not (
            ValidationRanges.MIN_RESCAN_INTERVAL <= interval <= ValidationRanges.MAX_RESCAN_INTERVAL
        ):
            self.logger.warning(f"Invalid rescan interval: {interval}, using default")
            return DefaultSettings.RESCAN_INTERVAL
        return interval
    
    def _validate_color(self, color: List[int]) -> List[int]:
        """色設定のバリデーション"""
        if not isinstance(color, list) or len(color) != 3:
            self.logger.warning(f"Invalid fallback color: {color}, using default")
            return DefaultSettings.FALLBACK_COLOR
        
        # RGB値の範囲チェック
        validated_color = []
        for component in color:
            if isinstance(component, int) and 0 <= component <= 255:
                validated_color.append(component)
            else:
                self.logger.warning(f"Invalid color component: {component}, using 0")
                validated_color.append(0)
        
        return validated_color
    
    def _validate_screen_size(self, size: int) -> int:
        """画面サイズのバリデーション"""
        if not isinstance(size, int) or not (
            ValidationRanges.MIN_SCREEN_SIZE <= size <= ValidationRanges.MAX_SCREEN_SIZE
        ):
            self.logger.warning(f"Invalid screen size: {size}, using default")
            return DefaultSettings.SCREEN_WIDTH if size == self.screen_width else DefaultSettings.SCREEN_HEIGHT
        return size
    
    def _scan_wallpaper_directory(self) -> List[str]:
        """
        壁紙ディレクトリをスキャンして対応形式の画像ファイルを取得
        
        Returns:
            対応形式の画像ファイルパスリスト（アルファベット順）
        """
        if not os.path.exists(self.wallpaper_directory):
            self.logger.warning(f"Wallpaper directory not found: {self.wallpaper_directory}")
            return []
        
        try:
            image_files = []
            
            for file in os.listdir(self.wallpaper_directory):
                if self._is_supported_format(file):
                    full_path = os.path.join(self.wallpaper_directory, file)
                    if os.path.isfile(full_path):
                        image_files.append(full_path)
            
            # アルファベット順でソート
            image_files.sort()
            
            # スキャン時刻更新
            self.last_scan_time = time.time()
            
            self.logger.info(f"Found {len(image_files)} supported images")
            return image_files
            
        except Exception as e:
            self.logger.error(f"Error scanning wallpaper directory: {e}")
            return []
    
    def _is_supported_format(self, filename: str) -> bool:
        """
        ファイルが対応形式かどうか判定
        
        Args:
            filename: ファイル名
            
        Returns:
            対応形式の場合True
        """
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in [fmt.lower() for fmt in self.supported_formats]
    
    def _select_best_image(self) -> Optional[str]:
        """
        最適な画像ファイルを選択
        
        Returns:
            選択された画像ファイルパス（なしの場合None）
        """
        available_images = self._scan_wallpaper_directory()
        
        for image_path in available_images:
            try:
                # 実際に画像として読み込み可能かテスト
                test_surface = pygame.image.load(image_path)
                if test_surface:
                    self.logger.info(f"Selected image: {os.path.basename(image_path)}")
                    return image_path
            except Exception as e:
                self.logger.warning(f"Failed to load image {image_path}: {e}")
                continue
        
        self.logger.warning("No valid images found")
        return None
    
    def _load_and_scale_image(self, image_path: str) -> Optional[pygame.Surface]:
        """
        画像を読み込んでスケーリング
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            スケール済みSurface（失敗時None）
        """
        try:
            self.logger.debug(f"Loading image: {os.path.basename(image_path)}")
            
            # 画像読み込み前検証
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return None
            
            # 画像読み込み
            original_surface = pygame.image.load(image_path)
            original_size = original_surface.get_size()
            
            if original_size[0] <= 0 or original_size[1] <= 0:
                self.logger.error(f"Invalid image dimensions: {original_size}")
                return None
            
            # スケーリング処理
            return self._prepare_scaled_surface(original_surface, original_size)
            
        except pygame.error as e:
            self.logger.error(f"Pygame error loading image {image_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading image {image_path}: {e}")
            return None
    
    def _prepare_scaled_surface(self, original_surface: pygame.Surface, 
                               original_size: Tuple[int, int]) -> pygame.Surface:
        """
        画像サーフェスをスケーリングして最終描画用サーフェスを作成
        
        Args:
            original_surface: 元画像サーフェス
            original_size: 元画像サイズ
            
        Returns:
            スケール済み最終サーフェス
        """
        target_size = (self.screen_width, self.screen_height)
        
        # スケールモードに応じて座標・サイズ計算
        if self.scale_mode == 'fit':
            dimensions = self._calculate_fit_dimensions(original_size, target_size)
        else:  # scale
            dimensions = self._calculate_scale_dimensions(original_size, target_size)
        
        # スケーリング実行
        scaled_surface = pygame.transform.scale(original_surface, 
                                               (dimensions['width'], dimensions['height']))
        
        # 最終描画用サーフェス作成（フォールバック色で塗りつぶし）
        final_surface = pygame.Surface(target_size)
        final_surface.fill(self.fallback_color)
        
        # 中央配置で合成
        final_surface.blit(scaled_surface, (dimensions['x'], dimensions['y']))
        
        self.logger.debug(f"Image scaled - Mode: {self.scale_mode}, "
                         f"Dimensions: {dimensions}")
        
        return final_surface
    
    def _calculate_fit_dimensions(self, original_size: Tuple[int, int], 
                                 target_size: Tuple[int, int]) -> Dict[str, int]:
        """
        fitモードでの表示座標・サイズ計算
        
        Args:
            original_size: 元画像サイズ (width, height)
            target_size: ターゲットサイズ (width, height)
            
        Returns:
            表示座標とサイズの辞書
        """
        orig_w, orig_h = original_size
        target_w, target_h = target_size
        
        # アスペクト比計算
        aspect_ratio = orig_w / orig_h
        target_aspect = target_w / target_h
        
        if aspect_ratio > target_aspect:
            # 横長: 幅に合わせる
            scaled_w = target_w
            scaled_h = int(target_w / aspect_ratio)
            x = 0
            y = (target_h - scaled_h) // 2
        else:
            # 縦長: 高さに合わせる
            scaled_h = target_h
            scaled_w = int(target_h * aspect_ratio)
            x = (target_w - scaled_w) // 2
            y = 0
        
        return {
            'x': x,
            'y': y,
            'width': scaled_w,
            'height': scaled_h
        }
    
    def _calculate_scale_dimensions(self, original_size: Tuple[int, int],
                                   target_size: Tuple[int, int]) -> Dict[str, int]:
        """
        scaleモードでの表示座標・サイズ計算
        
        Args:
            original_size: 元画像サイズ (width, height)
            target_size: ターゲットサイズ (width, height)
            
        Returns:
            表示座標とサイズの辞書
        """
        target_w, target_h = target_size
        
        return {
            'x': 0,
            'y': 0,
            'width': target_w,
            'height': target_h
        }
    
    def _should_rescan(self) -> bool:
        """
        再スキャンが必要かどうか判定
        
        Returns:
            再スキャンが必要な場合True
        """
        if self.last_scan_time == 0:  # 初回は常に実行
            return True
        current_time = time.time()
        return (current_time - self.last_scan_time) >= self.rescan_interval
    
    def update(self):
        """定期更新処理"""
        if self._should_rescan() or self.current_image_path is None:
            self.logger.debug("Executing periodic rescan")
            
            # 再スキャン実行
            new_image_path = self._select_best_image()
            
            # 画像が変更された場合のみ再読み込み
            if new_image_path != self.current_image_path:
                self.current_image_path = new_image_path
                self.cached_surface = None  # キャッシュクリア
                
                if self.current_image_path:
                    self.cached_surface = self._load_and_scale_image(self.current_image_path)
            
            # updateでの明示的な時刻更新（_select_best_image内でも更新される）
            if self.last_scan_time == 0:
                self.last_scan_time = time.time()
    
    def render(self, surface: pygame.Surface):
        """
        背景描画
        
        Args:
            surface: 描画先Surface
        """
        if self.cached_surface:
            # 背景画像描画
            surface.blit(self.cached_surface, (0, 0))
        else:
            # 単色背景描画
            surface.fill(self.fallback_color)
    
    def get_current_image_path(self) -> Optional[str]:
        """
        現在の画像パス取得
        
        Returns:
            現在の画像ファイルパス（なしの場合None）
        """
        return self.current_image_path
    
    def set_wallpaper_directory(self, path: str):
        """
        壁紙ディレクトリ変更
        
        Args:
            path: 新しいディレクトリパス
        """
        self.wallpaper_directory = path
        self.force_rescan()
    
    def set_scale_mode(self, mode: str):
        """
        スケールモード変更
        
        Args:
            mode: 'fit' または 'scale'
        """
        if mode in ['fit', 'scale']:
            old_mode = self.scale_mode
            self.scale_mode = mode
            
            if old_mode != mode and self.current_image_path:
                # モード変更時は再描画が必要
                self.cached_surface = self._load_and_scale_image(self.current_image_path)
                self.logger.info(f"Scale mode changed: {old_mode} -> {mode}")
    
    def force_rescan(self):
        """強制再スキャン実行"""
        self.last_scan_time = 0  # 強制的に期限切れにする
        self.update()
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.cached_surface = None
        self.current_image_path = None
        self.available_images = []
        self.logger.info("BackgroundImageRenderer cleanup completed")