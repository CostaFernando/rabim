"""Bars on a fixed linear scale sharing an explicit zero baseline."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ValueBars:
    left: float
    width: float
    low: float
    high: float

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.left,self.width,self.low,self.high)):
            raise ValueError("Bar geometry and domain must be finite")
        if self.width <= 0 or not self.low <= 0 <= self.high or self.low == self.high:
            raise ValueError("Use a positive width and a nonempty domain containing zero")

    def bar(self, canvas, y, value, *, height, color, track=None):
        if not isfinite(value) or not self.low <= value <= self.high or height <= 0:
            raise ValueError("Bar value outside domain or invalid height")
        top = y - height / 2
        if track is not None:
            canvas.fill_rect(self.left, top, self.width, height, color=track)
        if value:
            scale = self.width / (self.high - self.low)
            zero = self.left - self.low * scale
            canvas.fill_rect(zero + min(0, value) * scale, top,
                             abs(value) * scale, height, color=color)
