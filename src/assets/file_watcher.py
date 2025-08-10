"""
ファイル変更監視
"""

import os
import time
import threading
import logging
from typing import List, Dict, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileWatcher:
    """ファイルの変更を監視"""
    
    def __init__(self, paths: List[str]):
        """
        初期化
        
        Args:
            paths: 監視するファイル/ディレクトリのリスト
        """
        self.paths = paths
        self.callbacks: List[Callable[[str], None]] = []
        self.file_times: Dict[str, float] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 1.0  # 秒
        
        # 初期のタイムスタンプを記録
        self._update_timestamps()
    
    def _update_timestamps(self) -> None:
        """ファイルのタイムスタンプを更新"""
        for path in self.paths:
            if os.path.exists(path):
                try:
                    mtime = os.path.getmtime(path)
                    self.file_times[path] = mtime
                except Exception as e:
                    logger.error(f"Failed to get mtime for {path}: {e}")
    
    def start(self) -> None:
        """監視を開始"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("File watcher started")
    
    def stop(self) -> None:
        """監視を停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        logger.info("File watcher stopped")
    
    def _watch_loop(self) -> None:
        """監視ループ"""
        while self.running:
            changes = self.check_changes()
            if changes:
                self._notify_callbacks(changes)
            time.sleep(self.check_interval)
    
    def check_changes(self) -> List[str]:
        """
        変更されたファイルをチェック
        
        Returns:
            変更されたファイルパスのリスト
        """
        changed = []
        
        for path in self.paths:
            if not os.path.exists(path):
                continue
            
            try:
                current_mtime = os.path.getmtime(path)
                
                # 新規ファイルまたは変更されたファイル
                if path not in self.file_times:
                    changed.append(path)
                    self.file_times[path] = current_mtime
                elif current_mtime > self.file_times[path]:
                    changed.append(path)
                    self.file_times[path] = current_mtime
                    
            except Exception as e:
                logger.error(f"Error checking file {path}: {e}")
        
        return changed
    
    def add_callback(self, callback: Callable[[str], None]) -> None:
        """
        変更通知コールバックを追加
        
        Args:
            callback: ファイルパスを引数に取るコールバック関数
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str], None]) -> None:
        """
        コールバックを削除
        
        Args:
            callback: 削除するコールバック関数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, changed_files: List[str]) -> None:
        """
        コールバックに通知
        
        Args:
            changed_files: 変更されたファイルのリスト
        """
        for file_path in changed_files:
            for callback in self.callbacks:
                try:
                    callback(file_path)
                except Exception as e:
                    logger.error(f"Error in file watcher callback: {e}")
    
    def add_path(self, path: str) -> None:
        """
        監視パスを追加
        
        Args:
            path: 追加するパス
        """
        if path not in self.paths:
            self.paths.append(path)
            if os.path.exists(path):
                self.file_times[path] = os.path.getmtime(path)
    
    def remove_path(self, path: str) -> None:
        """
        監視パスを削除
        
        Args:
            path: 削除するパス
        """
        if path in self.paths:
            self.paths.remove(path)
            if path in self.file_times:
                del self.file_times[path]