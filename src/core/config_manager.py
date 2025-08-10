"""
設定管理システム
YAMLファイルから設定を読み込み、デフォルト値管理、環境変数オーバーライド、
バリデーション機能を提供する
"""

import os
import logging
import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_CONFIG = {
    'screen': {
        'width': 1024,
        'height': 600,
        'fps': 30,
        'fullscreen': True,
        'hide_cursor': True
    },
    'ui': {
        'margins': {'x': 24, 'y': 16},
        'clock_font_px': 130,
        'date_font_px': 36,
        'cal_font_px': 22,
        'weather_font_px': 22,
        'colors': {
            'text': [255, 255, 255],
            'sunday': [255, 100, 100],
            'saturday': [100, 100, 255],
            'weekday': [255, 255, 255],
            'background': [0, 0, 0],
            'weather_panel': [40, 40, 40],
            'weather_panel_alpha': 200
        }
    },
    'calendar': {
        'first_weekday': 'SUNDAY'
    },
    'background': {
        'dir': './wallpapers',
        'mode': 'fit',
        'rescan_sec': 300
    },
    'weather': {
        'provider': 'openmeteo',
        'refresh_sec': 1800,
        'timeout_sec': 10,
        'location': {
            'lat': 35.681236,
            'lon': 139.767125
        }
    },
    'character': {
        'enabled': False,
        'sprite': './assets/sprites/char_idle.png',
        'frame_width': 128,
        'frame_height': 128,
        'fps': 8
    },
    'fonts': {
        'main': {
            'path': './assets/fonts/NotoSansCJK-Regular.otf',
            'fallback': '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf'
        }
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    }
}

# バリデーションルール
VALIDATION_RULES = {
    'screen.fps': {'type': int, 'min': 1, 'max': 60},
    'screen.width': {'type': int, 'min': 1},
    'screen.height': {'type': int, 'min': 1},
    'ui.clock_font_px': {'type': int, 'min': 10, 'max': 500},
    'ui.date_font_px': {'type': int, 'min': 10, 'max': 200},
    'ui.cal_font_px': {'type': int, 'min': 8, 'max': 100},
    'ui.weather_font_px': {'type': int, 'min': 8, 'max': 100},
    'weather.refresh_sec': {'type': int, 'min': 60, 'max': 7200},
    'weather.timeout_sec': {'type': int, 'min': 1, 'max': 60},
}


class ConfigDict(dict):
    """ドット記法でアクセス可能な辞書"""
    
    def __init__(self, data: dict):
        super().__init__()
        for key, value in data.items():
            if isinstance(value, dict):
                self[key] = ConfigDict(value)
            else:
                self[key] = value
    
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'ConfigDict' object has no attribute '{key}'")
    
    def __setattr__(self, key, value):
        self[key] = value


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "settings.yaml"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self._config = ConfigDict({})
        self.load()
    
    def load(self) -> None:
        """設定ファイルを読み込む"""
        # デフォルト設定をベースとする
        config_data = copy.deepcopy(DEFAULT_CONFIG)
        
        # YAMLファイルから読み込み
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                    
                # ファイルの設定をマージ
                self._deep_merge(config_data, file_config)
                logger.info(f"Configuration loaded from {self.config_path}")
                
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML file {self.config_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load configuration file {self.config_path}: {e}")
        else:
            logger.warning(f"Configuration file {self.config_path} not found, using defaults")
        
        # 環境変数でオーバーライド
        self._apply_environment_variables(config_data)
        
        # バリデーション
        self._validate(config_data)
        
        # ConfigDictに変換
        self._config = ConfigDict(config_data)
    
    def _deep_merge(self, base: dict, override: dict) -> None:
        """
        辞書を深くマージする（破壊的）
        
        Args:
            base: ベースとなる辞書
            override: 上書きする辞書
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _apply_environment_variables(self, config: dict) -> None:
        """
        環境変数による設定のオーバーライド
        
        Args:
            config: 設定辞書
        """
        env_prefix = "PICALENDAR_"
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(env_prefix):
                continue
            
            # 環境変数名を設定キーに変換
            # PICALENDAR_SCREEN_WIDTH -> screen.width
            key_parts = env_key[len(env_prefix):].lower().split('_')
            
            try:
                # 設定を更新
                parsed_value = self._parse_env_value(env_value)
                self._set_nested_value(config, key_parts, parsed_value)
                logger.info(f"Applied environment override: {env_key} = {parsed_value}")
            except Exception as e:
                logger.warning(f"Failed to apply environment variable {env_key}: {e}")
    
    def _parse_env_value(self, value: str) -> Any:
        """
        環境変数の値を適切な型に変換
        
        Args:
            value: 環境変数の文字列値
            
        Returns:
            変換後の値
        """
        # bool値
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数値
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # リスト（JSON形式）
        if value.startswith('[') and value.endswith(']'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 文字列として返す
        return value
    
    def _set_nested_value(self, data: dict, keys: list, value: Any) -> None:
        """
        ネストされた辞書に値を設定
        
        Args:
            data: 辞書
            keys: キーのリスト
            value: 設定する値
        """
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def _validate(self, config: dict) -> None:
        """
        設定値を検証する
        
        Args:
            config: 設定辞書
        """
        for rule_key, rule in VALIDATION_RULES.items():
            keys = rule_key.split('.')
            value = self._get_nested_value(config, keys)
            
            if value is None:
                continue
            
            # 型チェック
            expected_type = rule.get('type')
            if expected_type and not isinstance(value, expected_type):
                logger.warning(f"Invalid type for {rule_key}: expected {expected_type.__name__}, got {type(value).__name__}")
                # デフォルト値を使用
                default_value = self._get_nested_value(DEFAULT_CONFIG, keys)
                self._set_nested_value(config, keys, default_value)
                continue
            
            # 範囲チェック
            if 'min' in rule and value < rule['min']:
                logger.warning(f"Value for {rule_key} out of range: {value} < {rule['min']}")
                self._set_nested_value(config, keys, self._get_nested_value(DEFAULT_CONFIG, keys))
            elif 'max' in rule and value > rule['max']:
                logger.warning(f"Value for {rule_key} out of range: {value} > {rule['max']}")
                self._set_nested_value(config, keys, rule['max'])
    
    def _get_nested_value(self, data: dict, keys: list) -> Any:
        """
        ネストされた辞書から値を取得
        
        Args:
            data: 辞書
            keys: キーのリスト
            
        Returns:
            値またはNone
        """
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: ドット区切りのキー
            default: デフォルト値
            
        Returns:
            設定値またはデフォルト値
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if not isinstance(current, (dict, ConfigDict)) or k not in current:
                return default
            current = current[k]
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        設定値を更新（実行時のみ）
        
        Args:
            key: ドット区切りのキー
            value: 設定する値
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = ConfigDict({})
            current = current[k]
        
        current[keys[-1]] = value
    
    def reload(self) -> None:
        """設定を再読み込み"""
        logger.info("Reloading configuration...")
        self.load()
    
    def to_dict(self) -> dict:
        """
        設定を辞書として取得
        
        Returns:
            設定の辞書
        """
        return self._to_plain_dict(self._config)
    
    def _to_plain_dict(self, config_dict: Union[ConfigDict, dict]) -> dict:
        """
        ConfigDictを通常の辞書に変換
        
        Args:
            config_dict: ConfigDictまたは辞書
            
        Returns:
            通常の辞書
        """
        result = {}
        for key, value in config_dict.items():
            if isinstance(value, (ConfigDict, dict)):
                result[key] = self._to_plain_dict(value)
            else:
                result[key] = value
        return result
    
    def __getattr__(self, key):
        """ドット記法でのアクセスを提供"""
        if key in self._config:
            return self._config[key]
        raise AttributeError(f"'ConfigManager' object has no attribute '{key}'")
    
    def __getitem__(self, key):
        """辞書記法でのアクセスを提供"""
        return self._config[key]