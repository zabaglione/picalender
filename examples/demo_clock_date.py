#!/usr/bin/env python3
"""
ClockRendererとDateRendererの統合デモ

時計と日付を一緒に表示するサンプル実装
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from src.ui.clock_renderer import ClockRenderer
from src.ui.date_renderer import DateRenderer
from src.assets.asset_manager import AssetManager
from src.core.config_manager import ConfigManager


def main():
    """メイン処理"""
    # pygame初期化
    pygame.init()
    
    # 設定とアセット管理の初期化
    config = ConfigManager()
    asset_manager = AssetManager(base_path="assets")
    
    # 画面の作成
    screen_width = config.get('screen.width', 1024)
    screen_height = config.get('screen.height', 600)
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Clock & Date Renderer Demo")
    
    # レンダラーの作成
    clock_renderer = ClockRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    date_renderer = DateRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    # FPS管理
    clock = pygame.time.Clock()
    target_fps = 30
    
    # 背景色
    bg_color = (30, 30, 40)
    
    # メインループ
    running = True
    while running:
        dt = clock.tick(target_fps) / 1000.0  # ミリ秒を秒に変換
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # スペースキーで表示/非表示切り替え
                    clock_renderer.set_visible(not clock_renderer.visible)
                    date_renderer.set_visible(not date_renderer.visible)
                elif event.key == pygame.K_r:
                    # Rキーで赤色に変更
                    clock_renderer.set_color((255, 0, 0))
                    date_renderer.set_color((255, 0, 0))
                elif event.key == pygame.K_g:
                    # Gキーで緑色に変更
                    clock_renderer.set_color((0, 255, 0))
                    date_renderer.set_color((0, 255, 0))
                elif event.key == pygame.K_b:
                    # Bキーで青色に変更
                    clock_renderer.set_color((0, 0, 255))
                    date_renderer.set_color((0, 0, 255))
                elif event.key == pygame.K_w:
                    # Wキーで白色に戻す
                    clock_renderer.set_color((255, 255, 255))
                    date_renderer.set_color((255, 255, 255))
                elif event.key == pygame.K_j:
                    # Jキーで日本語曜日
                    date_renderer.set_weekday_language('jp')
                elif event.key == pygame.K_e:
                    # Eキーで英語曜日
                    date_renderer.set_weekday_language('en')
                elif event.key == pygame.K_UP:
                    # 上キーで時計フォントサイズ増加
                    new_size = min(clock_renderer.font_size + 10, 300)
                    clock_renderer.set_font_size(new_size)
                elif event.key == pygame.K_DOWN:
                    # 下キーで時計フォントサイズ減少
                    new_size = max(clock_renderer.font_size - 10, 30)
                    clock_renderer.set_font_size(new_size)
        
        # 更新処理
        clock_renderer.update(dt)
        date_renderer.update(dt)
        
        # 描画処理
        need_redraw = clock_renderer.is_dirty() or date_renderer.is_dirty()
        
        if need_redraw:
            # 全画面クリア
            screen.fill(bg_color)
            
            # 時計と日付を描画
            clock_renderer.render(screen)
            date_renderer.render(screen)
            
            # 操作説明を表示
            font = pygame.font.Font(None, 20)
            instructions = [
                "Controls:",
                "  ESC: Exit",
                "  SPACE: Toggle visibility",
                "  R/G/B/W: Change color",
                "  J/E: Japanese/English weekday",
                "  UP/DOWN: Change clock size"
            ]
            y = screen_height - 140
            for text in instructions:
                rendered = font.render(text, True, (128, 128, 128))
                screen.blit(rendered, (10, y))
                y += 22
            
            # 現在の設定を表示
            status_texts = [
                f"Weekday: {date_renderer.weekday_lang}",
                f"Clock size: {clock_renderer.font_size}px"
            ]
            y = 10
            for text in status_texts:
                rendered = font.render(text, True, (100, 100, 100))
                screen.blit(rendered, (screen_width - 150, y))
                y += 22
            
            # 画面更新
            pygame.display.flip()
        
        # FPS表示
        pygame.display.set_caption(f"Clock & Date Demo - FPS: {clock.get_fps():.1f}")
    
    # 終了処理
    pygame.quit()


if __name__ == "__main__":
    main()