"""Timed notebook pages assembled from editable, cached drawing layers."""

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
        page.label(0, (60, 30), self.masthead, 23, "curve", mono=True, duration=0)
        page.label(0, (930, 30), self.edition, 20, "muted", mono=True, duration=0)
        page.layer(0, 0, lambda c: c.path([(60, 76), (630, 75), (1220, 77)], color=self.theme.muted, width=2))
        page.label(0, (64, 106), title, 64)
        return page

    def frame(self, time, width):
        image = Image.new("RGB", (1280, 720), self.theme.paper)
        for start, page in reversed(self.pages):
            if time >= start:
                page.paint(image, time - start)
                break
        return image if width == 1280 else image.resize((width, width * 9 // 16), Image.Resampling.LANCZOS)


class Page:
    def __init__(self, theme):
        self.theme = theme
        self.layers = []

    def layer(self, at, duration, draw):
        image = Image.new("RGBA", (1280, 720))
        draw(Canvas(image, self.theme, 17))
        box = image.getbbox()
        if box:
            self.layers.append((at, duration, box[:2], image.crop(box)))

    def label(self, at, xy, words, size, color="ink", *, mono=False, duration=0.8):
        self.layer(at, duration, lambda c: c.text(
            xy, words, size=size, face="mono" if mono else "sans",
            color=getattr(self.theme, color), anchor="la",
        ))

    def callout(self, at, xy, words, size, polygon):
        def draw(canvas):
            canvas.draw.polygon(polygon, fill=self.theme.wash)
            canvas.text(xy, words, size=size, anchor="la")
        self.layer(at, 1, draw)

    def paint(self, image, time):
        for at, duration, xy, layer in self.layers:
            if time < at:
                continue
            fraction = min(1, (time - at) / duration) if duration else 1
            width = round(layer.width * fraction)
            if width:
                visible = layer if width == layer.width else layer.crop((0, 0, width, layer.height))
                image.paste(visible, xy, visible)
