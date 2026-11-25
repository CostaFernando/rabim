"""Drawing primitives in a 1280 × 720 logical space."""

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from math import atan2, ceil, cos, dist, pi, sin

from PIL import Image, ImageChops, ImageDraw, ImageFont


@dataclass(frozen=True)
class Theme:
    paper: str = "#f7f4e9"
    ink: str = "#202e32"
    muted: str = "#526464"
    grid: str = "#d1d6ca"
    curve: str = "#176c75"
    accent: str = "#b54929"
    wash: str = "#f1d692"
    stroke: float = 3
    reveal: float = 1.25
    motion: float = 2.1
    serif: str = "/System/Library/Fonts/Supplemental/Georgia.ttf"
    sans: str = "/System/Library/Fonts/Avenir Next.ttc"
    mono: str = "/System/Library/Fonts/Supplemental/Andale Mono.ttf"


    @classmethod
    def notebook(cls, **overrides):
        """Create a notebook theme using the bundled handwriting face."""
        overrides.setdefault("sans", str(Path(__file__).parent / "fonts/caveat/Caveat-SemiBold.ttf"))
        return cls(**overrides)

@lru_cache(maxsize=128)
def _font(face, size):
    return ImageFont.truetype(face, size)


@lru_cache(maxsize=64)
def _handwriting(font, words, anchor):
    """Order connected ink regions left to right and follow each one's bends."""
    left, top, right, bottom = font.getbbox(words, anchor=anchor)
    alpha = Image.new("L", (right-left, bottom-top))
    ImageDraw.Draw(alpha).text((-left, -top), words, font=font, anchor=anchor, fill=255)
    remaining = {(i % alpha.width, i // alpha.width)
                 for i, value in enumerate(alpha.tobytes()) if value}
    neighbors = ((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1))

    def walk(start, pixels):
        queue = deque([start])
        pixels.remove(start)
        while queue:
            x, y = queue.popleft()
            yield x, y
            for dx, dy in neighbors:
                point = (x+dx, y+dy)
                if point in pixels:
                    pixels.remove(point)
                    queue.append(point)

    regions = []
    for point in sorted(remaining, key=lambda pt: (pt[1], pt[0])):
        if point in remaining:
            region = set(walk(point, remaining))
            regions.append((min(x for x,y in region), region))
    order = []
    for _, region in sorted(regions, key=lambda item: item[0]):
        entry = min(region, key=lambda pt: (pt[0] + .35*pt[1], pt[1], pt[0]))
        order.extend(walk(entry, region))
    return left, top, alpha, order


class Canvas:
    def __init__(self, image, theme, seed):
        self.image = image
        self.draw = ImageDraw.Draw(image)
        self.scale = image.width / 1280
        self.theme = theme
        self.seed = seed

    def text(self, xy, words, *, size=26, face="sans", color=None, anchor="lm"):
        font = _font(getattr(self.theme, face), round(size * self.scale))
        self.draw.text(
            tuple(v * self.scale for v in xy),
            words,
            font=font,
            fill=color or self.theme.ink,
            anchor=anchor,
        )

    def write_text(self, xy, words, *, progress=1, size=26, face="sans", color=None, anchor="lm"):
        """Trace the ink of a single line using the selected theme font."""
        if progress <= 0 or not words:
            return
        if progress >= 1:
            self.text(xy, words, size=size, face=face, color=color, anchor=anchor)
            return
        font = _font(getattr(self.theme, face), round(size * self.scale))
        left, top, alpha, order = _handwriting(font, words, anchor)
        if not order:
            return
        coverage = Image.new("L", alpha.size)
        ImageDraw.Draw(coverage).point(order[:ceil(len(order)*progress)], fill=255)
        pos = (round(xy[0]*self.scale+left), round(xy[1]*self.scale+top))
        self.draw.bitmap(pos, ImageChops.multiply(alpha, coverage), fill=color or self.theme.ink)

    def brush_fill(self, points, *, progress=1, color=None):
        """Lay successive diagonal strokes inside the painted silhouette."""
        polygon = [(x*self.scale, y*self.scale) for x,y in points]
        color = color or self.theme.wash
        if progress <= 0 or len(polygon) < 3:
            return
        if progress >= 1:
            self.draw.polygon(polygon, fill=color)
            return
        x0 = int(min(x for x,y in polygon))-1
        y0 = int(min(y for x,y in polygon))-1
        w = ceil(max(x for x,y in polygon))-x0+2
        h = ceil(max(y for x,y in polygon))-y0+2
        shape = Image.new("L",(w,h))
        ImageDraw.Draw(shape).polygon([(x-x0,y-y0) for x,y in polygon],fill=255)
        paint = Image.new("L",(w,h))
        brush = ImageDraw.Draw(paint)
        pitch = max(1,round(4*self.scale),round(h/7))
        tilt = round(h*.23)
        rows = ceil((h+tilt)/pitch)+1
        for i in range(rows):
            amount = max(0,min(1,rows*progress-i))
            if amount == 0:
                break
            a,b = (-3, i*pitch), (w+3, i*pitch-tilt)
            if i%2:
                a,b = b,a
            brush.line([a,(a[0]+(b[0]-a[0])*amount,a[1]+(b[1]-a[1])*amount)],
                       fill=255,width=pitch+3)
        self.draw.bitmap((x0,y0),ImageChops.multiply(paint,shape),fill=color)


    def path(self, points, *, progress=1, color=None, width=None, wobble=0.8):
        """Trace a stable, lightly perturbed polyline by fraction of arc length."""
        points = tuple(points)
        lengths = [dist(a, b) for a, b in pairwise(points)]
        remaining = sum(lengths) * min(1, progress)
        ink = []
        for a, b, length in zip(points, points[1:], lengths):
            if remaining <= 0:
                break
            if length == 0:
                continue
            used = min(remaining, length)
            steps = max(1, ceil(length / 6))
            for i in range(ceil(steps * used / length) + 1):
                t = min(i / steps, used / length)
                x, y = (u + (v - u) * t for u, v in zip(a, b))
                phase = x * 0.031 + y * 0.049 + self.seed
                ink.append(
                    (
                        (x + wobble * cos(phase)) * self.scale,
                        (y + wobble * sin(phase * 1.3)) * self.scale,
                    )
                )
            remaining -= used
        if len(ink) >= 2:
            self.draw.line(
                ink,
                fill=color or self.theme.ink,
                joint="curve",
                width=max(1, round((width or self.theme.stroke) * self.scale)),
            )

    def arrow(self, start, end, *, progress=1, color=None):
        angle = atan2(end[1] - start[1], end[0] - start[0])
        self.path([start, end], color=color, progress=min(1, progress / 0.84))
        for delta in (-pi / 6, pi / 6):
            tip = (end[0] - 14 * cos(angle + delta), end[1] - 14 * sin(angle + delta))
            self.path([end, tip], color=color, progress=(progress - 0.84) / 0.16)

    def highlight(self, start, end, *, progress=1, width=14, color=None):
        self.path(
            [start, end], progress=progress, width=width, color=color or self.theme.wash
        )

    def dot(self, xy, *, radius=8, color=None):
        x, y = xy
        bounds = (x - radius, y - radius, x + radius, y + radius)
        self.draw.ellipse(
            tuple(v * self.scale for v in bounds),
            fill=color or self.theme.accent,
            outline=self.theme.paper,
            width=max(1, round(2 * self.scale)),
        )
