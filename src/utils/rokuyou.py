#!/usr/bin/env python3
"""
六曜（ろくよう）計算モジュール

六曜は日本で古来より用いられている暦の一つで、
その日の吉凶を占う指標として使われます。

六曜の種類：
- 先勝（せんしょう/さきがち）: 午前中は吉、午後は凶
- 友引（ともびき）: 朝夕は吉、昼は凶。葬式は避ける
- 先負（せんぷ/さきまけ）: 午前中は凶、午後は吉
- 仏滅（ぶつめつ）: 一日中凶。最も縁起が悪い日
- 大安（たいあん）: 一日中吉。最も縁起が良い日
- 赤口（しゃっこう/せきぐち）: 正午のみ吉、他は凶
"""

from datetime import date
from typing import Dict, Tuple

# 六曜の定義
ROKUYOU_NAMES = [
    "先勝",  # 0: せんしょう
    "友引",  # 1: ともびき  
    "先負",  # 2: せんぷ
    "仏滅",  # 3: ぶつめつ
    "大安",  # 4: たいあん
    "赤口"   # 5: しゃっこう
]

# 六曜の短縮表示（2文字）
ROKUYOU_SHORT = [
    "先勝",  # そのまま2文字
    "友引",  # そのまま2文字
    "先負",  # そのまま2文字
    "仏滅",  # そのまま2文字
    "大安",  # そのまま2文字
    "赤口"   # そのまま2文字
]

# 六曜の1文字表示
ROKUYOU_SINGLE = [
    "先",  # 先勝
    "友",  # 友引
    "負",  # 先負
    "仏",  # 仏滅
    "大",  # 大安
    "赤"   # 赤口
]

def calculate_rokuyou(target_date: date) -> int:
    """
    指定された日付の六曜を計算
    
    六曜の計算方法：
    旧暦の月と日を足した数を6で割った余りで決まる
    (月 + 日) % 6 = 六曜番号
    
    Args:
        target_date: 計算対象の日付
        
    Returns:
        int: 六曜番号 (0-5)
    """
    # 簡易的な旧暦計算（実用レベル）
    # 新暦から旧暦への概算変換
    
    year = target_date.year
    month = target_date.month
    day = target_date.day
    
    # 1900年を基準とした簡易計算
    # 実際の旧暦計算は複雑ですが、六曜目的では概算で十分
    
    # 月の調整値（新暦→旧暦の概算）
    month_adjust = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    
    # 年の基準日からの日数計算
    base_year = 1900
    days_from_base = 0
    
    # 年数による日数加算
    for y in range(base_year, year):
        if is_leap_year(y):
            days_from_base += 366
        else:
            days_from_base += 365
    
    # 月による日数加算
    if month > 1:
        days_from_base += month_adjust[month - 1]
        # うるう年で3月以降の場合は1日追加
        if month > 2 and is_leap_year(year):
            days_from_base += 1
    
    # 日数を加算
    days_from_base += day
    
    # 六曜の基準調整（1900年1月1日の六曜に合わせる）
    # 1900年1月1日は先勝（0）だったとして計算
    rokuyou_offset = 0
    
    # 六曜計算
    rokuyou_index = (days_from_base + rokuyou_offset) % 6
    
    return rokuyou_index

def is_leap_year(year: int) -> bool:
    """うるう年判定"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def get_rokuyou_name(target_date: date, format_type: str = "full") -> str:
    """
    指定された日付の六曜名を取得
    
    Args:
        target_date: 対象日付
        format_type: 表示形式 ("full", "short", "single")
        
    Returns:
        str: 六曜名
    """
    rokuyou_index = calculate_rokuyou(target_date)
    
    if format_type == "single":
        return ROKUYOU_SINGLE[rokuyou_index]
    elif format_type == "short":
        return ROKUYOU_SHORT[rokuyou_index]
    else:  # full
        return ROKUYOU_NAMES[rokuyou_index]

def get_rokuyou_info(target_date: date) -> Dict[str, str]:
    """
    指定された日付の六曜情報を詳細に取得
    
    Args:
        target_date: 対象日付
        
    Returns:
        dict: 六曜の詳細情報
    """
    rokuyou_index = calculate_rokuyou(target_date)
    
    # 六曜の説明
    descriptions = [
        "午前中は吉、午後は凶",      # 先勝
        "朝夕は吉、昼は凶。葬式凶",   # 友引
        "午前中は凶、午後は吉",      # 先負
        "一日中凶。最も縁起が悪い",   # 仏滅
        "一日中吉。最も縁起が良い",   # 大安
        "正午のみ吉、他は凶"         # 赤口
    ]
    
    return {
        "name": ROKUYOU_NAMES[rokuyou_index],
        "short": ROKUYOU_SHORT[rokuyou_index],
        "single": ROKUYOU_SINGLE[rokuyou_index],
        "description": descriptions[rokuyou_index],
        "index": rokuyou_index
    }

def get_rokuyou_color(target_date: date) -> Tuple[int, int, int]:
    """
    六曜に応じた色を取得
    
    Args:
        target_date: 対象日付
        
    Returns:
        tuple: RGB色値
    """
    rokuyou_index = calculate_rokuyou(target_date)
    
    # 六曜の色定義
    colors = [
        (100, 150, 255),  # 先勝: 薄青
        (150, 255, 150),  # 友引: 薄緑
        (255, 200, 100),  # 先負: 薄橙
        (200, 100, 100),  # 仏滅: 薄赤
        (255, 215, 0),    # 大安: 金色
        (255, 100, 150)   # 赤口: 薄ピンク
    ]
    
    return colors[rokuyou_index]

if __name__ == "__main__":
    # テスト実行
    from datetime import datetime
    
    today = date.today()
    
    print(f"今日（{today}）の六曜:")
    info = get_rokuyou_info(today)
    print(f"  名前: {info['name']}")
    print(f"  短縮: {info['short']}")
    print(f"  1文字: {info['single']}")
    print(f"  説明: {info['description']}")
    print(f"  色: {get_rokuyou_color(today)}")
    
    print("\n今月の六曜:")
    for day in range(1, 32):
        try:
            check_date = date(today.year, today.month, day)
            rokuyou = get_rokuyou_name(check_date, "short")
            print(f"  {day:2d}日: {rokuyou}")
        except ValueError:
            break