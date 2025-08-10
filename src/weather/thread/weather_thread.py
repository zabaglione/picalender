#!/usr/bin/env python3
"""
天気データ取得スレッド管理クラス

バックグラウンドで定期的に天気データを取得・更新する。
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from ..providers.base import WeatherProvider
from ..cache.weather_cache import WeatherCache
from ..cache.cache_key import generate_cache_key
from .exceptions import (
    WeatherThreadError, ThreadStartError, ThreadStopError, UpdateError
)


class WeatherThread:
    """天気データ取得スレッド管理クラス
    
    バックグラウンドスレッドで定期的に天気データを取得し、
    キャッシュに保存する。
    """
    
    # スレッド状態
    STATE_STOPPED = "STOPPED"
    STATE_STARTING = "STARTING"
    STATE_RUNNING = "RUNNING"
    STATE_PAUSED = "PAUSED"
    STATE_STOPPING = "STOPPING"
    
    def __init__(self, provider: WeatherProvider, cache: WeatherCache, settings: Dict[str, Any]):
        """初期化
        
        Args:
            provider: 天気プロバイダ
            cache: キャッシュシステム
            settings: 設定辞書
        """
        self.logger = logging.getLogger(__name__)
        
        self.provider = provider
        self.cache = cache
        
        # スレッド設定
        thread_config = settings.get('weather', {}).get('thread', {})
        self.enabled = thread_config.get('enabled', True)
        self.update_interval = thread_config.get('update_interval', 1800)  # 30分
        self.retry_interval = thread_config.get('retry_interval', 60)  # 1分
        self.max_retries = thread_config.get('max_retries', 5)
        self.retry_backoff = thread_config.get('retry_backoff', 2.0)
        self.timeout = thread_config.get('timeout', 30)
        
        # コールバック（オプション）
        self.update_callback = thread_config.get('update_callback')
        self.error_callback = thread_config.get('error_callback')
        
        # 位置情報（providerから取得）
        self.location = getattr(provider, 'location', settings.get('weather', {}).get('location', {}))
        
        # スレッド管理
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._force_update_event = threading.Event()
        self._state = self.STATE_STOPPED
        self._state_lock = threading.RLock()
        
        # データと統計
        self._latest_data = None
        self._latest_data_lock = threading.RLock()
        
        self._stats = {
            'update_count': 0,
            'success_count': 0,
            'error_count': 0,
            'last_update': None,
            'last_error': None,
            'consecutive_errors': 0
        }
        self._stats_lock = threading.RLock()
        
        self.logger.info("WeatherThread initialized")
    
    def start(self) -> bool:
        """スレッド開始
        
        Returns:
            開始成功の場合True
        """
        with self._state_lock:
            if self._state != self.STATE_STOPPED:
                self.logger.warning(f"Cannot start: already in state {self._state}")
                return False
            
            try:
                self._state = self.STATE_STARTING
                
                # イベントをリセット
                self._stop_event.clear()
                self._pause_event.clear()
                self._force_update_event.clear()
                
                # スレッド作成・開始
                self._thread = threading.Thread(
                    target=self._thread_worker,
                    name="WeatherThread",
                    daemon=True
                )
                self._thread.start()
                
                # 起動待機（最大1秒）
                for i in range(10):
                    time.sleep(0.1)
                    if self._state == self.STATE_RUNNING:
                        break
                    self.logger.debug(f"Waiting for thread to start... attempt {i+1}/10, state={self._state}")
                
                if self._state == self.STATE_RUNNING:
                    self.logger.info("WeatherThread started successfully")
                    return True
                else:
                    raise ThreadStartError("Thread failed to reach RUNNING state")
                    
            except Exception as e:
                self.logger.error(f"Failed to start thread: {e}")
                self._state = self.STATE_STOPPED
                return False
    
    def stop(self, timeout: float = 5.0) -> bool:
        """スレッド停止
        
        Args:
            timeout: 停止待機タイムアウト（秒）
            
        Returns:
            正常停止の場合True
        """
        with self._state_lock:
            if self._state == self.STATE_STOPPED:
                return True
            
            if self._state not in [self.STATE_RUNNING, self.STATE_PAUSED]:
                self.logger.warning(f"Cannot stop: in state {self._state}")
                return False
            
            self._state = self.STATE_STOPPING
        
        # 停止要求
        self._stop_event.set()
        
        # スレッド終了待機
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            
            if self._thread.is_alive():
                self.logger.warning("Thread did not stop within timeout")
                return False
        
        with self._state_lock:
            self._state = self.STATE_STOPPED
        
        self.logger.info("WeatherThread stopped")
        return True
    
    def pause(self) -> None:
        """一時停止"""
        with self._state_lock:
            if self._state == self.STATE_RUNNING:
                self._pause_event.set()
                self._state = self.STATE_PAUSED
                self.logger.info("WeatherThread paused")
    
    def resume(self) -> None:
        """再開"""
        with self._state_lock:
            if self._state == self.STATE_PAUSED:
                self._pause_event.clear()
                self._state = self.STATE_RUNNING
                self.logger.info("WeatherThread resumed")
    
    def force_update(self) -> bool:
        """強制更新
        
        Returns:
            更新成功の場合True
        """
        if self._state in [self.STATE_RUNNING, self.STATE_PAUSED]:
            self._force_update_event.set()
            return True
        return False
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """最新データ取得
        
        Returns:
            最新の天気データまたはNone
        """
        with self._latest_data_lock:
            return self._latest_data
    
    def get_status(self) -> Dict[str, Any]:
        """ステータス取得
        
        Returns:
            スレッド状態情報
        """
        with self._state_lock:
            state = self._state
        
        with self._stats_lock:
            stats = self._stats.copy()
        
        return {
            'state': state,
            'is_alive': self._thread.is_alive() if self._thread else False,
            'enabled': self.enabled,
            'update_interval': self.update_interval,
            'statistics': stats
        }
    
    def is_alive(self) -> bool:
        """スレッドが生きているか確認
        
        Returns:
            生きている場合True
        """
        return self._thread and self._thread.is_alive()
    
    def _thread_worker(self):
        """スレッドワーカー（メインループ）"""
        self.logger.debug("Weather thread worker started")
        
        with self._state_lock:
            self._state = self.STATE_RUNNING
        
        retry_count = 0
        next_retry_interval = self.retry_interval
        
        while not self._stop_event.is_set():
            try:
                # 一時停止チェック
                if self._pause_event.is_set():
                    time.sleep(0.1)
                    continue
                
                # 強制更新または定期更新
                if self._force_update_event.is_set() or retry_count > 0:
                    self._force_update_event.clear()
                    wait_time = 0 if self._force_update_event.is_set() else min(next_retry_interval, 1)
                else:
                    wait_time = self.update_interval
                
                # 更新実行または待機
                if wait_time == 0 or self._wait_interruptible(wait_time):
                    # データ取得
                    self.logger.debug("Fetching weather data...")
                    data = self._fetch_weather_data()
                    
                    if data:
                        # 成功
                        self._save_to_cache(data)
                        self._update_latest_data(data)
                        self._notify_update(data)
                        self._update_statistics(success=True)
                        
                        # 再試行カウンタリセット
                        retry_count = 0
                        next_retry_interval = self.retry_interval
                    else:
                        # 失敗
                        raise UpdateError("Failed to fetch weather data")
                        
            except Exception as e:
                # エラー処理
                self.logger.error(f"Weather update error: {e}")
                self._handle_error(e)
                self._update_statistics(success=False, error=str(e))
                
                # 再試行戦略
                retry_count += 1
                if retry_count <= self.max_retries:
                    next_retry_interval = self.retry_interval * (self.retry_backoff ** (retry_count - 1))
                    self.logger.info(f"Retry {retry_count}/{self.max_retries} in {next_retry_interval:.1f}s")
                else:
                    # 最大再試行回数に達した
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded")
                    retry_count = 0
                    next_retry_interval = self.retry_interval
        
        self.logger.debug("Weather thread worker stopped")
    
    def _wait_interruptible(self, seconds: float) -> bool:
        """中断可能な待機
        
        Args:
            seconds: 待機時間（秒）
            
        Returns:
            中断された場合True
        """
        start_time = time.time()
        while time.time() - start_time < seconds:
            if self._stop_event.is_set():
                return False
            if self._force_update_event.is_set():
                return True
            time.sleep(0.1)
        return True
    
    def _fetch_weather_data(self) -> Optional[Dict[str, Any]]:
        """天気データ取得"""
        try:
            return self.provider.fetch()
        except Exception as e:
            self.logger.error(f"Provider fetch error: {e}")
            return None
    
    def _save_to_cache(self, data: Dict[str, Any]):
        """キャッシュに保存"""
        try:
            # キャッシュキー生成
            provider_name = self.provider.__class__.__name__.lower().replace('provider', '')
            key = generate_cache_key(provider_name, self.location)
            
            # キャッシュ保存
            self.cache.set(key, data)
            self.logger.debug(f"Weather data cached: {key}")
            
        except Exception as e:
            self.logger.error(f"Cache save error: {e}")
    
    def _update_latest_data(self, data: Dict[str, Any]):
        """最新データ更新"""
        with self._latest_data_lock:
            self._latest_data = data
    
    def _notify_update(self, data: Dict[str, Any]):
        """更新通知"""
        if self.update_callback:
            try:
                self.update_callback(data)
            except Exception as e:
                self.logger.error(f"Update callback error: {e}")
    
    def _handle_error(self, error: Exception):
        """エラー処理"""
        if self.error_callback:
            try:
                self.error_callback(error)
            except Exception as e:
                self.logger.error(f"Error callback error: {e}")
    
    def _update_statistics(self, success: bool, error: str = None):
        """統計更新"""
        with self._stats_lock:
            self._stats['update_count'] += 1
            
            if success:
                self._stats['success_count'] += 1
                self._stats['last_update'] = datetime.now().isoformat()
                self._stats['consecutive_errors'] = 0
            else:
                self._stats['error_count'] += 1
                self._stats['last_error'] = error
                self._stats['consecutive_errors'] += 1