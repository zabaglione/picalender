"""
設定管理システムのテストコード
"""

import os
import tempfile
import pytest
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path

# テスト対象のインポート（まだ実装されていないのでエラーになる）
from src.core.config_manager import ConfigManager, DEFAULT_CONFIG


class TestConfigManager:
    """ConfigManagerのテストクラス"""
    
    @pytest.fixture
    def temp_config_file(self):
        """一時的な設定ファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'screen': {
                    'width': 1920,
                    'height': 1080,
                    'fps': 60
                },
                'ui': {
                    'clock_font_px': 150
                }
            }
            yaml.dump(config, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def invalid_yaml_file(self):
        """不正なYAMLファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def partial_config_file(self):
        """部分的な設定ファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'screen': {
                    'width': 800
                    # height, fpsは未定義
                }
            }
            yaml.dump(config, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    # TC-001: デフォルト設定の読み込み
    def test_load_default_config_when_file_not_exists(self):
        """設定ファイルが存在しない場合、デフォルト設定が読み込まれる"""
        config = ConfigManager('non_existent_file.yaml')
        
        assert config.screen.width == 1024
        assert config.screen.height == 600
        assert config.screen.fps == 30
        assert config.ui.clock_font_px == 130
    
    # TC-002: YAMLファイルからの読み込み
    def test_load_from_yaml_file(self, temp_config_file):
        """有効なYAMLファイルから設定を読み込む"""
        config = ConfigManager(temp_config_file)
        
        assert config.screen.width == 1920
        assert config.screen.height == 1080
        assert config.screen.fps == 60
        assert config.ui.clock_font_px == 150
    
    # TC-003: 部分的な設定の読み込み
    def test_load_partial_config(self, partial_config_file):
        """部分的な設定ファイルの場合、不足分はデフォルト値を使用"""
        config = ConfigManager(partial_config_file)
        
        assert config.screen.width == 800  # カスタム値
        assert config.screen.height == 600  # デフォルト値
        assert config.screen.fps == 30  # デフォルト値
    
    # TC-004: ドット記法でのアクセス
    def test_dot_notation_access(self):
        """ドット記法でのアクセスが可能"""
        config = ConfigManager('non_existent.yaml')
        
        # エラーなくアクセスできる
        width = config.screen.width
        margin_x = config.ui.margins.x
        
        assert width == 1024
        assert margin_x == 24
    
    # TC-005: 辞書記法でのアクセス
    def test_dict_notation_access(self):
        """辞書記法でのアクセスが可能"""
        config = ConfigManager('non_existent.yaml')
        
        # エラーなくアクセスできる
        width = config['screen']['width']
        margin_x = config['ui']['margins']['x']
        
        assert width == 1024
        assert margin_x == 24
    
    # TC-006: get()メソッドでのアクセス
    def test_get_method_access(self):
        """get()メソッドでのアクセスとデフォルト値"""
        config = ConfigManager('non_existent.yaml')
        
        # 存在するキー
        width = config.get('screen.width')
        assert width == 1024
        
        # 存在しないキー（デフォルト値を返す）
        non_existent = config.get('non.existent.key', 'default_value')
        assert non_existent == 'default_value'
    
    # TC-007: 環境変数によるオーバーライド
    def test_environment_variable_override(self, temp_config_file):
        """環境変数による設定の上書き"""
        with patch.dict(os.environ, {'PICALENDAR_SCREEN_WIDTH': '800'}):
            config = ConfigManager(temp_config_file)
            
            # 環境変数の値が優先される
            assert config.screen.width == 800
            # 他の値はファイルから
            assert config.screen.height == 1080
    
    # TC-008: 環境変数の型変換
    def test_environment_variable_type_conversion(self):
        """環境変数の適切な型変換"""
        env_vars = {
            'PICALENDAR_SCREEN_FPS': '45',  # 文字列 -> int
            'PICALENDAR_SCREEN_FULLSCREEN': 'false',  # 文字列 -> bool
            'PICALENDAR_UI_COLORS_TEXT': '[128,128,128]'  # 文字列 -> list
        }
        
        with patch.dict(os.environ, env_vars):
            config = ConfigManager('non_existent.yaml')
            
            assert config.screen.fps == 45
            assert isinstance(config.screen.fps, int)
            
            assert config.screen.fullscreen is False
            assert isinstance(config.screen.fullscreen, bool)
            
            assert config.ui.colors.text == [128, 128, 128]
            assert isinstance(config.ui.colors.text, list)
    
    # TC-009: 型チェック
    def test_type_validation(self, caplog):
        """不正な型の値に対する警告とデフォルト値の使用"""
        # 不正な型の設定ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'screen': {
                    'fps': 'thirty',  # 文字列（期待はint）
                    'width': 1024
                }
            }
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            
            # 警告ログが出力される
            assert "Invalid type for screen.fps" in caplog.text
            
            # デフォルト値が使用される
            assert config.screen.fps == 30
            
            # 正しい値は維持される
            assert config.screen.width == 1024
        finally:
            os.unlink(temp_path)
    
    # TC-010: 範囲チェック
    def test_range_validation(self, caplog):
        """範囲外の値に対する警告と修正"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'screen': {
                    'fps': 100,  # 範囲外（1-60）
                    'width': -1024  # 負の値
                }
            }
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            
            # 警告ログが出力される
            assert "out of range" in caplog.text.lower()
            
            # FPSは最大値に修正
            assert config.screen.fps == 60
            
            # 負の値はデフォルトに
            assert config.screen.width == 1024
        finally:
            os.unlink(temp_path)
    
    # TC-012: 不正なYAMLファイル
    def test_invalid_yaml_file(self, invalid_yaml_file, caplog):
        """不正なYAMLファイルの処理"""
        config = ConfigManager(invalid_yaml_file)
        
        # エラーログが出力される
        assert "Failed to parse YAML" in caplog.text
        
        # デフォルト設定で継続
        assert config.screen.width == 1024
        assert config.screen.height == 600
    
    # TC-014: 設定の更新
    def test_set_config_value(self):
        """実行時の設定値更新"""
        config = ConfigManager('non_existent.yaml')
        
        # 初期値
        assert config.screen.width == 1024
        
        # 値を更新
        config.set('screen.width', 1920)
        
        # 新しい値が反映される
        assert config.screen.width == 1920
        assert config.get('screen.width') == 1920
    
    # TC-015: 設定の再読み込み
    def test_reload_config(self, temp_config_file):
        """設定ファイルの再読み込み"""
        config = ConfigManager(temp_config_file)
        
        # 初期値
        assert config.screen.width == 1920
        
        # ファイルを更新
        with open(temp_config_file, 'w') as f:
            new_config = {
                'screen': {
                    'width': 2560,
                    'height': 1440
                }
            }
            yaml.dump(new_config, f)
        
        # 再読み込み
        config.reload()
        
        # 新しい値が反映される
        assert config.screen.width == 2560
        assert config.screen.height == 1440
    
    # TC-016: 読み込み速度
    def test_load_performance(self, temp_config_file):
        """設定の読み込みが100ms以内に完了"""
        import time
        
        start = time.time()
        config = ConfigManager(temp_config_file)
        end = time.time()
        
        load_time = (end - start) * 1000  # ms
        assert load_time < 100
    
    # TC-018: 空の設定ファイル
    def test_empty_config_file(self):
        """空の設定ファイルの場合、デフォルト設定を使用"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # 空ファイル
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            
            # すべてデフォルト値
            assert config.screen.width == 1024
            assert config.screen.height == 600
            assert config.screen.fps == 30
        finally:
            os.unlink(temp_path)
    
    # TC-019: 深くネストされた設定
    def test_deeply_nested_config(self):
        """深い階層の設定へのアクセス"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'level1': {
                    'level2': {
                        'level3': {
                            'level4': {
                                'level5': {
                                    'value': 'deep_value'
                                }
                            }
                        }
                    }
                }
            }
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            
            # ドット記法でアクセス
            assert config.level1.level2.level3.level4.level5.value == 'deep_value'
            
            # 辞書記法でアクセス
            assert config['level1']['level2']['level3']['level4']['level5']['value'] == 'deep_value'
            
            # get()メソッドでアクセス
            assert config.get('level1.level2.level3.level4.level5.value') == 'deep_value'
        finally:
            os.unlink(temp_path)
    
    # to_dict()メソッドのテスト
    def test_to_dict_method(self):
        """設定を辞書として取得"""
        config = ConfigManager('non_existent.yaml')
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['screen']['width'] == 1024
        assert config_dict['ui']['margins']['x'] == 24