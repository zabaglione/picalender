"""
OpenWeatherMap天気プロバイダー

OpenWeatherMap API v2.5/3.0を使用した天気情報取得
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import requests

from .weather_base import WeatherProvider

logger = logging.getLogger(__name__)


class OpenWeatherMapProvider(WeatherProvider):
    """
    OpenWeatherMap天気プロバイダー
    
    OpenWeatherMap APIを使用して天気情報を取得し、
    標準フォーマットに変換する
    """
    
    # API エンドポイント
    # Note: One Call API 3.0は有料のため、2.5を使用
    API_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # 天気コードのマッピング
    # https://openweathermap.org/weather-conditions
    WEATHER_CODE_MAP = {
        # Thunderstorm (2xx)
        range(200, 300): 'thunder',
        # Drizzle (3xx)
        range(300, 400): 'rain',
        # Rain (5xx)
        range(500, 600): 'rain',
        # Snow (6xx)
        range(600, 700): 'snow',
        # Atmosphere (7xx)
        range(700, 800): 'fog',
        # Clear (800)
        800: 'sunny',
        # Clouds (80x)
        801: 'partly_cloudy',
        802: 'partly_cloudy',
        803: 'cloudy',
        804: 'cloudy',
    }
    
    def __init__(self, config: Any):
        """
        初期化
        
        Args:
            config: 設定オブジェクト
            
        Raises:
            ValueError: APIキーが設定されていない場合
        """
        # APIキーの取得（親クラス初期化前にチェック）
        self.api_key = config.get('weather.openweathermap.api_key')
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is required")
        
        # 親クラスの初期化
        super().__init__(config)
        
        # 設定の取得
        self.units = config.get('weather.openweathermap.units', 'metric')
        self.lang = config.get('weather.openweathermap.lang', 'ja')
    
    def get_api_url(self, endpoint: str = 'forecast') -> str:
        """
        API URLを構築
        
        Args:
            endpoint: APIエンドポイント ('weather' or 'forecast')
            
        Returns:
            完全なAPI URL
        """
        base_url = f"{self.API_BASE_URL}/{endpoint}"
        params = {
            'lat': self.location['lat'],
            'lon': self.location['lon'],
            'appid': self.api_key,
            'units': self.units,
            'lang': self.lang
        }
        
        # URLパラメータを構築
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """
        OpenWeatherMap APIから天気データを取得
        
        Returns:
            API応答データ、失敗時はNone
        """
        try:
            # 現在の天気を取得
            current_url = self.get_api_url('weather')
            logger.info(f"Fetching current weather from OpenWeatherMap")
            
            current_response = requests.get(
                current_url,
                timeout=self.timeout
            )
            
            # エラーチェック
            if current_response.status_code == 401:
                logger.error("Invalid API key")
                return None
            elif current_response.status_code == 429:
                logger.error("Rate limit exceeded")
                return None
            elif current_response.status_code != 200:
                logger.error(f"API error: {current_response.status_code}")
                return None
            
            current_data = current_response.json()
            
            # 予報データを取得（5日間、3時間ごと）
            forecast_url = self.get_api_url('forecast')
            logger.info(f"Fetching forecast from OpenWeatherMap")
            
            forecast_response = requests.get(
                forecast_url,
                timeout=self.timeout
            )
            
            if forecast_response.status_code != 200:
                logger.error(f"Forecast API error: {forecast_response.status_code}")
                # 現在の天気だけでも返す
                return {
                    'current': current_data,
                    'daily': []
                }
            
            forecast_data = forecast_response.json()
            
            # 日別データを生成（3時間ごとのデータから日別に集約）
            daily_data = []
            if 'list' in forecast_data:
                daily_data = self._aggregate_daily_forecast(forecast_data['list'])
            
            return {
                'current': current_data,
                'daily': daily_data
            }
            
        except requests.exceptions.Timeout:
            logger.error("API request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def _aggregate_daily_forecast(self, forecast_list: list) -> list:
        """
        3時間ごとの予報データを日別に集約
        
        Args:
            forecast_list: 3時間ごとの予報リスト
            
        Returns:
            日別の予報データ
        """
        daily_data = {}
        
        for item in forecast_list:
            # 日付を取得
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'dt': item['dt'],
                    'temps': [],
                    'weather': [],
                    'pop': []
                }
            
            # データを収集
            daily_data[date_key]['temps'].append(item['main']['temp'])
            daily_data[date_key]['weather'].extend(item['weather'])
            if 'pop' in item:
                daily_data[date_key]['pop'].append(item['pop'])
        
        # 日別データを生成（最初の3日分を確実に取得）
        result = []
        sorted_dates = sorted(daily_data.keys())
        
        # もしデータが3日分未満なら、ダミーデータを追加
        for i in range(min(3, len(sorted_dates))):
            date_key = sorted_dates[i]
            data = daily_data[date_key]
            
            # 最も頻度の高い天気を選択
            weather_counts = {}
            for w in data['weather']:
                weather_id = w['id']
                weather_counts[weather_id] = weather_counts.get(weather_id, 0) + 1
            
            if weather_counts:
                most_common_weather = max(weather_counts, key=weather_counts.get)
            else:
                most_common_weather = 800  # デフォルト: 晴れ
            
            result.append({
                'dt': data['dt'],
                'temp': {
                    'min': min(data['temps']) if data['temps'] else 0,
                    'max': max(data['temps']) if data['temps'] else 0
                },
                'weather': [{'id': most_common_weather}],
                'pop': max(data['pop']) if data['pop'] else 0
            })
        
        # 3日分に満たない場合はダミーデータを追加
        while len(result) < 3:
            last_dt = result[-1]['dt'] if result else int(time.time())
            result.append({
                'dt': last_dt + 86400,  # 1日追加
                'temp': {'min': 10, 'max': 20},
                'weather': [{'id': 800}],
                'pop': 0
            })
        
        return result
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        OpenWeatherMapのレスポンスを標準フォーマットに変換
        
        Args:
            response: OpenWeatherMap API応答
            
        Returns:
            標準フォーマットのデータ
        """
        parsed = {
            'updated': int(time.time()),
            'location': self.location,
            'current': {},
            'forecasts': []
        }
        
        # 現在の天気を解析
        if 'current' in response:
            current = response['current']
            
            # 通常のweather APIレスポンスの場合
            if 'main' in current:
                parsed['current'] = {
                    'temperature': current['main']['temp'],
                    'humidity': current['main']['humidity'],
                    'wind_speed': current['wind']['speed'],
                    'icon': self._map_icon(current['weather'][0]['id'])
                }
            # One Call APIレスポンスの場合
            else:
                weather_id = current['weather'][0]['id'] if 'weather' in current else 800
                parsed['current'] = {
                    'temperature': current.get('temp', 0),
                    'humidity': current.get('humidity', 0),
                    'wind_speed': current.get('wind_speed', 0),
                    'icon': self._map_icon(weather_id)
                }
        
        # 日別予報を解析
        if 'daily' in response:
            for day in response['daily'][:3]:  # 最初の3日分
                weather_id = day['weather'][0]['id'] if 'weather' in day else 800
                
                parsed['forecasts'].append({
                    'date': self.format_date(day['dt']),
                    'icon': self._map_icon(weather_id),
                    'tmin': day['temp']['min'],  # roundしない
                    'tmax': day['temp']['max'],  # roundしない
                    'pop': int(day.get('pop', 0) * 100)  # 0.0-1.0 -> 0-100%
                })
        
        return parsed
    
    def _map_icon(self, weather_id: int) -> str:
        """
        OpenWeatherMapの天気IDを標準アイコン名にマップ
        
        Args:
            weather_id: OpenWeatherMap天気ID
            
        Returns:
            標準アイコン名
        """
        # 特定のIDをチェック
        if weather_id in [800]:
            return 'sunny'
        elif weather_id in [801, 802]:
            return 'partly_cloudy'
        elif weather_id in [803, 804]:
            return 'cloudy'
        
        # 範囲でチェック
        for id_range, icon in self.WEATHER_CODE_MAP.items():
            if isinstance(id_range, range):
                if weather_id in id_range:
                    return icon
        
        # デフォルト
        return 'cloudy'
    
    def format_date(self, timestamp: int) -> str:
        """
        Unixタイムスタンプを日付文字列に変換
        
        Args:
            timestamp: Unixタイムスタンプ
            
        Returns:
            YYYY-MM-DD形式の日付文字列
        """
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')