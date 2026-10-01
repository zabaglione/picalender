"""Handcrafted calendar dashboard, composed at 1024x600 and cached by minute."""
import calendar
from datetime import datetime, timedelta
import logging
import math
from pathlib import Path
import time
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import holidays
import pygame
import astronomy

from src.renderers.moon_disk import moon_surface
from src.renderers.wafu_theme_design import draw_dashboard_base, draw_selected_day
from src.utils.moon_phase import MOON_PHASES_JA, get_moon_info, get_next_moon_phases
from src.utils.rokuyou import get_rokuyou_name
from src.utils.sky_events import SkyTimes, clock_time, rise_set_times
from src.weather.dashboard_weather import DashboardWeather, WeatherSnapshot

@dataclass(frozen=True)
class MonthTheme:
    paper: tuple[int, int, int]
    card: tuple[int, int, int]
    ink: tuple[int, int, int]
    muted: tuple[int, int, int]
    line: tuple[int, int, int]
    accent: tuple[int, int, int]
    secondary: tuple[int, int, int]
    highlight: tuple[int, int, int]
    cloud: tuple[int, int, int]
    page_ink: tuple[int, int, int] | None = None
    page_muted: tuple[int, int, int] | None = None


# Monthly illustrations share warm paper and readable dark lettering.
# Ink, weekend accents and weather colors echo each illustration's pigments.
_MONTH_PIGMENTS = (
    ((76, 48, 41), (167, 64, 49), (69, 108, 78), (183, 133, 55), (208, 188, 151)),
    ((64, 47, 68), (158, 72, 99), (115, 91, 134), (183, 126, 92), (207, 177, 202)),
    ((47, 68, 53), (158, 78, 78), (75, 115, 80), (190, 143, 78), (187, 211, 175)),
    ((49, 70, 53), (150, 89, 67), (78, 116, 86), (191, 153, 91), (199, 214, 187)),
    ((40, 69, 53), (167, 90, 65), (55, 116, 83), (184, 146, 65), (177, 209, 177)),
    ((40, 60, 76), (157, 86, 112), (67, 112, 145), (177, 136, 83), (175, 199, 215)),
    ((68, 65, 39), (164, 78, 53), (95, 110, 65), (182, 132, 47), (209, 200, 150)),
    ((76, 50, 41), (163, 70, 44), (108, 105, 58), (191, 129, 50), (220, 188, 151)),
    ((36, 51, 73), (163, 81, 61), (76, 114, 126), (200, 161, 81), (174, 192, 200)),
    ((42, 65, 50), (170, 60, 44), (70, 112, 78), (183, 137, 67), (181, 202, 170)),
    ((43, 61, 73), (144, 80, 82), (64, 112, 135), (164, 140, 101), (174, 200, 216)),
    ((67, 51, 40), (165, 63, 43), (79, 111, 90), (199, 148, 65), (199, 187, 152)),
)
MONTHLY_THEMES = {
    month: MonthTheme(
        paper=(244, 235, 216), card=(252, 246, 229), ink=ink,
        muted=(91, 94, 82), line=(186, 190, 172), accent=accent,
        secondary=secondary, highlight=highlight, cloud=cloud,
    )
    for month, (ink, accent, secondary, highlight, cloud)
    in enumerate(_MONTH_PIGMENTS, 1)
}
MONTHS = tuple(calendar.month_name)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
LOGGER = logging.getLogger(__name__)


class FieldNotesRenderer:
    SIZE = (1024, 600)

    def __init__(self, settings=None, *, weather=None, start_worker=True):
        self.settings = settings or {}
        self.root = Path(__file__).resolve().parents[2]
        self.assets = self.root / "assets" / "field_notes"
        self.timezone = ZoneInfo(self.settings.get("weather", {}).get("timezone", "Asia/Tokyo"))
        location = self.settings.get("weather", {}).get("location", {})
        self.latitude = location.get("lat", 35.681236)
        self.longitude = location.get("lon", 139.767125)
        self.weather = weather or DashboardWeather(self.settings, self.root, start_worker)
        self.fonts = {}
        self._base_key = None
        self._base = None
        self._calendar_key = None
        self._calendar_surface = None
        self._holiday_year = None
        self._holidays = {}
        self._sky_day = None
        self._sky_times = SkyTimes(None, None, None, None)
        self._next_moon_event = None
        self._moon_last_now = None
        self._artwork_signature = None
        self._artwork_next_check = 0.0
        self._artwork_revision = 0
        self._artwork = None
        self._theme_month = datetime.now(self.timezone).month
        self.theme = MONTHLY_THEMES[self._theme_month]
        self._static = self._make_static()

    def font(self, size, family="sans"):
        key = (family, size)
        if key not in self.fonts:
            filename = {"sans": "dmsans.ttf", "serif": "fraunces.ttf", "jp": "zenmaru.ttf"}[family]
            self.fonts[key] = pygame.font.Font(str(self.assets / filename), size)
        return self.fonts[key]

    def text(self, surface, value, pos, size=16, color=None, family="sans", center=False):
        if color is None:
            color = self.theme.ink
        rendered = self.font(size, family).render(str(value), True, color)
        rect = rendered.get_rect()
        if center:
            rect.midtop = pos
        else:
            rect.topleft = pos
        surface.blit(rendered, rect)
        return rect

    def _make_static(self):
        surface = pygame.Surface(self.SIZE)
        draw_dashboard_base(surface, self._theme_month, self.theme,
                            title_width=self.font(36, "serif").size(MONTHS[self._theme_month])[0])
        artwork = self._artwork
        if artwork is None:
            artwork = pygame.image.load(str(self.assets / "forest-fox.png")).convert()
            artwork = pygame.transform.smoothscale(artwork, (400, 225))
        surface.blit(artwork, (28, 337))
        return surface

    def _sky(self, surface, now):
        if self._sky_day != now.date():
            self._sky_day = now.date()
            try:
                self._sky_times = rise_set_times(now.date(), self.latitude, self.longitude,
                                                 self.timezone.key)
            except (ValueError, astronomy.Error) as exc:
                self._sky_times = SkyTimes(None, None, None, None)
                LOGGER.warning("Rise/set calculation failed: %s", exc)
        sky = self._sky_times
        self.text(surface, f"日の出 {clock_time(sky.sunrise)}    日の入 {clock_time(sky.sunset)}",
                  (30, 21), 16, self.theme.page_muted or self.theme.muted, "jp")
        self.text(surface, f"月の出 {clock_time(sky.moonrise)}    月の入 {clock_time(sky.moonset)}",
                  (30, 47), 14, self.theme.page_muted or self.theme.muted, "jp")

    def _refresh_artwork(self):
        if not self.settings.get("daily_art", {}).get("enabled", False):
            return
        stamp = time.monotonic()
        if stamp < self._artwork_next_check:
            return
        self._artwork_next_check = stamp + 5
        path = self.root / "cache/daily_art/current.png"
        try:
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature == self._artwork_signature:
                return
            self._artwork_signature = signature
            # The sync job validates and atomically replaces a small 800x450 PNG.
            if stat.st_size > 20 * 1024 * 1024:
                raise ValueError("Artwork cache is too large")
            artwork = pygame.image.load(str(path)).convert()
            artwork = pygame.transform.smoothscale(artwork, (400, 225))
            self._artwork = artwork
            self._static.blit(artwork, (28, 337))
            self._artwork_revision += 1
            LOGGER.info("Daily artwork reloaded")
        except FileNotFoundError:
            pass
        except (OSError, ValueError, pygame.error) as exc:
            LOGGER.warning("Artwork reload failed; keeping the previous image: %s", exc)

    def _calendar(self, now):
        config = self.settings.get("calendar", {})
        if self._holiday_year != now.year:
            self._holidays = (holidays.country_holidays(config.get("holidays_country", "JP"),
                                                       years=[now.year, now.year + 1], language="ja")
                              if config.get("holidays_enabled", True) else {})
            self._holiday_year = now.year
        key = (now.year, now.month, now.day)
        if key == self._calendar_key:
            return self._calendar_surface
        result = pygame.Surface(self.SIZE, pygame.SRCALPHA)
        self.text(result, MONTHS[now.month], (474, 35), 36, family="serif")
        year = self.font(23, "serif").render(str(now.year), True, self.theme.muted)
        result.blit(year, (976 - year.get_width(), 48))
        pygame.draw.line(result, self.theme.line, (476, 90), (975, 89), 1)
        monday_first = config.get("first_weekday", "SUNDAY").upper() == "MONDAY"
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        if not monday_first:
            weekdays = [weekdays[-1]] + weekdays[:-1]
        width = 72
        for column, label in enumerate(weekdays):
            color = self.theme.accent if label == "SUN" else self.theme.secondary if label == "SAT" else self.theme.muted
            self.text(result, label, (510 + column * width, 102), 11, color, center=True)
        weeks = calendar.Calendar(0 if monday_first else 6).monthdayscalendar(now.year, now.month)
        row_height = 252 / len(weeks)
        for row, week in enumerate(weeks):
            for column, day in enumerate(week):
                if not day:
                    continue
                target = now.date().replace(day=day)
                x, y = 510 + column * width, 125 + int(row * row_height)
                color = self.theme.accent if target in self._holidays or target.weekday() == 6 else self.theme.secondary if target.weekday() == 5 else self.theme.ink
                selected = day == now.day
                if selected:
                    draw_selected_day(result, (x - 26, y - 1, 52, 45),
                                      self._theme_month, self.theme)
                    color = self.theme.card
                self.text(result, day, (x, y), 22, color, center=True)
                if config.get("rokuyou_enabled", True) and config.get("show_rokuyou_names", True):
                    label = get_rokuyou_name(target)
                    self.text(result, label, (x, y + 25), 12, self.theme.card if selected else self.theme.muted, "jp", center=True)
                if target in self._holidays and not selected:
                    pygame.draw.circle(result, self.theme.accent, (x + 21, y + 15), 2)
        pygame.draw.line(result, self.theme.line, (476, 383), (975, 382), 1)
        upcoming = sorted(day for day in self._holidays if now.date() <= day)
        if upcoming and config.get("show_holiday_names", True):
            day = upcoming[0]
            label = "今日の祝日" if day == now.date() else "次の祝日"
            self.text(result, label, (476, 386), 13, self.theme.accent, "jp")
            self.text(result, f"{day.month}/{day.day}", (554, 386), 14, self.theme.accent)
            self.text(result, self._holidays[day], (610, 386), 14, self.theme.muted, "jp")
        self._calendar_key, self._calendar_surface = key, result
        return result

    def _moon(self, surface, now):
        if not self.settings.get("calendar", {}).get("moon_phase_enabled", True):
            return
        if (self._next_moon_event is None or
                (self._moon_last_now is not None and now < self._moon_last_now) or
                now >= self._next_moon_event["time"].astimezone(self.timezone)):
            events = get_next_moon_phases(now, 12)
            self._next_moon_event = events[0] if events else None
        self._moon_last_now = now
        if self._next_moon_event:
            event = self._next_moon_event
            local = event["time"].astimezone(self.timezone)
            self.text(surface, f"次の{MOON_PHASES_JA[event['phase']]}  {local.month}/{local.day} {local:%H:%M}",
                      (30, 201), 13, self.theme.page_muted or self.theme.muted, "jp")
        info = get_moon_info(now)
        surface.blit(moon_surface(info, 64), (42, 233))
        self.text(surface, info["phase_name"], (119, 230), 19, self.theme.card, "serif")
        self.text(surface, info["phase_name_ja"], (120, 254), 15, self.theme.card, "jp")
        self.text(surface, f"Age {info['age']:.1f} days  /  {info['illumination']:.0f}% lit",
                  (120, 281), 13, self.theme.line)

    @staticmethod
    def _weather_kind(code):
        if code in (0, 1):
            return "sun"
        if code == 2:
            return "partly"
        if code == 3:
            return "cloud"
        if code in (45, 48):
            return "fog"
        if code in (71, 73, 75, 77, 85, 86):
            return "snow"
        if code in (95, 96, 99):
            return "thunder"
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
            return "rain"
        return "unknown"

    def _weather_icon(self, surface, center, kind):
        x, y = center
        if kind == "unknown":
            pygame.draw.line(surface, self.theme.line, (x - 8, y), (x + 8, y), 2)
            return
        if kind in ("sun", "partly"):
            sx, sy = (x, y) if kind == "sun" else (x - 9, y - 7)
            for index in range(8):
                angle = index * math.pi / 4
                a = (sx + round(14 * math.cos(angle)), sy + round(14 * math.sin(angle)))
                b = (sx + round(18 * math.cos(angle)), sy + round(18 * math.sin(angle)))
                pygame.draw.line(surface, self.theme.highlight, a, b, 2)
            pygame.draw.circle(surface, self.theme.highlight, (sx, sy), 10)
            pygame.draw.circle(surface, self.theme.ink, (sx, sy), 10, 1)
        if kind == "sun":
            return
        # The outline follows the combined cloud silhouette, not three outlined circles.
        cloud = pygame.Surface((52, 39), pygame.SRCALPHA)
        for color, inset in ((self.theme.ink, 0), (self.theme.cloud, 2)):
            pygame.draw.ellipse(cloud, color, (5 + inset, 14 + inset, 42 - 2 * inset, 17 - 2 * inset))
            pygame.draw.circle(cloud, color, (20, 16), 11 - inset)
            pygame.draw.circle(cloud, color, (33, 18), 9 - inset)
        surface.blit(cloud, (x - 26, y - 21))
        if kind == "rain":
            for dx in (-12, 0, 12):
                pygame.draw.line(surface, self.theme.secondary, (x + dx, y + 13), (x + dx - 3, y + 19), 2)
        elif kind == "snow":
            for dx in (-11, 2, 14):
                pygame.draw.line(surface, self.theme.secondary, (x + dx - 2, y + 15), (x + dx + 2, y + 19), 1)
                pygame.draw.line(surface, self.theme.secondary, (x + dx + 2, y + 15), (x + dx - 2, y + 19), 1)
        elif kind == "thunder":
            pygame.draw.lines(surface, self.theme.highlight, False, [(x + 3, y + 10), (x - 3, y + 17), (x + 2, y + 17), (x - 3, y + 23)], 3)
        elif kind == "fog":
            for dy in (14, 19):
                pygame.draw.line(surface, self.theme.secondary, (x - 16, y + dy), (x + 16, y + dy), 2)

    def _forecast(self, surface, now, snapshot):
        stale = snapshot.error or (snapshot.updated is not None and
                                  (now - snapshot.updated).total_seconds() > 7200)
        by_day = {forecast.date: forecast for forecast in snapshot.forecasts}
        if snapshot.updated is None:
            status = "予報取得不可" if snapshot.error else "予報取得中"
        elif now.date() not in by_day:
            status = "今日の予報なし"
        else:
            prefix = "予報更新遅延" if stale else "予報更新"
            updated = snapshot.updated.astimezone(self.timezone)
            status = f"{prefix} {updated.month}/{updated.day} {updated:%H:%M}"
        self.text(surface, status, (474, 435), 11, self.theme.muted, "jp")
        for index in range(3):
            target = now.date() + timedelta(days=index)
            x = 474 + index * 170
            if index:
                pygame.draw.line(surface, self.theme.line, (x - 12, 467), (x - 12, 558), 1)
            day_label = f"{target.month}/{target.day} {WEEKDAYS[target.weekday()][:3].upper()}"
            self.text(surface, day_label, (x, 462), 11, self.theme.muted)
            forecast = by_day.get(target)
            icon = self._weather_kind(forecast.code if forecast else None)
            self._weather_icon(surface, (x + 24, 512), icon)
            high = f"{forecast.high:.0f}" if forecast and forecast.high is not None else "--"
            low = f"{forecast.low:.0f}" if forecast and forecast.low is not None else "--"
            self.text(surface, f"{high}°", (x + 56, 486), 25, self.theme.ink, "serif")
            self.text(surface, f"/ {low}°", (x + 106, 495), 14, self.theme.muted)
            rain = f"{forecast.rain:.0f}%" if forecast and forecast.rain is not None else "--"
            self.text(surface, f"Rain {rain}", (x + 57, 526), 12, self.theme.muted)
        self.text(surface, "Weather: Open-Meteo / CC BY 4.0", (454, 584), 9,
                  self.theme.page_muted or self.theme.muted)

    def render(self, screen, now=None):
        now = now or datetime.now(self.timezone)
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)
        if now.month != self._theme_month:
            self._theme_month = now.month
            self.theme = MONTHLY_THEMES[now.month]
            self._static = self._make_static()
            self._calendar_key = None
            self._base_key = None
        self._refresh_artwork()
        snapshot = self.weather.snapshot()
        key = (now.year, now.month, now.day, now.hour, now.minute, snapshot.revision, self._artwork_revision)
        if key != self._base_key:
            self._base = self._static.copy()
            self._sky(self._base, now)
            self._base.blit(self._calendar(now), (0, 0))
            self._moon(self._base, now)
            self._forecast(self._base, now, snapshot)
            self.text(self._base, f"{WEEKDAYS[now.weekday()]}, {MONTHS[now.month]} {now.day}",
                      (30, 172), 21, self.theme.page_ink or self.theme.ink)
            self._base_key = key
        frame = self._base.copy()
        clock = self.text(frame, now.strftime("%H:%M"), (26, 64), 112,
                          self.theme.page_ink or self.theme.ink, "serif")
        seconds = self.font(34, "serif").render(now.strftime("%S"), True,
                                               self.theme.page_muted or self.theme.muted)
        seconds_x = min(clock.right + 12, 445 - seconds.get_width())
        frame.blit(seconds, seconds.get_rect(bottomleft=(seconds_x, 166)))
        if screen.get_size() == self.SIZE:
            screen.blit(frame, (0, 0))
        else:
            scale = min(screen.get_width() / 1024, screen.get_height() / 600)
            size = (round(1024 * scale), round(600 * scale))
            screen.fill(self.theme.ink)
            screen.blit(pygame.transform.smoothscale(frame, size),
                        ((screen.get_width() - size[0]) // 2, (screen.get_height() - size[1]) // 2))

    def cleanup(self):
        self.weather.cleanup()
