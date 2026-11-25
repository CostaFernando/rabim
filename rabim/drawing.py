"""Drawing primitives in a 1280 × 720 logical space."""

from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from math import atan2, ceil, cos, dist, pi, sin

from PIL import ImageDraw, ImageFont


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
