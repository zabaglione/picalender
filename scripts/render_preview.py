#!/usr/bin/env python3
"""Render the real dashboard offscreen; never starts or stops a service."""
import argparse
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
    renderer.render(screen, datetime.fromisoformat(args.at) if args.at else None)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, str(output))
    renderer.cleanup()
    pygame.quit()
    print(f"Preview saved: {output}")


if __name__ == "__main__":
    main()
