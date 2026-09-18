"""Handcrafted calendar dashboard, composed at 1024x600 and cached by minute."""
import calendar
from datetime import datetime, timedelta
import math
from pathlib import Path
import random
from zoneinfo import ZoneInfo

import holidays
import pygame

from src.renderers.moon_disk import moon_surface
from src.utils.moon_phase import get_moon_info
from src.utils.rokuyou import get_rokuyou_name
from src.weather.dashboard_weather import DashboardWeather, WeatherSnapshot

PAPER = (237, 232, 216)
CARD = (248, 244, 231)
INK = (39, 63, 57)
MUTED = (102, 115, 98)
LINE = (195, 199, 174)
RUST = (173, 87, 62)
SAGE = (113, 139, 129)
GOLD = (192, 141, 77)
MONTHS = tuple(calendar.month_name)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class FieldNotesRenderer:
    SIZE = (1024, 600)

    def __init__(self, settings=None, *, weather=None, start_worker=True):
        self.settings = settings or {}
        self.root = Path(__file__).resolve().parents[2]
        self.assets = self.root / "assets" / "field_notes"
        self.timezone = ZoneInfo(self.settings.get("weather", {}).get("timezone", "Asia/Tokyo"))
        self.weather = weather or DashboardWeather(self.settings, self.root, start_worker)
        self.fonts = {}
        self._base_key = None
        self._base = None
        self._calendar_key = None
        self._calendar_surface = None
        self._holiday_year = None
        self._holidays = {}
        self._static = self._make_static()

    def font(self, size, family="sans"):
        key = (family, size)
        if key not in self.fonts:
            filename = {"sans": "dmsans.ttf", "serif": "fraunces.ttf", "jp": "zenmaru.ttf"}[family]
            self.fonts[key] = pygame.font.Font(str(self.assets / filename), size)
        return self.fonts[key]

    def text(self, surface, value, pos, size=16, color=INK, family="sans", center=False):
        rendered = self.font(size, family).render(str(value), True, color)
        rect = rendered.get_rect()
        if center:
            rect.midtop = pos
        else:
            rect.topleft = pos
        surface.blit(rendered, rect)
        return rect

    @staticmethod
    def panel(surface, rect, fill=CARD, border=LINE):
        x, y, w, h = rect
        points = [(x + 10, y + 1), (x + w - 15, y), (x + w - 2, y + 10),
                  (x + w, y + h - 13), (x + w - 12, y + h - 1),
                  (x + 9, y + h), (x, y + h - 11), (x + 1, y + 12)]
        pygame.draw.polygon(surface, fill, points)
        pygame.draw.lines(surface, border, True, points, 1)

    def _make_static(self):
        surface = pygame.Surface(self.SIZE)
        surface.fill(PAPER)
        rng = random.Random(918)
        for _ in range(9000):
            point = (rng.randrange(1024), rng.randrange(600))
            shade = rng.choice((-4, -2, 2, 4))
            surface.set_at(point, tuple(channel + shade for channel in PAPER))
        self.panel(surface, (452, 24, 548, 387))
        self.panel(surface, (452, 427, 548, 149))
        self.panel(surface, (28, 224, 400, 82), INK, INK)
        artwork = pygame.image.load(str(self.assets / "forest-fox.png")).convert()
        artwork = pygame.transform.smoothscale(artwork, (400, 225))
        surface.blit(artwork, (28, 337))
        pygame.draw.line(surface, LINE, (28, 562), (428, 562), 1)
        self.text(surface, "FIELD NOTES", (30, 25), 14, MUTED)
        self.text(surface, "A SMALL WINDOW INTO TODAY", (30, 48), 10, MUTED)
        self.text(surface, "THE MOON", (30, 202), 11, MUTED)
        self.text(surface, "A MOMENT OF QUIET", (30, 318), 10, MUTED)
        self.text(surface, "PiCalendar", (30, 575), 11, MUTED)
        self.text(surface, "LOCAL TIME", (350, 578), 9, MUTED)
        self.text(surface, "THREE-DAY FORECAST", (474, 437), 11, MUTED)
        return surface

    def _calendar(self, now):
        config = self.settings.get("calendar", {})
        if self._holiday_year != now.year:
            self._holidays = (holidays.country_holidays(config.get("holidays_country", "JP"),
                                                       years=[now.year], language="ja")
                              if config.get("holidays_enabled", True) else {})
            self._holiday_year = now.year
        key = (now.year, now.month, now.day)
        if key == self._calendar_key:
            return self._calendar_surface
        result = pygame.Surface(self.SIZE, pygame.SRCALPHA)
        self.text(result, MONTHS[now.month], (474, 35), 36, family="serif")
        year = self.font(23, "serif").render(str(now.year), True, MUTED)
        result.blit(year, (976 - year.get_width(), 48))
        pygame.draw.line(result, LINE, (476, 90), (975, 89), 1)
        monday_first = config.get("first_weekday", "SUNDAY").upper() == "MONDAY"
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        if not monday_first:
            weekdays = [weekdays[-1]] + weekdays[:-1]
        width = 72
        for column, label in enumerate(weekdays):
            color = RUST if label == "SUN" else SAGE if label == "SAT" else MUTED
            self.text(result, label, (510 + column * width, 102), 11, color, center=True)
        weeks = calendar.Calendar(0 if monday_first else 6).monthdayscalendar(now.year, now.month)
        row_height = 252 / len(weeks)
        for row, week in enumerate(weeks):
            for column, day in enumerate(week):
                if not day:
                    continue
                target = now.date().replace(day=day)
                x, y = 510 + column * width, 125 + int(row * row_height)
                color = RUST if target in self._holidays or target.weekday() == 6 else SAGE if target.weekday() == 5 else INK
                selected = day == now.day
                if selected:
                    self.panel(result, (x - 26, y - 1, 52, 45), INK, INK)
                    color = CARD
                self.text(result, day, (x, y), 22, color, center=True)
                if config.get("rokuyou_enabled", True) and config.get("show_rokuyou_names", True):
                    label = get_rokuyou_name(target)
                    self.text(result, label, (x, y + 25), 12, PAPER if selected else MUTED, "jp", center=True)
                if target in self._holidays and not selected:
                    pygame.draw.circle(result, RUST, (x + 21, y + 15), 2)
        pygame.draw.line(result, LINE, (476, 383), (975, 382), 1)
        upcoming = sorted(day for day in self._holidays if now.date() <= day and day.month == now.month)
        if upcoming and config.get("show_holiday_names", True):
            day = upcoming[0]
            self.text(result, f"{day.month:02}.{day.day:02}", (476, 390), 11, RUST)
            self.text(result, self._holidays[day], (522, 386), 13, MUTED, "jp")
        else:
            self.text(result, "A DAY AT A TIME", (476, 390), 10, MUTED)
        self._calendar_key, self._calendar_surface = key, result
        return result

    def _moon(self, surface, now):
        if not self.settings.get("calendar", {}).get("moon_phase_enabled", True):
            self.text(surface, "Take a little time.", (105, 248), 20, PAPER, "serif")
            return
        info = get_moon_info(now)
        surface.blit(moon_surface(info, 64), (42, 233))
        self.text(surface, info["phase_name"], (119, 234), 21, CARD, "serif")
        self.text(surface, f"Age {info['age']:.1f} days  /  {info['illumination']:.0f}% lit",
                  (120, 268), 14, (199, 207, 180))

    @staticmethod
    def _condition(code):
        if code in (0, 1):
            return "Clear", "sun"
        if code == 2:
            return "Partly cloudy", "partly"
        if code == 3:
            return "Cloudy", "cloud"
        if code in (45, 48):
            return "Fog", "fog"
        if code in (71, 73, 75, 77, 85, 86):
            return "Snow", "snow"
        if code in (95, 96, 99):
            return "Thunder", "thunder"
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
            return "Rain", "rain"
        return "Unavailable", "unknown"

    @staticmethod
    def _weather_icon(surface, center, kind):
        x, y = center
        if kind == "unknown":
            pygame.draw.line(surface, LINE, (x - 8, y), (x + 8, y), 2)
            return
        if kind in ("sun", "partly"):
            sx, sy = (x, y) if kind == "sun" else (x - 9, y - 7)
            for index in range(8):
                angle = index * math.pi / 4
                a = (sx + round(14 * math.cos(angle)), sy + round(14 * math.sin(angle)))
                b = (sx + round(18 * math.cos(angle)), sy + round(18 * math.sin(angle)))
                pygame.draw.line(surface, GOLD, a, b, 2)
            pygame.draw.circle(surface, GOLD, (sx, sy), 10)
            pygame.draw.circle(surface, INK, (sx, sy), 10, 1)
        if kind == "sun":
            return
        # The outline follows the combined cloud silhouette, not three outlined circles.
        cloud = pygame.Surface((52, 39), pygame.SRCALPHA)
        for color, inset in ((INK, 0), ((178, 192, 167), 2)):
            pygame.draw.ellipse(cloud, color, (5 + inset, 14 + inset, 42 - 2 * inset, 17 - 2 * inset))
            pygame.draw.circle(cloud, color, (20, 16), 11 - inset)
            pygame.draw.circle(cloud, color, (33, 18), 9 - inset)
        surface.blit(cloud, (x - 26, y - 21))
        if kind == "rain":
            for dx in (-12, 0, 12):
                pygame.draw.line(surface, SAGE, (x + dx, y + 13), (x + dx - 3, y + 19), 2)
        elif kind == "snow":
            for dx in (-11, 2, 14):
                pygame.draw.line(surface, SAGE, (x + dx - 2, y + 15), (x + dx + 2, y + 19), 1)
                pygame.draw.line(surface, SAGE, (x + dx + 2, y + 15), (x + dx - 2, y + 19), 1)
        elif kind == "thunder":
            pygame.draw.lines(surface, GOLD, False, [(x + 3, y + 10), (x - 3, y + 17), (x + 2, y + 17), (x - 3, y + 23)], 3)
        elif kind == "fog":
            for dy in (14, 19):
                pygame.draw.line(surface, SAGE, (x - 16, y + dy), (x + 16, y + dy), 2)

    def _forecast(self, surface, now, snapshot):
        stale = snapshot.error or (snapshot.updated is not None and
                                  (now - snapshot.updated).total_seconds() > 7200)
        by_day = {forecast.date: forecast for forecast in snapshot.forecasts}
        if snapshot.updated is None:
            status = "OFFLINE" if snapshot.error else "CONNECTING"
        elif now.date() not in by_day:
            status = "NO FORECAST"
        else:
            status = ("CACHED" if stale else "UPDATED") + " " + snapshot.updated.astimezone(self.timezone).strftime("%H:%M")
        self.text(surface, status, (870, 438), 9, MUTED)
        for index in range(3):
            target = now.date() + timedelta(days=index)
            x = 474 + index * 170
            if index:
                pygame.draw.line(surface, LINE, (x - 12, 467), (x - 12, 558), 1)
            day_label = "TODAY" if index == 0 else "TOMORROW" if index == 1 else WEEKDAYS[target.weekday()].upper()
            self.text(surface, day_label, (x, 462), 11, MUTED)
            forecast = by_day.get(target)
            label, icon = self._condition(forecast.code if forecast else None)
            self._weather_icon(surface, (x + 24, 512), icon)
            high = f"{forecast.high:.0f}" if forecast and forecast.high is not None else "--"
            low = f"{forecast.low:.0f}" if forecast and forecast.low is not None else "--"
            self.text(surface, f"{high}°", (x + 56, 486), 25, INK, "serif")
            self.text(surface, f"/ {low}°", (x + 106, 495), 14, MUTED)
            rain = f"{forecast.rain:.0f}%" if forecast and forecast.rain is not None else "--"
            self.text(surface, f"Rain {rain}", (x + 57, 526), 12, MUTED)
            self.text(surface, label, (x, 551), 10, MUTED)
        self.text(surface, "Weather: Open-Meteo / CC BY 4.0", (454, 584), 9, MUTED)

    def render(self, screen, now=None):
        now = now or datetime.now(self.timezone)
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)
        snapshot = self.weather.snapshot()
        key = (now.year, now.month, now.day, now.hour, now.minute, snapshot.revision)
        if key != self._base_key:
            self._base = self._static.copy()
            self._base.blit(self._calendar(now), (0, 0))
            self._moon(self._base, now)
            self._forecast(self._base, now, snapshot)
            self.text(self._base, f"{WEEKDAYS[now.weekday()]}, {MONTHS[now.month]} {now.day}",
                      (30, 172), 21, INK)
            self._base_key = key
        frame = self._base.copy()
        self.text(frame, now.strftime("%H:%M"), (26, 64), 112, INK, "serif")
        self.text(frame, now.strftime("%S"), (398, 133), 23, MUTED, "serif")
        if screen.get_size() == self.SIZE:
            screen.blit(frame, (0, 0))
        else:
            scale = min(screen.get_width() / 1024, screen.get_height() / 600)
            size = (round(1024 * scale), round(600 * scale))
            screen.fill(INK)
            screen.blit(pygame.transform.smoothscale(frame, size),
                        ((screen.get_width() - size[0]) // 2, (screen.get_height() - size[1]) // 2))

    def cleanup(self):
        self.weather.cleanup()
