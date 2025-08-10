#!/usr/bin/env python3
"""
Weather Provider デモンストレーション

Weather provider abstractionの動作確認デモ
同期・非同期両方の取得方法を実演
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from typing import Dict, Any, Optional
from src.providers.weather_base import WeatherProvider, WeatherCache
from src.core.config_manager import ConfigManager


class MockWeatherProvider(WeatherProvider):
    """
    モック天気プロバイダー
    
    デモ用のサンプル実装
    """
    
    def __init__(self, config: Any):
        """初期化"""
        super().__init__(config)
        self.call_count = 0
    
    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """
        APIからデータ取得のモック
        
        Returns:
            モックAPIレスポンス
        """
        self.call_count += 1
        print(f"  [API] 天気データを取得中... (呼び出し回数: {self.call_count})")
        
        # APIアクセスをシミュレート（1秒待機）
        time.sleep(1)
        
        # モックレスポンスを返す
        return {
            "current": {
                "temperature": 22,
                "condition": "partly_cloudy",
                "humidity": 65,
                "wind_speed": 5
            },
            "daily": [
                {
                    "date": "2024-01-15",
                    "temp_min": 8,
                    "temp_max": 18,
                    "condition": "sunny",
                    "precipitation_probability": 10
                },
                {
                    "date": "2024-01-16",
                    "temp_min": 10,
                    "temp_max": 20,
                    "condition": "partly_cloudy",
                    "precipitation_probability": 30
                },
                {
                    "date": "2024-01-17",
                    "temp_min": 12,
                    "temp_max": 17,
                    "condition": "rain",
                    "precipitation_probability": 80
                }
            ]
        }
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        レスポンスを標準フォーマットに変換
        
        Args:
            response: API応答
            
        Returns:
            標準フォーマットのデータ
        """
        # 標準フォーマットに変換
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
        
        # 日次予報を変換
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
        """
        天気状態を標準アイコン名にマップ
        
        Args:
            condition: プロバイダ固有の天気状態
            
        Returns:
            標準アイコン名
        """
        icon_map = {
            "clear": "sunny",
            "sunny": "sunny",
            "partly_cloudy": "partly_cloudy",
            "cloudy": "cloudy",
            "rain": "rain",
            "thunderstorm": "thunder",
            "snow": "snow",
            "fog": "fog"
        }
        
        return icon_map.get(condition, "cloudy")


def print_weather_data(data: Optional[Dict[str, Any]], title: str = "天気データ"):
    """
    天気データを整形して表示
    
    Args:
        data: 天気データ
        title: タイトル
    """
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)
    
    if not data:
        print("  データなし")
        return
    
    # 更新時刻
    from datetime import datetime
    update_time = datetime.fromtimestamp(data['updated'])
    print(f"  更新時刻: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 現在の天気
    if 'current' in data:
        current = data['current']
        print(f"\n  【現在の天気】")
        print(f"    気温: {current['temperature']}°C")
        print(f"    天気: {current['icon']}")
        print(f"    湿度: {current['humidity']}%")
        print(f"    風速: {current['wind_speed']}m/s")
    
    # 予報
    if 'forecasts' in data:
        print(f"\n  【3日間予報】")
        for forecast in data['forecasts']:
            print(f"    {forecast['date']}:")
            print(f"      天気: {forecast['icon']}")
            print(f"      気温: {forecast['tmin']}°C - {forecast['tmax']}°C")
            print(f"      降水確率: {forecast['pop']}%")
    
    print('=' * 60)


def demo_sync_fetch(provider: WeatherProvider):
    """
    同期取得のデモ
    
    Args:
        provider: 天気プロバイダー
    """
    print("\n■ 同期取得のデモ")
    print("-" * 40)
    
    # 1回目の取得（API呼び出し）
    print("\n1. 初回取得（APIから取得）:")
    start_time = time.time()
    data = provider.fetch()
    elapsed = time.time() - start_time
    print(f"  取得時間: {elapsed:.2f}秒")
    print_weather_data(data, "初回取得結果")
    
    # 2回目の取得（キャッシュから）
    print("\n2. 2回目の取得（キャッシュから）:")
    start_time = time.time()
    data = provider.fetch()
    elapsed = time.time() - start_time
    print(f"  取得時間: {elapsed:.2f}秒")
    print_weather_data(data, "キャッシュからの取得結果")
    
    # キャッシュクリア後の取得（レート制限のため61秒待機）
    print("\n3. キャッシュクリア後の取得:")
    provider.clear_cache()
    print("  キャッシュをクリアしました")
    print("  レート制限回避のため61秒待機...")
    time.sleep(61)  # レート制限をリセット
    start_time = time.time()
    data = provider.fetch()
    elapsed = time.time() - start_time
    print(f"  取得時間: {elapsed:.2f}秒")
    print_weather_data(data, "キャッシュクリア後の結果")


def demo_async_fetch(provider: WeatherProvider):
    """
    非同期取得のデモ
    
    Args:
        provider: 天気プロバイダー
    """
    print("\n■ 非同期取得のデモ")
    print("-" * 40)
    
    # キャッシュをクリアしてレート制限をリセット
    provider.clear_cache()
    print("  レート制限リセットのため61秒待機...")
    time.sleep(61)
    
    # コールバック関数
    def on_weather_fetched(data: Optional[Dict[str, Any]]):
        """天気データ取得完了時のコールバック"""
        print("\n  [コールバック] 天気データ取得完了!")
        if data:
            print(f"    現在の気温: {data['current']['temperature']}°C")
            print(f"    現在の天気: {data['current']['icon']}")
    
    # 非同期取得開始
    print("\n1. 非同期取得を開始:")
    future = provider.fetch_async(callback=on_weather_fetched)
    print("  非同期取得を開始しました（バックグラウンドで処理中）")
    
    # 他の処理を実行
    print("\n2. 他の処理を実行中...")
    for i in range(3):
        print(f"  処理 {i+1}/3 を実行中...")
        time.sleep(0.5)
    
    # 結果を待機
    print("\n3. 結果を待機:")
    result = future.result(timeout=5)  # 最大5秒待機
    print_weather_data(result, "非同期取得の結果")
    
    # 複数の非同期取得（キャッシュから取得するため高速）
    print("\n4. 複数の非同期取得（キャッシュ利用）:")
    
    futures = []
    for i in range(3):
        print(f"  非同期リクエスト {i+1} を開始")
        future = provider.fetch_async()
        futures.append(future)
        time.sleep(0.1)  # 少し間隔を空ける
    
    print("\n  全ての結果を待機中...")
    for i, future in enumerate(futures):
        result = future.result()
        if result:
            print(f"  リクエスト {i+1} 完了: 気温 {result['current']['temperature']}°C")
        else:
            print(f"  リクエスト {i+1} 完了: データなし")


def demo_cache_expiration(provider: WeatherProvider):
    """
    キャッシュ有効期限のデモ
    
    Args:
        provider: 天気プロバイダー
    """
    print("\n■ キャッシュ有効期限のデモ")
    print("-" * 40)
    
    # レート制限リセット
    print("  レート制限リセットのため61秒待機...")
    time.sleep(61)
    
    # 短い有効期限でキャッシュを再作成
    short_cache = WeatherCache(cache_dir="./cache_test", duration=2)  # 2秒で期限切れ
    provider.cache = short_cache
    provider._last_fetch_time = 0  # レート制限リセット
    
    # データ取得
    print("\n1. データを取得してキャッシュに保存:")
    data = provider.fetch()
    if data:
        print(f"  取得成功: 気温 {data['current']['temperature']}°C")
    else:
        print("  取得失敗")
    
    # すぐに再取得（キャッシュから）
    print("\n2. すぐに再取得（キャッシュ有効）:")
    data = provider.fetch()
    if data:
        print(f"  キャッシュから取得: 気温 {data['current']['temperature']}°C")
    
    # 3秒待機
    print("\n3. 3秒待機...")
    time.sleep(3)
    
    # 期限切れ後の取得（レート制限のため61秒待機）
    print("\n4. キャッシュ期限切れ後の取得:")
    print("  レート制限回避のため61秒待機...")
    time.sleep(61)
    provider._last_fetch_time = 0  # レート制限リセット
    data = provider.fetch()
    if data:
        print(f"  新規取得: 気温 {data['current']['temperature']}°C")
    else:
        print("  取得失敗")
    
    # クリーンアップ
    import shutil
    shutil.rmtree("./cache_test", ignore_errors=True)


def main():
    """メイン処理"""
    print("=" * 60)
    print(" Weather Provider Abstraction デモ")
    print("=" * 60)
    
    # 設定を作成
    config = ConfigManager()
    
    # モックプロバイダーを作成
    provider = MockWeatherProvider(config)
    
    # 各種デモを実行
    demo_sync_fetch(provider)
    demo_async_fetch(provider)
    demo_cache_expiration(provider)
    
    print("\n" + "=" * 60)
    print(" デモ完了")
    print("=" * 60)
    print("\n主な機能:")
    print("  ✓ 同期/非同期の天気データ取得")
    print("  ✓ キャッシュによる高速化")
    print("  ✓ キャッシュ有効期限管理")
    print("  ✓ レート制限")
    print("  ✓ 標準データフォーマット")
    print("  ✓ エラーハンドリング")


if __name__ == "__main__":
    main()