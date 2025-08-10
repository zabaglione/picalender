#!/usr/bin/env python3
"""
パフォーマンスベンチマークスクリプト

PiCalendarアプリケーションのパフォーマンスを測定する。
"""

import sys
import os
import time
import psutil
import pygame
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config_manager import ConfigManager
from src.core.performance_optimizer import PerformanceOptimizer, RenderOptimizer


class PerformanceBenchmark:
    """パフォーマンスベンチマーククラス"""
    
    def __init__(self, config_path: str = None):
        """初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        # 設定読み込み
        self.config_manager = ConfigManager(config_path)
        self.settings = self.config_manager.get_all()
        
        # プロセス情報
        self.process = psutil.Process(os.getpid())
        
        # 結果保存用
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'benchmarks': []
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得"""
        return {
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total_mb': psutil.virtual_memory().total / (1024 * 1024),
            'pygame_version': pygame.version.ver
        }
    
    def benchmark_memory_usage(self, duration: int = 10) -> Dict[str, float]:
        """メモリ使用量をベンチマーク
        
        Args:
            duration: 測定時間（秒）
            
        Returns:
            メモリ使用量の統計
        """
        print(f"メモリ使用量ベンチマーク（{duration}秒）...")
        
        samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            samples.append(memory_mb)
            time.sleep(0.1)
        
        result = {
            'min_mb': min(samples),
            'max_mb': max(samples),
            'avg_mb': sum(samples) / len(samples),
            'samples': len(samples)
        }
        
        print(f"  最小: {result['min_mb']:.1f}MB")
        print(f"  最大: {result['max_mb']:.1f}MB")
        print(f"  平均: {result['avg_mb']:.1f}MB")
        
        return result
    
    def benchmark_cpu_usage(self, duration: int = 10) -> Dict[str, float]:
        """CPU使用率をベンチマーク
        
        Args:
            duration: 測定時間（秒）
            
        Returns:
            CPU使用率の統計
        """
        print(f"CPU使用率ベンチマーク（{duration}秒）...")
        
        samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            samples.append(cpu_percent)
            time.sleep(0.1)
        
        result = {
            'min_percent': min(samples),
            'max_percent': max(samples),
            'avg_percent': sum(samples) / len(samples),
            'samples': len(samples)
        }
        
        print(f"  最小: {result['min_percent']:.1f}%")
        print(f"  最大: {result['max_percent']:.1f}%")
        print(f"  平均: {result['avg_percent']:.1f}%")
        
        return result
    
    def benchmark_pygame_init(self) -> Dict[str, float]:
        """Pygame初期化時間をベンチマーク
        
        Returns:
            初期化時間の統計
        """
        print("Pygame初期化ベンチマーク...")
        
        times = []
        
        for i in range(5):
            pygame.quit()
            
            start = time.time()
            pygame.init()
            elapsed = time.time() - start
            
            times.append(elapsed)
            print(f"  試行 {i+1}: {elapsed*1000:.1f}ms")
        
        pygame.quit()
        
        result = {
            'min_ms': min(times) * 1000,
            'max_ms': max(times) * 1000,
            'avg_ms': sum(times) / len(times) * 1000,
            'samples': len(times)
        }
        
        print(f"  平均: {result['avg_ms']:.1f}ms")
        
        return result
    
    def benchmark_optimizer(self) -> Dict[str, Any]:
        """最適化機能をベンチマーク
        
        Returns:
            最適化機能のベンチマーク結果
        """
        print("最適化機能ベンチマーク...")
        
        optimizer = PerformanceOptimizer(self.settings)
        render_optimizer = RenderOptimizer()
        
        # 品質レベル別のテスト
        quality_results = {}
        
        for quality in ['ultra_low', 'low', 'medium', 'high']:
            optimizer.quality_level = quality
            settings = optimizer.get_optimized_settings()
            
            quality_results[quality] = {
                'fps': settings['fps'],
                'cache_size': settings['cache_size'],
                'description': settings['description']
            }
            
            print(f"  {quality}: FPS={settings['fps']}, Cache={settings['cache_size']}")
        
        # メモリ解放テスト
        print("  メモリ解放テスト...")
        freed_bytes = optimizer.free_memory()
        
        # キャッシュテスト
        print("  サーフェスキャッシュテスト...")
        pygame.init()
        test_surface = pygame.Surface((100, 100))
        
        # キャッシュなし
        start = time.time()
        for _ in range(1000):
            scaled = pygame.transform.scale(test_surface, (50, 50))
        no_cache_time = time.time() - start
        
        # キャッシュあり
        start = time.time()
        for _ in range(1000):
            scaled = render_optimizer.get_scaled_surface(test_surface, 0.5)
        cache_time = time.time() - start
        
        pygame.quit()
        
        result = {
            'quality_levels': quality_results,
            'memory_freed_bytes': freed_bytes,
            'cache_performance': {
                'no_cache_ms': no_cache_time * 1000,
                'with_cache_ms': cache_time * 1000,
                'speedup': no_cache_time / cache_time if cache_time > 0 else 0
            }
        }
        
        print(f"  キャッシュ高速化: {result['cache_performance']['speedup']:.2f}x")
        
        return result
    
    def benchmark_render_components(self) -> Dict[str, float]:
        """レンダリングコンポーネントをベンチマーク
        
        Returns:
            各コンポーネントのレンダリング時間
        """
        print("レンダリングコンポーネントベンチマーク...")
        
        # Pygame初期化
        pygame.init()
        screen = pygame.display.set_mode((1024, 600))
        font = pygame.font.Font(None, 24)
        
        results = {}
        
        # テキストレンダリング
        print("  テキストレンダリング...")
        start = time.time()
        for i in range(100):
            text_surface = font.render(f"Test {i}", True, (255, 255, 255))
            screen.blit(text_surface, (10, 10))
        text_time = time.time() - start
        results['text_render_ms'] = text_time * 1000
        
        # 図形描画
        print("  図形描画...")
        start = time.time()
        for i in range(100):
            pygame.draw.circle(screen, (255, 0, 0), (50, 50), 25)
            pygame.draw.rect(screen, (0, 255, 0), (100, 100, 50, 50))
        shape_time = time.time() - start
        results['shape_render_ms'] = shape_time * 1000
        
        # サーフェス合成
        print("  サーフェス合成...")
        test_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        test_surface.fill((100, 100, 100, 128))
        
        start = time.time()
        for i in range(100):
            screen.blit(test_surface, (200, 200))
        blit_time = time.time() - start
        results['blit_ms'] = blit_time * 1000
        
        pygame.quit()
        
        for key, value in results.items():
            print(f"    {key}: {value:.2f}ms")
        
        return results
    
    def run_all_benchmarks(self):
        """すべてのベンチマークを実行"""
        print("=" * 50)
        print("PiCalendar パフォーマンスベンチマーク")
        print("=" * 50)
        print()
        
        # 各ベンチマーク実行
        benchmarks = [
            ("Memory Usage", self.benchmark_memory_usage),
            ("CPU Usage", self.benchmark_cpu_usage),
            ("Pygame Init", self.benchmark_pygame_init),
            ("Optimizer", self.benchmark_optimizer),
            ("Render Components", self.benchmark_render_components)
        ]
        
        for name, benchmark_func in benchmarks:
            print(f"\n[{name}]")
            try:
                result = benchmark_func()
                self.results['benchmarks'].append({
                    'name': name,
                    'result': result,
                    'status': 'success'
                })
            except Exception as e:
                print(f"  エラー: {e}")
                self.results['benchmarks'].append({
                    'name': name,
                    'error': str(e),
                    'status': 'failed'
                })
            print()
        
        # 結果のサマリー
        self._print_summary()
        
        # 結果をファイルに保存
        self._save_results()
    
    def _print_summary(self):
        """結果のサマリーを表示"""
        print("=" * 50)
        print("サマリー")
        print("=" * 50)
        
        # メモリ使用量チェック
        memory_benchmark = next((b for b in self.results['benchmarks'] 
                                if b['name'] == 'Memory Usage' and b['status'] == 'success'), None)
        if memory_benchmark:
            avg_memory = memory_benchmark['result']['avg_mb']
            target = 180
            status = "✓ OK" if avg_memory <= target else "✗ NG"
            print(f"メモリ使用量: {avg_memory:.1f}MB / {target}MB {status}")
        
        # CPU使用率チェック
        cpu_benchmark = next((b for b in self.results['benchmarks'] 
                            if b['name'] == 'CPU Usage' and b['status'] == 'success'), None)
        if cpu_benchmark:
            avg_cpu = cpu_benchmark['result']['avg_percent']
            target = 30
            status = "✓ OK" if avg_cpu <= target else "✗ NG"
            print(f"CPU使用率: {avg_cpu:.1f}% / {target}% {status}")
        
        # 最適化効果
        optimizer_benchmark = next((b for b in self.results['benchmarks'] 
                                  if b['name'] == 'Optimizer' and b['status'] == 'success'), None)
        if optimizer_benchmark:
            speedup = optimizer_benchmark['result']['cache_performance']['speedup']
            print(f"キャッシュによる高速化: {speedup:.2f}x")
    
    def _save_results(self):
        """結果をファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n結果を保存しました: {filename}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='PiCalendar パフォーマンスベンチマーク')
    parser.add_argument('--config', help='設定ファイルのパス')
    parser.add_argument('--quick', action='store_true', help='クイックテスト（短時間）')
    
    args = parser.parse_args()
    
    # ベンチマーク実行
    benchmark = PerformanceBenchmark(args.config)
    
    if args.quick:
        # クイックテスト
        print("クイックテストモード\n")
        benchmark.benchmark_memory_usage(duration=5)
        benchmark.benchmark_cpu_usage(duration=5)
    else:
        # フルテスト
        benchmark.run_all_benchmarks()


if __name__ == '__main__':
    main()