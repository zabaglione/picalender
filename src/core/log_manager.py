"""
ログ管理システム
設定管理システムと連携し、レベル別ログ出力、journald連携、
ファイル出力オプション、モジュール別ログ制御を提供する
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# journald対応（Linuxのみ）
try:
    from systemd.journal import JournalHandler
    HAS_JOURNALD = True
except ImportError:
    HAS_JOURNALD = False


# ANSIカラーコード
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m'       # Reset
}


class ColoredConsoleHandler(logging.StreamHandler):
    """カラー出力対応コンソールハンドラー"""
    
    def __init__(self, stream=None):
        """初期化"""
        super().__init__(stream)
        # TTY（端末）かどうかをチェック
        self.is_tty = hasattr(self.stream, 'isatty') and self.stream.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """レベルに応じて色付けしたメッセージを返す"""
        formatted = super().format(record)
        
        if self.is_tty and not os.environ.get('NO_COLOR'):
            # TTY環境でカラー出力
            color = COLORS.get(record.levelname, '')
            reset = COLORS['RESET']
            return f"{color}{formatted}{reset}"
        
        return formatted


class RotatingFileHandlerWithCount(logging.handlers.RotatingFileHandler):
    """ファイル数制限付きローテーティングファイルハンドラー"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, errors=None):
        """初期化"""
        super().__init__(filename, mode, maxBytes, backupCount, 
                        encoding, delay, errors)
    
    def doRollover(self):
        """ローテーション実行"""
        super().doRollover()
        # 古いファイルを削除
        self._delete_old_files()
    
    def _delete_old_files(self):
        """古いローテーションファイルを削除"""
        if self.backupCount > 0:
            for i in range(self.backupCount, 100):
                old_file = f"{self.baseFilename}.{i}"
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except OSError:
                        pass
                else:
                    break


class LogManager:
    """ログ管理クラス"""
    
    def __init__(self, config):
        """
        初期化
        
        Args:
            config: ConfigManagerインスタンス
        """
        self.config = config
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        self.root_logger = logging.getLogger()
        
        # セットアップ
        self.setup()
    
    def setup(self) -> None:
        """ログシステムをセットアップ"""
        # ルートロガーの設定
        level_str = self.config.get('logging.level', 'INFO')
        self.root_logger.setLevel(self._get_log_level(level_str))
        
        # 既存のハンドラーをクリア
        self.root_logger.handlers.clear()
        
        # フォーマッターの作成
        format_str = self.config.get('logging.format', 
                                     '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
        
        # コンソール出力の設定
        if self.config.get('logging.output.console', True):
            console_handler = ColoredConsoleHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)  # ハンドラーは全レベルを受け入れる
            self.root_logger.addHandler(console_handler)
            self.handlers['console'] = console_handler
        
        # ファイル出力の設定
        if self.config.get('logging.output.file', False):
            file_path = self.config.get('logging.file.path', './logs/picalendar.log')
            self._setup_file_handler(file_path, formatter)
        
        # journald出力の設定（Linux環境のみ）
        if HAS_JOURNALD and self.config.get('logging.output.journald', False):
            try:
                journal_handler = JournalHandler()
                journal_handler.setFormatter(formatter)
                self.root_logger.addHandler(journal_handler)
                self.handlers['journald'] = journal_handler
            except Exception as e:
                self.root_logger.warning(f"Failed to setup journald handler: {e}")
        
        # モジュール別ログレベルの設定
        modules_config = self.config.get('logging.modules', {})
        if isinstance(modules_config, dict):
            for module_name, level_str in modules_config.items():
                module_logger = logging.getLogger(module_name)
                module_logger.setLevel(self._get_log_level(level_str))
    
    def _setup_file_handler(self, file_path: str, formatter: logging.Formatter) -> None:
        """
        ファイルハンドラーをセットアップ
        
        Args:
            file_path: ログファイルパス
            formatter: フォーマッター
        """
        try:
            # ディレクトリを作成
            log_dir = Path(file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # ローテーション設定
            max_bytes = self.config.get('logging.file.rotate_size_mb', 10) * 1024 * 1024
            backup_count = self.config.get('logging.file.rotate_count', 5)
            
            # ファイルハンドラー作成
            file_handler = RotatingFileHandlerWithCount(
                file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            
            self.root_logger.addHandler(file_handler)
            self.handlers['file'] = file_handler
            
        except Exception as e:
            self.root_logger.error(f"Failed to setup file handler: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        指定された名前のロガーを取得
        
        Args:
            name: ロガー名
            
        Returns:
            Logger インスタンス
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
            
            # モジュール別設定があれば適用
            modules_config = self.config.get('logging.modules', {})
            if isinstance(modules_config, dict) and name in modules_config:
                level_str = modules_config[name]
                logger.setLevel(self._get_log_level(level_str))
        
        return self.loggers[name]
    
    def set_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """
        ログレベルを設定
        
        Args:
            level: ログレベル文字列
            logger_name: ロガー名（Noneの場合はルート）
        """
        log_level = self._get_log_level(level)
        
        if logger_name:
            # 特定のロガー
            if logger_name in self.loggers:
                self.loggers[logger_name].setLevel(log_level)
            else:
                logger = logging.getLogger(logger_name)
                logger.setLevel(log_level)
                self.loggers[logger_name] = logger
        else:
            # ルートロガー
            self.root_logger.setLevel(log_level)
            # 既存のロガーも更新（モジュール別設定がない場合）
            modules_config = self.config.get('logging.modules', {})
            for name, logger in self.loggers.items():
                if name not in modules_config:
                    logger.setLevel(log_level)
    
    def add_file_handler(self, filepath: str, level: Optional[str] = None,
                        rotate_size_mb: Optional[float] = None) -> None:
        """
        ファイルハンドラーを追加
        
        Args:
            filepath: ファイルパス
            level: ログレベル
            rotate_size_mb: ローテーションサイズ（MB）
        """
        try:
            # ディレクトリ作成
            log_dir = Path(filepath).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # フォーマッター
            format_str = self.config.get('logging.format',
                                        '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
            
            # ローテーション設定
            if rotate_size_mb is None:
                rotate_size_mb = self.config.get('logging.file.rotate_size_mb', 10)
            max_bytes = int(rotate_size_mb * 1024 * 1024)
            backup_count = self.config.get('logging.file.rotate_count', 5)
            
            # ハンドラー作成
            handler = RotatingFileHandlerWithCount(
                filepath,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            handler.setFormatter(formatter)
            
            if level:
                handler.setLevel(self._get_log_level(level))
            else:
                handler.setLevel(logging.DEBUG)
            
            # ハンドラー追加
            self.root_logger.addHandler(handler)
            handler_key = f"file_{filepath}"
            self.handlers[handler_key] = handler
            
        except Exception as e:
            self.root_logger.error(f"Failed to add file handler for {filepath}: {e}")
    
    def remove_file_handler(self, filepath: str) -> None:
        """
        ファイルハンドラーを削除
        
        Args:
            filepath: ファイルパス
        """
        handler_key = f"file_{filepath}"
        if handler_key in self.handlers:
            handler = self.handlers[handler_key]
            self.root_logger.removeHandler(handler)
            handler.close()
            del self.handlers[handler_key]
    
    def flush(self) -> None:
        """バッファをフラッシュ"""
        for handler in self.handlers.values():
            if hasattr(handler, 'flush'):
                handler.flush()
    
    def close(self) -> None:
        """ログシステムをクローズ"""
        self.flush()
        for handler in self.handlers.values():
            if hasattr(handler, 'close'):
                handler.close()
        self.handlers.clear()
        logging.shutdown()
    
    def _get_log_level(self, level_str: str) -> int:
        """
        文字列からログレベルを取得
        
        Args:
            level_str: レベル文字列
            
        Returns:
            ログレベル定数
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        level = level_map.get(level_str.upper(), logging.INFO)
        
        # 不正なレベルの場合は警告
        if level_str.upper() not in level_map:
            self.root_logger.warning(f"Invalid log level: {level_str}, using INFO")
        
        return level