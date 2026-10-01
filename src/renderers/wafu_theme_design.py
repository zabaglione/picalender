"""Painted monthly paper with quiet, consistent surfaces for live information."""

import logging
from pathlib import Path

import pygame


SIZE = (1024, 600)
ART = pygame.Rect(28, 337, 400, 225)
ASSETS = Path(__file__).resolve().parents[2] / "assets/field_notes/monthly"
LOGGER = logging.getLogger(__name__)
MONTH_BACKGROUNDS = (
    "01-mutsuki.png", "02-kisaragi.png", "03-yayoi.png", "04-uzuki.png",
    "05-satsuki.png", "06-minazuki.png", "07-fumizuki.png", "08-hazuki.png",
    "09-nagatsuki.png", "10-kannazuki.png", "11-shimotsuki.png", "12-shiwasu.png",
)


def _wash(surface, rect, color, alpha, radius=12):
    """Lay translucent paper over busy illustration where live text belongs."""
    layer = pygame.Surface(rect[2:], pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=radius)
    surface.blit(layer, rect[:2])


def _rounded(surface, rect, color, radius):
    """Supersample only the small rounded shape, not the entire dashboard."""
    x, y, width, height = rect
    layer = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    pygame.draw.rect(layer, color, layer.get_rect(), border_radius=radius * 2)
    surface.blit(pygame.transform.smoothscale(layer, (width, height)), (x, y))


def draw_dashboard_base(surface, month, theme, *, title_width=240):
    path = ASSETS / MONTH_BACKGROUNDS[month - 1]
    try:
        background = pygame.image.load(str(path))
    except (OSError, pygame.error):
        LOGGER.warning("Monthly background unavailable: %s", path.name)
        background = pygame.Surface(SIZE)
        background.fill(theme.paper)
    if background.get_size() != SIZE:
        background = pygame.transform.smoothscale(background, SIZE)
    page = background.copy()

    # Illustrations remain visible above the calendar and around the outer edge.
    # Text regions share the same paper and restrained rounded geometry all year.
    _wash(page, (20, 15, 284, 53), theme.card, 218, 9)
    _wash(page, (18, 78, 415, 140), theme.card, 105, 12)
    _wash(page, (463, 31, title_width + 24, 52), theme.card, 248, 10)
    _wash(page, (912, 39, 74, 40), theme.card, 250, 9)
    _wash(page, (452, 93, 550, 319), theme.card, 247, 14)
    _wash(page, (452, 427, 550, 150), theme.card, 244, 14)

    _rounded(page, (28, 225, 400, 81), (*theme.ink, 255), 15)
    # A narrow paper mount preserves the daily illustration's original pixels.
    _rounded(page, (23, 332, 410, 235), (*theme.card, 255), 9)
    pygame.draw.line(page, theme.line, (30, 218), (428, 218), 1)
    _wash(page, (450, 580, 230, 18), theme.card, 230, 5)

    # Drawing this layer must never paint over an already loaded daily image.
    for rect in ((0, 0, 1024, ART.top), (0, ART.bottom, 1024, 600 - ART.bottom),
                 (0, ART.top, ART.left, ART.height),
                 (ART.right, ART.top, 1024 - ART.right, ART.height)):
        surface.blit(page, rect[:2], rect)


def draw_selected_day(surface, rect, month, theme):
    # A consistent ink seal is readable across every seasonal background.
    _rounded(surface, rect, (*theme.ink, 255), 13)
