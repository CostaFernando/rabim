"""A sampled function, its axis labels, and a cue-driven numerical probe."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Axis:
    label: str
    low: float
    high: float
    ticks: tuple = ()

    def __post_init__(self):
        if not self.low < self.high or not all(map(isfinite, (self.low, self.high))):
            raise ValueError("Axis limits must be finite and increasing")

    def marks(self):
        return self.ticks or (self.low, (self.low + self.high) / 2, self.high)


class LabeledCurve:
    def __init__(self, scene, function, *, x, y, formula, at=None, color=None):
        self.scene, self.function = scene, function
        self.x, self.y = x, y
        self.color = color or scene.theme.curve
        self.last = None
        left, top, right, bottom = 115, 262, 773, 565

        def position(value):
            return (
                left + (right - left) * (value - x.low) / (x.high - x.low),
                bottom - (bottom - top) * (function(value) - y.low) / (y.high - y.low),
            )

        self.position = position
        samples = [position(x.low + (x.high - x.low) * i / 320) for i in range(321)]
        if any(
            not isfinite(b) or not top - 1e-6 <= b <= bottom + 1e-6 for a, b in samples
        ):
            raise ValueError(
                "Choose y limits containing the function over the entire x axis"
            )

        def plot(c, p):
            t = c.theme
            c.text((left, top - 43), y.label, size=22, color=t.muted)
            for v in y.marks():
                py = bottom - (bottom - top) * (v - y.low) / (y.high - y.low)
                c.path([(left, py), (right, py)], width=1, color=t.grid)
                c.text((left - 15, py), f"{v:g}", size=18, face="mono", anchor="rm")
            for v in x.marks():
                px = left + (right - left) * (v - x.low) / (x.high - x.low)
                c.path([(px, bottom), (px, bottom + 6)], width=2)
                c.text((px, bottom + 24), f"{v:g}", size=18, face="mono", anchor="mm")
            c.path([(left, top), (left, bottom), (right, bottom)], width=2)
            c.text(
                ((left + right) / 2, bottom + 65),
                x.label,
                size=22,
                anchor="mm",
                color=t.muted,
            )
            c.path(samples, progress=p, color=self.color, width=4.5)
            c.path([(832, 215), (832, 635)], color=t.grid, width=1)
            c.text((885, 246), "FUNCTION", size=17, face="mono", color=t.muted)
            c.text((885, 308), formula, size=36, face="serif")

        scene.reveal(plot, at=at)

    def point(self, value, *, at, duration=None):
        if not self.x.low <= value <= self.x.high:
            raise ValueError("Point outside the x axis")
        start = self.last

        def probe(c, p):
            smooth = p * p * (3 - 2 * p)
            current = value if start is None else start + (value - start) * smooth
            px, py = self.position(current)
            c.path([(px, 565), (px, py), (115, py)], color=c.theme.accent, width=1)
            c.dot((px, py), radius=9)
            for row, (label, number) in enumerate(
                ((self.x.label, current), (self.y.label, self.function(current)))
            ):
                y = 414 + row * 100
                c.text((885, y), label, size=22, color=c.theme.muted)
                c.text(
                    (885, y + 41),
                    f"{number:.2f}",
                    size=39,
                    face="mono",
                    color=c.theme.accent,
                )

        self.scene.reveal(
            probe,
            at=at,
            duration=self.scene.theme.motion if duration is None else duration,
            track=self,
        )
        self.last = value
