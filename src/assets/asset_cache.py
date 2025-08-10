"""
アセットキャッシュ管理
"""

from typing import Any, Dict, Optional
from collections import OrderedDict
import time


class AssetCache:
    """LRUアルゴリズムによるアセットキャッシュ"""
    
    def __init__(self, max_size: int = 100):
        """
        初期化
        
        Args:
            max_size: 最大キャッシュサイズ
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされた値、存在しない場合はNone
        """
        if key in self.cache:
            # LRU: 最後に移動
            self.cache.move_to_end(key)
            self.access_times[key] = time.time()
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """
        キャッシュに追加
        
        Args:
            key: キャッシュキー
            value: 値
        """
        # 既存のキーの場合は更新
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            # サイズ制限チェック
            if len(self.cache) >= self.max_size:
                # 最も古いアイテムを削除（LRU）
                oldest_key = next(iter(self.cache))
                self.remove(oldest_key)
            
            self.cache[key] = value
        
        self.access_times[key] = time.time()
    
    def remove(self, key: str) -> None:
        """
        キャッシュから削除
        
        Args:
            key: キャッシュキー
        """
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def clear(self) -> None:
        """キャッシュを全クリア"""
        self.cache.clear()
        self.access_times.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        total_accesses = self.hits + self.misses
        hit_rate = self.hits / total_accesses if total_accesses > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_accesses': total_accesses
        }
    
    def evict_oldest(self, count: int = 1) -> None:
        """
        最も古いアイテムを削除
        
        Args:
            count: 削除する数
        """
        for _ in range(min(count, len(self.cache))):
            if self.cache:
                oldest_key = next(iter(self.cache))
                self.remove(oldest_key)