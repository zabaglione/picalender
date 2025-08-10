#!/usr/bin/env python3
"""
TASK-303: 天気キャッシュシステム実装 - テストコード（Red Phase）

WeatherCacheクラスのテストスイート。
Priority 1の15個のテストケースを実装。
"""

import json
import os
import tempfile
import time
import shutil
import unittest
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any
import threading

# まだ実装されていないがテスト対象のクラス
try:
    from src.weather.cache.weather_cache import WeatherCache
    from src.weather.cache.cache_key import generate_cache_key
    from src.weather.cache.exceptions import (
        CacheError, CacheReadError, CacheWriteError, CacheInvalidError
    )
except ImportError:
    # Red Phaseではクラスが存在しないのでダミー定義
    class WeatherCache:
        def __init__(self, settings):
            pass
        
        def get(self, key):
            return None
        
        def set(self, key, data):
            return False
        
        def get_or_fetch(self, key, fetcher):
            return {}
        
        def invalidate(self, key=None):
            return 0
        
        def cleanup(self):
            return 0
    
    def generate_cache_key(provider, location):
        return ""
    
    class CacheError(Exception):
        pass
    
    class CacheReadError(CacheError):
        pass
    
    class CacheWriteError(CacheError):
        pass
    
    class CacheInvalidError(CacheError):
        pass


class TestWeatherCache(unittest.TestCase):
    """天気キャッシュシステムのテストケース"""
    
    def setUp(self):
        """各テストの前処理"""
        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp(prefix="test_cache_")
        
        # テスト設定
        self.test_settings = {
            'weather': {
                'cache': {
                    'enabled': True,
                    'directory': self.test_dir,
                    'ttl': 1800,  # 30分
                    'max_size': 1048576,  # 1MB
                    'max_entries': 10,
                    'fallback_on_error': True,
                    'cleanup_interval': 3600
                }
            }
        }
        
        # テスト用天気データ
        self.test_weather_data = {
            "updated": 1705123200,
            "location": {
                "latitude": 35.681236,
                "longitude": 139.767125
            },
            "forecasts": [
                {
                    "date": "2025-01-11",
                    "icon": "sunny",
                    "temperature": {"min": 5, "max": 13},
                    "precipitation_probability": 30
                }
            ]
        }
    
    def tearDown(self):
        """各テスト後の後処理"""
        # テスト用ディレクトリを削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    # =================================================================
    # Test Category 1: 基本機能テスト
    # =================================================================
    
    def test_weather_cache_initialization(self):
        """Test Case 1.1: WeatherCache初期化"""
        # WeatherCacheが正しく初期化されることを確認
        cache = WeatherCache(self.test_settings)
        
        # インスタンスが作成されることを確認
        self.assertIsNotNone(cache)
        
        # キャッシュディレクトリが作成されることを確認
        self.assertTrue(os.path.exists(self.test_dir))
    
    def test_cache_set_operation(self):
        """Test Case 1.2: キャッシュ保存（set）"""
        cache = WeatherCache(self.test_settings)
        
        # データ保存
        key = "test_key"
        result = cache.set(key, self.test_weather_data)
        
        # 保存成功を確認
        self.assertTrue(result)
        
        # ファイルが作成されることを確認
        cache_file = os.path.join(self.test_dir, f"{key}.json")
        self.assertTrue(os.path.exists(cache_file))
    
    def test_cache_get_operation(self):
        """Test Case 1.3: キャッシュ取得（get）"""
        cache = WeatherCache(self.test_settings)
        
        # データ保存
        key = "test_key"
        cache.set(key, self.test_weather_data)
        
        # データ取得
        retrieved_data = cache.get(key)
        
        # データが一致することを確認
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data['location']['latitude'], 35.681236)
        self.assertEqual(len(retrieved_data['forecasts']), 1)
    
    # =================================================================
    # Test Category 2: 有効期限管理テスト
    # =================================================================
    
    def test_cache_within_ttl(self):
        """Test Case 2.1: 有効期限内のキャッシュ取得"""
        cache = WeatherCache(self.test_settings)
        
        # データ保存
        key = "ttl_test"
        cache.set(key, self.test_weather_data)
        
        # 即座に取得
        data = cache.get(key)
        
        # データが取得できることを確認
        self.assertIsNotNone(data)
        self.assertEqual(data['location']['latitude'], 35.681236)
    
    def test_cache_expired_ttl(self):
        """Test Case 2.2: 有効期限切れのキャッシュ"""
        # TTL=1秒の設定
        short_ttl_settings = self.test_settings.copy()
        short_ttl_settings['weather']['cache']['ttl'] = 1
        
        cache = WeatherCache(short_ttl_settings)
        
        # データ保存
        key = "expired_test"
        cache.set(key, self.test_weather_data)
        
        # 2秒待機
        time.sleep(2)
        
        # 期限切れでNoneが返ることを確認
        data = cache.get(key)
        self.assertIsNone(data)
    
    # =================================================================
    # Test Category 3: キャッシュキー生成テスト
    # =================================================================
    
    def test_cache_key_generation(self):
        """Test Case 3.1: 標準キー生成"""
        provider = "openmeteo"
        location = {
            "latitude": 35.681236,
            "longitude": 139.767125
        }
        
        # キー生成
        key = generate_cache_key(provider, location)
        
        # キー形式を確認
        self.assertIsInstance(key, str)
        self.assertIn(provider, key)
        self.assertIn("35.681", key)
        self.assertIn("139.767", key)
    
    # =================================================================
    # Test Category 4: LRU管理テスト
    # =================================================================
    
    def test_max_entries_limit(self):
        """Test Case 4.1: エントリ数制限"""
        # max_entries=3の設定
        limited_settings = self.test_settings.copy()
        limited_settings['weather']['cache']['max_entries'] = 3
        
        cache = WeatherCache(limited_settings)
        
        # 4つのエントリを保存
        for i in range(4):
            key = f"entry_{i}"
            cache.set(key, self.test_weather_data)
            time.sleep(0.1)  # 順序を確実にするため
        
        # 最古のエントリが削除されていることを確認
        oldest_data = cache.get("entry_0")
        self.assertIsNone(oldest_data)
        
        # 新しい3つは残っていることを確認
        for i in range(1, 4):
            data = cache.get(f"entry_{i}")
            self.assertIsNotNone(data)
    
    # =================================================================
    # Test Category 5: get_or_fetchテスト
    # =================================================================
    
    def test_get_or_fetch_cache_hit(self):
        """Test Case 5.1: キャッシュヒット時"""
        cache = WeatherCache(self.test_settings)
        
        # データを事前に保存
        key = "cached_key"
        cache.set(key, self.test_weather_data)
        
        # fetcherモック（呼ばれないはず）
        fetcher = Mock(return_value={"new": "data"})
        
        # get_or_fetch実行
        result = cache.get_or_fetch(key, fetcher)
        
        # fetcherが呼ばれていないことを確認
        fetcher.assert_not_called()
        
        # キャッシュデータが返されることを確認
        self.assertEqual(result['location']['latitude'], 35.681236)
    
    def test_get_or_fetch_cache_miss(self):
        """Test Case 5.2: キャッシュミス時"""
        cache = WeatherCache(self.test_settings)
        
        # fetcherモック
        new_data = {"new": "fetched_data"}
        fetcher = Mock(return_value=new_data)
        
        # get_or_fetch実行（キャッシュなし）
        key = "missing_key"
        result = cache.get_or_fetch(key, fetcher)
        
        # fetcherが呼ばれたことを確認
        fetcher.assert_called_once()
        
        # 新規データが返されることを確認
        self.assertEqual(result, new_data)
        
        # データがキャッシュされていることを確認
        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached, new_data)
    
    # =================================================================
    # Test Category 6: クリーンアップテスト
    # =================================================================
    
    def test_cleanup_expired_entries(self):
        """Test Case 6.1: 期限切れエントリ削除"""
        # 短いTTLで設定
        short_ttl_settings = self.test_settings.copy()
        short_ttl_settings['weather']['cache']['ttl'] = 1
        
        cache = WeatherCache(short_ttl_settings)
        
        # 複数エントリ保存
        cache.set("old_1", self.test_weather_data)
        cache.set("old_2", self.test_weather_data)
        
        # 期限切れにする
        time.sleep(2)
        
        # 新しいエントリも追加
        cache.set("new_1", self.test_weather_data)
        
        # cleanup実行
        deleted_count = cache.cleanup()
        
        # 期限切れ2つが削除されることを確認
        self.assertEqual(deleted_count, 2)
        
        # 新しいエントリは残っていることを確認
        self.assertIsNotNone(cache.get("new_1"))
        self.assertIsNone(cache.get("old_1"))
        self.assertIsNone(cache.get("old_2"))
    
    def test_invalidate_specific_key(self):
        """Test Case 6.2: 特定キーの無効化"""
        cache = WeatherCache(self.test_settings)
        
        # 複数エントリ保存
        cache.set("keep_1", self.test_weather_data)
        cache.set("delete_me", self.test_weather_data)
        cache.set("keep_2", self.test_weather_data)
        
        # 特定キーを無効化
        deleted = cache.invalidate("delete_me")
        
        # 1つ削除されたことを確認
        self.assertEqual(deleted, 1)
        
        # 指定キーが削除されていることを確認
        self.assertIsNone(cache.get("delete_me"))
        
        # 他のキーは残っていることを確認
        self.assertIsNotNone(cache.get("keep_1"))
        self.assertIsNotNone(cache.get("keep_2"))
    
    # =================================================================
    # Test Category 7: エラーハンドリングテスト
    # =================================================================
    
    def test_corrupted_cache_file_handling(self):
        """Test Case 7.2: ファイル破損時"""
        cache = WeatherCache(self.test_settings)
        
        # 破損ファイルを作成
        key = "corrupted"
        cache_file = os.path.join(self.test_dir, f"{key}.json")
        with open(cache_file, 'w') as f:
            f.write("{ invalid json }")
        
        # ファイルが存在することを確認
        self.assertTrue(os.path.exists(cache_file))
        
        # get実行
        data = cache.get(key)
        
        # Noneが返されることを確認
        self.assertIsNone(data)
        
        # 破損ファイルが削除されていることを確認
        # 少し待機（ファイルシステムの遅延を考慮）
        import time
        time.sleep(0.1)
        self.assertFalse(os.path.exists(cache_file), f"File should be deleted: {cache_file}")
    
    # =================================================================
    # Test Category 8: 並行アクセステスト
    # =================================================================
    
    def test_concurrent_read_access(self):
        """Test Case 8.1: 同時読み取り"""
        cache = WeatherCache(self.test_settings)
        
        # データを事前保存
        key = "concurrent_read"
        cache.set(key, self.test_weather_data)
        
        # 結果格納用
        results = []
        errors = []
        
        def read_cache():
            try:
                data = cache.get(key)
                results.append(data is not None)
            except Exception as e:
                errors.append(str(e))
        
        # 10スレッドで同時読み取り
        threads = []
        for _ in range(10):
            t = threading.Thread(target=read_cache)
            threads.append(t)
            t.start()
        
        # 全スレッド完了待ち
        for t in threads:
            t.join()
        
        # エラーがないことを確認
        self.assertEqual(len(errors), 0)
        
        # 全て成功していることを確認
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
    
    # =================================================================
    # Test Category 9: パフォーマンステスト
    # =================================================================
    
    def test_cache_hit_performance(self):
        """Test Case 9.1: キャッシュヒット速度"""
        cache = WeatherCache(self.test_settings)
        
        # データ保存
        key = "perf_test"
        cache.set(key, self.test_weather_data)
        
        # 時間計測
        start_time = time.time()
        data = cache.get(key)
        elapsed_time = time.time() - start_time
        
        # データ取得成功を確認
        self.assertIsNotNone(data)
        
        # 10ms以内であることを確認（実際のRed Phaseでは失敗する可能性あり）
        self.assertLess(elapsed_time, 0.01)  # 10ms


if __name__ == '__main__':
    unittest.main()