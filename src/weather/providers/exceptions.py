#!/usr/bin/env python3
"""
天気プロバイダ例外クラス定義

天気データ取得に関する各種例外を定義する。
"""


class WeatherProviderError(Exception):
    """天気プロバイダ基底例外"""
    
    def __init__(self, message: str, details: str = None):
        """
        例外初期化
        
        Args:
            message: エラーメッセージ
            details: 詳細情報（オプション）
        """
        super().__init__(message)
        self.message = message
        self.details = details


class NetworkError(WeatherProviderError):
    """ネットワーク関連エラー
    
    接続タイムアウト、DNS解決失敗、SSL証明書エラーなど
    ネットワーク通信に関連するエラーで使用される。
    """
    pass


class APIError(WeatherProviderError):
    """API関連エラー
    
    HTTP 4XX/5XXエラー、API制限、認証失敗など
    天気APIとの通信で発生するエラーで使用される。
    """
    pass


class DataFormatError(WeatherProviderError):
    """データ形式エラー
    
    不正なJSON、必須フィールド欠如、型不整合など
    レスポンスデータの形式に問題がある場合に使用される。
    """
    pass


class AuthenticationError(WeatherProviderError):
    """認証エラー
    
    APIキー無効、認証失敗、権限不足など
    認証に関連するエラーで使用される。
    """
    pass