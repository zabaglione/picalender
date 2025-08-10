"""
ファイル監視システム実装

TASK-103: 動的リロード機能
- ファイル変更検出
- 自動リロード
- 依存関係更新
"""

import os
import time
import threading
import logging
from typing import Dict, Callable, List, Optional, Any
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class FileMonitor:
    """ファイル監視クラス"""
    
    def __init__(self, poll_interval: float = 1.0):
        """
        初期化
        
        Args:
            poll_interval: ポーリング間隔（秒）
        """
        self.poll_interval = poll_interval
        self.watching = False
        self.watch_thread: Optional[threading.Thread] = None
        
        # 監視対象ファイルと対応するハンドラー
        self.watched_files: Dict[str, Dict[str, Any]] = {}
        
        # ファイルの最終変更時刻とハッシュを記録
        self.file_states: Dict[str, Dict[str, Any]] = {}
        
        # イベント統計
        self.event_count = 0
        
    def add_watch(self, file_path: str, event_handler: Callable[[str, str], None]) -> None:
        """
        ファイル監視を追加
        
        Args:
            file_path: 監視対象ファイルパス
            event_handler: イベントハンドラー関数 (event_type, file_path)
        """
        abs_path = os.path.abspath(file_path)
        
        # 監視情報を記録
        self.watched_files[abs_path] = {
            'handler': event_handler,
            'exists': os.path.exists(abs_path)
        }
        
        # 初期状態を記録
        self._update_file_state(abs_path)
        
        logger.debug(f"Added file watch: {abs_path}")
    
    def remove_watch(self, file_path: str) -> None:
        """
        ファイル監視を削除
        
        Args:
            file_path: 監視対象ファイルパス
        """
        abs_path = os.path.abspath(file_path)
        
        if abs_path in self.watched_files:
            del self.watched_files[abs_path]
            
        if abs_path in self.file_states:
            del self.file_states[abs_path]
            
        logger.debug(f"Removed file watch: {abs_path}")
    
    def start(self) -> None:
        """監視を開始"""
        if not self.watching:
            self.watching = True
            self.watch_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.watch_thread.start()
            logger.info("File monitoring started")
    
    def stop(self) -> None:
        """監視を停止"""
        if self.watching:
            self.watching = False
            if self.watch_thread and self.watch_thread.is_alive():
                self.watch_thread.join(timeout=2.0)
            logger.info("File monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """監視メインループ"""
        while self.watching:
            try:
                self._check_file_changes()
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                time.sleep(self.poll_interval)
    
    def _check_file_changes(self) -> None:
        """ファイル変更をチェック"""
        for file_path, watch_info in list(self.watched_files.items()):
            try:
                current_exists = os.path.exists(file_path)
                previous_exists = watch_info['exists']
                
                # ファイルの存在状態変化をチェック
                if current_exists != previous_exists:
                    if current_exists:
                        self._trigger_event("created", file_path, watch_info['handler'])
                    else:
                        self._trigger_event("deleted", file_path, watch_info['handler'])
                    
                    # 状態更新
                    watch_info['exists'] = current_exists
                    self._update_file_state(file_path)
                    continue
                
                # ファイルが存在する場合のみ変更チェック
                if current_exists:
                    if self._has_file_changed(file_path):
                        self._trigger_event("modified", file_path, watch_info['handler'])
                        self._update_file_state(file_path)
                        
            except Exception as e:
                logger.warning(f"Error checking file {file_path}: {e}")
    
    def _has_file_changed(self, file_path: str) -> bool:
        """
        ファイルが変更されたかチェック
        
        Args:
            file_path: ファイルパス
            
        Returns:
            変更有無
        """
        try:
            # 修正時刻チェック
            current_mtime = os.path.getmtime(file_path)
            previous_state = self.file_states.get(file_path, {})
            previous_mtime = previous_state.get('mtime', 0)
            
            if current_mtime != previous_mtime:
                # 修正時刻が変更された場合、ハッシュでも確認
                return self._has_content_changed(file_path)
            
            return False
            
        except (OSError, IOError):
            return False
    
    def _has_content_changed(self, file_path: str) -> bool:
        """
        ファイル内容が変更されたかハッシュでチェック
        
        Args:
            file_path: ファイルパス
            
        Returns:
            内容変更有無
        """
        try:
            current_hash = self._calculate_file_hash(file_path)
            previous_state = self.file_states.get(file_path, {})
            previous_hash = previous_state.get('hash', '')
            
            return current_hash != previous_hash
            
        except Exception:
            return True  # エラーの場合は変更ありと判定
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        ファイルのハッシュ値を計算
        
        Args:
            file_path: ファイルパス
            
        Returns:
            ハッシュ値
        """
        hash_obj = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # 大きなファイルの場合はチャンクごとに読み込み
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""
    
    def _update_file_state(self, file_path: str) -> None:
        """
        ファイル状態を更新
        
        Args:
            file_path: ファイルパス
        """
        try:
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                file_hash = self._calculate_file_hash(file_path)
                size = os.path.getsize(file_path)
                
                self.file_states[file_path] = {
                    'mtime': mtime,
                    'hash': file_hash,
                    'size': size,
                    'last_checked': time.time()
                }
            else:
                # ファイルが存在しない場合
                self.file_states[file_path] = {
                    'mtime': 0,
                    'hash': '',
                    'size': 0,
                    'last_checked': time.time()
                }
        except Exception as e:
            logger.warning(f"Failed to update file state for {file_path}: {e}")
    
    def _trigger_event(self, event_type: str, file_path: str, 
                      handler: Callable[[str, str], None]) -> None:
        """
        イベントを発火
        
        Args:
            event_type: イベントタイプ
            file_path: ファイルパス
            handler: イベントハンドラー
        """
        try:
            handler(event_type, file_path)
            self.event_count += 1
            logger.debug(f"File event: {event_type} - {file_path}")
        except Exception as e:
            logger.error(f"Event handler error: {e}")
    
    def add_directory_watch(self, dir_path: str, 
                           event_handler: Callable[[str, str], None],
                           recursive: bool = False) -> None:
        """
        ディレクトリ内の全ファイルを監視
        
        Args:
            dir_path: ディレクトリパス
            event_handler: イベントハンドラー
            recursive: 再帰的に監視するか
        """
        dir_path = os.path.abspath(dir_path)
        
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            logger.warning(f"Directory not found: {dir_path}")
            return
        
        # ディレクトリ内のファイルを監視対象に追加
        if recursive:
            for root, dirs, files in os.walk(dir_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    self.add_watch(file_path, event_handler)
        else:
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    self.add_watch(file_path, event_handler)
        
        logger.info(f"Added directory watch: {dir_path} (recursive: {recursive})")
    
    def get_watched_files(self) -> List[str]:
        """
        監視中のファイル一覧を取得
        
        Returns:
            監視中ファイルパスのリスト
        """
        return list(self.watched_files.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        監視統計情報を取得
        
        Returns:
            統計情報
        """
        return {
            'watching': self.watching,
            'watched_file_count': len(self.watched_files),
            'event_count': self.event_count,
            'poll_interval': self.poll_interval,
            'thread_active': self.watch_thread is not None and self.watch_thread.is_alive()
        }
    
    def force_check(self) -> None:
        """強制的にファイルチェックを実行"""
        if self.watching:
            self._check_file_changes()
            logger.debug("Forced file check completed")