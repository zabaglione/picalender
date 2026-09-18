"""North-up schematic Moon: waxing lights the right, waning the left."""
import math
import pygame


def is_illuminated(x: float, y: float, fraction: float, waxing: bool) -> bool:
    radius2 = x * x + y * y
    if radius2 > 1:
        return False
    fraction = min(1.0, max(0.0, fraction))
    cos_phase = 2 * fraction - 1
    side = math.sqrt(max(0.0, 1 - cos_phase * cos_phase)) * (1 if waxing else -1)
    return x * side + math.sqrt(max(0.0, 1 - radius2)) * cos_phase > 0


def moon_surface(info: dict, diameter: int = 64) -> pygame.Surface:
    """Use spherical illumination instead of a linear age-to-shape mapping."""
    scale = 2
    size = diameter * scale
    radius = size / 2 - 3
    result = pygame.Surface((size, size), pygame.SRCALPHA)
    fraction = info["illumination_fraction"]
    for y in range(size):
        for x in range(size):
            nx, ny = (x + 0.5 - size / 2) / radius, (y + 0.5 - size / 2) / radius
            if nx * nx + ny * ny > 1:
                continue
            lit = is_illuminated(nx, ny, fraction, info["waxing"])
            color = (234, 215, 166) if lit else (57, 76, 68)
            # Restrained, deterministic surface grain; never changes the phase.
            grain = ((x * 23 + y * 17) % 7) - 3
            result.set_at((x, y), tuple(channel + grain for channel in color))
    pygame.draw.circle(result, (152, 158, 119), (size // 2, size // 2), int(radius), 2)
    return pygame.transform.smoothscale(result, (diameter, diameter))
