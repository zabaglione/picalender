#!/usr/bin/env python3
"""
天気アイコン画像を生成するスクリプト
"""

import os
import sys
from pathlib import Path

# Pillowライブラリを使用
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillowライブラリが必要です: pip3 install Pillow")
    sys.exit(1)

# アイコンディレクトリ
ICONS_DIR = Path(__file__).parent.parent / "assets" / "weather_icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# アイコンサイズ
ICON_SIZE = 64
HALF_SIZE = 48

def create_circle(size, color, bg_color=(0, 0, 0, 0)):
    """円形のアイコンを作成"""
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    padding = 2
    draw.ellipse([padding, padding, size-padding, size-padding], fill=color)
    return img

def create_cloud(size, color):
    """雲のアイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 雲の形を楕円で近似
    # メインの雲
    draw.ellipse([size*0.2, size*0.4, size*0.8, size*0.7], fill=color)
    # 上部の膨らみ
    draw.ellipse([size*0.3, size*0.25, size*0.6, size*0.55], fill=color)
    draw.ellipse([size*0.5, size*0.3, size*0.75, size*0.6], fill=color)
    
    return img

def create_rain_drops(img, x_offset=0, y_offset=0):
    """雨粒を追加"""
    draw = ImageDraw.Draw(img)
    rain_color = (100, 150, 255, 200)
    
    # 雨粒の位置
    drops = [
        (0.3, 0.7), (0.5, 0.75), (0.7, 0.7),
        (0.4, 0.85), (0.6, 0.85)
    ]
    
    for x, y in drops:
        drop_x = img.width * x + x_offset
        drop_y = img.height * y + y_offset
        # 雨粒（小さな楕円）
        draw.ellipse([drop_x-2, drop_y-4, drop_x+2, drop_y+4], fill=rain_color)
    
    return img

def create_snow_flakes(img, x_offset=0, y_offset=0):
    """雪の結晶を追加"""
    draw = ImageDraw.Draw(img)
    snow_color = (255, 255, 255, 230)
    
    # 雪の結晶の位置
    flakes = [
        (0.3, 0.7), (0.5, 0.75), (0.7, 0.7),
        (0.4, 0.85), (0.6, 0.85)
    ]
    
    for x, y in flakes:
        flake_x = img.width * x + x_offset
        flake_y = img.height * y + y_offset
        # 雪の結晶（十字とX字を重ねる）
        draw.line([flake_x-4, flake_y, flake_x+4, flake_y], fill=snow_color, width=2)
        draw.line([flake_x, flake_y-4, flake_x, flake_y+4], fill=snow_color, width=2)
        draw.line([flake_x-3, flake_y-3, flake_x+3, flake_y+3], fill=snow_color, width=1)
        draw.line([flake_x-3, flake_y+3, flake_x+3, flake_y-3], fill=snow_color, width=1)
    
    return img

def create_thunder_bolt(img, x_offset=0, y_offset=0):
    """稲妻を追加"""
    draw = ImageDraw.Draw(img)
    thunder_color = (255, 255, 100, 255)
    
    # 稲妻の形
    bolt_x = img.width * 0.5 + x_offset
    bolt_y = img.height * 0.5 + y_offset
    
    points = [
        (bolt_x-5, bolt_y),
        (bolt_x-2, bolt_y+8),
        (bolt_x+2, bolt_y+6),
        (bolt_x, bolt_y+15),
        (bolt_x+5, bolt_y+3),
        (bolt_x+1, bolt_y+5),
        (bolt_x+3, bolt_y-3)
    ]
    
    draw.polygon(points, fill=thunder_color)
    return img

def generate_icons():
    """全ての天気アイコンを生成"""
    
    print("天気アイコンを生成中...")
    
    # 1. 晴れ (sunny.png)
    sunny = create_circle(ICON_SIZE, (255, 220, 0))
    # 太陽の光線を追加
    draw = ImageDraw.Draw(sunny)
    center = ICON_SIZE // 2
    for angle in range(0, 360, 45):
        import math
        x1 = center + 20 * math.cos(math.radians(angle))
        y1 = center + 20 * math.sin(math.radians(angle))
        x2 = center + 28 * math.cos(math.radians(angle))
        y2 = center + 28 * math.sin(math.radians(angle))
        draw.line([x1, y1, x2, y2], fill=(255, 220, 0), width=3)
    sunny.save(ICONS_DIR / "sunny.png")
    print("  ✓ sunny.png")
    
    # 2. 曇り (cloudy.png)
    cloudy = create_cloud(ICON_SIZE, (200, 200, 200))
    cloudy.save(ICONS_DIR / "cloudy.png")
    print("  ✓ cloudy.png")
    
    # 3. 雨 (rainy.png)
    rainy = create_cloud(ICON_SIZE, (150, 150, 150))
    rainy = create_rain_drops(rainy)
    rainy.save(ICONS_DIR / "rainy.png")
    print("  ✓ rainy.png")
    
    # 4. 雪 (snowy.png)
    snowy = create_cloud(ICON_SIZE, (220, 220, 220))
    snowy = create_snow_flakes(snowy)
    snowy.save(ICONS_DIR / "snowy.png")
    print("  ✓ snowy.png")
    
    # 5. 雷雨 (thunder.png)
    thunder = create_cloud(ICON_SIZE, (100, 100, 100))
    thunder = create_thunder_bolt(thunder)
    thunder = create_rain_drops(thunder)
    thunder.save(ICONS_DIR / "thunder.png")
    print("  ✓ thunder.png")
    
    # 6. 霧 (foggy.png)
    foggy = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(foggy)
    # 横線で霧を表現
    for y in range(20, 50, 8):
        draw.rectangle([10, y, 54, y+3], fill=(200, 200, 200, 150))
    foggy.save(ICONS_DIR / "foggy.png")
    print("  ✓ foggy.png")
    
    # 7. 晴れ時々曇り (partly_cloudy.png)
    partly_cloudy = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    # 太陽を左上に配置
    sun_small = create_circle(HALF_SIZE, (255, 220, 0))
    partly_cloudy.paste(sun_small, (5, 5), sun_small)
    # 雲を右下に配置
    cloud_small = create_cloud(HALF_SIZE, (200, 200, 200))
    partly_cloudy.paste(cloud_small, (20, 20), cloud_small)
    partly_cloudy.save(ICONS_DIR / "partly_cloudy.png")
    print("  ✓ partly_cloudy.png")
    
    # 8. 曇り時々雨 (cloudy_rainy.png)
    cloudy_rainy = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    # 雲を上部に配置
    cloud_top = create_cloud(ICON_SIZE, (180, 180, 180))
    cloudy_rainy.paste(cloud_top, (0, -10), cloud_top)
    # 雨粒を右側に追加
    create_rain_drops(cloudy_rainy, 15, 0)
    cloudy_rainy.save(ICONS_DIR / "cloudy_rainy.png")
    print("  ✓ cloudy_rainy.png")
    
    # 9. 曇りのち雨 (cloudy_then_rainy.png)
    cloudy_then_rainy = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    # 左側に曇り
    cloud_left = create_cloud(HALF_SIZE, (200, 200, 200))
    cloudy_then_rainy.paste(cloud_left, (0, 10), cloud_left)
    # 矢印
    draw = ImageDraw.Draw(cloudy_then_rainy)
    draw.line([30, 32, 38, 32], fill=(100, 100, 100), width=2)
    draw.polygon([(38, 32), (35, 29), (35, 35)], fill=(100, 100, 100))
    # 右側に雨
    rain_cloud = create_cloud(HALF_SIZE, (150, 150, 150))
    rain_cloud = create_rain_drops(rain_cloud)
    cloudy_then_rainy.paste(rain_cloud, (32, 10), rain_cloud)
    cloudy_then_rainy.save(ICONS_DIR / "cloudy_then_rainy.png")
    print("  ✓ cloudy_then_rainy.png")
    
    # 10. 晴れのち曇り (sunny_then_cloudy.png)
    sunny_then_cloudy = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    # 左側に太陽
    sun_left = create_circle(HALF_SIZE-5, (255, 220, 0))
    sunny_then_cloudy.paste(sun_left, (2, 12), sun_left)
    # 矢印
    draw = ImageDraw.Draw(sunny_then_cloudy)
    draw.line([28, 32, 36, 32], fill=(100, 100, 100), width=2)
    draw.polygon([(36, 32), (33, 29), (33, 35)], fill=(100, 100, 100))
    # 右側に雲
    cloud_right = create_cloud(HALF_SIZE, (200, 200, 200))
    sunny_then_cloudy.paste(cloud_right, (32, 10), cloud_right)
    sunny_then_cloudy.save(ICONS_DIR / "sunny_then_cloudy.png")
    print("  ✓ sunny_then_cloudy.png")
    
    # 11. デフォルト/不明 (unknown.png)
    unknown = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(unknown)
    draw.text((ICON_SIZE//2, ICON_SIZE//2), "?", fill=(150, 150, 150), anchor="mm")
    unknown.save(ICONS_DIR / "unknown.png")
    print("  ✓ unknown.png")
    
    print(f"\n全てのアイコンを生成しました: {ICONS_DIR}")
    print(f"生成されたアイコン数: {len(list(ICONS_DIR.glob('*.png')))}")

if __name__ == "__main__":
    generate_icons()