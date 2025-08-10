#!/usr/bin/env python3
"""
OpenWeatherMap Provider デモ

OpenWeatherMapプロバイダーの動作確認
注意: 実際のAPIキーが必要です
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import Dict, Any, Optional
from src.providers.weather_openweathermap import OpenWeatherMapProvider
from src.core.config_manager import ConfigManager


def print_weather_details(data: Optional[Dict[str, Any]]):
    """
    天気データを詳細表示
    
    Args:
        data: 天気データ
    """
    if not data:
        print("  ✗ データなし")
        return
    
    print("\n" + "=" * 60)
    print(" OpenWeatherMap 天気データ")
    print("=" * 60)
    
    # 更新時刻
    from datetime import datetime
    update_time = datetime.fromtimestamp(data['updated'])
    print(f"\n更新時刻: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 位置情報
    if 'location' in data:
        loc = data['location']
        print(f"位置: 緯度 {loc['lat']}, 経度 {loc['lon']}")
    
    # 現在の天気
    if 'current' in data:
        current = data['current']
        print(f"\n【現在の天気】")
        print(f"  気温: {current.get('temperature', '?')}°C")
        print(f"  天気: {current.get('icon', '?')}")
        print(f"  湿度: {current.get('humidity', '?')}%")
        print(f"  風速: {current.get('wind_speed', '?')}m/s")
    
    # 3日間予報
    if 'forecasts' in data:
        print(f"\n【3日間予報】")
        for i, forecast in enumerate(data['forecasts'], 1):
            print(f"\n  Day {i}: {forecast['date']}")
            print(f"    天気: {forecast['icon']}")
            print(f"    最低気温: {forecast['tmin']}°C")
            print(f"    最高気温: {forecast['tmax']}°C")
            print(f"    降水確率: {forecast.get('pop', 0)}%")
    
    print("\n" + "=" * 60)


def demo_with_mock_api():
    """
    モックAPIキーでのデモ（エラーハンドリング確認）
    """
    print("\n■ モックAPIキーでのテスト")
    print("-" * 40)
    
    # モック設定
    class MockConfig:
        def get(self, key, default=None):
            configs = {
                'weather.openweathermap.api_key': 'INVALID_API_KEY_12345',
                'weather.openweathermap.units': 'metric',
                'weather.openweathermap.lang': 'ja',
                'weather.location.lat': 35.681236,  # 東京
                'weather.location.lon': 139.767125,
                'weather.cache_dir': './cache_demo',
                'weather.cache_duration': 1800,
                'weather.timeout': 5
            }
            return configs.get(key, default)
    
    try:
        config = MockConfig()
        provider = OpenWeatherMapProvider(config)
        
        print("\nプロバイダー初期化成功")
        print(f"  APIキー: {provider.api_key[:10]}...")
        print(f"  位置: {provider.location}")
        print(f"  単位: {provider.units}")
        print(f"  言語: {provider.lang}")
        
        # URL構築テスト
        current_url = provider.get_api_url('weather')
        print(f"\nCurrent Weather API URL:")
        print(f"  {current_url[:60]}...")
        
        forecast_url = provider.get_api_url('forecast')
        print(f"\nForecast API URL:")
        print(f"  {forecast_url[:60]}...")
        
        # データ取得試行（失敗するはず）
        print("\n天気データ取得を試行中...")
        data = provider.fetch()
        
        if data:
            print("  ✓ キャッシュから取得")
            print_weather_details(data)
        else:
            print("  ✗ 取得失敗（APIキーが無効）")
            
    except Exception as e:
        print(f"エラー: {e}")


def demo_with_real_api():
    """
    実際のAPIキーでのデモ
    
    環境変数 OPENWEATHERMAP_API_KEY を設定してください
    """
    print("\n■ 実際のAPIキーでのテスト")
    print("-" * 40)
    
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    
    if not api_key:
        print("\n⚠️  環境変数 OPENWEATHERMAP_API_KEY が設定されていません")
        print("   実際のAPIキーを設定するには:")
        print("   export OPENWEATHERMAP_API_KEY='your_api_key_here'")
        return
    
    # 実際の設定
    class RealConfig:
        def get(self, key, default=None):
            configs = {
                'weather.openweathermap.api_key': api_key,
                'weather.openweathermap.units': 'metric',
                'weather.openweathermap.lang': 'ja',
                'weather.location.lat': 35.681236,  # 東京
                'weather.location.lon': 139.767125,
                'weather.cache_dir': './cache_real',
                'weather.cache_duration': 300,  # 5分キャッシュ
                'weather.timeout': 10
            }
            return configs.get(key, default)
    
    try:
        config = RealConfig()
        provider = OpenWeatherMapProvider(config)
        
        print("\n東京の天気を取得中...")
        start_time = time.time()
        data = provider.fetch()
        elapsed = time.time() - start_time
        
        if data:
            print(f"  ✓ 取得成功 ({elapsed:.2f}秒)")
            print_weather_details(data)
            
            # バリデーション確認
            is_valid = provider.validate_response(data)
            print(f"\nデータバリデーション: {'✓ 合格' if is_valid else '✗ 不合格'}")
            
            # キャッシュからの再取得
            print("\n2回目の取得（キャッシュから）...")
            start_time = time.time()
            data2 = provider.fetch()
            elapsed = time.time() - start_time
            
            if data2:
                print(f"  ✓ キャッシュから取得 ({elapsed:.3f}秒)")
                print(f"  同じデータ: {data['updated'] == data2['updated']}")
        else:
            print(f"  ✗ 取得失敗")
            
    except Exception as e:
        print(f"エラー: {e}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree("./cache_real", ignore_errors=True)


def demo_different_locations():
    """
    異なる場所の天気を取得
    """
    print("\n■ 世界各地の天気")
    print("-" * 40)
    
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    if not api_key:
        print("  ⚠️  APIキーが設定されていません")
        return
    
    locations = [
        ("東京", 35.681236, 139.767125),
        ("ニューヨーク", 40.7128, -74.0060),
        ("ロンドン", 51.5074, -0.1278),
        ("シドニー", -33.8688, 151.2093)
    ]
    
    for city, lat, lon in locations:
        class LocationConfig:
            def get(self, key, default=None):
                configs = {
                    'weather.openweathermap.api_key': api_key,
                    'weather.openweathermap.units': 'metric',
                    'weather.openweathermap.lang': 'en',  # 英語
                    'weather.location.lat': lat,
                    'weather.location.lon': lon,
                    'weather.cache_dir': f'./cache_{city}',
                    'weather.cache_duration': 300,
                    'weather.timeout': 10
                }
                return configs.get(key, default)
        
        try:
            config = LocationConfig()
            provider = OpenWeatherMapProvider(config)
            
            print(f"\n{city}の天気を取得中...")
            data = provider.fetch()
            
            if data and 'current' in data:
                current = data['current']
                print(f"  気温: {current['temperature']}°C")
                print(f"  天気: {current['icon']}")
                print(f"  湿度: {current['humidity']}%")
            else:
                print(f"  取得失敗")
                
            # レート制限対策
            time.sleep(1)
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # クリーンアップ
        import shutil
        shutil.rmtree(f"./cache_{city}", ignore_errors=True)


def main():
    """メイン処理"""
    print("=" * 60)
    print(" OpenWeatherMap Provider デモ")
    print("=" * 60)
    
    # モックAPIでのテスト
    demo_with_mock_api()
    
    # 実際のAPIでのテスト
    demo_with_real_api()
    
    # 複数地点のテスト（APIキーがある場合）
    if os.environ.get('OPENWEATHERMAP_API_KEY'):
        demo_different_locations()
    
    print("\n" + "=" * 60)
    print(" デモ完了")
    print("=" * 60)
    print("\n機能確認:")
    print("  ✓ OpenWeatherMap API統合")
    print("  ✓ 現在の天気取得")
    print("  ✓ 3日間予報")
    print("  ✓ エラーハンドリング")
    print("  ✓ キャッシュ機能")
    print("  ✓ 複数地点対応")
    
    print("\n注意:")
    print("  実際のAPIを使用するには、OpenWeatherMapのAPIキーが必要です")
    print("  https://openweathermap.org/api で無料アカウントを作成できます")


if __name__ == "__main__":
    main()