#!/usr/bin/env python3
"""
月齢・月相計算モジュール

月の満ち欠けを計算し、現在の月相を判定します。
"""

from datetime import date, datetime, timedelta
from typing import Dict, Tuple
import math

# 月相の定義
MOON_PHASES = {
    "new": "新月",
    "waxing_crescent": "三日月",
    "first_quarter": "上弦",
    "waxing_gibbous": "十三夜",
    "full": "満月",
    "waning_gibbous": "寝待月",
    "last_quarter": "下弦",
    "waning_crescent": "有明月"
}

# 月相の絵文字（Unicode）
MOON_EMOJIS = {
    "new": "🌑",
    "waxing_crescent": "🌒",
    "first_quarter": "🌓",
    "waxing_gibbous": "🌔",
    "full": "🌕",
    "waning_gibbous": "🌖",
    "last_quarter": "🌗",
    "waning_crescent": "🌘"
}

# 月相のASCIIアート（小サイズ）
MOON_ASCII = {
    "new": "●",
    "waxing_crescent": ")",
    "first_quarter": "D",
    "waxing_gibbous": "⊃",
    "full": "○",
    "waning_gibbous": "⊂",
    "last_quarter": "C",
    "waning_crescent": "("
}

def calculate_moon_age(target_date: date) -> float:
    """
    指定された日付の月齢を計算
    
    月齢は新月を0として、満月が約14.75日となる周期で計算されます。
    1朔望月（新月から次の新月まで）は約29.53日です。
    
    Args:
        target_date: 計算対象の日付
        
    Returns:
        float: 月齢（0.0〜29.53）
    """
    # 基準日（既知の新月日）: 2000年1月6日 18:14 UTC
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    
    # 対象日のdatetimeオブジェクトを作成（正午で計算）
    if isinstance(target_date, date) and not isinstance(target_date, datetime):
        target_datetime = datetime.combine(target_date, datetime.min.time())
        target_datetime = target_datetime.replace(hour=12)  # 正午
    else:
        target_datetime = target_date
    
    # 基準日からの経過日数
    days_elapsed = (target_datetime - known_new_moon).total_seconds() / 86400
    
    # 朔望月の周期（日数）
    lunation_period = 29.530588853
    
    # 月齢を計算（0〜29.53の範囲）
    moon_age = days_elapsed % lunation_period
    
    return moon_age

def get_moon_phase(target_date: date) -> str:
    """
    指定された日付の月相を取得
    
    Args:
        target_date: 対象日付
        
    Returns:
        str: 月相のキー（new, waxing_crescent, etc.）
    """
    moon_age = calculate_moon_age(target_date)
    
    # 月齢から月相を判定
    # 各月相の範囲（概算）
    if moon_age < 1.84:
        return "new"
    elif moon_age < 5.53:
        return "waxing_crescent"
    elif moon_age < 9.22:
        return "first_quarter"
    elif moon_age < 12.91:
        return "waxing_gibbous"
    elif moon_age < 16.61:
        return "full"
    elif moon_age < 20.30:
        return "waning_gibbous"
    elif moon_age < 23.99:
        return "last_quarter"
    elif moon_age < 27.68:
        return "waning_crescent"
    else:
        return "new"

def get_moon_info(target_date: date) -> Dict[str, any]:
    """
    指定された日付の月の詳細情報を取得
    
    Args:
        target_date: 対象日付
        
    Returns:
        dict: 月の詳細情報
    """
    moon_age = calculate_moon_age(target_date)
    moon_phase = get_moon_phase(target_date)
    
    # 照明率を計算（簡易版）
    illumination = (1 - math.cos(2 * math.pi * moon_age / 29.530588853)) / 2
    
    return {
        "age": round(moon_age, 1),
        "phase": moon_phase,
        "phase_name": MOON_PHASES[moon_phase],
        "emoji": MOON_EMOJIS[moon_phase],
        "ascii": MOON_ASCII[moon_phase],
        "illumination": round(illumination * 100, 1)
    }

def get_moon_display(target_date: date, format_type: str = "emoji") -> str:
    """
    表示用の月相文字列を取得
    
    Args:
        target_date: 対象日付
        format_type: 表示形式（"emoji", "text", "ascii", "full"）
        
    Returns:
        str: 表示用文字列
    """
    info = get_moon_info(target_date)
    
    if format_type == "emoji":
        return info["emoji"]
    elif format_type == "text":
        return info["phase_name"]
    elif format_type == "ascii":
        return info["ascii"]
    elif format_type == "full":
        return f"{info['emoji']} {info['phase_name']} (月齢{info['age']})"
    else:
        return info["emoji"]

def get_next_moon_phases(start_date: date, days: int = 30) -> list:
    """
    今後の主要な月相の日付を取得
    
    Args:
        start_date: 開始日
        days: 検索する日数
        
    Returns:
        list: 月相変化の日付リスト
    """
    phases = []
    current_phase = get_moon_phase(start_date)
    
    for i in range(1, days + 1):
        check_date = start_date + timedelta(days=i)
        new_phase = get_moon_phase(check_date)
        
        if new_phase != current_phase:
            phases.append({
                "date": check_date,
                "phase": new_phase,
                "name": MOON_PHASES[new_phase]
            })
            current_phase = new_phase
    
    return phases

if __name__ == "__main__":
    # テスト実行
    from datetime import datetime
    
    today = date.today()
    
    print(f"今日（{today}）の月情報:")
    info = get_moon_info(today)
    print(f"  月齢: {info['age']}日")
    print(f"  月相: {info['phase_name']}")
    print(f"  絵文字: {info['emoji']}")
    print(f"  ASCII: {info['ascii']}")
    print(f"  照明率: {info['illumination']}%")
    print()
    
    print("今月の月相:")
    for day in range(1, 32):
        try:
            check_date = date(today.year, today.month, day)
            display = get_moon_display(check_date, "full")
            print(f"  {day:2d}日: {display}")
        except ValueError:
            break
    
    print("\n今後30日間の月相変化:")
    next_phases = get_next_moon_phases(today, 30)
    for phase_info in next_phases[:5]:  # 最初の5件のみ表示
        print(f"  {phase_info['date']}: {phase_info['name']}")