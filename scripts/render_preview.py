#!/usr/bin/env python3
"""Render the real dashboard offscreen; never starts or stops a service."""
import argparse
import calendar
from datetime import datetime
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import yaml
from src.renderers.field_notes_renderer import FieldNotesRenderer
from src.weather.dashboard_weather import DashboardWeather


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="output/redesign/preview.png")
    parser.add_argument("--at", help="ISO timestamp; default is the current time")
    parser.add_argument("--offline", action="store_true", help="Use only cached weather")
    parser.add_argument("--all-months", action="store_true", help="Save twelve monthly frames and a contact sheet")
    args = parser.parse_args()
    settings_path = ROOT / "settings.yaml"
    settings = yaml.safe_load(settings_path.read_text()) if settings_path.exists() else {}
    pygame.init()
    pygame.mixer.quit()
    screen = pygame.display.set_mode((1024, 600))
    weather = DashboardWeather(settings, ROOT, start_worker=False)
    if not args.offline:
        weather.refresh()
    renderer = FieldNotesRenderer(settings, weather=weather)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.fromisoformat(args.at) if args.at else datetime.now(renderer.timezone)
    if now.tzinfo is None:
        now = now.replace(tzinfo=renderer.timezone)
    else:
        now = now.astimezone(renderer.timezone)
    if args.all_months:
        names = ("睦月", "如月", "弥生", "卯月", "皐月", "水無月",
                 "文月", "葉月", "長月", "神無月", "霜月", "師走")
        sheet = pygame.Surface((1536, 1328))
        sheet.fill((246, 241, 230))
        for month, name in enumerate(names, 1):
            day = min(now.day, calendar.monthrange(now.year, month)[1])
            renderer.render(screen, now.replace(month=month, day=day))
            frame_path = output.with_name(f"{output.stem}-{month:02d}.png")
            pygame.image.save(screen, str(frame_path))
            x, y = ((month - 1) % 3) * 512, ((month - 1) // 3) * 332
            title = renderer.font(19, "jp").render(f"{month}月  {name}", True, (49, 56, 51))
            sheet.blit(title, (x + 12, y + 4))
            sheet.blit(pygame.transform.smoothscale(screen, (512, 300)), (x, y + 32))
        pygame.image.save(sheet, str(output))
    else:
        renderer.render(screen, now)
        pygame.image.save(screen, str(output))
    renderer.cleanup()
    pygame.quit()
    print(f"Preview saved: {output}")


if __name__ == "__main__":
    main()
