"""Japanese seasonal designs change without replacing dashboard content."""

from datetime import datetime, timezone
import hashlib

import pytest


@pytest.mark.parametrize("year,month,next_year,next_month", [(2026, 1, 2026, 2), (2026, 12, 2027, 1)])
def test_local_month_boundary_updates_design_and_preserves_artwork(
        tmp_path, monkeypatch, year, month, next_year, next_month):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    import pygame
    from src.renderers.field_notes_renderer import FieldNotesRenderer, MONTHLY_THEMES

    assert set(MONTHLY_THEMES) == set(range(1, 13))
    assert len(set(MONTHLY_THEMES.values())) == 12

    pygame.init()
    try:
        screen = pygame.display.set_mode((1024, 600))
        artwork_path = tmp_path / "cache/daily_art/current.png"
        artwork_path.parent.mkdir(parents=True)
        artwork = pygame.Surface((800, 450))
        artwork.fill((255, 0, 0))
        pygame.image.save(artwork, str(artwork_path))

        renderer = FieldNotesRenderer({"daily_art": {"enabled": True}}, start_worker=False)
        renderer.root = tmp_path
        try:
            renderer.render(screen, datetime(year, month, 31, 14, 59, tzinfo=timezone.utc))
            previous_background = pygame.image.tostring(renderer._static, "RGB")
            assert renderer._calendar_key == (year, month, 31)
            assert screen.get_at((100, 400))[:3] == (255, 0, 0)

            # 15:00 UTC is midnight in the configured Asia/Tokyo timezone.
            # A missing cache must not discard the last valid artwork at month change.
            artwork_path.unlink()
            renderer.render(screen, datetime(year, month, 31, 15, 0, tzinfo=timezone.utc))
            assert renderer.theme == MONTHLY_THEMES[next_month]
            assert renderer._calendar_key == (next_year, next_month, 1)
            assert pygame.image.tostring(renderer._static, "RGB") != previous_background
            assert screen.get_at((100, 400))[:3] == (255, 0, 0)
        finally:
            renderer.cleanup()
    finally:
        pygame.quit()


def test_month_designs_differ_even_with_identical_colors(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from src.renderers.field_notes_renderer import MONTHLY_THEMES
    from src.renderers.wafu_theme_design import draw_dashboard_base

    pygame.init()
    try:
        surface = pygame.Surface((1024, 600))
        fingerprints = []
        for month in range(1, 13):
            draw_dashboard_base(surface, month, MONTHLY_THEMES[1])
            first = pygame.image.tostring(surface, "RGB")
            draw_dashboard_base(surface, month, MONTHLY_THEMES[1])
            assert pygame.image.tostring(surface, "RGB") == first
            fingerprints.append(hashlib.sha256(first).hexdigest())
        assert len(set(fingerprints)) == 12
    finally:
        pygame.quit()


@pytest.mark.parametrize("corrupt", [False, True])
def test_unavailable_background_keeps_information_surface_and_daily_art(
        tmp_path, monkeypatch, corrupt):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from src.renderers.field_notes_renderer import MONTHLY_THEMES
    from src.renderers import wafu_theme_design as design

    monkeypatch.setattr(design, "ASSETS", tmp_path)
    if corrupt:
        (tmp_path / design.MONTH_BACKGROUNDS[0]).write_bytes(b"not an image")
    pygame.init()
    try:
        surface = pygame.Surface((1024, 600))
        surface.fill((255, 0, 255))
        design.draw_dashboard_base(surface, 1, MONTHLY_THEMES[1])
        assert surface.get_at((100, 400))[:3] == (255, 0, 255)
        assert surface.get_at((600, 250))[:3] != (255, 0, 255)
        assert surface.get_at((120, 260))[:3] == MONTHLY_THEMES[1].ink
    finally:
        pygame.quit()
