#!/usr/bin/env python3
"""
日本語フォントテスト
Raspberry Piで日本語が正しく表示されるかテスト
"""

import pygame
import sys
from pathlib import Path

def test_japanese_font():
    """日本語フォントをテスト"""
    pygame.init()
    
    # 小さいウィンドウでテスト
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Japanese Font Test")
    
    # テスト用の日本語テキスト
    test_texts = [
        "月齢 19.1",
        "寝待月",
        "大安",
        "今日",
        "明日",
        "天気予報"
    ]
    
    # フォントパス候補
    font_paths = [
        "./assets/fonts/NotoSansCJK-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf"
    ]
    
    font = None
    used_font_path = None
    
    # フォント読み込み
    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                font = pygame.font.Font(font_path, 24)
                used_font_path = font_path
                print(f"✓ Using font: {font_path}")
                break
            except Exception as e:
                print(f"✗ Failed to load {font_path}: {e}")
    
    if not font:
        print("Warning: Using default font (Japanese may not display)")
        font = pygame.font.Font(None, 24)
        used_font_path = "Default"
    
    # 背景を白に
    screen.fill((255, 255, 255))
    
    # テキストを描画
    y_pos = 20
    for i, text in enumerate(test_texts):
        try:
            # 黒い文字で描画
            text_surface = font.render(text, True, (0, 0, 0))
            screen.blit(text_surface, (20, y_pos))
            
            # サーフェースのサイズを確認
            width = text_surface.get_width()
            height = text_surface.get_height()
            print(f"Text '{text}': size={width}x{height}")
            
            y_pos += 40
        except Exception as e:
            print(f"✗ Failed to render '{text}': {e}")
    
    # フォント情報を表示
    info_text = f"Font: {used_font_path}"
    info_surface = pygame.font.Font(None, 16).render(info_text, True, (100, 100, 100))
    screen.blit(info_surface, (20, 250))
    
    pygame.display.flip()
    
    print("Close the window to exit...")
    
    # イベントループ
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
    
    pygame.quit()

if __name__ == "__main__":
    test_japanese_font()