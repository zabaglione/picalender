"""
イベント処理システム

TASK-102: イベント処理の詳細実装
- キーボード/マウスイベント処理
- カスタムイベント管理
- イベント優先度制御
- イベント記録と再生（デバッグ用）
"""

import pygame
import time
import json
from typing import Dict, List, Callable, Any, Optional, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """イベント処理優先度"""
    CRITICAL = 0    # システムイベント（終了など）
    HIGH = 1        # ユーザー入力
    NORMAL = 2      # 通常のイベント
    LOW = 3         # バックグラウンド処理


class CustomEventType(IntEnum):
    """カスタムイベントタイプ"""
    # pygame.USEREVENT から開始
    WEATHER_UPDATE = pygame.USEREVENT + 1
    TIME_TICK = pygame.USEREVENT + 2
    COMPONENT_READY = pygame.USEREVENT + 3
    PERFORMANCE_WARNING = pygame.USEREVENT + 4
    DEBUG_TOGGLE = pygame.USEREVENT + 5
    SCREENSHOT_REQUEST = pygame.USEREVENT + 6


@dataclass
class EventRecord:
    """イベント記録用データクラス"""
    timestamp: float
    event_type: int
    event_dict: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp,
            'type': self.event_type,
            'data': self.event_dict
        }
    
    @classmethod
    def from_pygame_event(cls, event: pygame.event.Event) -> 'EventRecord':
        """pygameイベントから作成"""
        event_dict = {'type': event.type}
        
        # イベントタイプ別の属性を記録
        if hasattr(event, 'key'):
            event_dict['key'] = event.key
        if hasattr(event, 'unicode'):
            event_dict['unicode'] = event.unicode
        if hasattr(event, 'mod'):
            event_dict['mod'] = event.mod
        if hasattr(event, 'pos'):
            event_dict['pos'] = event.pos
        if hasattr(event, 'button'):
            event_dict['button'] = event.button
        if hasattr(event, 'buttons'):
            event_dict['buttons'] = event.buttons
        if hasattr(event, 'rel'):
            event_dict['rel'] = event.rel
        
        return cls(
            timestamp=time.time(),
            event_type=event.type,
            event_dict=event_dict
        )


class EventHandler:
    """イベントハンドラー管理"""
    
    def __init__(self, handler_func: Callable, priority: EventPriority = EventPriority.NORMAL,
                 enabled: bool = True, filter_func: Optional[Callable] = None):
        """
        初期化
        
        Args:
            handler_func: イベント処理関数
            priority: 処理優先度
            enabled: 有効/無効
            filter_func: イベントフィルター関数
        """
        self.handler_func = handler_func
        self.priority = priority
        self.enabled = enabled
        self.filter_func = filter_func
        self.call_count = 0
        self.last_call_time = 0.0
        self.total_process_time = 0.0
    
    def can_handle(self, event: pygame.event.Event) -> bool:
        """イベントを処理可能かチェック"""
        if not self.enabled:
            return False
        
        if self.filter_func:
            try:
                return self.filter_func(event)
            except Exception as e:
                logger.warning(f"Event filter error: {e}")
                return False
        
        return True
    
    def handle(self, event: pygame.event.Event) -> bool:
        """
        イベントを処理
        
        Returns:
            処理が完了した場合True（他のハンドラーをスキップ）
        """
        if not self.can_handle(event):
            return False
        
        start_time = time.time()
        try:
            result = self.handler_func(event)
            self.call_count += 1
            self.last_call_time = start_time
            self.total_process_time += time.time() - start_time
            return bool(result)
        except Exception as e:
            logger.error(f"Event handler error: {e}")
            return False


class EventSystem:
    """イベントシステム管理"""
    
    def __init__(self, record_events: bool = False, max_records: int = 1000):
        """
        初期化
        
        Args:
            record_events: イベント記録を有効にするか
            max_records: 最大記録数
        """
        self.handlers: Dict[int, List[EventHandler]] = {}
        self.global_handlers: List[EventHandler] = []
        
        # イベント記録
        self.record_events = record_events
        self.event_records: deque = deque(maxlen=max_records)
        
        # 統計情報
        self.event_counts: Dict[int, int] = {}
        self.processing_times: Dict[int, float] = {}
        
        # 再生機能
        self.playback_mode = False
        self.playback_events: List[EventRecord] = []
        self.playback_index = 0
        self.playback_start_time = 0.0
        
        # デフォルトハンドラーを登録
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """デフォルトのイベントハンドラーを登録"""
        # ESCキーで終了
        self.add_handler(
            pygame.KEYDOWN,
            lambda event: event.key == pygame.K_ESCAPE,
            EventPriority.CRITICAL,
            lambda event: pygame.event.post(pygame.event.Event(pygame.QUIT))
        )
        
        # F11でフルスクリーン切り替え
        self.add_handler(
            pygame.KEYDOWN,
            lambda event: event.key == pygame.K_F11,
            EventPriority.HIGH,
            self._toggle_fullscreen
        )
        
        # F12でデバッグモード切り替え
        self.add_handler(
            pygame.KEYDOWN,
            lambda event: event.key == pygame.K_F12,
            EventPriority.HIGH,
            self._toggle_debug_mode
        )
    
    def add_handler(self, event_type: int, filter_func: Optional[Callable],
                   priority: EventPriority, handler_func: Callable) -> EventHandler:
        """
        イベントハンドラーを追加
        
        Args:
            event_type: イベントタイプ
            filter_func: フィルター関数
            priority: 優先度
            handler_func: ハンドラー関数
            
        Returns:
            作成されたEventHandler
        """
        handler = EventHandler(handler_func, priority, True, filter_func)
        
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        # 優先度順でソートして挿入
        self.handlers[event_type].append(handler)
        self.handlers[event_type].sort(key=lambda h: h.priority.value)
        
        logger.debug(f"Added event handler for type {event_type} with priority {priority.name}")
        return handler
    
    def add_global_handler(self, handler_func: Callable, priority: EventPriority = EventPriority.NORMAL,
                          filter_func: Optional[Callable] = None) -> EventHandler:
        """
        全イベント対象のグローバルハンドラーを追加
        
        Args:
            handler_func: ハンドラー関数
            priority: 優先度
            filter_func: フィルター関数
            
        Returns:
            作成されたEventHandler
        """
        handler = EventHandler(handler_func, priority, True, filter_func)
        self.global_handlers.append(handler)
        self.global_handlers.sort(key=lambda h: h.priority.value)
        return handler
    
    def remove_handler(self, event_type: int, handler: EventHandler):
        """イベントハンドラーを削除"""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
    
    def remove_global_handler(self, handler: EventHandler):
        """グローバルハンドラーを削除"""
        if handler in self.global_handlers:
            self.global_handlers.remove(handler)
    
    def process_events(self) -> List[pygame.event.Event]:
        """
        イベントを処理
        
        Returns:
            処理されなかったイベントのリスト
        """
        unhandled_events = []
        
        if self.playback_mode:
            events = self._get_playback_events()
        else:
            events = pygame.event.get()
        
        for event in events:
            # イベントを記録
            if self.record_events and not self.playback_mode:
                self.event_records.append(EventRecord.from_pygame_event(event))
            
            # 統計更新
            self.event_counts[event.type] = self.event_counts.get(event.type, 0) + 1
            
            handled = False
            
            # グローバルハンドラーを最初に処理
            for handler in self.global_handlers:
                if handler.handle(event):
                    handled = True
                    break
            
            # 特定タイプのハンドラーを処理
            if not handled and event.type in self.handlers:
                for handler in self.handlers[event.type]:
                    if handler.handle(event):
                        handled = True
                        break
            
            # 処理されなかったイベントを記録
            if not handled:
                unhandled_events.append(event)
        
        return unhandled_events
    
    def post_custom_event(self, event_type: CustomEventType, data: Dict[str, Any] = None):
        """カスタムイベントを投稿"""
        event_dict = {}
        if data:
            event_dict.update(data)
        
        custom_event = pygame.event.Event(event_type.value, event_dict)
        pygame.event.post(custom_event)
        
        logger.debug(f"Posted custom event: {event_type.name}")
    
    def start_recording(self):
        """イベント記録を開始"""
        self.record_events = True
        self.event_records.clear()
        logger.info("Event recording started")
    
    def stop_recording(self):
        """イベント記録を停止"""
        self.record_events = False
        logger.info(f"Event recording stopped. Recorded {len(self.event_records)} events")
    
    def save_recording(self, filename: str):
        """記録したイベントをファイルに保存"""
        if not self.event_records:
            logger.warning("No events to save")
            return
        
        data = {
            'events': [record.to_dict() for record in self.event_records],
            'total_time': self.event_records[-1].timestamp - self.event_records[0].timestamp
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Events saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save events: {e}")
    
    def load_recording(self, filename: str) -> bool:
        """記録したイベントをファイルから読み込み"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.playback_events = []
            for event_data in data['events']:
                record = EventRecord(
                    timestamp=event_data['timestamp'],
                    event_type=event_data['type'],
                    event_dict=event_data['data']
                )
                self.playback_events.append(record)
            
            logger.info(f"Loaded {len(self.playback_events)} events from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load events: {e}")
            return False
    
    def start_playback(self):
        """イベント再生を開始"""
        if not self.playback_events:
            logger.warning("No events to playback")
            return
        
        self.playback_mode = True
        self.playback_index = 0
        self.playback_start_time = time.time()
        logger.info(f"Started event playback with {len(self.playback_events)} events")
    
    def stop_playback(self):
        """イベント再生を停止"""
        self.playback_mode = False
        self.playback_index = 0
        logger.info("Event playback stopped")
    
    def _get_playback_events(self) -> List[pygame.event.Event]:
        """再生用のイベントを取得"""
        if not self.playback_mode or self.playback_index >= len(self.playback_events):
            return []
        
        current_time = time.time()
        relative_time = current_time - self.playback_start_time
        events = []
        
        # 時刻に基づいてイベントを取得
        while (self.playback_index < len(self.playback_events) and
               self.playback_events[self.playback_index].timestamp <= 
               self.playback_events[0].timestamp + relative_time):
            
            record = self.playback_events[self.playback_index]
            event = pygame.event.Event(record.event_type, record.event_dict)
            events.append(event)
            self.playback_index += 1
        
        return events
    
    def _toggle_fullscreen(self, event: pygame.event.Event):
        """フルスクリーンを切り替え"""
        self.post_custom_event(CustomEventType.DEBUG_TOGGLE, {'action': 'fullscreen'})
        return True
    
    def _toggle_debug_mode(self, event: pygame.event.Event):
        """デバッグモードを切り替え"""
        self.post_custom_event(CustomEventType.DEBUG_TOGGLE, {'action': 'debug'})
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """イベント処理統計を取得"""
        total_events = sum(self.event_counts.values())
        handler_stats = {}
        
        # ハンドラー統計
        for event_type, handlers in self.handlers.items():
            for i, handler in enumerate(handlers):
                key = f"type_{event_type}_handler_{i}"
                handler_stats[key] = {
                    'call_count': handler.call_count,
                    'total_time': handler.total_process_time,
                    'avg_time': handler.total_process_time / max(handler.call_count, 1),
                    'enabled': handler.enabled
                }
        
        return {
            'total_events': total_events,
            'event_counts': self.event_counts.copy(),
            'handler_stats': handler_stats,
            'recording': self.record_events,
            'recorded_events': len(self.event_records),
            'playback_mode': self.playback_mode,
            'playback_progress': self.playback_index / max(len(self.playback_events), 1)
        }
    
    def clear_statistics(self):
        """統計情報をクリア"""
        self.event_counts.clear()
        self.processing_times.clear()
        
        # ハンドラー統計もクリア
        for handlers in self.handlers.values():
            for handler in handlers:
                handler.call_count = 0
                handler.total_process_time = 0.0
        
        for handler in self.global_handlers:
            handler.call_count = 0
            handler.total_process_time = 0.0