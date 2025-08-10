#!/usr/bin/env python3
"""
Weather Provider クイックデモ

Weather provider abstractionの主要機能を短時間で確認
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from typing import Dict, Any, Optional
from src.providers.weather_base import WeatherProvider, WeatherCache
from src.core.config_manager import ConfigManager


class QuickMockProvider(WeatherProvider):
    """
    クイックデモ用モックプロバイダー
    
    レート制限を緩和した実装
    """
    
    def __init__(self, config: Any):
        """初期化"""
        super().__init__(config)
        self.call_count = 0
        self._min_fetch_interval = 1  # 1秒に短縮（デモ用）
    
    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """APIからデータ取得のモック"""
        self.call_count += 1
        print(f"    → API呼び出し #{self.call_count}")
        
        # 短い待機時間（0.2秒）
        time.sleep(0.2)
        
        # モックレスポンス（呼び出し回数で変化）
        temp = 20 + self.call_count
        
        return {
            "current": {
                "temperature": temp,
                "condition": ["sunny", "partly_cloudy", "cloudy", "rain"][self.call_count % 4],
                "humidity": 60 + (self.call_count * 5) % 30,
                "wind_speed": 3 + self.call_count
            },
            "daily": [
                {
                    "date": f"2024-01-{15+i}",
                    "temp_min": 5 + i,
                    "temp_max": 15 + i,
                    "condition": ["sunny", "cloudy", "rain"][i % 3],
                    "precipitation_probability": i * 30
                }
                for i in range(3)
            ]
        }
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """レスポンスを標準フォーマットに変換"""
        parsed = {
            "updated": int(time.time()),
            "location": self.location,
            "current": {
                "temperature": response["current"]["temperature"],
                "icon": self._map_icon(response["current"]["condition"]),
                "humidity": response["current"]["humidity"],
                "wind_speed": response["current"]["wind_speed"]
            },
            "forecasts": []
        }
        
        for day in response["daily"]:
            parsed["forecasts"].append({
                "date": day["date"],
                "icon": self._map_icon(day["condition"]),
                "tmin": day["temp_min"],
                "tmax": day["temp_max"],
                "pop": day.get("precipitation_probability", 0)
            })
        
        return parsed
    
    def _map_icon(self, condition: str) -> str:
        """天気状態を標準アイコン名にマップ"""
        icon_map = {
            "sunny": "sunny",
            "partly_cloudy": "partly_cloudy",
            "cloudy": "cloudy",
            "rain": "rain",
            "thunderstorm": "thunder",
            "snow": "snow",
            "fog": "fog"
        }
        return icon_map.get(condition, "cloudy")


def print_summary(data: Optional[Dict[str, Any]]):
    """
    天気データの概要を1行で表示
    
    Args:
        data: 天気データ
    """
    if not data:
        print("    ✗ データなし")
        return
    
    current = data.get('current', {})
    temp = current.get('temperature', '?')
    icon = current.get('icon', '?')
    humidity = current.get('humidity', '?')
    
    from datetime import datetime
    update_time = datetime.fromtimestamp(data['updated']).strftime('%H:%M:%S')
    
    print(f"    ✓ {temp}°C, {icon}, 湿度{humidity}% (更新: {update_time})")


def main():
    """メイン処理"""
    print("=" * 60)
    print(" Weather Provider クイックデモ")
    print("=" * 60)
    
    # 設定とプロバイダーの初期化
    config = ConfigManager()
    provider = QuickMockProvider(config)
    
    # 1. 基本的な取得とキャッシュ
    print("\n【1. 基本的な取得とキャッシュ】")
    print("-" * 40)
    
    print("1回目: APIから取得")
    data1 = provider.fetch()
    print_summary(data1)
    
    print("\n2回目: キャッシュから取得（高速）")
    start = time.time()
    data2 = provider.fetch()
    elapsed = time.time() - start
    print_summary(data2)
    print(f"    処理時間: {elapsed:.3f}秒")
    
    # 2. キャッシュクリア
    print("\n【2. キャッシュ管理】")
    print("-" * 40)
    
    print("キャッシュをクリア")
    provider.clear_cache()
    
    print("レート制限待機（1秒）...")
    time.sleep(1.5)
    
    print("3回目: 再度APIから取得")
    data3 = provider.fetch()
    print_summary(data3)
    
    # 3. 非同期取得
    print("\n【3. 非同期取得】")
    print("-" * 40)
    
    print("キャッシュクリア & レート制限リセット")
    provider.clear_cache()
    time.sleep(1.5)
    
    # コールバック付き非同期取得
    callback_called = [False]
    def callback(result):
        callback_called[0] = True
        print("  → コールバック実行完了")
    
    print("非同期取得開始（コールバック付き）")
    future = provider.fetch_async(callback=callback)
    
    print("他の処理を実行中...")
    for i in range(3):
        print(f"  処理 {i+1}/3")
        time.sleep(0.1)
    
    print("結果を待機...")
    result = future.result()
    print_summary(result)
    print(f"  コールバック呼び出し: {callback_called[0]}")
    
    # 4. 短命キャッシュのデモ
    print("\n【4. キャッシュ有効期限】")
    print("-" * 40)
    
    # 1秒の短命キャッシュを作成
    short_cache = WeatherCache(cache_dir="./cache_demo", duration=1)
    provider.cache = short_cache
    provider._last_fetch_time = 0
    
    print("短命キャッシュ（1秒）でデータ取得")
    data4 = provider.fetch()
    print_summary(data4)
    
    print("\n0.5秒後: まだ有効")
    time.sleep(0.5)
    data5 = provider.fetch()
    print_summary(data5)
    print(f"    同じデータ: {data4['updated'] == data5['updated']}")
    
    print("\n1.5秒後: 期限切れ")
    time.sleep(1)
    provider._last_fetch_time = 0  # レート制限リセット
    data6 = provider.fetch()
    print_summary(data6)
    print(f"    新しいデータ: {data5['updated'] != data6['updated']}")
    
    # 5. バリデーション
    print("\n【5. データバリデーション】")
    print("-" * 40)
    
    # 正常なデータ
    valid_data = {
        "updated": int(time.time()),
        "forecasts": [
            {"date": "2024-01-15", "icon": "sunny", "tmin": 5, "tmax": 15}
        ]
    }
    print(f"正常なデータ: {provider.validate_response(valid_data)}")
    
    # 不正なデータ（forecastsなし）
    invalid_data = {"updated": int(time.time())}
    print(f"不正なデータ（forecastsなし）: {provider.validate_response(invalid_data)}")
    
    # 不正なデータ（必須フィールド不足）
    invalid_data2 = {
        "updated": int(time.time()),
        "forecasts": [{"date": "2024-01-15"}]  # icon, tmin, tmaxが不足
    }
    print(f"不正なデータ（フィールド不足）: {provider.validate_response(invalid_data2)}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree("./cache_demo", ignore_errors=True)
    
    # サマリー
    print("\n" + "=" * 60)
    print(" デモ完了")
    print("=" * 60)
    print(f"  総API呼び出し回数: {provider.call_count}")
    print("\n確認された機能:")
    print("  ✓ 同期/非同期取得")
    print("  ✓ キャッシュによる高速化")
    print("  ✓ キャッシュ有効期限")
    print("  ✓ レート制限")
    print("  ✓ データバリデーション")
    print("  ✓ コールバック機能")


if __name__ == "__main__":
    main()