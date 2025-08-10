"""
パフォーマンス監視・最適化システム

TASK-102: パフォーマンス最適化
- CPU/メモリ使用量監視
- FPS安定化
- 動的品質調整
- プロファイリング機能
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PerformanceLevel(Enum):
    """パフォーマンスレベル"""
    HIGH = "high"           # 最高品質
    BALANCED = "balanced"   # バランス重視
    FAST = "fast"          # 速度重視
    MINIMAL = "minimal"    # 最小負荷


@dataclass
class PerformanceMetrics:
    """パフォーマンス指標"""
    timestamp: float = field(default_factory=time.time)
    
    # FPS関連
    current_fps: float = 0.0
    target_fps: float = 30.0
    frame_time_ms: float = 0.0
    frame_drops: int = 0
    
    # CPU関連
    cpu_percent: float = 0.0
    cpu_temperature: Optional[float] = None
    
    # メモリ関連
    memory_usage_mb: float = 0.0
    memory_percent: float = 0.0
    memory_available_mb: float = 0.0
    
    # GPU関連（利用可能な場合）
    gpu_usage: Optional[float] = None
    gpu_memory_mb: Optional[float] = None
    
    # システム関連
    load_average: Optional[Tuple[float, float, float]] = None
    disk_usage_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp,
            'fps': {
                'current': self.current_fps,
                'target': self.target_fps,
                'frame_time_ms': self.frame_time_ms,
                'drops': self.frame_drops
            },
            'cpu': {
                'percent': self.cpu_percent,
                'temperature': self.cpu_temperature
            },
            'memory': {
                'usage_mb': self.memory_usage_mb,
                'percent': self.memory_percent,
                'available_mb': self.memory_available_mb
            },
            'gpu': {
                'usage': self.gpu_usage,
                'memory_mb': self.gpu_memory_mb
            },
            'system': {
                'load_average': self.load_average,
                'disk_usage': self.disk_usage_percent
            }
        }


class AdaptiveQualityController:
    """動的品質制御"""
    
    def __init__(self, target_fps: float = 30.0, target_cpu: float = 30.0):
        """
        初期化
        
        Args:
            target_fps: 目標FPS
            target_cpu: 目標CPU使用率（%）
        """
        self.target_fps = target_fps
        self.target_cpu = target_cpu
        
        self.current_level = PerformanceLevel.BALANCED
        self.adjustment_cooldown = 2.0  # 調整間隔（秒）
        self.last_adjustment = 0.0
        
        # 品質設定
        self.quality_settings = {
            PerformanceLevel.HIGH: {
                'vsync': True,
                'antialiasing': True,
                'texture_quality': 'high',
                'effect_quality': 'high',
                'update_frequency': 1.0,
                'dirty_region_optimization': False
            },
            PerformanceLevel.BALANCED: {
                'vsync': True,
                'antialiasing': True,
                'texture_quality': 'medium',
                'effect_quality': 'medium',
                'update_frequency': 0.8,
                'dirty_region_optimization': True
            },
            PerformanceLevel.FAST: {
                'vsync': False,
                'antialiasing': False,
                'texture_quality': 'low',
                'effect_quality': 'low',
                'update_frequency': 0.5,
                'dirty_region_optimization': True
            },
            PerformanceLevel.MINIMAL: {
                'vsync': False,
                'antialiasing': False,
                'texture_quality': 'minimal',
                'effect_quality': 'minimal',
                'update_frequency': 0.3,
                'dirty_region_optimization': True
            }
        }
        
        self.adjustment_callbacks: List[Callable] = []
    
    def add_adjustment_callback(self, callback: Callable):
        """品質調整コールバックを追加"""
        self.adjustment_callbacks.append(callback)
    
    def remove_adjustment_callback(self, callback: Callable):
        """品質調整コールバックを削除"""
        if callback in self.adjustment_callbacks:
            self.adjustment_callbacks.remove(callback)
    
    def analyze_performance(self, metrics: PerformanceMetrics) -> Optional[PerformanceLevel]:
        """
        パフォーマンスを分析して最適なレベルを決定
        
        Args:
            metrics: パフォーマンス指標
            
        Returns:
            推奨される品質レベル（変更不要な場合None）
        """
        current_time = time.time()
        
        # クールダウン中は調整しない
        if current_time - self.last_adjustment < self.adjustment_cooldown:
            return None
        
        fps_ratio = metrics.current_fps / self.target_fps
        cpu_ratio = metrics.cpu_percent / self.target_cpu
        
        # パフォーマンス問題を検出
        performance_score = 0
        
        # FPS評価
        if fps_ratio < 0.8:  # FPSが目標の80%未満
            performance_score -= 2
        elif fps_ratio < 0.9:  # FPSが目標の90%未満
            performance_score -= 1
        elif fps_ratio > 1.1:  # FPSが目標の110%以上
            performance_score += 1
        
        # CPU評価
        if cpu_ratio > 1.2:  # CPUが目標の120%以上
            performance_score -= 2
        elif cpu_ratio > 1.1:  # CPUが目標の110%以上
            performance_score -= 1
        elif cpu_ratio < 0.7:  # CPUが目標の70%未満
            performance_score += 1
        
        # メモリ評価
        if metrics.memory_percent > 85:  # メモリ使用率85%以上
            performance_score -= 1
        elif metrics.memory_percent < 50:  # メモリ使用率50%未満
            performance_score += 1
        
        # 品質レベルの決定
        current_index = list(PerformanceLevel).index(self.current_level)
        new_level = None
        
        if performance_score <= -3:
            # パフォーマンス大幅低下 - 2段階下げる
            new_index = min(len(PerformanceLevel) - 1, current_index + 2)
            new_level = list(PerformanceLevel)[new_index]
        elif performance_score <= -1:
            # パフォーマンス低下 - 1段階下げる
            new_index = min(len(PerformanceLevel) - 1, current_index + 1)
            new_level = list(PerformanceLevel)[new_index]
        elif performance_score >= 2:
            # パフォーマンス余裕あり - 1段階上げる
            new_index = max(0, current_index - 1)
            new_level = list(PerformanceLevel)[new_index]
        
        if new_level and new_level != self.current_level:
            logger.info(f"Performance level adjustment: {self.current_level.value} -> {new_level.value}")
            self.current_level = new_level
            self.last_adjustment = current_time
            
            # コールバック実行
            settings = self.quality_settings[new_level]
            for callback in self.adjustment_callbacks:
                try:
                    callback(new_level, settings)
                except Exception as e:
                    logger.error(f"Quality adjustment callback error: {e}")
            
            return new_level
        
        return None
    
    def get_current_settings(self) -> Dict[str, Any]:
        """現在の品質設定を取得"""
        return self.quality_settings[self.current_level].copy()
    
    def force_level(self, level: PerformanceLevel):
        """強制的に品質レベルを設定"""
        if level != self.current_level:
            logger.info(f"Forced performance level: {self.current_level.value} -> {level.value}")
            self.current_level = level
            self.last_adjustment = time.time()
            
            settings = self.quality_settings[level]
            for callback in self.adjustment_callbacks:
                try:
                    callback(level, settings)
                except Exception as e:
                    logger.error(f"Quality adjustment callback error: {e}")


class PerformanceMonitor:
    """パフォーマンス監視システム"""
    
    def __init__(self, monitor_interval: float = 1.0, history_size: int = 60):
        """
        初期化
        
        Args:
            monitor_interval: 監視間隔（秒）
            history_size: 履歴保持数
        """
        self.monitor_interval = monitor_interval
        self.history_size = history_size
        
        self.metrics_history: deque = deque(maxlen=history_size)
        self.current_metrics = PerformanceMetrics()
        
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # システム情報
        self.process = psutil.Process()
        self.cpu_count = psutil.cpu_count()
        
        # 温度監視（Raspberry Pi対応）
        self.temp_file = "/sys/class/thermal/thermal_zone0/temp"
        self.has_temp_sensor = self._check_temperature_sensor()
        
        # 閾値設定
        self.thresholds = {
            'fps_warning': 20.0,
            'cpu_warning': 70.0,
            'memory_warning': 80.0,
            'temperature_warning': 70.0,
            'frame_drop_warning': 5
        }
        
        self.warning_callbacks: List[Callable] = []
    
    def _check_temperature_sensor(self) -> bool:
        """温度センサーの利用可能性を確認"""
        try:
            with open(self.temp_file, 'r') as f:
                f.read()
            return True
        except (FileNotFoundError, PermissionError):
            return False
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """CPU温度を取得（Raspberry Pi）"""
        if not self.has_temp_sensor:
            return None
        
        try:
            with open(self.temp_file, 'r') as f:
                temp_str = f.read().strip()
                return float(temp_str) / 1000.0  # milli℃ to ℃
        except Exception:
            return None
    
    def update_fps_metrics(self, current_fps: float, target_fps: float, 
                          frame_time_ms: float, frame_drops: int = 0):
        """FPS関連メトリクスを更新"""
        self.current_metrics.current_fps = current_fps
        self.current_metrics.target_fps = target_fps
        self.current_metrics.frame_time_ms = frame_time_ms
        self.current_metrics.frame_drops = frame_drops
    
    def collect_system_metrics(self) -> PerformanceMetrics:
        """システムメトリクスを収集"""
        metrics = PerformanceMetrics()
        
        try:
            # CPU使用率
            metrics.cpu_percent = self.process.cpu_percent()
            metrics.cpu_temperature = self._get_cpu_temperature()
            
            # メモリ使用量
            memory_info = self.process.memory_info()
            metrics.memory_usage_mb = memory_info.rss / 1024 / 1024
            
            # システムメモリ情報
            system_memory = psutil.virtual_memory()
            metrics.memory_percent = system_memory.percent
            metrics.memory_available_mb = system_memory.available / 1024 / 1024
            
            # システム負荷平均（Linux/macOS）
            try:
                metrics.load_average = psutil.getloadavg()
            except AttributeError:
                pass  # Windowsでは利用不可
            
            # ディスク使用量
            try:
                disk_usage = psutil.disk_usage('/')
                metrics.disk_usage_percent = disk_usage.percent
            except Exception:
                pass
            
            # FPSメトリクスをコピー
            metrics.current_fps = self.current_metrics.current_fps
            metrics.target_fps = self.current_metrics.target_fps
            metrics.frame_time_ms = self.current_metrics.frame_time_ms
            metrics.frame_drops = self.current_metrics.frame_drops
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
        
        return metrics
    
    def start_monitoring(self):
        """監視を開始"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """監視メインループ"""
        while self.monitoring:
            try:
                metrics = self.collect_system_metrics()
                self.metrics_history.append(metrics)
                self.current_metrics = metrics
                
                # 警告チェック
                self._check_warnings(metrics)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(self.monitor_interval)
    
    def _check_warnings(self, metrics: PerformanceMetrics):
        """警告条件をチェック"""
        warnings = []
        
        if metrics.current_fps < self.thresholds['fps_warning']:
            warnings.append(f"Low FPS: {metrics.current_fps:.1f}")
        
        if metrics.cpu_percent > self.thresholds['cpu_warning']:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.thresholds['memory_warning']:
            warnings.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if (metrics.cpu_temperature and 
            metrics.cpu_temperature > self.thresholds['temperature_warning']):
            warnings.append(f"High temperature: {metrics.cpu_temperature:.1f}°C")
        
        if metrics.frame_drops > self.thresholds['frame_drop_warning']:
            warnings.append(f"Frame drops: {metrics.frame_drops}")
        
        # 警告コールバック実行
        if warnings:
            for callback in self.warning_callbacks:
                try:
                    callback(warnings, metrics)
                except Exception as e:
                    logger.error(f"Warning callback error: {e}")
    
    def add_warning_callback(self, callback: Callable):
        """警告コールバックを追加"""
        self.warning_callbacks.append(callback)
    
    def remove_warning_callback(self, callback: Callable):
        """警告コールバックを削除"""
        if callback in self.warning_callbacks:
            self.warning_callbacks.remove(callback)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """現在のメトリクスを取得"""
        return self.current_metrics
    
    def get_metrics_history(self, seconds: Optional[int] = None) -> List[PerformanceMetrics]:
        """メトリクス履歴を取得"""
        if seconds is None:
            return list(self.metrics_history)
        
        # 指定秒数分の履歴を取得
        cutoff_time = time.time() - seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, seconds: int = 30) -> Dict[str, float]:
        """指定期間の平均メトリクスを取得"""
        recent_metrics = self.get_metrics_history(seconds)
        
        if not recent_metrics:
            return {}
        
        total_count = len(recent_metrics)
        averages = {
            'fps': sum(m.current_fps for m in recent_metrics) / total_count,
            'cpu_percent': sum(m.cpu_percent for m in recent_metrics) / total_count,
            'memory_usage_mb': sum(m.memory_usage_mb for m in recent_metrics) / total_count,
            'memory_percent': sum(m.memory_percent for m in recent_metrics) / total_count,
            'frame_time_ms': sum(m.frame_time_ms for m in recent_metrics) / total_count
        }
        
        # 温度の平均（利用可能な場合のみ）
        temp_values = [m.cpu_temperature for m in recent_metrics if m.cpu_temperature is not None]
        if temp_values:
            averages['cpu_temperature'] = sum(temp_values) / len(temp_values)
        
        return averages
    
    def is_performance_stable(self, seconds: int = 10, fps_threshold: float = 2.0) -> bool:
        """パフォーマンスが安定しているかチェック"""
        recent_metrics = self.get_metrics_history(seconds)
        
        if len(recent_metrics) < 5:  # 最低5サンプル必要
            return False
        
        fps_values = [m.current_fps for m in recent_metrics]
        fps_std = (sum((x - sum(fps_values)/len(fps_values))**2 for x in fps_values) / len(fps_values))**0.5
        
        return fps_std < fps_threshold
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        current = self.get_current_metrics()
        averages = self.get_average_metrics(60)  # 1分平均
        
        return {
            'current': current.to_dict(),
            'averages': averages,
            'stable': self.is_performance_stable(),
            'history_count': len(self.metrics_history),
            'monitoring': self.monitoring,
            'thresholds': self.thresholds.copy()
        }