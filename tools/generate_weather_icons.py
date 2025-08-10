#!/usr/bin/env python3
"""
天気アイコン生成ツール

プログラムで天気アイコンを生成
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
import math


def create_sunny_icon(size: int) -> Image.Image:
    """晴れアイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    radius = size // 4
    
    # 太陽の本体
    draw.ellipse([center - radius, center - radius, 
                  center + radius, center + radius],
                 fill=(255, 200, 0), outline=(255, 180, 0), width=2)
    
    # 光線
    ray_length = size // 6
    ray_count = 8
    for i in range(ray_count):
        angle = i * (2 * math.pi / ray_count)
        start_r = radius + 5
        end_r = radius + ray_length
        
        x1 = center + start_r * math.cos(angle)
        y1 = center + start_r * math.sin(angle)
        x2 = center + end_r * math.cos(angle)
        y2 = center + end_r * math.sin(angle)
        
        draw.line([x1, y1, x2, y2], fill=(255, 200, 0), width=3)
    
    return img


def create_cloudy_icon(size: int) -> Image.Image:
    """曇りアイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 雲の色
    cloud_color = (200, 200, 200)
    cloud_outline = (180, 180, 180)
    
    # 雲を円の組み合わせで描画
    circles = [
        (size * 0.35, size * 0.5, size * 0.18),  # 左
        (size * 0.5, size * 0.45, size * 0.22),   # 中央上
        (size * 0.65, size * 0.5, size * 0.18),   # 右
        (size * 0.5, size * 0.55, size * 0.15),   # 中央下
    ]
    
    for x, y, r in circles:
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=cloud_color, outline=cloud_outline, width=2)
    
    return img


def create_partly_cloudy_icon(size: int) -> Image.Image:
    """晴れ時々曇りアイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 太陽（少し小さめ、左上に配置）
    sun_center_x = size * 0.35
    sun_center_y = size * 0.35
    sun_radius = size // 6
    
    # 太陽の本体
    draw.ellipse([sun_center_x - sun_radius, sun_center_y - sun_radius,
                  sun_center_x + sun_radius, sun_center_y + sun_radius],
                 fill=(255, 200, 0), outline=(255, 180, 0), width=2)
    
    # 短い光線
    ray_length = size // 12
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        start_r = sun_radius + 3
        end_r = sun_radius + ray_length
        
        x1 = sun_center_x + start_r * math.cos(angle)
        y1 = sun_center_y + start_r * math.sin(angle)
        x2 = sun_center_x + end_r * math.cos(angle)
        y2 = sun_center_y + end_r * math.sin(angle)
        
        draw.line([x1, y1, x2, y2], fill=(255, 200, 0), width=2)
    
    # 雲（右下に配置）
    cloud_color = (220, 220, 220)
    cloud_outline = (200, 200, 200)
    
    circles = [
        (size * 0.5, size * 0.6, size * 0.15),
        (size * 0.65, size * 0.6, size * 0.18),
        (size * 0.55, size * 0.7, size * 0.12),
    ]
    
    for x, y, r in circles:
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=cloud_color, outline=cloud_outline, width=2)
    
    return img


def create_rain_icon(size: int) -> Image.Image:
    """雨アイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 暗い雲
    cloud_color = (150, 150, 150)
    cloud_outline = (130, 130, 130)
    
    circles = [
        (size * 0.35, size * 0.35, size * 0.18),
        (size * 0.5, size * 0.3, size * 0.22),
        (size * 0.65, size * 0.35, size * 0.18),
    ]
    
    for x, y, r in circles:
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=cloud_color, outline=cloud_outline, width=2)
    
    # 雨粒
    rain_color = (100, 150, 255)
    drop_width = 3
    drop_height = size // 8
    
    drops = [
        (size * 0.3, size * 0.55),
        (size * 0.5, size * 0.6),
        (size * 0.7, size * 0.55),
        (size * 0.4, size * 0.7),
        (size * 0.6, size * 0.7),
    ]
    
    for x, y in drops:
        draw.line([x, y, x - 2, y + drop_height], fill=rain_color, width=drop_width)
    
    return img


def create_thunder_icon(size: int) -> Image.Image:
    """雷アイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 暗い雲
    cloud_color = (100, 100, 100)
    cloud_outline = (80, 80, 80)
    
    circles = [
        (size * 0.35, size * 0.3, size * 0.18),
        (size * 0.5, size * 0.25, size * 0.22),
        (size * 0.65, size * 0.3, size * 0.18),
    ]
    
    for x, y, r in circles:
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=cloud_color, outline=cloud_outline, width=2)
    
    # 稲妻
    lightning_color = (255, 255, 0)
    lightning_points = [
        (size * 0.55, size * 0.45),
        (size * 0.45, size * 0.6),
        (size * 0.5, size * 0.6),
        (size * 0.4, size * 0.8),
        (size * 0.55, size * 0.65),
        (size * 0.5, size * 0.65),
        (size * 0.6, size * 0.45),
    ]
    
    draw.polygon(lightning_points, fill=lightning_color, outline=(255, 200, 0))
    
    return img


def create_snow_icon(size: int) -> Image.Image:
    """雪アイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 薄い雲
    cloud_color = (230, 230, 230)
    cloud_outline = (210, 210, 210)
    
    circles = [
        (size * 0.35, size * 0.35, size * 0.18),
        (size * 0.5, size * 0.3, size * 0.22),
        (size * 0.65, size * 0.35, size * 0.18),
    ]
    
    for x, y, r in circles:
        draw.ellipse([x - r, y - r, x + r, y + r],
                    fill=cloud_color, outline=cloud_outline, width=2)
    
    # 雪の結晶
    snow_color = (255, 255, 255)
    snow_size = size // 20
    
    snowflakes = [
        (size * 0.3, size * 0.6),
        (size * 0.5, size * 0.65),
        (size * 0.7, size * 0.6),
        (size * 0.4, size * 0.75),
        (size * 0.6, size * 0.75),
    ]
    
    for x, y in snowflakes:
        # 六角形の雪の結晶
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x2 = x + snow_size * math.cos(rad)
            y2 = y + snow_size * math.sin(rad)
            draw.line([x, y, x2, y2], fill=snow_color, width=2)
        
        # 中心点
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=snow_color)
    
    return img


def create_fog_icon(size: int) -> Image.Image:
    """霧アイコンを作成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 霧の線
    fog_color = (180, 180, 180, 200)
    line_height = max(2, size // 16)
    
    y_positions = [
        size * 0.3,
        size * 0.4,
        size * 0.5,
        size * 0.6,
        size * 0.7,
    ]
    
    for i, y in enumerate(y_positions):
        # 左右の余白を変えて波のような効果
        margin = max(5, size // 10) + (i % 2) * max(5, size // 20)
        x0 = margin
        y0 = int(y - line_height // 2)
        x1 = size - margin
        y1 = int(y + line_height // 2)
        
        # x0 < x1, y0 < y1 を保証
        if x0 < x1 and y0 < y1:
            draw.rectangle([x0, y0, x1, y1], fill=fog_color)
    
    return img


def save_icon_set(icon_func, name: str, output_dir: str):
    """アイコンセットを保存"""
    sizes = [32, 48, 64, 128]
    
    for size in sizes:
        icon = icon_func(size)
        filename = f"{name}_{size}.png"
        filepath = os.path.join(output_dir, filename)
        icon.save(filepath)
        print(f"  Saved: {filename}")


def main():
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = "assets/icons/weather"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating weather icons...")
    
    # アイコン生成
    icons = [
        (create_sunny_icon, "sunny"),
        (create_cloudy_icon, "cloudy"),
        (create_partly_cloudy_icon, "partly_cloudy"),
        (create_rain_icon, "rain"),
        (create_thunder_icon, "thunder"),
        (create_snow_icon, "snow"),
        (create_fog_icon, "fog"),
    ]
    
    for func, name in icons:
        print(f"\nGenerating {name} icons...")
        save_icon_set(func, name, output_dir)
    
    # デフォルトアイコン（unknown）も作成
    print("\nGenerating unknown icon...")
    
    def create_unknown_icon(size: int) -> Image.Image:
        """不明アイコンを作成"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 疑問符
        center = size // 2
        radius = size // 3
        
        # 背景円
        draw.ellipse([center - radius, center - radius,
                     center + radius, center + radius],
                    fill=(150, 150, 150), outline=(130, 130, 130), width=2)
        
        # 疑問符（簡易版）
        try:
            from PIL import ImageFont
            font_size = int(size * 0.5)
            # システムフォントを試す
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            text = "?"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = center - text_width // 2
            y = center - text_height // 2
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
        except:
            # フォントが使えない場合は手動で描画
            draw.text((center - 8, center - 12), "?", fill=(255, 255, 255))
        
        return img
    
    save_icon_set(create_unknown_icon, "unknown", output_dir)
    
    print("\n✓ All weather icons generated successfully!")
    print(f"  Output directory: {output_dir}")
    print(f"  Total icons: {len(icons) + 1} types × 4 sizes = {(len(icons) + 1) * 4} files")


if __name__ == "__main__":
    main()