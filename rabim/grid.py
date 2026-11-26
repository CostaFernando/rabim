"""Address cells in the same logical coordinates as Canvas."""
from dataclasses import dataclass
from math import isfinite
from operator import index
from PIL import Image


@dataclass(frozen=True)
class Grid:
    x: float
    y: float
    width: float
    height: float
    rows: int
    columns: int

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.x, self.y, self.width, self.height)):
            raise ValueError("Grid coordinates must be finite")
        if min(self.width, self.height) <= 0:
            raise ValueError("Grid extent must be positive")
        if any(not isinstance(n, int) or n <= 0 for n in (self.rows, self.columns)):
            raise ValueError("Grid dimensions must be positive integers")

    def bounds(self, row, col):
        row, col = index(row), index(col)
        if not (0 <= row < self.rows and 0 <= col < self.columns):
            raise IndexError((row, col))
        w, h = self.width / self.columns, self.height / self.rows
        return self.x + col*w, self.y + row*h, self.x + (col+1)*w, self.y + (row+1)*h

    def center(self, row, col):
        left, top, right, bottom = self.bounds(row, col)
        return (left+right)/2, (top+bottom)/2

    def highlight(self, canvas, row, col, *, color, padding=0, width=3, progress=1):
        l, t, r, b = self.bounds(row, col)
        l, t, r, b = l-padding, t-padding, r+padding, b+padding
        canvas.path([(l,t),(r,t),(r,b),(l,b),(l,t)], color=color, width=width, progress=progress)

    def paint(self, canvas, cells):
        """Draw an RGB raster with one source pixel per cell."""
        if cells.size != (self.columns, self.rows) or cells.mode != "RGB":
            raise ValueError("Supply an RGB image matching the grid dimensions")
        scale = canvas.scale
        left, top = round(self.x*scale), round(self.y*scale)
        w = round((self.x+self.width)*scale) - left
        h = round((self.y+self.height)*scale) - top
        if w and h:
            canvas.image.paste(cells.resize((w,h), Image.Resampling.NEAREST), (left,top))
