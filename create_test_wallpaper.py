#!/usr/bin/env python3
"""
テスト用壁紙画像を生成
"""

import pygame
import os

# pygame初期化
pygame.init()

# グラデーション壁紙を作成
width, height = 1920, 1080
surface = pygame.Surface((width, height))

# グラデーション描画
for y in range(height):
    # 上から下へのグラデーション（青から紫へ）
    r = int(20 + (y / height) * 60)
    g = int(30 + (y / height) * 20)
    b = int(80 + (y / height) * 40)
    pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

# パターンを追加
for x in range(0, width, 100):
    for y in range(0, height, 100):
        pygame.draw.circle(surface, (r+10, g+10, b+20), (x, y), 2)

# 保存
os.makedirs("wallpapers", exist_ok=True)
pygame.image.save(surface, "wallpapers/gradient_blue.jpg")
print("Created wallpapers/gradient_blue.jpg")

# もう一つ作成（赤系）
for y in range(height):
    # 上から下へのグラデーション（赤からオレンジへ）
    r = int(80 + (y / height) * 40)
    g = int(20 + (y / height) * 60)
    b = int(30 + (y / height) * 20)
    pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

pygame.image.save(surface, "wallpapers/gradient_red.jpg")
print("Created wallpapers/gradient_red.jpg")

pygame.quit()