"""
背景画像表示コンポーネント

壁紙画像を読み込み、スケーリングして背景として表示するレンダラー。
複数のスケーリングモードに対応。
"""

import os
import logging
from typing import Optional, Tuple, List, Dict, Any
import pygame

from src.rendering.renderable import Renderable

logger = logging.getLogger(__name__)


class BackgroundRenderer(Renderable):
    """
    背景画像レンダラー
    
    Attributes:
        SUPPORTED_FORMATS: サポートする画像形式
        DEFAULT_BG_COLOR: デフォルト背景色
    """
    
    SUPPORTED_FORMATS: List[str] = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    DEFAULT_BG_COLOR: Tuple[int, int, int] = (0, 0, 0)
    
    def __init__(self, asset_manager: Any, config: Any) -> None:
        """
        初期化
        
        Args:
            asset_manager: アセット管理オブジェクト
            config: 設定管理オブジェクト
        """
        self.asset_manager = asset_manager
        self.config = config
        
        # 設定値の取得
        self.wallpaper_dir: str = config.get('background.dir', './wallpapers')
        self.scale_mode: str = config.get('background.mode', 'fit')
        self.rescan_interval: float = config.get('background.rescan_sec', 300)
        self.default_color: Tuple[int, int, int] = config.get('background.default_color', self.DEFAULT_BG_COLOR)
        self.screen_width: int = config.get('screen.width', 1024)
        self.screen_height: int = config.get('screen.height', 600)
        
        # 状態管理
        self.visible: bool = True
        self._dirty: bool = True
        self.smooth_scaling: bool = True
        self.current_image: Optional[pygame.Surface] = None
        self._scaled_image: Optional[pygame.Surface] = None
        self._wallpaper_list: List[str] = []
        self._current_index: int = 0
        self._last_scan_time: float = 0
        self._elapsed_time: float = 0
        self._position: Tuple[int, int] = (0, 0)
        self._dirty_rect: Optional[pygame.Rect] = None
        
        # 初回スキャン
        self._wallpaper_list = self.scan_wallpapers()
        if self._wallpaper_list:
            self.load_image(self._wallpaper_list[0])
    
    def scan_wallpapers(self) -> List[str]:
        """
        壁紙ディレクトリをスキャン
        
        Returns:
            画像ファイルのリスト
        """
        wallpapers = []
        
        if not os.path.exists(self.wallpaper_dir):
            logger.warning(f"Wallpaper directory not found: {self.wallpaper_dir}")
            return wallpapers
        
        try:
            for filename in os.listdir(self.wallpaper_dir):
                if any(filename.lower().endswith(fmt) for fmt in self.SUPPORTED_FORMATS):
                    wallpapers.append(filename)
            
            wallpapers.sort()  # アルファベット順
            logger.info(f"Found {len(wallpapers)} wallpapers")
            
        except Exception as e:
            logger.error(f"Error scanning wallpapers: {e}")
        
        return wallpapers
    
    def load_image(self, filename: str) -> bool:
        """
        画像を読み込み
        
        Args:
            filename: 画像ファイル名
            
        Returns:
            成功した場合True
        """
        try:
            filepath = os.path.join(self.wallpaper_dir, filename)
            self.current_image = self.asset_manager.load_image(filepath, alpha=False)
            
            if self.current_image:
                self._scaled_image = None  # スケーリングをリセット
                self._dirty = True
                logger.info(f"Loaded wallpaper: {filename}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to load wallpaper {filename}: {e}")
        
        return False
    
    def calculate_fit_scaling(self, img_size: Tuple[int, int], 
                             screen_size: Tuple[int, int]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        fitモードのスケーリング計算
        
        Args:
            img_size: 画像サイズ (幅, 高さ)
            screen_size: 画面サイズ (幅, 高さ)
            
        Returns:
            (スケール後サイズ, 表示位置)
        """
        img_w, img_h = img_size
        screen_w, screen_h = screen_size
        
        # アスペクト比を計算
        img_aspect = img_w / img_h
        screen_aspect = screen_w / screen_h
        
        if img_aspect > screen_aspect:
            # 画像の方が横長 -> 幅に合わせる
            new_w = screen_w
            new_h = int(screen_w / img_aspect)
            x = 0
            y = (screen_h - new_h) // 2
        else:
            # 画像の方が縦長 -> 高さに合わせる
            new_h = screen_h
            new_w = int(screen_h * img_aspect)
            x = (screen_w - new_w) // 2
            y = 0
        
        return ((new_w, new_h), (x, y))
    
    def calculate_scale_scaling(self, img_size: Tuple[int, int],
                               screen_size: Tuple[int, int]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        scaleモードのスケーリング計算
        
        Args:
            img_size: 画像サイズ (幅, 高さ)
            screen_size: 画面サイズ (幅, 高さ)
            
        Returns:
            (スケール後サイズ, 表示位置)
        """
        return (screen_size, (0, 0))
    
    def calculate_center_scaling(self, img_size: Tuple[int, int],
                                screen_size: Tuple[int, int]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        centerモードのスケーリング計算
        
        Args:
            img_size: 画像サイズ (幅, 高さ)
            screen_size: 画面サイズ (幅, 高さ)
            
        Returns:
            (元のサイズ, 中央表示位置)
        """
        img_w, img_h = img_size
        screen_w, screen_h = screen_size
        
        x = (screen_w - img_w) // 2
        y = (screen_h - img_h) // 2
        
        return (img_size, (x, y))
    
    def _scale_image(self) -> None:
        """現在の画像をスケーリング"""
        if not self.current_image:
            return
        
        img_size = self.current_image.get_size()
        screen_size = (self.screen_width, self.screen_height)
        
        # スケーリングモードに応じて計算
        if self.scale_mode == 'fit':
            new_size, self._position = self.calculate_fit_scaling(img_size, screen_size)
        elif self.scale_mode == 'scale':
            new_size, self._position = self.calculate_scale_scaling(img_size, screen_size)
        elif self.scale_mode == 'center':
            new_size, self._position = self.calculate_center_scaling(img_size, screen_size)
        else:
            # デフォルト: fit
            new_size, self._position = self.calculate_fit_scaling(img_size, screen_size)
        
        # スケーリング実行
        if new_size != img_size:
            if self.smooth_scaling:
                self._scaled_image = pygame.transform.smoothscale(self.current_image, new_size)
            else:
                self._scaled_image = pygame.transform.scale(self.current_image, new_size)
        else:
            self._scaled_image = self.current_image
    
    def _should_rescan(self) -> bool:
        """再スキャンが必要かどうか"""
        return self.rescan_interval > 0 and self._elapsed_time >= self.rescan_interval
    
    def update(self, dt: float) -> None:
        """
        更新処理
        
        Args:
            dt: 前フレームからの経過時間（秒）
        """
        if not self.visible:
            return
        
        # 経過時間を更新
        self._elapsed_time += dt
        
        # 再スキャンチェック
        if self._should_rescan():
            self._elapsed_time = 0
            new_list = self.scan_wallpapers()
            
            # リストが変わった場合
            if new_list != self._wallpaper_list:
                self._wallpaper_list = new_list
                if self._wallpaper_list and self._current_index >= len(self._wallpaper_list):
                    self._current_index = 0
                    self.load_image(self._wallpaper_list[0])
    
    def render(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """
        描画処理
        
        Args:
            surface: 描画対象のサーフェス
            
        Returns:
            更新された領域のリスト
        """
        if not self.visible:
            return []
        
        if not self._dirty:
            return []
        
        dirty_rects = []
        
        try:
            # 背景色で塗りつぶし
            surface.fill(self.default_color)
            
            # 画像がある場合
            if self.current_image:
                # スケーリングが必要な場合
                if self._scaled_image is None:
                    self._scale_image()
                
                # 画像を描画
                if self._scaled_image and isinstance(surface, pygame.Surface):
                    surface.blit(self._scaled_image, self._position)
            
            # 全画面をdirtyとして返す
            rect = pygame.Rect(0, 0, self.screen_width, self.screen_height)
            dirty_rects.append(rect)
            self._dirty_rect = rect
            
            # dirtyフラグをクリア
            self._dirty = False
            
        except Exception as e:
            logger.error(f"Error rendering background: {e}")
            self._dirty = False
        
        return dirty_rects
    
    def is_dirty(self) -> bool:
        """
        更新が必要かどうか
        
        Returns:
            更新が必要な場合True
        """
        return self._dirty
    
    def get_dirty_rect(self) -> Optional[pygame.Rect]:
        """
        更新領域を取得
        
        Returns:
            更新領域のRect、なければNone
        """
        if self._dirty_rect:
            return self._dirty_rect
        
        # 全画面
        return pygame.Rect(0, 0, self.screen_width, self.screen_height)
    
    def get_bounds(self) -> pygame.Rect:
        """
        境界矩形を取得
        
        Returns:
            オブジェクトの境界矩形
        """
        return pygame.Rect(0, 0, self.screen_width, self.screen_height)
    
    def set_visible(self, visible: bool) -> None:
        """
        表示/非表示を設定
        
        Args:
            visible: 表示する場合True
        """
        if self.visible != visible:
            self.visible = visible
            self._dirty = True
    
    def set_scale_mode(self, mode: str) -> None:
        """
        スケールモードを設定
        
        Args:
            mode: 'fit', 'scale', 'center'のいずれか
        """
        if self.scale_mode != mode:
            self.scale_mode = mode
            self._scaled_image = None  # 再スケーリングが必要
            self._dirty = True
    
    def set_smooth_scaling(self, smooth: bool) -> None:
        """
        スムーズスケーリングの有効/無効
        
        Args:
            smooth: スムーズスケーリングを使用する場合True
        """
        if self.smooth_scaling != smooth:
            self.smooth_scaling = smooth
            self._scaled_image = None  # 再スケーリングが必要
            self._dirty = True
    
    def next_wallpaper(self) -> None:
        """次の壁紙に切り替え"""
        if not self._wallpaper_list:
            return
        
        self._current_index = (self._current_index + 1) % len(self._wallpaper_list)
        self.load_image(self._wallpaper_list[self._current_index])
    
    def previous_wallpaper(self) -> None:
        """前の壁紙に切り替え"""
        if not self._wallpaper_list:
            return
        
        self._current_index = (self._current_index - 1) % len(self._wallpaper_list)
        self.load_image(self._wallpaper_list[self._current_index])