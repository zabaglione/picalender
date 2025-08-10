"""
天気情報プロバイダーの基底クラス

全ての天気プロバイダーが実装すべきインターフェースを定義
"""

import os
import json
import time
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import threading
import concurrent.futures

logger = logging.getLogger(__name__)


class WeatherCache:
    """天気データのキャッシュ管理"""
    
    def __init__(self, cache_dir: str = "./cache", duration: int = 1800):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            duration: キャッシュ有効期間（秒）
        """
        self.cache_dir = cache_dir
        self.duration = duration
        self._lock = threading.Lock()
        
        # キャッシュディレクトリを作成
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """キャッシュファイルパスを取得"""
        # キーをハッシュ化してファイル名にする
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"weather_{hash_key}.json")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        キャッシュからデータを取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュデータ、期限切れまたは存在しない場合はNone
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            if not os.path.exists(cache_path):
                return None
            
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 有効期限チェック
                cached_time = cache_data.get('cached_at', 0)
                if time.time() - cached_time > self.duration:
                    # 期限切れ
                    os.remove(cache_path)
                    return None
                
                return cache_data.get('data')
                
            except Exception as e:
                logger.error(f"Cache read error: {e}")
                return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        キャッシュにデータを保存
        
        Args:
            key: キャッシュキー
            data: 保存するデータ
        """
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'cached_at': time.time(),
            'data': data
        }
        
        with self._lock:
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                logger.error(f"Cache write error: {e}")
    
    def invalidate(self, key: str) -> None:
        """
        特定のキャッシュを無効化
        
        Args:
            key: キャッシュキー
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception as e:
                    logger.error(f"Cache invalidation error: {e}")
    
    def clear_all(self) -> None:
        """全てのキャッシュをクリア"""
        with self._lock:
            try:
                for file in Path(self.cache_dir).glob("weather_*.json"):
                    file.unlink()
            except Exception as e:
                logger.error(f"Cache clear error: {e}")


class WeatherProvider(ABC):
    """
    天気情報プロバイダーの基底クラス
    
    全ての天気プロバイダーはこのクラスを継承して実装する
    """
    
    # 標準アイコン名
    STANDARD_ICONS = {
        'sunny', 'cloudy', 'rain', 'thunder', 'fog', 'snow', 'partly_cloudy'
    }
    
    def __init__(self, config: Any):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.timeout = config.get('weather.timeout', 10)
        self.location = {
            'lat': config.get('weather.location.lat', 35.681236),
            'lon': config.get('weather.location.lon', 139.767125)
        }
        
        # キャッシュの初期化
        cache_dir = config.get('weather.cache_dir', './cache')
        cache_duration = config.get('weather.cache_duration', 1800)
        self.cache = WeatherCache(cache_dir, cache_duration)
        
        # レート制限用
        self._last_fetch_time = 0
        self._min_fetch_interval = 60  # 最小60秒間隔
    
    def fetch(self) -> Optional[Dict[str, Any]]:
        """
        天気データを取得（同期版）
        
        Returns:
            標準フォーマットの天気データ、失敗時はNone
        """
        # キャッシュキーを生成
        cache_key = f"{self.__class__.__name__}_{self.location['lat']}_{self.location['lon']}"
        
        # キャッシュから取得を試みる
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info("Using cached weather data")
            return cached_data
        
        # レート制限チェック
        current_time = time.time()
        if current_time - self._last_fetch_time < self._min_fetch_interval:
            logger.warning("Rate limit: too frequent requests")
            return None
        
        try:
            # APIからデータを取得
            logger.info(f"Fetching weather from {self.__class__.__name__}")
            self._last_fetch_time = current_time
            
            raw_response = self._fetch_from_api()
            if not raw_response:
                return None
            
            # レスポンスを標準フォーマットに変換
            parsed_data = self._parse_response(raw_response)
            
            # バリデーション
            if self.validate_response(parsed_data):
                # キャッシュに保存
                self.cache.set(cache_key, parsed_data)
                return parsed_data
            else:
                logger.error("Invalid response format")
                return None
                
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return None
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        レスポンスの妥当性を検証
        
        Args:
            response: 検証するレスポンス
            
        Returns:
            妥当な場合True
        """
        if not response:
            return False
        
        # 必須フィールドの確認
        required_fields = ['updated', 'forecasts']
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field: {field}")
                return False
        
        # forecastsが配列であることを確認
        if not isinstance(response['forecasts'], list):
            logger.error("forecasts must be a list")
            return False
        
        # 各予報の必須フィールドを確認
        for forecast in response['forecasts']:
            required_forecast_fields = ['date', 'icon', 'tmin', 'tmax']
            for field in required_forecast_fields:
                if field not in forecast:
                    logger.error(f"Missing forecast field: {field}")
                    return False
        
        return True
    
    @abstractmethod
    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """
        APIから生データを取得
        
        Returns:
            API応答の生データ
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        API応答を標準フォーマットに変換
        
        Args:
            response: API応答
            
        Returns:
            標準フォーマットのデータ
        """
        pass
    
    @abstractmethod
    def _map_icon(self, condition: str) -> str:
        """
        天気状態を標準アイコン名にマップ
        
        Args:
            condition: プロバイダ固有の天気状態
            
        Returns:
            標準アイコン名
        """
        pass
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        cache_key = f"{self.__class__.__name__}_{self.location['lat']}_{self.location['lon']}"
        self.cache.invalidate(cache_key)
    
    def fetch_async(self, callback=None) -> concurrent.futures.Future:
        """
        天気データを非同期で取得
        
        Args:
            callback: 完了時に呼ばれるコールバック関数（オプション）
            
        Returns:
            Future オブジェクト
        """
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.fetch)
        
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
        
        return future