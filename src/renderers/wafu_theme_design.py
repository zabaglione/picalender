"""Twelve illustrated, text-free backdrops for the field-notes dashboard.

All coordinates are in the fixed 1024 x 600 dashboard space. Drawing takes place
at twice that size, then is reduced once. The artwork rectangle is deliberately
excluded from the final blit so an existing image is never painted over.
"""

import math
import random

import pygame


SIZE = (1024, 600)
ART = pygame.Rect(28, 337, 400, 225)
SCALE = 2


def _mix(a, b, amount):
    return tuple(round(left * (1 - amount) + right * amount)
                 for left, right in zip(a[:3], b[:3]))


def _color(value):
    return tuple(value[:3])


class _Pen:
    """Small coordinate adapter for the supersampled Pygame canvas."""

    def __init__(self, surface):
        self.surface = surface

    @staticmethod
    def _p(point):
        return round(point[0] * SCALE), round(point[1] * SCALE)

    @staticmethod
    def _r(rect):
        return pygame.Rect(*(round(v * SCALE) for v in rect))

    def line(self, color, start, end, width=1):
        pygame.draw.line(self.surface, color, self._p(start), self._p(end),
                         max(1, round(width * SCALE)))

    def lines(self, color, points, width=1, closed=False):
        pygame.draw.lines(self.surface, color, closed,
                          [self._p(point) for point in points],
                          max(1, round(width * SCALE)))

    def polygon(self, color, points, width=0):
        pygame.draw.polygon(self.surface, color,
                            [self._p(point) for point in points],
                            round(width * SCALE))

    def rect(self, color, rect, width=0, radius=0):
        pygame.draw.rect(self.surface, color, self._r(rect),
                         round(width * SCALE), border_radius=round(radius * SCALE))

    def ellipse(self, color, rect, width=0):
        pygame.draw.ellipse(self.surface, color, self._r(rect), round(width * SCALE))

    def circle(self, color, center, radius, width=0):
        pygame.draw.circle(self.surface, color, self._p(center),
                           max(1, round(radius * SCALE)), round(width * SCALE))

    def arc(self, color, rect, begin, end, width=1):
        pygame.draw.arc(self.surface, color, self._r(rect), begin, end,
                        max(1, round(width * SCALE)))

    def bezier(self, color, a, b, c, d, width=1, steps=28):
        points = []
        for index in range(steps + 1):
            t = index / steps
            u = 1 - t
            points.append((u**3 * a[0] + 3*u*u*t*b[0] + 3*u*t*t*c[0] + t**3*d[0],
                           u**3 * a[1] + 3*u*u*t*b[1] + 3*u*t*t*c[1] + t**3*d[1]))
        self.lines(color, points, width)


def _leaf(pen, center, length, width, angle, fill, edge=None):
    """Pointed, hand-drawn leaf; angle is the direction of its long axis."""
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    points = []
    for side in (1, -1):
        sequence = range(9) if side == 1 else range(8, -1, -1)
        for index in sequence:
            t = index / 8
            swell = math.sin(math.pi * t) * width * side
            points.append((center[0] + dx * length * (t - .5) + nx * swell,
                           center[1] + dy * length * (t - .5) + ny * swell))
    pen.polygon(fill, points)
    if edge:
        pen.lines(edge, points, .7, True)
        pen.line(edge,
                 (center[0] - dx * length * .42, center[1] - dy * length * .42),
                 (center[0] + dx * length * .37, center[1] + dy * length * .37), .7)


def _flower(pen, center, radius, petal, outline, middle):
    for index in range(5):
        angle = -math.pi / 2 + index * 2 * math.pi / 5
        cx = center[0] + math.cos(angle) * radius * .55
        cy = center[1] + math.sin(angle) * radius * .55
        _leaf(pen, (cx, cy), radius * 1.13, radius * .36, angle,
              petal, outline)
    pen.circle(middle, center, radius * .17)


def _spark(pen, center, radius, color):
    x, y = center
    pen.line(color, (x - radius, y), (x + radius, y), .9)
    pen.line(color, (x, y - radius), (x, y + radius), .9)
    pen.circle(color, center, .75)


def _panel_points(rect, month):
    x, y, w, h = rect
    right, bottom = x + w, y + h
    if month == 2:  # Folded textile corners.
        return [(x, y + 13), (x + 13, y), (right - 28, y),
                (right, y + 28), (right, bottom - 8), (right - 8, bottom),
                (x + 8, bottom), (x, bottom - 8)]
    if month == 5:  # Terraced steps.
        return [(x, y + 12), (x + 6, y + 12), (x + 6, y + 6),
                (x + 12, y + 6), (x + 12, y), (right - 12, y),
                (right - 12, y + 6), (right - 6, y + 6),
                (right - 6, y + 12), (right, y + 12),
                (right, bottom - 12), (right - 6, bottom - 12),
                (right - 6, bottom - 6), (right - 12, bottom - 6),
                (right - 12, bottom), (x + 12, bottom),
                (x + 12, bottom - 6), (x + 6, bottom - 6),
                (x + 6, bottom - 12), (x, bottom - 12)]
    if month in (8, 11):
        return [(x + 20, y), (right - 13, y + 2),
                (right, y + 16), (right - 2, bottom - 22),
                (right - 20, bottom), (x + 8, bottom - 2),
                (x, bottom - 14), (x + 3, y + 16)]
    cut = {1: 10, 3: 14, 4: 8, 7: 16, 9: 15}.get(month, 11)
    return [(x + cut, y), (right - cut, y), (right, y + cut),
            (right, bottom - cut), (right - cut, bottom),
            (x + cut, bottom), (x, bottom - cut), (x, y + cut)]


def _card(pen, rect, month, card, border, shadow, accent):
    x, y, w, h = rect
    if month in (6, 12):
        pen.rect(shadow, (x + 4, y + 5, w, h), radius=15)
        pen.rect(card, rect, radius=15)
        pen.rect(border, rect, 1, radius=15)
    else:
        points = _panel_points((x + 4, y + 5, w, h), month)
        pen.polygon(shadow, points)
        points = _panel_points(rect, month)
        pen.polygon(card, points)
        pen.lines(border, points, 1, True)
    # The forecast starts only eight pixels below its top edge, so leave that
    # frame undecorated. Calendar detailing stays inside its header or rim.
    if h < 200:
        return
    if month == 1:
        for corner in (x + 24, x + w - 24):
            pen.circle(accent, (corner, y + 5), 2)
    elif month == 2:
        pen.line(accent, (x + w - 29, y + 1), (x + w - 1, y + 28), 1)
    elif month == 5:
        pen.line(accent, (x + 18, y + 5), (x + w - 18, y + 5), 1.5)
    elif month == 6:
        pen.arc(accent, (x + 4, y + 4, 22, 22),
                math.pi * .5, math.pi, 1)
    elif month == 9:
        pen.line(accent, (x + 23, y + 4), (x + w - 23, y + 4), 1)
    elif month == 10:
        pen.line(accent, (x + 19, y + 5), (x + w - 19, y + 5), 2)
        pen.line(accent, (x + 19, y + h - 2), (x + w - 19, y + h - 2), 2)
    elif month == 11:
        for cx in (x + 19, x + w - 19):
            _spark(pen, (cx, y + 10), 3, accent)
    elif month == 12:
        pen.arc(accent, (x + 7, y + 7, 25, 25),
                math.pi * .5, math.pi, 1.2)


def _art_frame(pen, month, border, accent, shadow):
    # All strokes stay outside ART, including the anti-aliased inner edge.
    pen.rect(shadow, (21, 330, 414, 239), radius=11)
    pen.rect(border, (24, 333, 408, 231), 2, radius=6)
    if month in (1, 7, 10, 12):
        for x in (24, 432):
            for y in (333, 564):
                pen.circle(accent, (x, y), 2.5)
    elif month in (3, 4, 5, 8):
        pen.line(accent, (22, 325), (38, 325), 2)
        pen.line(accent, (418, 571), (434, 571), 2)
    elif month in (6, 9, 11):
        pen.line(accent, (21, 574), (434, 574), 1)


def _base_texture(pen, month, tint):
    rng = random.Random(7900 + month)
    for _ in range(660):
        x = rng.randrange(SIZE[0])
        y = rng.randrange(SIZE[1])
        if 452 <= x < 1000 and (24 <= y < 411 or 427 <= y < 576):
            continue
        if ART.collidepoint(x, y):
            continue
        pen.circle(tint, (x, y), rng.choice((.25, .35, .5)))


def _page_scene(p, month, c):
    """Broad seasonal masses beneath the left-column typography and panels.

    These colors stay close to the paper so the clock, sky data, and date retain
    their original contrast. The cards subsequently cover the right-hand body.
    """
    paper = c['paper']
    ink = c['page_ink']
    shade = _mix(paper, ink, .055)
    fine = _mix(paper, ink, .105)
    accent = _mix(paper, c['accent'], .13)
    secondary = _mix(paper, c['secondary'], .15)
    highlight = _mix(paper, c['highlight'], .18)

    if month == 1:
        # A celebratory open fan gathers its ribs at the lower right.
        origin = (430, 219)
        for index in range(8):
            a = math.pi + index * math.pi / 16
            b = math.pi + (index + 1) * math.pi / 16
            outer = lambda angle: (origin[0] + 460 * math.cos(angle),
                                   origin[1] + 460 * math.sin(angle))
            p.polygon((accent, highlight, shade)[index % 3],
                      [origin, outer(a), outer((a + b) / 2), outer(b)])
            p.line(fine, origin, outer(a), .8)
        p.circle(highlight, origin, 13)
        p.circle(accent, origin, 6)
    elif month == 2:
        # Layered cloth and angled hems occupy the full upper-left field.
        p.polygon(shade, [(70, -10), (439, -10), (439, 183),
                          (266, 225), (66, 174)])
        p.polygon(secondary, [(130, -10), (439, -10), (439, 146),
                              (326, 205), (107, 131)])
        p.polygon(accent, [(204, -10), (439, -10), (439, 109),
                           (363, 173), (179, 91)])
        for start, end in (((66, 174), (266, 225)),
                           ((107, 131), (326, 205)),
                           ((179, 91), (363, 173))):
            p.line(fine, start, end, 1)
        for offset in range(0, 6):
            p.line(highlight, (270 + offset * 18, -5),
                   (439, 66 + offset * 15), .7)
    elif month == 3:
        # A single strong climbing shoot spreads leaves into the open space.
        p.bezier(secondary, (431, 221), (300, 185), (382, 72),
                 (258, -12), 17)
        p.bezier(fine, (431, 221), (300, 185), (382, 72),
                 (258, -12), 1.2)
        for center, angle, size in (((337, 38), -.35, 66),
                                    ((384, 82), -2.2, 72),
                                    ((303, 137), -.7, 82),
                                    ((398, 173), -2.3, 64)):
            _leaf(p, center, size, size * .25, angle,
                  secondary if center[0] < 370 else shade, fine)
    elif month == 4:
        # Large five-petal flowers drift from a pale branch, kept under type.
        p.bezier(secondary, (437, 196), (330, 137), (403, 40),
                 (236, -16), 8)
        p.bezier(fine, (437, 196), (330, 137), (403, 40),
                 (236, -16), 1)
        petal = _mix(paper, c['card'], .83)
        for center, radius in (((324, 39), 23), ((381, 90), 30),
                               ((333, 143), 25), ((414, 170), 20)):
            _flower(p, center, radius, petal, shade, highlight)
        for center in ((286, 19), (399, 40), (288, 106)):
            p.circle(petal, center, 5)
    elif month == 5:
        # Alternating water and field terraces form broad stepped horizons.
        fields = [
            (shade, [(0, 40), (190, 40), (190, 57), (438, 57),
                     (438, 79), (212, 79), (212, 63), (0, 63)]),
            (secondary, [(0, 88), (122, 88), (122, 105), (438, 105),
                         (438, 132), (146, 132), (146, 115), (0, 115)]),
            (highlight, [(0, 152), (260, 152), (260, 167), (438, 167),
                         (438, 206), (276, 206), (276, 182), (0, 182)]),
        ]
        for fill, outline in fields:
            p.polygon(fill, outline)
            p.lines(fine, outline, .7)
        for x, y in ((331, 46), (373, 93), (304, 155), (405, 165)):
            _rice_shoot(p, x, y, 18, fine, secondary)
    elif month == 6:
        # Three sinuous blue channels cross the page at different depths.
        for index, base in enumerate((32, 91, 155)):
            top = [(x, base + 12 * math.sin(x / 50 + index * 1.4))
                   for x in range(-20, 461, 8)]
            bottom = [(x, base + 28 + 12 * math.sin(x / 50 + index * 1.4))
                      for x in range(456, -21, -8)]
            p.polygon((secondary, shade, highlight)[index], top + bottom)
            p.lines(fine, top, .8)
        for x, y in ((367, 33), (392, 118), (335, 188)):
            p.arc(fine, (x - 26, y - 7, 52, 15), 0, math.pi, 1)
    elif month == 7:
        # Rounded harvest fields and a fan of laden stalks.
        for index, base in enumerate((101, 144, 181)):
            top = [(x, base - 22 * math.sin((x + 20) / 180))
                   for x in range(-10, 451, 10)]
            bottom = [(x, y + 36) for x, y in reversed(top)]
            p.polygon((shade, highlight, secondary)[index], top + bottom)
            p.lines(fine, top, .8)
        for dx in (-100, -65, -29, 6):
            p.bezier(fine, (434, 212), (400 + dx, 140),
                     (389 + dx, 70), (365 + dx, -18), 2)
        for x, y in ((292, 47), (338, 77), (393, 108)):
            _leaf(p, (x, y), 46, 13, -.95, highlight, fine)
    elif month == 8:
        # Oblique gust planes and sizeable drifting leaves.
        p.polygon(shade, [(48, -12), (258, -12), (438, 133),
                          (438, 173), (184, 40)])
        p.polygon(highlight, [(214, -12), (346, -12), (438, 75),
                              (438, 123)])
        p.polygon(secondary, [(-20, 110), (92, 75), (438, 198),
                              (438, 218), (149, 139), (-20, 157)])
        for center, angle, size in (((327, 53), -.5, 89),
                                    ((397, 151), 2.35, 74),
                                    ((204, 191), -.2, 63)):
            _leaf(p, center, size, size * .23, angle,
                  highlight if center[0] > 300 else shade, fine)
    elif month == 9:
        # Layered long-night ridges; stars, but deliberately no moon.
        p.polygon(shade, [(0, 53), (128, 38), (239, 53),
                          (345, 34), (438, 51), (438, 198), (0, 198)])
        p.polygon(secondary, [(0, 159), (95, 136), (212, 168),
                              (324, 119), (438, 155), (438, 222), (0, 222)])
        p.polygon(accent, [(0, 199), (116, 177), (228, 194),
                           (359, 167), (438, 181), (438, 240), (0, 240)])
        rng = random.Random(998)
        for _ in range(70):
            x, y = rng.randrange(18, 428), rng.randrange(20, 176)
            p.circle(_mix(paper, c['page_ink'], .22), (x, y), .55)
    elif month == 10:
        # A quiet architectural torii shadow sits behind the large clock.
        p.polygon(accent, [(0, 40), (438, 40), (438, 59), (0, 59)])
        p.polygon(shade, [(25, 60), (75, 60), (75, 218), (25, 218)])
        p.polygon(shade, [(372, 60), (420, 60), (420, 218), (372, 218)])
        p.polygon(secondary, [(0, 63), (438, 63), (438, 70), (0, 70)])
        for x in (319, 360, 400):
            p.polygon(secondary, [(x, 91), (x - 17, 151),
                                  (x + 19, 151)])
            p.polygon(shade, [(x, 123), (x - 24, 194),
                              (x + 27, 194)])
    elif month == 11:
        # Uneven translucent ice facets, joined by hairline cracks.
        facets = [
            [(0, 0), (168, 0), (91, 98), (0, 75)],
            [(168, 0), (341, 0), (294, 85), (91, 98)],
            [(341, 0), (438, 0), (438, 125), (294, 85)],
            [(0, 75), (91, 98), (195, 215), (0, 215)],
            [(91, 98), (294, 85), (323, 215), (195, 215)],
            [(294, 85), (438, 125), (438, 215), (323, 215)],
        ]
        for index, facet in enumerate(facets):
            p.polygon((shade, secondary, highlight)[index % 3], facet)
            p.lines(fine, facet, .75, True)
        for x, y in ((358, 56), (396, 148), (266, 185)):
            _spark(p, (x, y), 10, fine)
    else:  # December: lantern glow and diagonal end-of-year movement.
        p.circle(highlight, (396, 55), 101)
        for index in range(5):
            y = -35 + index * 48
            p.polygon((shade, accent, highlight)[index % 3],
                      [(-20, y + 65), (370, y - 48),
                       (438, y - 27), (40, y + 104)])
        for index in range(4):
            y = 43 + index * 39
            p.bezier(fine, (24, y + 40), (130, y - 37),
                     (296, y + 57), (438, y - 25), .9)


def _rice_shoot(pen, x, y, height, color, light):
    pen.bezier(color, (x, y), (x - 1, y - height * .48),
               (x - 8, y - height * .75), (x - 11, y - height), 1.8)
    pen.bezier(color, (x, y), (x + 1, y - height * .5),
               (x + 7, y - height * .8), (x + 10, y - height * .91), 1.6)
    pen.bezier(light, (x, y), (x + 1, y - height * .45),
               (x - 1, y - height * .75), (x + 1, y - height), 1.4)


def _grain_ear(pen, x, y, bend, color, light):
    tip = (x + bend, y + 41)
    pen.bezier(color, (x, y), (x + bend * .1, y + 7),
               (x + bend * .8, y + 29), tip, 1.8)
    for index in range(7):
        t = (index + 1) / 8
        px = x + bend * t * t
        py = y + 41 * t
        direction = -1 if index % 2 else 1
        _leaf(pen, (px + direction * 4, py), 11, 2.9,
              .15 * direction + (math.pi if direction < 0 else 0), light, color)


def _motif_january(p, c):
    accent, gold, green = c['accent'], c['highlight'], c['secondary']
    for index, color in enumerate((accent, gold, green, accent, gold)):
        y = 45 + index * 3
        p.bezier(color, (736, y), (764, y - 25), (778, y + 27),
                 (810, y + 4), 1.8)
        p.bezier(color, (810, y + 4), (844, y - 30), (852, y + 28),
                 (905, y - 8), 1.8)
    p.circle(gold, (809, 55), 4)
    for anchor in ((384, 31), (36, 578)):
        x, y = anchor
        p.line(green, (x, y + 22), (x + 20, y - 5), 2)
        for offset in (3, 9, 15, 20):
            cx, cy = x + offset, y + 20 - offset * 1.25
            for sign in (-1, 1):
                p.line(green, (cx, cy), (cx + sign * 11, cy - 8), 1)
    p.bezier(accent, (62, 584), (190, 569), (268, 600), (425, 578), 1.4)


def _motif_february(p, c):
    accent, plum, gold, line = c['accent'], c['secondary'], c['highlight'], c['line']
    folds = [((748, 36), (835, 38), (864, 67), (776, 67)),
             ((761, 31), (852, 33), (880, 64), (785, 63)),
             ((776, 27), (872, 30), (901, 58), (804, 59))]
    for index, fold in enumerate(folds):
        p.polygon((line, plum, c['card'])[index], fold)
        p.lines((plum, accent, gold)[index], fold, 1, True)
        p.line(accent, fold[3], fold[2], 1)
    for x in range(4, 26, 10):
        for y in range(30, 330, 18):
            p.lines(line, [(x - 5, y), (x, y - 5), (x + 5, y),
                           (x, y + 5)], .8, True)
            p.line(line, (x - 5, y), (x + 5, y), .7)
    p.bezier(plum, (35, 582), (188, 560), (307, 595), (425, 580), 2)
    p.bezier(gold, (35, 588), (188, 566), (307, 601), (425, 586), 1)


def _motif_march(p, c):
    green, pale, gold = c['secondary'], c['cloud'], c['highlight']
    for origin in ((752, 84), (793, 84), (844, 84), (889, 84)):
        x, y = origin
        height = 23 + (x % 3) * 5
        p.bezier(green, (x, y), (x - 5, y - 18),
                 (x + 6, y - height + 4), (x, y - height), 1.7)
        for off, side in ((-.55, -1), (-.32, 1), (-.1, -1)):
            _leaf(p, (x + side * 10, y + off * height), 21, 5,
                  -.8 if side < 0 else -2.3, pale, green)
    p.bezier(green, (8, 600), (3, 560), (16, 521), (8, 465), 2)
    for y in (480, 512, 543, 574):
        _leaf(p, (19, y), 25, 6, -.9, pale, green)
    for x in range(48, 425, 42):
        _rice_shoot(p, x, 591, 11 + (x % 5), green, gold)


def _motif_april(p, c):
    stem, edge, gold = c['secondary'], c['line'], c['highlight']
    p.bezier(stem, (740, 78), (770, 39), (809, 51), (900, 33), 1.5)
    for center, radius in (((771, 55), 11), ((804, 50), 14),
                           ((838, 48), 12), ((879, 37), 9)):
        _flower(p, center, radius, (255, 253, 247), edge, gold)
    p.bezier(stem, (8, 574), (19, 541), (10, 517), (22, 485), 1.7)
    for center in ((17, 498), (9, 533), (19, 553)):
        _flower(p, center, 6, (255, 253, 247), edge, gold)
    for x in (41, 107, 312, 411):
        p.circle((255, 253, 247), (x, 582), 2)


def _motif_may(p, c):
    water, green, gold = c['secondary'], c['cloud'], c['highlight']
    for index in range(4):
        y = 43 + index * 11
        p.lines(water, [(743, y), (762, y), (762, y + 4),
                        (788, y + 4), (788, y + 8), (906, y + 8)], 1)
    for x, y, height in ((762, 67, 16), (809, 73, 25),
                         (856, 77, 28), (894, 82, 22)):
        _rice_shoot(p, x, y, height, green, gold)
    for index in range(4):
        y = 575 + index * 5
        p.lines(water, [(35, y), (144, y), (144, y + 2),
                        (273, y + 2), (273, y + 4), (428, y + 4)], 1)
    for x in range(8, 27, 10):
        for y in range(96, 326, 44):
            _rice_shoot(p, x, y, 15, green, gold)


def _motif_june(p, c):
    water, light, border = c['secondary'], c['cloud'], c['line']
    for index in range(5):
        y = 38 + index * 9
        p.bezier((water, light)[index % 2], (738, y), (786, y - 19),
                 (825, y + 23), (904, y + 1), 1.5)
    for cx in (767, 827, 883):
        p.arc(water, (cx - 13, 59, 26, 10), 0, math.pi, 1)
        p.arc(border, (cx - 19, 56, 38, 15), 0, math.pi, .7)
    for index in range(8):
        y = 573 + index * 4
        p.bezier(light if index % 2 else water,
                 (22, y), (127, y - 15), (268, y + 18), (433, y), 1)
    for y in range(37, 320, 23):
        p.arc(water, (2, y, 21, 10), 0, math.pi, 1)


def _motif_july(p, c):
    stem, grain, dark = c['secondary'], c['highlight'], c['accent']
    for x, bend in ((762, -18), (798, -8), (833, 12),
                    (867, 20), (895, 12)):
        _grain_ear(p, x, 31, bend, stem, grain)
    for y in range(28, 321, 19):
        p.line(stem, (2, y), (22, y + 8), .8)
        p.line(grain, (22, y), (2, y + 8), .8)
    for x in range(36, 430, 15):
        p.line(dark if x % 3 else grain, (x, 579), (x + 9, 590), .8)
        p.line(stem, (x + 9, 579), (x, 590), .8)


def _motif_august(p, c):
    wind, leaf, edge = c['line'], c['highlight'], c['secondary']
    for index in range(4):
        y = 44 + index * 10
        p.bezier(wind, (737, y), (781, y - 13),
                 (835, y + 13), (909, y - 8), 1.3)
    for center, angle, size in (((766, 38), -.5, 22),
                                ((828, 65), 2.4, 27),
                                ((880, 43), -.1, 20)):
        _leaf(p, center, size, size * .24, angle, leaf, edge)
    for index, x in enumerate((38, 94, 161, 230, 307, 394)):
        y = 580 + (index % 3) * 3
        _leaf(p, (x, y), 17, 4, -.55 if index % 2 else 2.65,
              leaf, edge)
    p.bezier(wind, (2, 462), (38, 478), (1, 525), (28, 548), 1.5)


def _motif_september(p, c):
    star, grass, silver = c['highlight'], c['secondary'], c['cloud']
    for x, y, radius in ((760, 43, 3), (784, 58, 1.5), (809, 38, 2.5),
                          (839, 69, 2), (866, 41, 3), (895, 61, 1.8)):
        _spark(p, (x, y), radius, star)
    rng = random.Random(901)
    for _ in range(85):
        x = rng.choice((rng.randrange(3, 25), rng.randrange(1001, 1022)))
        y = rng.randrange(18, 568)
        p.circle(silver if rng.randrange(3) else star, (x, y), .6)
    for x in (11, 19, 27):
        p.bezier(grass, (x, 590), (x - 3, 563),
                 (x + 13, 540), (x + 19, 521), 1.5)
        for dy in (5, 10, 15, 20):
            cy = 521 + dy
            cx = x + 19 - dy * .27
            p.line(silver, (cx, cy), (cx - 8, cy - 5), .7)
            p.line(silver, (cx, cy), (cx + 7, cy - 5), .7)
    p.line(star, (45, 581), (426, 581), .8)


def _motif_october(p, c):
    lacquer, cedar, gold = c['accent'], c['secondary'], c['highlight']
    # A torii silhouette fills the calendar title's right-hand opening.
    p.polygon(lacquer, [(750, 39), (902, 39), (894, 45), (758, 45)])
    p.polygon(lacquer, [(763, 48), (891, 48), (885, 52), (769, 52)])
    p.rect(lacquer, (778, 46, 6, 37))
    p.rect(lacquer, (867, 46, 6, 37))
    p.rect(gold, (802, 42, 47, 8), radius=2)
    for x in (7, 16):
        p.line(cedar, (x, 318), (x, 32), 1)
        for y in range(42, 314, 23):
            p.polygon(cedar, [(x, y), (x - 7, y + 13), (x + 7, y + 13)])
    for x in (50, 143, 236, 329, 415):
        p.line(lacquer, (x, 573), (x + 6, 582), 1.5)
        p.line(lacquer, (x + 6, 582), (x, 591), 1.5)


def _motif_november(p, c):
    ice, branch, glint = c['cloud'], c['secondary'], c['highlight']
    for root, tip in (((746, 79), (786, 38)),
                      ((895, 77), (850, 34)),
                      ((807, 78), (824, 29))):
        p.line(branch, root, tip, 1.5)
        for index in (1, 2, 3):
            t = index / 4
            x = root[0] + (tip[0] - root[0]) * t
            y = root[1] + (tip[1] - root[1]) * t
            _spark(p, (x, y), 3 + index, ice)
    for x in range(38, 430, 37):
        _spark(p, (x, 583 + (x % 3)), 4, ice)
    for y in range(28, 324, 25):
        _spark(p, (13, y), 3, glint if y % 2 else ice)
    p.lines(branch, [(26, 570), (33, 563), (40, 570),
                     (47, 563), (54, 570)], 1)


def _motif_december(p, c):
    gold, lacquer, smoke = c['highlight'], c['accent'], c['line']
    for index in range(4):
        y = 42 + index * 9
        p.bezier(smoke, (739, y), (778, y - 15),
                 (852, y + 10), (902, y - 9), 1.2)
    # A lantern and temple bell share a busy year-end eave.
    p.line(lacquer, (759, 33), (899, 33), 2)
    x = 800
    p.line(lacquer, (x, 33), (x, 42), 1)
    p.ellipse(gold, (x - 11, 42, 22, 28))
    p.ellipse(lacquer, (x - 11, 42, 22, 28), 1)
    p.line(lacquer, (x - 10, 48), (x + 10, 48), 1)
    p.line(lacquer, (x - 10, 64), (x + 10, 64), 1)
    p.rect(lacquer, (x - 5, 70, 10, 3), radius=1)
    p.line(lacquer, (860, 33), (860, 42), 1)
    p.circle(lacquer, (860, 44), 3)
    bell = [(854, 46), (866, 46), (871, 52), (871, 62),
            (876, 69), (844, 69), (849, 62), (849, 52)]
    p.polygon(gold, bell)
    p.lines(lacquer, bell, 1, True)
    p.line(lacquer, (846, 65), (874, 65), 1)
    p.circle(lacquer, (860, 72), 2)
    for index in range(5):
        y = 572 + index * 5
        p.bezier(gold if index % 2 else lacquer, (32, y),
                 (129, y - 16), (286, y + 18), (430, y - 4), 1)
    for y in range(42, 322, 26):
        p.line(gold, (8, y), (25, y - 7), 1)
        p.line(lacquer, (9, y + 6), (21, y + 1), 1)


_MOTIFS = {
    1: _motif_january, 2: _motif_february, 3: _motif_march,
    4: _motif_april, 5: _motif_may, 6: _motif_june,
    7: _motif_july, 8: _motif_august, 9: _motif_september,
    10: _motif_october, 11: _motif_november, 12: _motif_december,
}


def draw_dashboard_base(surface, month, palette):
    """Paint a deterministic monthly base; leave the daily-art pixels untouched.

    ``palette`` supplies paper, card, ink, muted, line, accent, secondary,
    highlight, and cloud. Optional page_ink/page_muted can be used for dark
    paper (notably September); those colors belong to the caller's text layer.
    """
    if surface.get_size() != SIZE:
        raise ValueError("Dashboard surface must be 1024x600")
    if month not in _MOTIFS:
        raise ValueError("Month must be 1..12")

    colors = {name: _color(getattr(palette, name)) for name in
              ('paper', 'card', 'ink', 'muted', 'line', 'accent',
               'secondary', 'highlight', 'cloud')}
    page_ink = getattr(palette, 'page_ink', None)
    page_muted = getattr(palette, 'page_muted', None)
    colors['page_ink'] = _color(page_ink) if page_ink is not None else colors['ink']
    colors['page_muted'] = _color(page_muted) if page_muted is not None else colors['muted']
    paper, card = colors['paper'], colors['card']
    edge = _mix(paper, colors['line'], .65)
    shadow = _mix(paper, colors['page_ink'], .10)

    large = pygame.Surface((SIZE[0] * SCALE, SIZE[1] * SCALE))
    large.fill(paper)
    pen = _Pen(large)
    _page_scene(pen, month, colors)
    _base_texture(pen, month, _mix(paper, colors['page_muted'], .17))

    # Page-wide structure is visible even when the illustration is replaced.
    pen.line(edge, (0, 16), (1024, 16), 1)
    pen.line(edge, (0, 594), (1024, 594), 1)
    pen.line(colors['accent'], (0, 16), (112, 16), 2)
    pen.line(colors['accent'], (912, 594), (1024, 594), 2)
    pen.line(edge, (12, 69), (12, 213), 1)
    pen.line(edge, (27, 218), (429, 218), 1)
    pen.line(edge, (438, 20), (438, 575), 1)
    pen.line(edge, (1009, 27), (1009, 571), 1)

    _card(pen, (452, 24, 548, 387), month, card, colors['line'],
          shadow, colors['accent'])
    _card(pen, (452, 427, 548, 149), month, card, colors['line'],
          shadow, colors['accent'])
    _art_frame(pen, month, colors['line'], colors['accent'], shadow)

    # The moon panel stays clear of the disk and three existing label lines.
    pen.rect(shadow, (31, 228, 400, 82), radius=16)
    pen.rect(colors['ink'], (28, 224, 400, 82), radius=16)
    pen.rect(_mix(colors['ink'], colors['highlight'], .55),
             (29, 225, 398, 80), 1, radius=15)
    _MOTIFS[month](pen, colors)
    reduced = pygame.transform.smoothscale(large, SIZE)
    # No final overlay pixels land on the image, even around an anti-aliased edge.
    for region in ((0, 0, 1024, ART.top),
                   (0, ART.top, ART.left, ART.height),
                   (ART.right, ART.top, 1024 - ART.right, ART.height),
                   (0, ART.bottom, 1024, 600 - ART.bottom)):
        surface.blit(reduced, region[:2], pygame.Rect(region))


def draw_selected_day(surface, rect, month, palette):
    """Draw the calendar's 52 x 45 selection behind its existing text."""
    if month not in _MOTIFS:
        raise ValueError("Month must be 1..12")
    rect = pygame.Rect(rect)
    if rect.width < 4 or rect.height < 4:
        return
    ink, accent = _color(palette.ink), _color(palette.highlight)
    edge = _mix(ink, accent, .44)
    shape = pygame.Surface((rect.width * SCALE, rect.height * SCALE),
                           pygame.SRCALPHA)
    pen = _Pen(shape)
    w, h = rect.size
    if month == 2:
        pen.polygon(edge, [(3, 3), (w - 1, 3), (w - 1, h - 1),
                           (3, h - 1)])
        pen.polygon(ink, [(0, 0), (w - 7, 0), (w, 7),
                          (w, h - 3), (4, h), (0, h - 4)])
    elif month == 5:
        pen.polygon(ink, [(5, 0), (w - 5, 0), (w - 5, 4),
                          (w, 4), (w, h - 4), (w - 5, h - 4),
                          (w - 5, h), (5, h), (5, h - 4),
                          (0, h - 4), (0, 4), (5, 4)])
    elif month == 11:
        pen.polygon(ink, [(8, 0), (w - 8, 0), (w, 8),
                          (w, h - 8), (w - 8, h), (8, h),
                          (0, h - 8), (0, 8)])
    elif month in (3, 4, 8):
        pen.rect(ink, (0, 0, w, h), radius=17)
        pen.rect(edge, (0, 0, w, h), 1, radius=17)
        for x, direction in ((4, -1), (w - 4, 1)):
            _leaf(pen, (x, h / 2), 7, 2, direction * math.pi / 2,
                  edge)
    else:
        radius = 20 if month == 7 else 10 if month in (1, 10, 12) else 13
        pen.rect(ink, (0, 0, w, h), radius=radius)
        pen.rect(edge, (0, 0, w, h), 1, radius=radius)
        if month in (1, 7, 9, 10, 12):
            for x in (6, w - 6):
                pen.circle(edge, (x, h - 5), 1.1)
    surface.blit(pygame.transform.smoothscale(shape, rect.size), rect.topleft)
