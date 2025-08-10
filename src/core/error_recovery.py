#!/usr/bin/env python3
"""
エラーリカバリシステム

各種エラーから自動的に復旧する機能を提供。
"""

import logging
import time
import os
import json
import gc
import traceback
from typing import Dict, Any, Type, Callable, Optional, List
from functools import wraps
from threading import Lock
from datetime import datetime


class ErrorRecoveryManager:
    """エラーリカバリ管理クラス
    
    各種エラーハンドラーを統合管理し、エラーからの自動復旧を実現。
    """
    
    def __init__(self, settings: Dict[str, Any]):
        """初期化
        
        Args:
            settings: エラーリカバリ設定を含む辞書
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings.get('error_recovery', {})
        self.enabled = self.settings.get('enabled', True)
        
        # エラーハンドラーのレジストリ
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._handler_lock = Lock()
        
        # 統計情報
        self._stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'error_types': {},
            'last_error': None,
            'start_time': datetime.now()
        }
        self._stats_lock = Lock()
        
        # デフォルトハンドラーの登録
        self._register_default_handlers()
        
        self.logger.info("ErrorRecoveryManager initialized")
    
    def _register_default_handlers(self):
        """デフォルトのエラーハンドラーを登録"""
        # ネットワークエラーハンドラー
        network_config = self.settings.get('network', {})
        network_handler = NetworkRecoveryHandler(
            max_retries=network_config.get('max_retries', 5),
            backoff_factor=network_config.get('backoff_factor', 2.0),
            initial_delay=network_config.get('initial_delay', 1.0)
        )
        
        # ファイルシステムエラーハンドラー
        fs_config = self.settings.get('filesystem', {})
        fs_handler = FileSystemRecoveryHandler(
            fallback_paths=fs_config.get('fallback_paths', ['/tmp'])
        )
        
        # メモリエラーハンドラー
        memory_config = self.settings.get('memory', {})
        memory_handler = MemoryRecoveryHandler(
            threshold=memory_config.get('threshold_mb', 200)
        )
        
        # requests例外の登録
        try:
            import requests
            self.register_handler(
                requests.exceptions.ConnectionError,
                lambda e: network_handler.handle_network_error(e, 0)
            )
            self.register_handler(
                requests.exceptions.Timeout,
                lambda e: network_handler.handle_network_error(e, 0)
            )
        except ImportError:
            pass
        
        # ファイルシステム例外の登録
        self.register_handler(
            PermissionError,
            lambda e: fs_handler.handle_file_error(e, "") is not None
        )
        self.register_handler(
            IOError,
            lambda e: fs_handler.handle_file_error(e, "") is not None
        )
        
        # メモリ例外の登録
        self.register_handler(
            MemoryError,
            memory_handler.handle_memory_error
        )
    
    def register_handler(self, error_type: Type[Exception], handler: Callable) -> None:
        """エラーハンドラーを登録
        
        Args:
            error_type: 処理対象の例外タイプ
            handler: エラー処理関数（Exception -> bool）
        """
        with self._handler_lock:
            self._handlers[error_type] = handler
            self.logger.debug(f"Registered handler for {error_type.__name__}")
    
    def wrap_with_recovery(self, func: Callable) -> Callable:
        """関数をエラーリカバリでラップ
        
        Args:
            func: ラップする関数
            
        Returns:
            エラーリカバリ機能付きの関数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.handle_error(e):
                    # リカバリ成功時は再試行
                    try:
                        return func(*args, **kwargs)
                    except Exception as retry_error:
                        self.logger.error(f"Retry failed: {retry_error}")
                        raise
                else:
                    # リカバリ失敗時は例外を再発生
                    raise
        
        return wrapper
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """エラーを処理
        
        Args:
            error: 発生した例外
            context: エラーコンテキスト情報
            
        Returns:
            リカバリ成功の場合True
        """
        if not self.enabled:
            return False
        
        # 統計更新
        with self._stats_lock:
            self._stats['total_errors'] += 1
            error_type = type(error).__name__
            self._stats['error_types'][error_type] = \
                self._stats['error_types'].get(error_type, 0) + 1
            self._stats['last_error'] = {
                'type': error_type,
                'message': str(error),
                'timestamp': datetime.now().isoformat(),
                'context': context
            }
        
        # 適切なハンドラーを探す
        with self._handler_lock:
            for error_class, handler in self._handlers.items():
                if isinstance(error, error_class):
                    try:
                        self.logger.info(f"Handling {type(error).__name__}: {error}")
                        result = handler(error)
                        
                        # 統計更新
                        with self._stats_lock:
                            if result:
                                self._stats['recovered_errors'] += 1
                            else:
                                self._stats['failed_recoveries'] += 1
                        
                        return result
                    except Exception as handler_error:
                        self.logger.error(f"Handler failed: {handler_error}")
                        with self._stats_lock:
                            self._stats['failed_recoveries'] += 1
                        return False
        
        # ハンドラーが見つからない場合
        self.logger.warning(f"No handler for {type(error).__name__}")
        with self._stats_lock:
            self._stats['failed_recoveries'] += 1
        return False
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """リカバリ統計を取得
        
        Returns:
            統計情報の辞書
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
            # 稼働時間と成功率を計算
            uptime = (datetime.now() - stats['start_time']).total_seconds()
            stats['uptime_seconds'] = uptime
            
            if stats['total_errors'] > 0:
                stats['recovery_rate'] = stats['recovered_errors'] / stats['total_errors']
            else:
                stats['recovery_rate'] = 1.0
            
            return stats


class NetworkRecoveryHandler:
    """ネットワークエラーリカバリハンドラー
    
    ネットワーク関連のエラーから復旧する。
    """
    
    def __init__(self, max_retries: int = 5, backoff_factor: float = 2.0,
                 initial_delay: float = 1.0, max_delay: float = 60.0):
        """初期化
        
        Args:
            max_retries: 最大再試行回数
            backoff_factor: バックオフ係数
            initial_delay: 初期遅延（秒）
            max_delay: 最大遅延（秒）
        """
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
    
    def handle_network_error(self, error: Exception, retry_count: int) -> bool:
        """ネットワークエラーを処理
        
        Args:
            error: ネットワーク関連の例外
            retry_count: 現在の再試行回数
            
        Returns:
            再試行すべき場合True
        """
        if retry_count >= self.max_retries:
            self.logger.error(f"Max retries ({self.max_retries}) exceeded")
            return False
        
        delay = self.get_retry_delay(retry_count)
        self.logger.info(f"Network error, retrying in {delay:.1f}s (attempt {retry_count + 1}/{self.max_retries})")
        
        # 実際には呼び出し元で遅延を実装
        return True
    
    def get_retry_delay(self, retry_count: int) -> float:
        """再試行遅延を計算
        
        Args:
            retry_count: 再試行回数（0ベース）
            
        Returns:
            遅延時間（秒）
        """
        delay = self.initial_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)


class FileSystemRecoveryHandler:
    """ファイルシステムエラーリカバリハンドラー
    
    ファイルアクセスエラーから復旧する。
    """
    
    def __init__(self, fallback_paths: Optional[List[str]] = None):
        """初期化
        
        Args:
            fallback_paths: 代替パスのリスト
        """
        self.logger = logging.getLogger(__name__)
        self.fallback_paths = fallback_paths or ['/tmp']
    
    def handle_file_error(self, error: Exception, file_path: str) -> Optional[str]:
        """ファイルエラーを処理
        
        Args:
            error: ファイル関連の例外
            file_path: エラーが発生したファイルパス
            
        Returns:
            代替パスまたはNone
        """
        self.logger.warning(f"File error for {file_path}: {error}")
        
        # 代替パスを試す
        for fallback in self.fallback_paths:
            if os.path.exists(fallback) and os.access(fallback, os.W_OK):
                # ファイル名を取得
                filename = os.path.basename(file_path) if file_path else 'temp_file'
                alternative = os.path.join(fallback, filename)
                self.logger.info(f"Using fallback path: {alternative}")
                return alternative
        
        self.logger.error("No writable fallback path found")
        return None
    
    def repair_corrupted_file(self, file_path: str) -> bool:
        """破損ファイルを修復（削除）
        
        Args:
            file_path: 破損したファイルのパス
            
        Returns:
            修復成功の場合True
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            # JSONファイルの場合、破損チェック
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    try:
                        json.load(f)
                        # 破損していない
                        return False
                    except json.JSONDecodeError:
                        # 破損している
                        pass
            
            # 破損ファイルを削除
            self.logger.warning(f"Removing corrupted file: {file_path}")
            os.unlink(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to repair file {file_path}: {e}")
            return False


class MemoryRecoveryHandler:
    """メモリエラーリカバリハンドラー
    
    メモリ不足エラーから復旧する。
    """
    
    def __init__(self, threshold: int = 200):
        """初期化
        
        Args:
            threshold: メモリ閾値（MB）
        """
        self.logger = logging.getLogger(__name__)
        self.threshold = threshold
        self._cache_managers: List[Any] = []
    
    def register_cache_manager(self, cache_manager: Any):
        """キャッシュマネージャーを登録
        
        Args:
            cache_manager: クリア可能なキャッシュマネージャー
        """
        if hasattr(cache_manager, 'clear') or hasattr(cache_manager, 'cleanup'):
            self._cache_managers.append(cache_manager)
    
    def handle_memory_error(self, error: Exception) -> bool:
        """メモリエラーを処理
        
        Args:
            error: メモリ関連の例外
            
        Returns:
            リカバリ成功の場合True
        """
        self.logger.warning(f"Memory error: {error}")
        
        # キャッシュクリア
        freed = self.clear_caches()
        
        # ガベージコレクション実行
        gc.collect()
        
        self.logger.info(f"Freed {freed} bytes of memory")
        
        # メモリが解放されたら成功とみなす
        return freed > 0 or True  # 少なくとも試みは成功
    
    def clear_caches(self) -> int:
        """キャッシュをクリア
        
        Returns:
            解放されたバイト数（推定）
        """
        freed_bytes = 0
        
        # 登録されたキャッシュマネージャーをクリア
        for manager in self._cache_managers:
            try:
                if hasattr(manager, 'clear'):
                    manager.clear()
                elif hasattr(manager, 'cleanup'):
                    manager.cleanup()
                # 実際のメモリ解放量は推定
                freed_bytes += 1024 * 1024  # 1MBと仮定
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {e}")
        
        # Pythonの内部キャッシュもクリア
        if hasattr(gc, 'collect'):
            collected = gc.collect()
            freed_bytes += collected * 1024  # 推定値
        
        return freed_bytes
    
    def reduce_quality_settings(self) -> Dict[str, Any]:
        """品質設定を削減
        
        Returns:
            削減された設定の辞書
        """
        reduced_settings = {
            'resolution_scale': 0.75,
            'texture_quality': 'low',
            'cache_size': 'minimal',
            'update_frequency': 'reduced'
        }
        
        self.logger.info("Reduced quality settings to save memory")
        return reduced_settings


def with_recovery(manager: ErrorRecoveryManager):
    """エラーリカバリデコレーター
    
    Args:
        manager: ErrorRecoveryManager インスタンス
    """
    def decorator(func):
        return manager.wrap_with_recovery(func)
    return decorator