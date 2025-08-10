"""
アセット管理システム

TASK-103: アセット管理の統合クラス
- フォント、画像、スプライトの統合管理
- キャッシュ管理
- 動的リロード
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
import pygame
from .loaders.font_loader import FontLoader
from .loaders.image_loader import ImageLoader, ScaleMode
from .loaders.sprite_loader import SpriteLoader
from .cache.lru_cache import LRUCache
from .monitor.file_monitor import FileMonitor

logger = logging.getLogger(__name__)


class AssetManager:
    """アセット管理メインクラス"""
    
    def __init__(self, memory_limit: int = 50 * 1024 * 1024):
        """
        初期化
        
        Args:
            memory_limit: メモリ使用量制限（バイト）
        """
        self.memory_limit = memory_limit
        
        # 各種ローダーを初期化
        self.font_loader = FontLoader(cache_size=50)
        self.image_loader = ImageLoader(cache_size=100)
        self.sprite_loader = SpriteLoader(cache_size=50)
        
        # ファイル監視システム
        self.file_monitor = FileMonitor(poll_interval=1.0)
        
        # アセット依存関係管理
        self.asset_dependencies: Dict[str, List[str]] = {}
        self.reload_callbacks: Dict[str, List[Callable]] = {}
        
        # 統計情報
        self.load_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        logger.info(f"AssetManager initialized with {memory_limit // 1024 // 1024}MB memory limit")
    
    def load_font(self, font_path: Optional[str], size: int) -> pygame.font.Font:
        """
        フォントを読み込み
        
        Args:
            font_path: フォントパス（Noneでシステムデフォルト）
            size: フォントサイズ
            
        Returns:
            pygame.font.Fontオブジェクト
        """
        self.load_count += 1
        
        # キャッシュ統計更新
        cache_stats = self.font_loader.get_cache_stats()
        old_hits = cache_stats.get('hits', 0)
        
        # フォント読み込み
        font = self.font_loader.load_font(font_path, size)
        
        # キャッシュヒット統計更新
        new_cache_stats = self.font_loader.get_cache_stats()
        new_hits = new_cache_stats.get('hits', 0)
        if new_hits > old_hits:
            self.cache_hit_count += 1
        else:
            self.cache_miss_count += 1
        
        # ファイル監視追加（パスが指定されている場合）
        if font_path and os.path.exists(font_path):
            self._add_file_watch(font_path, 'font')
        
        return font
    
    def load_image(self, image_path: str, target_size: Optional[Tuple[int, int]] = None,
                  scale_mode: ScaleMode = ScaleMode.FIT) -> pygame.Surface:
        """
        画像を読み込み
        
        Args:
            image_path: 画像パス
            target_size: 目標サイズ
            scale_mode: スケーリングモード
            
        Returns:
            pygame.Surfaceオブジェクト
        """
        self.load_count += 1
        
        # キャッシュ統計更新
        cache_stats = self.image_loader.get_cache_stats()
        old_hits = cache_stats.get('hits', 0)
        
        # 画像読み込み
        surface = self.image_loader.load_image(image_path, target_size, scale_mode)
        
        # キャッシュヒット統計更新
        new_cache_stats = self.image_loader.get_cache_stats()
        new_hits = new_cache_stats.get('hits', 0)
        if new_hits > old_hits:
            self.cache_hit_count += 1
        else:
            self.cache_miss_count += 1
        
        # ファイル監視追加
        if os.path.exists(image_path):
            self._add_file_watch(image_path, 'image')
        
        return surface
    
    def load_sprite_sheet(self, sprite_path: str, frame_width: int, frame_height: int,
                         frame_count: int) -> List[pygame.Surface]:
        """
        スプライトシートを読み込み
        
        Args:
            sprite_path: スプライトシートパス
            frame_width: フレーム幅
            frame_height: フレーム高さ
            frame_count: フレーム数
            
        Returns:
            フレームサーフェスのリスト
        """
        self.load_count += 1
        
        # キャッシュ統計更新
        cache_stats = self.sprite_loader.get_cache_stats()
        old_hits = cache_stats.get('hits', 0)
        
        # スプライト読み込み
        frames = self.sprite_loader.load_sprite_sheet(
            sprite_path, frame_width, frame_height, frame_count
        )
        
        # キャッシュヒット統計更新
        new_cache_stats = self.sprite_loader.get_cache_stats()
        new_hits = new_cache_stats.get('hits', 0)
        if new_hits > old_hits:
            self.cache_hit_count += 1
        else:
            self.cache_miss_count += 1
        
        # ファイル監視追加
        if os.path.exists(sprite_path):
            self._add_file_watch(sprite_path, 'sprite')
        
        return frames
    
    def load_animation(self, sprite_path: str, frame_def_path: str) -> Dict[str, Any]:
        """
        アニメーションを読み込み
        
        Args:
            sprite_path: スプライトシートパス
            frame_def_path: フレーム定義パス
            
        Returns:
            アニメーション情報
        """
        animation = self.sprite_loader.load_animation(sprite_path, frame_def_path)
        
        # 両ファイルを監視
        if os.path.exists(sprite_path):
            self._add_file_watch(sprite_path, 'sprite')
        if os.path.exists(frame_def_path):
            self._add_file_watch(frame_def_path, 'definition')
        
        # 依存関係を記録
        self.asset_dependencies[sprite_path] = [frame_def_path]
        
        return animation
    
    def set_memory_limit(self, limit: int) -> None:
        """
        メモリ使用量制限を設定
        
        Args:
            limit: 制限値（バイト）
        """
        self.memory_limit = limit
        logger.info(f"Memory limit set to {limit // 1024 // 1024}MB")
        
        # 制限を超えている場合はキャッシュクリア
        current_usage = self.get_memory_usage()
        if current_usage > limit:
            self._enforce_memory_limit()
    
    def get_memory_usage(self) -> int:
        """
        現在のメモリ使用量を取得
        
        Returns:
            メモリ使用量（バイト）
        """
        font_usage = self.font_loader.cache.memory_usage()
        image_usage = self.image_loader.cache.memory_usage()
        sprite_usage = self.sprite_loader.cache.memory_usage()
        
        return font_usage + image_usage + sprite_usage
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        統合キャッシュ統計情報を取得
        
        Returns:
            統計情報
        """
        font_stats = self.font_loader.get_cache_stats()
        image_stats = self.image_loader.get_cache_stats()
        sprite_stats = self.sprite_loader.get_cache_stats()
        
        total_hits = self.cache_hit_count
        total_misses = self.cache_miss_count
        total_requests = total_hits + total_misses
        hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'total_memory_usage': self.get_memory_usage(),
            'memory_limit': self.memory_limit,
            'load_count': self.load_count,
            'hit_rate': hit_rate,  # hit_rate キーを追加
            'cache_hit_rate': hit_rate,
            'font_cache': font_stats,
            'image_cache': image_stats,
            'sprite_cache': sprite_stats,
            'watched_files': len(self.file_monitor.get_watched_files()),
            'asset_dependencies': len(self.asset_dependencies)
        }
    
    def start_file_monitoring(self) -> None:
        """ファイル監視を開始"""
        if not self.file_monitor.watching:
            self.file_monitor.start()
            logger.info("File monitoring started")
    
    def stop_file_monitoring(self) -> None:
        """ファイル監視を停止"""
        if self.file_monitor.watching:
            self.file_monitor.stop()
            logger.info("File monitoring stopped")
    
    def add_reload_callback(self, file_path: str, callback: Callable[[str], None]) -> None:
        """
        リロードコールバックを追加
        
        Args:
            file_path: ファイルパス
            callback: コールバック関数
        """
        if file_path not in self.reload_callbacks:
            self.reload_callbacks[file_path] = []
        
        self.reload_callbacks[file_path].append(callback)
        logger.debug(f"Added reload callback for {file_path}")
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        キャッシュをクリア
        
        Args:
            cache_type: クリア対象（'font', 'image', 'sprite', None=全部）
        """
        if cache_type is None or cache_type == 'font':
            self.font_loader.clear_cache()
        
        if cache_type is None or cache_type == 'image':
            self.image_loader.clear_cache()
        
        if cache_type is None or cache_type == 'sprite':
            self.sprite_loader.clear_cache()
        
        logger.info(f"Cache cleared: {cache_type or 'all'}")
    
    def cleanup(self) -> None:
        """リソースをクリーンアップ"""
        # ファイル監視を停止
        self.stop_file_monitoring()
        
        # キャッシュをクリア
        self.clear_cache()
        
        # 統計情報をリセット
        self.load_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        logger.info("AssetManager cleanup completed")
    
    def _add_file_watch(self, file_path: str, asset_type: str) -> None:
        """
        ファイル監視を追加
        
        Args:
            file_path: ファイルパス
            asset_type: アセットタイプ
        """
        def reload_handler(event_type: str, changed_file: str):
            logger.info(f"File {event_type}: {changed_file}")
            
            # キャッシュから削除
            if asset_type == 'font':
                self.font_loader.clear_cache()
            elif asset_type == 'image':
                self.image_loader.clear_cache()
            elif asset_type == 'sprite':
                self.sprite_loader.clear_cache()
            
            # 依存関係があるアセットも更新
            self._reload_dependencies(changed_file)
            
            # コールバック実行
            self._execute_reload_callbacks(changed_file)
        
        self.file_monitor.add_watch(file_path, reload_handler)
    
    def _reload_dependencies(self, changed_file: str) -> None:
        """
        依存関係があるアセットを再読み込み
        
        Args:
            changed_file: 変更されたファイル
        """
        for asset_file, dependencies in self.asset_dependencies.items():
            if changed_file in dependencies:
                logger.debug(f"Reloading dependent asset: {asset_file}")
                # 依存元のキャッシュもクリア
                self.sprite_loader.clear_cache()
    
    def _execute_reload_callbacks(self, changed_file: str) -> None:
        """
        リロードコールバックを実行
        
        Args:
            changed_file: 変更されたファイル
        """
        callbacks = self.reload_callbacks.get(changed_file, [])
        for callback in callbacks:
            try:
                callback(changed_file)
            except Exception as e:
                logger.error(f"Reload callback error: {e}")
    
    def _enforce_memory_limit(self) -> None:
        """メモリ制限を強制"""
        current_usage = self.get_memory_usage()
        
        if current_usage <= self.memory_limit:
            return
        
        # 使用量の多い順でキャッシュをクリア
        caches = [
            (self.image_loader.cache.memory_usage(), self.image_loader.clear_cache),
            (self.sprite_loader.cache.memory_usage(), self.sprite_loader.clear_cache),
            (self.font_loader.cache.memory_usage(), self.font_loader.clear_cache)
        ]
        
        # 使用量の多い順にソート
        caches.sort(key=lambda x: x[0], reverse=True)
        
        for usage, clear_func in caches:
            if self.get_memory_usage() <= self.memory_limit:
                break
            
            if usage > 0:
                clear_func()
                logger.info(f"Cleared cache to enforce memory limit")
        
        logger.warning(f"Memory usage reduced from {current_usage} to {self.get_memory_usage()} bytes")