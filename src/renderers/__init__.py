"""
レンダラーパッケージ

TASK-201: 時計レンダラー
TASK-202: 日付レンダラー  
TASK-203: カレンダーレンダラー
TASK-204: 背景画像レンダラー
"""

# インポートを条件付きにして、エラーを防ぐ
__all__ = []

try:
    from .clock_renderer import ClockRenderer
    __all__.append('ClockRenderer')
except ImportError:
    pass

try:
    from .date_renderer import DateRenderer
    __all__.append('DateRenderer')
except ImportError:
    pass

try:
    from .calendar_renderer import CalendarRenderer
    __all__.append('CalendarRenderer')
except ImportError:
    pass

try:
    from .background_image_renderer import BackgroundImageRenderer
    __all__.append('BackgroundImageRenderer')
except ImportError:
    pass

# シンプルレンダラーも追加
try:
    from .simple_clock_renderer import SimpleClockRenderer
    __all__.append('SimpleClockRenderer')
except ImportError:
    pass

try:
    from .simple_date_renderer import SimpleDateRenderer
    __all__.append('SimpleDateRenderer')
except ImportError:
    pass

try:
    from .simple_calendar_renderer import SimpleCalendarRenderer
    __all__.append('SimpleCalendarRenderer')
except ImportError:
    pass