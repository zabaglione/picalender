#!/usr/bin/env python3
"""
Open-Meteo天気プロバイダ実装

無料・認証不要のOpen-Meteo APIから天気データを取得する。
"""

import time
from typing import Dict, Any, List, Optional

from .base import WeatherProvider
from .exceptions import DataFormatError


class OpenMeteoSettings:
    """Open-Meteo固有の設定定数"""
    FORECAST_DAYS = 3
    TIMEZONE = 'Asia/Tokyo'
    MAX_RETRY_COUNT = 3
    DEFAULT_ICON = 'cloudy'
    
    # API必須パラメータ
    DAILY_PARAMS = [
        'temperature_2m_max',
        'temperature_2m_min',
        'weathercode',
        'precipitation_probability_max'
    ]
    
    # レスポンス必須フィールド
    REQUIRED_DAILY_FIELDS = [
        'time',
        'temperature_2m_max',
        'temperature_2m_min',
        'weathercode',
        'precipitation_probability_max'
    ]


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo天気プロバイダ
    
    Open-Meteo APIから3日分の天気予報を取得し、
    標準形式に変換して提供する。
    """
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # WMO Weather Code → 内部アイコンマッピング
    WMO_ICON_MAPPING = {
        # Clear/Sunny (0-1)
        0: "sunny",      # Clear sky
        1: "sunny",      # Mainly clear
        
        # Cloudy (2-3)
        2: "cloudy",     # Partly cloudy
        3: "cloudy",     # Overcast
        
        # Fog (45, 48)
        45: "fog",       # Foggy
        48: "fog",       # Depositing rime fog
        
        # Rain (51-67, 80-82)
        51: "rain",      # Light drizzle
        53: "rain",      # Moderate drizzle
        55: "rain",      # Dense drizzle
        61: "rain",      # Slight rain
        63: "rain",      # Moderate rain
        65: "rain",      # Heavy rain
        66: "rain",      # Light freezing rain
        67: "rain",      # Heavy freezing rain
        80: "rain",      # Slight rain showers
        81: "rain",      # Moderate rain showers
        82: "rain",      # Violent rain showers
        
        # Thunder (95, 96, 99)
        95: "thunder",   # Thunderstorm
        96: "thunder",   # Thunderstorm with hail
        99: "thunder",   # Thunderstorm with heavy hail
        
        # Snow (71-77, 85-86) -> rain として扱う
        71: "rain",      # Light snow
        73: "rain",      # Moderate snow
        75: "rain",      # Heavy snow
        77: "rain",      # Snow grains
        85: "rain",      # Light snow showers
        86: "rain",      # Heavy snow showers
    }
    
    def __init__(self, settings: Dict[str, Any]):
        """初期化
        
        Args:
            settings: 設定辞書
        """
        super().__init__(settings)
        self.logger.info("OpenMeteoProvider initialized")
    
    def fetch(self) -> Dict[str, Any]:
        """天気データ取得
        
        Open-Meteo APIから天気データを取得し、標準形式に変換する。
        
        Returns:
            標準形式の天気データ辞書
            
        Raises:
            WeatherProviderError: 各種エラー
        """
        start_time = time.time()
        self.logger.debug(f"Fetching weather from Open-Meteo for location: {self.location}")
        
        try:
            # APIリクエストパラメータ構築
            params = self._build_request_params()
            
            # APIリクエスト実行
            response_data = self._make_request(self.BASE_URL, params)
            
            # レスポンスを標準形式に変換
            result = self._parse_openmeteo_response(response_data)
            
            # バリデーション
            self.validate_response(result)
            
            # パフォーマンスログ
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"Successfully fetched {len(result['forecasts'])} day(s) forecast "
                f"from Open-Meteo in {elapsed_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fetch weather from Open-Meteo: {str(e)}")
            raise
    
    def _build_request_params(self) -> Dict[str, Any]:
        """Open-Meteo APIリクエストパラメータ構築
        
        Returns:
            リクエストパラメータ辞書
        """
        params = {
            'latitude': self.location['latitude'],
            'longitude': self.location['longitude'],
            'daily': OpenMeteoSettings.DAILY_PARAMS,
            'timezone': OpenMeteoSettings.TIMEZONE,
            'forecast_days': OpenMeteoSettings.FORECAST_DAYS
        }
        
        self.logger.debug(f"Built request params: lat={params['latitude']:.3f}, lon={params['longitude']:.3f}")
        
        return params
    
    def _parse_openmeteo_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Open-Meteoレスポンスを標準形式に変換
        
        Args:
            data: Open-MeteoのAPIレスポンス
            
        Returns:
            標準形式の天気データ
            
        Raises:
            DataFormatError: レスポンス形式エラー
        """
        # 必須フィールドチェック
        if 'daily' not in data:
            raise DataFormatError("Missing required field: daily")
        
        daily_data = data['daily']
        
        # 日次データの必須フィールドチェック
        self._validate_daily_data(daily_data)
        
        # 予報データの変換
        forecasts = self._build_forecasts(daily_data)
        
        # 標準形式の構築
        result = {
            'updated': int(time.time()),
            'location': {
                'latitude': self.location['latitude'],
                'longitude': self.location['longitude'],
                'name': None  # Open-Meteoは地名を返さない
            },
            'forecasts': forecasts
        }
        
        self.logger.debug(f"Parsed Open-Meteo response: {len(forecasts)} forecasts")
        
        return result
    
    def _validate_daily_data(self, daily_data: Dict[str, Any]) -> None:
        """日次データの妥当性検証
        
        Args:
            daily_data: 日次データ辞書
            
        Raises:
            DataFormatError: 必須フィールド欠如
        """
        for field in OpenMeteoSettings.REQUIRED_DAILY_FIELDS:
            if field not in daily_data:
                raise DataFormatError(f"Missing required field in daily data: {field}")
    
    def _build_forecasts(self, daily_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """予報データリストの構築
        
        Args:
            daily_data: Open-Meteoの日次データ
            
        Returns:
            標準形式の予報データリスト
        """
        forecasts = []
        num_days = len(daily_data['time'])
        days_to_process = min(num_days, OpenMeteoSettings.FORECAST_DAYS)
        
        for i in range(days_to_process):
            forecast = self._convert_daily_data(daily_data, i)
            forecasts.append(forecast)
        
        return forecasts
    
    def _convert_daily_data(self, daily_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """日次データを標準形式の予報データに変換
        
        Args:
            daily_data: Open-Meteoの日次データ
            index: データインデックス
            
        Returns:
            標準形式の予報データ
        """
        # WMOコードからアイコンへの変換
        wmo_code = daily_data['weathercode'][index]
        icon = self._map_wmo_code_to_icon(wmo_code)
        
        # 予報データの構築
        forecast = {
            'date': daily_data['time'][index],
            'icon': icon,
            'temperature': {
                'min': round(daily_data['temperature_2m_min'][index]),
                'max': round(daily_data['temperature_2m_max'][index])
            },
            'precipitation_probability': int(daily_data['precipitation_probability_max'][index]),
            'description': None  # Open-Meteoは説明文を返さない
        }
        
        return forecast
    
    def _map_wmo_code_to_icon(self, wmo_code: int) -> str:
        """WMO天気コードを内部アイコンにマッピング
        
        Args:
            wmo_code: WMO天気コード
            
        Returns:
            内部アイコン名
        """
        # 入力検証
        if not isinstance(wmo_code, (int, float)):
            self.logger.warning(f"Invalid WMO code type: {type(wmo_code)}, using default")
            return OpenMeteoSettings.DEFAULT_ICON
        
        # マッピングテーブルから検索
        icon = self.WMO_ICON_MAPPING.get(int(wmo_code))
        
        if icon:
            self.logger.debug(f"Mapped WMO code {wmo_code} to icon '{icon}'")
            return icon
        else:
            # 不明なコードはデフォルト
            self.logger.warning(f"Unknown WMO weather code: {wmo_code}, using default '{OpenMeteoSettings.DEFAULT_ICON}'")
            return OpenMeteoSettings.DEFAULT_ICON