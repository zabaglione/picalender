#!/usr/bin/env python3
"""
天気スレッド関連の例外クラス

スレッド管理で使用される例外クラスを定義。
"""


class WeatherThreadError(Exception):
    """天気スレッドエラーの基底クラス"""
    pass


class ThreadStartError(WeatherThreadError):
    """スレッド開始エラー"""
    pass


class ThreadStopError(WeatherThreadError):
    """スレッド停止エラー"""
    pass


class UpdateError(WeatherThreadError):
    """更新エラー"""
    pass