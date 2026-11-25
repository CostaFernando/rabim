"""Timed notebook pages assembled from editable, cached drawing layers."""

from functools import lru_cache

from PIL import Image

from .drawing import Canvas, Theme


class Notebook:
    def __init__(self, *, duration, masthead="", edition="", theme=None):
        self.theme = theme or Theme.notebook()
        self.duration = duration
        self.masthead = masthead
        self.edition = edition
        self.pages = []

    def page(self, at, title):
        if at < 0 or at >= self.duration or (self.pages and at <= self.pages[-1][0]):
            raise ValueError("Page starts must increase and fall within the runtime")
        page = Page(self.theme)
        self.pages.append((at, page))
        has_header = bool(self.masthead or self.edition)
        if has_header:
            page.label(0, (60, 30), self.masthead, 23, "curve", mono=True, duration=0)
            page.label(0, (930, 30), self.edition, 20, "muted", mono=True, duration=0)
            page.layer(0, 0, lambda c: c.path([(60, 76), (630, 75), (1220, 77)], color=self.theme.muted, width=2), native=True)
        page.label(0, (64, 106 if has_header else 65), title, 64)
        return page

    def frame(self, time, width):
        image = Image.new("RGB", (width, width * 9 // 16), self.theme.paper)
        for start, page in reversed(self.pages):
            if time >= start:
                page.paint(image, time - start)
                break
        return image


class Page:
    def __init__(self, theme):
        self.theme = theme
        self.layers = []

    def layer(self, at, duration, draw, *, native=False):
        def rasterize(width):
            image = Image.new("RGBA", (width, width * 9 // 16))
            draw(Canvas(image, self.theme, 17))
            box = image.getbbox()
            return (box[:2], image.crop(box)) if box else None

        if native:
            bitmap = lru_cache(maxsize=1)(rasterize)
        else:
            # Raw Pillow callbacks may use pixel coordinates or mutable authoring state.
            snapshot = rasterize(1280)
            if snapshot is None:
                return
            xy, source = snapshot

            @lru_cache(maxsize=1)
            def bitmap(width):
                if width == 1280:
                    return snapshot
                scale = width / 1280
                position = tuple(round(v * scale) for v in xy)
                size = tuple(max(1, round(v * scale)) for v in source.size)
                return position, source.resize(size, Image.Resampling.LANCZOS)

        self.layers.append((at, duration, bitmap, None))

    def label(self, at, xy, words, size, color="ink", *, mono=False, duration=0.8, reveal="wipe"):
        if reveal == "handwrite":
            def write(canvas, progress):
                canvas.write_text(xy, words, size=size, face="mono" if mono else "sans",
                                  color=getattr(self.theme, color), anchor="la", progress=progress)
            self.layers.append((at, duration, None, write))
            return
        if reveal != "wipe":
            raise ValueError(f"Unknown label reveal: {reveal!r}")
        self.layer(at, duration, lambda c: c.text(
            xy, words, size=size, face="mono" if mono else "sans",
            color=getattr(self.theme, color), anchor="la",
        ), native=True)

    def callout(self, at, xy, words, size, polygon):
        def draw(canvas):
            canvas.brush_fill(polygon, color=self.theme.wash)
            canvas.text(xy, words, size=size, anchor="la")
        self.layer(at, 1, draw, native=True)

    def paint(self, image, time):
        for at, duration, bitmap, write in self.layers:
            if time < at:
                continue
            fraction = min(1, (time - at) / duration) if duration else 1
            if write is not None:
                write(Canvas(image, self.theme, 17), fraction)
                continue
            result = bitmap(image.width)
            if result is None:
                continue
            xy, layer = result
            width = round(layer.width * fraction)
            if width:
                visible = layer if width == layer.width else layer.crop((0, 0, width, layer.height))
                image.paste(visible, xy, visible)
