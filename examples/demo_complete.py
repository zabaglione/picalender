#!/usr/bin/env python3
"""
完全統合デモ

背景画像を含む全てのUI要素を表示するサンプル実装
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from src.ui.background_renderer import BackgroundRenderer
from src.ui.clock_renderer import ClockRenderer
from src.ui.date_renderer import DateRenderer
from src.ui.calendar_renderer import CalendarRenderer
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
    pygame.display.set_caption("Complete UI Demo - PiCalendar")
    
    # レンダラーの作成（描画順序: 背景 -> 時計 -> 日付 -> カレンダー）
    background_renderer = BackgroundRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    clock_renderer = ClockRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    date_renderer = DateRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    calendar_renderer = CalendarRenderer(
        asset_manager=asset_manager,
        config=config
    )
    
    # FPS管理
    clock = pygame.time.Clock()
    target_fps = 30
    
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
                    # スペースキーでUI要素の表示/非表示切り替え
                    visible = not clock_renderer.visible
                    clock_renderer.set_visible(visible)
                    date_renderer.set_visible(visible)
                    calendar_renderer.set_visible(visible)
                elif event.key == pygame.K_b:
                    # Bキーで背景の表示/非表示切り替え
                    background_renderer.set_visible(not background_renderer.visible)
                elif event.key == pygame.K_RIGHT:
                    # 右矢印で次の壁紙
                    background_renderer.next_wallpaper()
                elif event.key == pygame.K_LEFT:
                    # 左矢印で前の壁紙
                    background_renderer.previous_wallpaper()
                elif event.key == pygame.K_f:
                    # Fキーでfitモード
                    background_renderer.set_scale_mode('fit')
                elif event.key == pygame.K_s:
                    # Sキーでscaleモード
                    background_renderer.set_scale_mode('scale')
                elif event.key == pygame.K_c:
                    # Cキーでcenterモード
                    background_renderer.set_scale_mode('center')
                elif event.key == pygame.K_j:
                    # Jキーで日本語曜日
                    date_renderer.set_weekday_language('jp')
                    calendar_renderer.set_weekday_language('jp')
                elif event.key == pygame.K_e:
                    # Eキーで英語曜日
                    date_renderer.set_weekday_language('en')
                    calendar_renderer.set_weekday_language('en')
        
        # 更新処理
        background_renderer.update(dt)
        clock_renderer.update(dt)
        date_renderer.update(dt)
        calendar_renderer.update(dt)
        
        # 描画処理
        need_redraw = (background_renderer.is_dirty() or
                      clock_renderer.is_dirty() or 
                      date_renderer.is_dirty() or 
                      calendar_renderer.is_dirty())
        
        if need_redraw:
            # レイヤー順に描画
            background_renderer.render(screen)  # 背景（最下層）
            clock_renderer.render(screen)       # 時計
            date_renderer.render(screen)        # 日付
            calendar_renderer.render(screen)    # カレンダー（最上層）
            
            # 操作説明を表示（半透明背景）
            font = pygame.font.Font(None, 16)
            help_surface = pygame.Surface((200, 180), pygame.SRCALPHA)
            help_surface.fill((0, 0, 0, 128))  # 半透明黒
            
            instructions = [
                "Controls:",
                "  ESC: Exit",
                "  SPACE: Toggle UI",
                "  B: Toggle background",
                "  LEFT/RIGHT: Switch wallpaper",
                "  F/S/C: Fit/Scale/Center",
                "  J/E: JP/EN weekday"
            ]
            
            y = 10
            for text in instructions:
                color = (200, 200, 200) if text.startswith("  ") else (255, 255, 255)
                rendered = font.render(text, True, color)
                help_surface.blit(rendered, (10, y))
                y += 22
            
            screen.blit(help_surface, (10, 10))
            
            # ステータス表示
            status_text = f"Mode: {background_renderer.scale_mode} | Lang: {date_renderer.weekday_lang} | FPS: {clock.get_fps():.1f}"
            status_surface = font.render(status_text, True, (180, 180, 180))
            status_bg = pygame.Surface((status_surface.get_width() + 20, 25), pygame.SRCALPHA)
            status_bg.fill((0, 0, 0, 100))
            status_bg.blit(status_surface, (10, 5))
            screen.blit(status_bg, (10, screen_height - 35))
            
            # 画面更新
            pygame.display.flip()
        
        # FPS表示
        pygame.display.set_caption(f"PiCalendar Demo - FPS: {clock.get_fps():.1f}")
    
    # 終了処理
    pygame.quit()


if __name__ == "__main__":
    main()