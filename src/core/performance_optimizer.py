#!/usr/bin/env python3
"""
パフォーマンス最適化モジュール

CPU使用率とメモリ使用量を最適化する機能を提供。
"""

import gc
import time
import pygame
import logging
import psutil
import os
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
from threading import Lock
from datetime import datetime, timedelta


class PerformanceOptimizer:
    """パフォーマンス最適化クラス
    
    Raspberry Pi Zero 2 W向けに最適化された設定と
    動的なパフォーマンス調整機能を提供。
    """
    
    # 目標値（Raspberry Pi Zero 2 W向け）
    TARGET_CPU_PERCENT = 30.0
    TARGET_MEMORY_MB = 180
    TARGET_FPS = 30
    
    # 品質レベル定義
    QUALITY_LEVELS = {
        'ultra_low': {
            'fps': 10,
            'update_intervals': {
                'clock': 1.0,
                'date': 60.0,
                'calendar': 300.0,
                'weather': 1800.0,
                'background': 3600.0,
                'character': 0.2
            },
            'render_scale': 0.5,
            'cache_size': 10,
            'max_sprites': 1,
            'description': 'Ultra Low - 最小リソース使用'
        },
        'low': {
            'fps': 15,
            'update_intervals': {
                'clock': 1.0,
                'date': 30.0,
                'calendar': 120.0,
                'weather': 900.0,
                'background': 1800.0,
                'character': 0.125
            },
            'render_scale': 0.75,
            'cache_size': 20,
            'max_sprites': 2,
            'description': 'Low - 低リソース使用'
        },
        'medium': {
            'fps': 20,
            'update_intervals': {
                'clock': 1.0,
                'date': 10.0,
                'calendar': 60.0,
                'weather': 600.0,
                'background': 600.0,
                'character': 0.1
            },
            'render_scale': 1.0,
            'cache_size': 50,
            'max_sprites': 5,
            'description': 'Medium - バランス重視'
        },
        'high': {
            'fps': 30,
            'update_intervals': {
                'clock': 1.0,
                'date': 1.0,
                'calendar': 60.0,
                'weather': 300.0,
                'background': 300.0,
                'character': 0.0625
            },
            'render_scale': 1.0,
            'cache_size': 100,
            'max_sprites': 10,
            'description': 'High - 高品質'
        }
    }
    
    def __init__(self, settings: Dict[str, Any]):
        """初期化
        
        Args:
            settings: アプリケーション設定
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        
        # パフォーマンス設定
        perf_config = settings.get('performance', {})
        self.auto_adjust = perf_config.get('auto_adjust', True)
        self.quality_level = perf_config.get('default_quality', 'medium')
        self.monitor_interval = perf_config.get('monitor_interval', 5.0)
        
        # 現在のプロセス
        self.process = psutil.Process(os.getpid())
        
        # 統計情報
        self._stats = {
            'cpu_samples': [],
            'memory_samples': [],
            'fps_samples': [],
            'quality_changes': 0,
            'last_adjustment': None,
            'start_time': datetime.now()
        }
        self._stats_lock = Lock()
        
        # 最後の調整時刻
        self._last_adjustment = datetime.now()
        self._adjustment_cooldown = timedelta(seconds=30)
        
        # Dirty Rectangle最適化用
        self._dirty_rects: List[pygame.Rect] = []
        self._full_redraw_needed = True
        
        self.logger.info(f"PerformanceOptimizer initialized with quality: {self.quality_level}")
    
    def get_optimized_settings(self) -> Dict[str, Any]:
        """最適化された設定を取得
        
        Returns:
            現在の品質レベルに基づく設定
        """
        level_config = self.QUALITY_LEVELS[self.quality_level]
        
        return {
            'fps': level_config['fps'],
            'update_intervals': level_config['update_intervals'].copy(),
            'render_scale': level_config['render_scale'],
            'cache_size': level_config['cache_size'],
            'max_sprites': level_config['max_sprites'],
            'quality_level': self.quality_level,
            'description': level_config['description']
        }
    
    def monitor_performance(self) -> Dict[str, float]:
        """パフォーマンスを監視
        
        Returns:
            CPU使用率とメモリ使用量
        """
        try:
            # CPU使用率（過去1秒間の平均）
            cpu_percent = self.process.cpu_percent(interval=0.1)
            
            # メモリ使用量（MB）
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # 統計に追加
            with self._stats_lock:
                self._stats['cpu_samples'].append(cpu_percent)
                self._stats['memory_samples'].append(memory_mb)
                
                # サンプル数を制限
                if len(self._stats['cpu_samples']) > 100:
                    self._stats['cpu_samples'].pop(0)
                if len(self._stats['memory_samples']) > 100:
                    self._stats['memory_samples'].pop(0)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'cpu_avg': self._get_average('cpu_samples'),
                'memory_avg': self._get_average('memory_samples')
            }
            
        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {e}")
            return {
                'cpu_percent': 0,
                'memory_mb': 0,
                'cpu_avg': 0,
                'memory_avg': 0
            }
    
    def _get_average(self, sample_key: str) -> float:
        """サンプルの平均値を計算
        
        Args:
            sample_key: サンプルのキー名
            
        Returns:
            平均値
        """
        with self._stats_lock:
            samples = self._stats.get(sample_key, [])
            if samples:
                return sum(samples) / len(samples)
        return 0
    
    def auto_adjust_quality(self, current_fps: float = 0) -> bool:
        """品質レベルを自動調整
        
        Args:
            current_fps: 現在のFPS
            
        Returns:
            調整が行われた場合True
        """
        if not self.auto_adjust:
            return False
        
        # クールダウン中は調整しない
        now = datetime.now()
        if now - self._last_adjustment < self._adjustment_cooldown:
            return False
        
        # パフォーマンス監視
        perf = self.monitor_performance()
        cpu_avg = perf['cpu_avg']
        memory_avg = perf['memory_avg']
        
        # FPSサンプル追加
        if current_fps > 0:
            with self._stats_lock:
                self._stats['fps_samples'].append(current_fps)
                if len(self._stats['fps_samples']) > 100:
                    self._stats['fps_samples'].pop(0)
        
        fps_avg = self._get_average('fps_samples')
        
        # 品質レベルの決定
        quality_levels = ['ultra_low', 'low', 'medium', 'high']
        current_index = quality_levels.index(self.quality_level)
        new_index = current_index
        
        # CPU使用率が高すぎる場合
        if cpu_avg > self.TARGET_CPU_PERCENT * 1.2:
            new_index = max(0, current_index - 1)
            self.logger.warning(f"High CPU usage: {cpu_avg:.1f}%, reducing quality")
        
        # メモリ使用量が多すぎる場合
        elif memory_avg > self.TARGET_MEMORY_MB:
            new_index = max(0, current_index - 1)
            self.logger.warning(f"High memory usage: {memory_avg:.1f}MB, reducing quality")
            # メモリ解放も実行
            self.free_memory()
        
        # FPSが目標を大きく下回る場合
        elif fps_avg > 0 and fps_avg < self.QUALITY_LEVELS[self.quality_level]['fps'] * 0.7:
            new_index = max(0, current_index - 1)
            self.logger.warning(f"Low FPS: {fps_avg:.1f}, reducing quality")
        
        # リソースに余裕がある場合
        elif (cpu_avg < self.TARGET_CPU_PERCENT * 0.5 and 
              memory_avg < self.TARGET_MEMORY_MB * 0.7 and
              fps_avg > self.QUALITY_LEVELS[self.quality_level]['fps'] * 0.9):
            new_index = min(len(quality_levels) - 1, current_index + 1)
            self.logger.info(f"Resources available, increasing quality")
        
        # 品質レベル変更
        if new_index != current_index:
            self.quality_level = quality_levels[new_index]
            self._last_adjustment = now
            
            with self._stats_lock:
                self._stats['quality_changes'] += 1
                self._stats['last_adjustment'] = now.isoformat()
            
            self.logger.info(f"Quality level changed to: {self.quality_level}")
            return True
        
        return False
    
    def free_memory(self) -> int:
        """メモリを解放
        
        Returns:
            解放されたメモリ量（推定、バイト）
        """
        freed = 0
        
        try:
            # ガベージコレクション実行
            collected = gc.collect()
            freed += collected * 1024  # 推定値
            
            # Pygameのサーフェスキャッシュをクリア（存在する場合）
            if hasattr(pygame, 'surfarray'):
                try:
                    pygame.surfarray.use_arraytype(None)
                    freed += 1024 * 1024  # 推定1MB
                except:
                    pass
            
            self.logger.info(f"Memory freed: approximately {freed/1024:.1f}KB")
            
        except Exception as e:
            self.logger.error(f"Memory free failed: {e}")
        
        return freed
    
    def optimize_pygame_settings(self):
        """Pygame設定を最適化"""
        try:
            # ハードウェアアクセラレーション無効化（Pi Zero 2 Wでは逆効果の場合あり）
            os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
            os.environ['SDL_RENDER_DRIVER'] = 'software'
            
            # ダブルバッファリング無効化（メモリ節約）
            pygame.display.set_mode(
                flags=pygame.FULLSCREEN | pygame.NOFRAME
            )
            
            # イベントの最適化
            pygame.event.set_blocked(None)
            pygame.event.set_allowed([
                pygame.QUIT,
                pygame.KEYDOWN,
                pygame.USEREVENT
            ])
            
            self.logger.info("Pygame settings optimized")
            
        except Exception as e:
            self.logger.error(f"Pygame optimization failed: {e}")
    
    def add_dirty_rect(self, rect: pygame.Rect):
        """Dirty Rectangle を追加
        
        Args:
            rect: 更新が必要な矩形領域
        """
        if rect:
            self._dirty_rects.append(rect)
    
    def get_dirty_rects(self) -> List[pygame.Rect]:
        """Dirty Rectangle リストを取得してクリア
        
        Returns:
            更新が必要な矩形領域のリスト
        """
        if self._full_redraw_needed:
            self._full_redraw_needed = False
            return []  # 空リストは全画面更新を意味する
        
        rects = self._dirty_rects.copy()
        self._dirty_rects.clear()
        
        # 重複を統合
        if len(rects) > 10:
            # 矩形が多すぎる場合は全画面更新の方が効率的
            return []
        
        return rects
    
    def request_full_redraw(self):
        """全画面再描画を要求"""
        self._full_redraw_needed = True
        self._dirty_rects.clear()
    
    @lru_cache(maxsize=128)
    def should_update_component(self, component: str, last_update: float) -> bool:
        """コンポーネントの更新が必要か判定
        
        Args:
            component: コンポーネント名
            last_update: 最後の更新時刻
            
        Returns:
            更新が必要な場合True
        """
        current_time = time.time()
        settings = self.get_optimized_settings()
        interval = settings['update_intervals'].get(component, 1.0)
        
        return (current_time - last_update) >= interval
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得
        
        Returns:
            統計情報の辞書
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
            # 稼働時間
            uptime = (datetime.now() - stats['start_time']).total_seconds()
            stats['uptime_seconds'] = uptime
            
            # 平均値
            stats['avg_cpu'] = self._get_average('cpu_samples')
            stats['avg_memory'] = self._get_average('memory_samples')
            stats['avg_fps'] = self._get_average('fps_samples')
            
            # 現在の品質レベル
            stats['current_quality'] = self.quality_level
            stats['quality_settings'] = self.get_optimized_settings()
            
            return stats


class RenderOptimizer:
    """レンダリング最適化クラス
    
    描画処理を最適化する機能を提供。
    """
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # サーフェスキャッシュ
        self._surface_cache: Dict[str, pygame.Surface] = {}
        self._cache_lock = Lock()
        
        # レンダリング統計
        self._render_times: List[float] = []
    
    @lru_cache(maxsize=32)
    def get_scaled_surface(self, original: pygame.Surface, scale: float) -> pygame.Surface:
        """スケールされたサーフェスを取得（キャッシュ付き）
        
        Args:
            original: 元のサーフェス
            scale: スケール係数
            
        Returns:
            スケールされたサーフェス
        """
        if scale == 1.0:
            return original
        
        new_size = (
            int(original.get_width() * scale),
            int(original.get_height() * scale)
        )
        
        # smoothscale は高品質だが遅い、scale は低品質だが速い
        if scale < 1.0:
            # 縮小時は smoothscale を使用
            return pygame.transform.smoothscale(original, new_size)
        else:
            # 拡大時は scale を使用（Pi Zero 2 Wでは速度優先）
            return pygame.transform.scale(original, new_size)
    
    def cache_surface(self, key: str, surface: pygame.Surface):
        """サーフェスをキャッシュ
        
        Args:
            key: キャッシュキー
            surface: キャッシュするサーフェス
        """
        with self._cache_lock:
            self._surface_cache[key] = surface.copy()
    
    def get_cached_surface(self, key: str) -> Optional[pygame.Surface]:
        """キャッシュされたサーフェスを取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされたサーフェスまたはNone
        """
        with self._cache_lock:
            return self._surface_cache.get(key)
    
    def clear_cache(self):
        """サーフェスキャッシュをクリア"""
        with self._cache_lock:
            self._surface_cache.clear()
        self.logger.info("Surface cache cleared")
    
    def optimize_text_rendering(self, font: pygame.font.Font, text: str, 
                              color: Tuple[int, int, int]) -> pygame.Surface:
        """テキストレンダリングを最適化
        
        Args:
            font: フォントオブジェクト
            text: レンダリングするテキスト
            color: テキストカラー
            
        Returns:
            レンダリングされたテキストサーフェス
        """
        # キャッシュキー生成
        cache_key = f"text_{id(font)}_{text}_{color}"
        
        # キャッシュチェック
        cached = self.get_cached_surface(cache_key)
        if cached:
            return cached
        
        # レンダリング
        surface = font.render(text, True, color)
        
        # キャッシュ保存
        self.cache_surface(cache_key, surface)
        
        return surface
    
    def record_render_time(self, render_time: float):
        """レンダリング時間を記録
        
        Args:
            render_time: レンダリング時間（秒）
        """
        self._render_times.append(render_time)
        if len(self._render_times) > 100:
            self._render_times.pop(0)
    
    def get_average_render_time(self) -> float:
        """平均レンダリング時間を取得
        
        Returns:
            平均レンダリング時間（秒）
        """
        if self._render_times:
            return sum(self._render_times) / len(self._render_times)
        return 0


# グローバルインスタンス（シングルトン）
_optimizer_instance: Optional[PerformanceOptimizer] = None
_render_optimizer_instance: Optional[RenderOptimizer] = None


def get_performance_optimizer(settings: Dict[str, Any]) -> PerformanceOptimizer:
    """PerformanceOptimizerのシングルトンインスタンスを取得
    
    Args:
        settings: アプリケーション設定
        
    Returns:
        PerformanceOptimizerインスタンス
    """
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PerformanceOptimizer(settings)
    return _optimizer_instance


def get_render_optimizer() -> RenderOptimizer:
    """RenderOptimizerのシングルトンインスタンスを取得
    
    Returns:
        RenderOptimizerインスタンス
    """
    global _render_optimizer_instance
    if _render_optimizer_instance is None:
        _render_optimizer_instance = RenderOptimizer()
    return _render_optimizer_instance