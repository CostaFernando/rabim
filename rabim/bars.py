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
        def fill(left, right, shade):
            top, bottom = y-height/2, y+height/2
            canvas.brush_fill([(left,top),(right,top),(right,bottom),(left,bottom)],color=shade)
        if track is not None:
            fill(self.left,self.left+self.width,track)
        if value:
            scale = self.width/(self.high-self.low)
            zero = self.left-self.low*scale
            fill(zero+min(0,value)*scale,zero+max(0,value)*scale,color)
