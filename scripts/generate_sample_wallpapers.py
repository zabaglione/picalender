#!/usr/bin/env python3
"""
サンプル壁紙を生成するスクリプト
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillowライブラリが必要です: pip3 install Pillow")
    exit(1)

# 壁紙ディレクトリ
WALLPAPER_DIR = Path(__file__).parent.parent / "wallpapers"
WALLPAPER_DIR.mkdir(exist_ok=True)

def create_gradient_wallpaper(name, color1, color2, size=(1024, 600)):
    """グラデーション壁紙を作成"""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    
    for y in range(size[1]):
        ratio = y / size[1]
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.rectangle([(0, y), (size[0], y+1)], fill=(r, g, b))
    
    return img

def create_pattern_wallpaper(name, primary_color, secondary_color, size=(1024, 600)):
    """パターン壁紙を作成"""
    img = Image.new('RGB', size, primary_color)
    draw = ImageDraw.Draw(img)
    
    # 円のパターン
    for x in range(0, size[0], 50):
        for y in range(0, size[1], 50):
            if (x // 50 + y // 50) % 2 == 0:
                draw.ellipse([x, y, x+30, y+30], fill=secondary_color)
    
    return img

def generate_wallpapers():
    """サンプル壁紙を生成"""
    print("サンプル壁紙を生成中...")
    
    # 1. 朝のグラデーション
    morning = create_gradient_wallpaper(
        "morning",
        (255, 200, 150),  # 薄いオレンジ
        (150, 200, 255)   # 薄い青
    )
    morning.save(WALLPAPER_DIR / "01_morning.jpg", quality=90)
    print("  ✓ 01_morning.jpg")
    
    # 2. 昼のグラデーション
    noon = create_gradient_wallpaper(
        "noon",
        (135, 206, 235),  # スカイブルー
        (255, 255, 255)   # 白
    )
    noon.save(WALLPAPER_DIR / "02_noon.jpg", quality=90)
    print("  ✓ 02_noon.jpg")
    
    # 3. 夕方のグラデーション
    evening = create_gradient_wallpaper(
        "evening",
        (255, 150, 100),  # オレンジ
        (100, 50, 150)    # 紫
    )
    evening.save(WALLPAPER_DIR / "03_evening.jpg", quality=90)
    print("  ✓ 03_evening.jpg")
    
    # 4. 夜のグラデーション
    night = create_gradient_wallpaper(
        "night",
        (10, 20, 40),     # 濃い青
        (50, 60, 100)     # 少し明るい青
    )
    night.save(WALLPAPER_DIR / "04_night.jpg", quality=90)
    print("  ✓ 04_night.jpg")
    
    # 5. パターン壁紙（青系）
    pattern_blue = create_pattern_wallpaper(
        "pattern_blue",
        (30, 60, 120),    # 濃い青
        (60, 120, 200)    # 明るい青
    )
    pattern_blue.save(WALLPAPER_DIR / "05_pattern_blue.jpg", quality=90)
    print("  ✓ 05_pattern_blue.jpg")
    
    # 6. パターン壁紙（緑系）
    pattern_green = create_pattern_wallpaper(
        "pattern_green",
        (20, 80, 40),     # 濃い緑
        (80, 200, 100)    # 明るい緑
    )
    pattern_green.save(WALLPAPER_DIR / "06_pattern_green.jpg", quality=90)
    print("  ✓ 06_pattern_green.jpg")
    
    print(f"\n壁紙を生成しました: {WALLPAPER_DIR}")
    print(f"生成された壁紙数: {len(list(WALLPAPER_DIR.glob('*.jpg')))}")

if __name__ == "__main__":
    generate_wallpapers()