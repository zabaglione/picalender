#!/usr/bin/env python3
"""
天気プロバイダ基底クラス

各種天気サービスプロバイダの共通インターフェースと機能を提供する。
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import requests

from .exceptions import (
    WeatherProviderError, NetworkError, APIError, 
    DataFormatError, AuthenticationError
)


class DefaultSettings:
    """デフォルト設定値"""
    TIMEOUT = 10
    USER_AGENT = 'PiCalendar/1.0 (Weather Display)'
    DEFAULT_ICON = 'cloudy'


class ValidationRanges:
    """バリデーション範囲定数"""
    LATITUDE_MIN = -90.0
    LATITUDE_MAX = 90.0
    LONGITUDE_MIN = -180.0
    LONGITUDE_MAX = 180.0
    TIMEOUT_MIN = 1
    TIMEOUT_MAX = 60
    PRECIPITATION_MIN = 0
    PRECIPITATION_MAX = 100


class SecuritySettings:
    """セキュリティ設定定数"""
    SENSITIVE_KEYS = ['key', 'api_key', 'appid', 'client_secret', 'password', 'token']
    MASK_CHAR = '*'
    MASK_VISIBLE_CHARS = 3


class WeatherProvider(ABC):
    """天気プロバイダ抽象基底クラス
    
    全ての天気サービスプロバイダが継承すべき基底クラス。
    共通のインターフェースと機能を提供する。
    """
    
    # 内部アイコンマッピングのデフォルト定義
    DEFAULT_ICON_MAPPING = {
        # sunny系
        'clear': 'sunny',
        'sunny': 'sunny',
        'fair': 'sunny',
        
        # cloudy系
        'cloudy': 'cloudy',
        'partly-cloudy': 'cloudy',
        'overcast': 'cloudy',
        'mostly-cloudy': 'cloudy',
        
        # rain系
        'rain': 'rain',
        'drizzle': 'rain',
        'shower': 'rain',
        'light-rain': 'rain',
        
        # thunder系
        'thunderstorm': 'thunder',
        'thunder': 'thunder',
        'storm': 'thunder',
        
        # fog系
        'fog': 'fog',
        'mist': 'fog',
        'haze': 'fog'
    }
    
    def __init__(self, settings: Dict[str, Any]):
        """
        プロバイダ初期化
        
        Args:
            settings: 設定辞書
            
        Raises:
            WeatherProviderError: 設定エラー
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        
        # 設定検証と読み込み
        self._validate_and_load_settings()
        
        # HTTPセッション初期化
        self._init_http_session()
        
        self.logger.info(f"WeatherProvider initialized: {self.__class__.__name__}")
    
    def _validate_and_load_settings(self):
        """設定検証と読み込み"""
        weather_config = self.settings.get('weather', {})
        
        # 必須設定チェック
        if 'location' not in weather_config:
            raise WeatherProviderError("Missing required setting: weather.location")
        
        location = weather_config['location']
        if 'latitude' not in location or 'longitude' not in location:
            raise WeatherProviderError("Missing required location coordinates")
        
        # 緯度経度の範囲チェック
        lat = location['latitude']
        lon = location['longitude']
        
        self._validate_latitude(lat)
        self._validate_longitude(lon)
        
        # 設定値の読み込み
        self.location = location
        self.timeout = self._validate_timeout(weather_config.get('timeout', DefaultSettings.TIMEOUT))
        
        self.logger.debug(f"Settings validated - Location: {lat:.3f}, {lon:.3f}, Timeout: {self.timeout}s")
    
    def _validate_latitude(self, lat: float) -> None:
        """緯度の妥当性検証"""
        if not isinstance(lat, (int, float)):
            raise WeatherProviderError(f"Latitude must be a number, got {type(lat).__name__}")
        if not (ValidationRanges.LATITUDE_MIN <= lat <= ValidationRanges.LATITUDE_MAX):
            raise WeatherProviderError(
                f"Invalid latitude: {lat} (must be {ValidationRanges.LATITUDE_MIN} to {ValidationRanges.LATITUDE_MAX})"
            )
    
    def _validate_longitude(self, lon: float) -> None:
        """経度の妥当性検証"""
        if not isinstance(lon, (int, float)):
            raise WeatherProviderError(f"Longitude must be a number, got {type(lon).__name__}")
        if not (ValidationRanges.LONGITUDE_MIN <= lon <= ValidationRanges.LONGITUDE_MAX):
            raise WeatherProviderError(
                f"Invalid longitude: {lon} (must be {ValidationRanges.LONGITUDE_MIN} to {ValidationRanges.LONGITUDE_MAX})"
            )
    
    def _validate_timeout(self, timeout: int) -> int:
        """タイムアウト値の妥当性検証"""
        if not isinstance(timeout, int):
            self.logger.warning(f"Timeout must be integer, got {type(timeout).__name__}, using default")
            return DefaultSettings.TIMEOUT
        if not (ValidationRanges.TIMEOUT_MIN <= timeout <= ValidationRanges.TIMEOUT_MAX):
            self.logger.warning(
                f"Invalid timeout: {timeout} (must be {ValidationRanges.TIMEOUT_MIN}-{ValidationRanges.TIMEOUT_MAX}), using default"
            )
            return DefaultSettings.TIMEOUT
        return timeout
    
    def _init_http_session(self):
        """HTTPセッション初期化"""
        self.session = requests.Session()
        self.session.timeout = self.timeout
        
        # User-Agent設定
        self.session.headers.update({
            'User-Agent': DefaultSettings.USER_AGENT,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """
        天気データ取得（抽象メソッド）
        
        各プロバイダで実装必須。標準形式の天気データを返す。
        
        Returns:
            標準形式の天気データ辞書
            
        Raises:
            WeatherProviderError: 各種エラー
        """
        pass
    
    def validate_response(self, data: Dict[str, Any]) -> bool:
        """
        レスポンスデータの妥当性検証
        
        Args:
            data: 検証対象のデータ
            
        Returns:
            データが有効な場合True
            
        Raises:
            DataFormatError: データ形式エラー
        """
        if not isinstance(data, dict):
            raise DataFormatError("Response data must be a dictionary")
        
        # 必須フィールドチェック
        required_fields = ['updated', 'forecasts']
        for field in required_fields:
            if field not in data:
                raise DataFormatError(f"Missing required field: {field}")
        
        # updated フィールドの型チェック
        if not isinstance(data['updated'], (int, float)):
            raise DataFormatError("Field 'updated' must be a number (timestamp)")
        
        # forecasts フィールドの型チェック
        forecasts = data['forecasts']
        if not isinstance(forecasts, list):
            raise DataFormatError("Field 'forecasts' must be a list")
        
        # 各予報データの検証
        for i, forecast in enumerate(forecasts):
            if not isinstance(forecast, dict):
                raise DataFormatError(f"Forecast {i} must be a dictionary")
            
            # 予報データの必須フィールド
            required_forecast_fields = ['date', 'icon', 'temperature', 'precipitation_probability']
            for field in required_forecast_fields:
                if field not in forecast:
                    raise DataFormatError(f"Missing required field in forecast {i}: {field}")
            
            # 日付形式チェック (YYYY-MM-DD)
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
            if not date_pattern.match(forecast['date']):
                raise DataFormatError(f"Invalid date format in forecast {i}: {forecast['date']}")
            
            # 温度データの検証
            temp = forecast['temperature']
            if not isinstance(temp, dict) or 'min' not in temp or 'max' not in temp:
                raise DataFormatError(f"Invalid temperature data in forecast {i}")
            
            # 降水確率の範囲チェック
            pop = forecast['precipitation_probability']
            if not isinstance(pop, (int, float)) or not (0 <= pop <= 100):
                raise DataFormatError(f"Invalid precipitation probability in forecast {i}: {pop}")
        
        return True
    
    def map_to_internal_icon(self, provider_code: str) -> str:
        """
        プロバイダ固有アイコン → 内部アイコンマッピング
        
        Args:
            provider_code: プロバイダ固有のアイコンコード
            
        Returns:
            内部アイコン名 (sunny, cloudy, rain, thunder, fog)
        """
        if not provider_code:
            self.logger.warning(f"Empty or None provider code, using default '{DefaultSettings.DEFAULT_ICON}'")
            return DefaultSettings.DEFAULT_ICON
        
        # 小文字に変換してマッピング
        code = provider_code.lower()
        
        # デフォルトマッピングから検索
        internal_icon = self.DEFAULT_ICON_MAPPING.get(code)
        
        if internal_icon:
            return internal_icon
        else:
            self.logger.warning(f"Unknown provider code '{provider_code}', using default '{DefaultSettings.DEFAULT_ICON}'")
            return DefaultSettings.DEFAULT_ICON
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        HTTP リクエスト実行（共通処理）
        
        Args:
            url: リクエストURL
            params: リクエストパラメータ（オプション）
            
        Returns:
            JSONレスポンス
            
        Raises:
            NetworkError: ネットワークエラー
            APIError: APIエラー
        """
        # HTTPS強制チェック
        if not url.startswith('https://'):
            raise NetworkError("HTTPS required: HTTP connections are not allowed")
        
        try:
            self.logger.debug(f"Making request to: {url}")
            
            # APIキーのマスク処理（ログ用）
            masked_params = self._mask_sensitive_params(params or {})
            self.logger.debug(f"Request params: {masked_params}")
            
            # HTTPリクエスト実行
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            # HTTPエラーハンドリング
            self._handle_http_error(response)
            
            # JSONレスポンス解析
            return response.json()
            
        except requests.Timeout as e:
            raise NetworkError(f"Request timeout after {self.timeout} seconds") from e
        except requests.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}") from e
        except requests.exceptions.SSLError as e:
            raise NetworkError(f"SSL certificate error: {str(e)}") from e
        except ValueError as e:  # JSON decode error
            raise DataFormatError(f"Invalid JSON response: {str(e)}") from e
    
    def _handle_http_error(self, response) -> None:
        """
        HTTPエラーハンドリング
        
        Args:
            response: レスポンスオブジェクト
            
        Raises:
            APIError: HTTPエラー
        """
        if response.status_code >= 400:
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed (HTTP {response.status_code})")
            elif response.status_code == 403:
                raise AuthenticationError(f"Access forbidden (HTTP {response.status_code})")
            elif 400 <= response.status_code < 500:
                raise APIError(f"Client error (HTTP {response.status_code}): {response.text}")
            else:  # 500+
                raise APIError(f"Server error (HTTP {response.status_code}): {response.text}")
    
    def _mask_sensitive_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        機密パラメータのマスク処理（ログ用）
        
        Args:
            params: リクエストパラメータ
            
        Returns:
            マスクされたパラメータ辞書
        """
        masked = params.copy()
        
        for key in masked:
            if self._is_sensitive_key(key):
                value = str(masked[key])
                masked[key] = self._mask_value(value)
        
        return masked
    
    def _is_sensitive_key(self, key: str) -> bool:
        """キーが機密情報かどうか判定"""
        key_lower = key.lower()
        return any(sensitive_key in key_lower for sensitive_key in SecuritySettings.SENSITIVE_KEYS)
    
    def _mask_value(self, value: str) -> str:
        """値のマスク処理"""
        if len(value) > SecuritySettings.MASK_VISIBLE_CHARS:
            return value[:SecuritySettings.MASK_VISIBLE_CHARS] + SecuritySettings.MASK_CHAR * (len(value) - SecuritySettings.MASK_VISIBLE_CHARS)
        else:
            return SecuritySettings.MASK_CHAR * len(value)
    
    def cleanup(self) -> None:
        """
        リソースクリーンアップ
        
        HTTPセッションのクローズなど、プロバイダ終了時の処理を実行。
        """
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.debug("HTTP session closed")
        
        self.logger.info(f"WeatherProvider cleanup completed: {self.__class__.__name__}")