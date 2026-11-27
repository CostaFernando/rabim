import unittest

from PIL import Image
from rabim import Canvas, Grid, NarrationCues, Theme, ValueBars


class TimedDiagrams(unittest.TestCase):
    def test_occurrences_and_reveal(self):
        text = "tap, tap"
        cues = NarrationCues({"characters": list(text), "character_start_times_seconds": list(range(len(text)))})
        self.assertEqual(cues.at("tap", occurrence=2), 5)
        self.assertEqual(cues.progress(6, "tap", duration=2, occurrence=2), .5)
        with self.assertRaises(ValueError):
            cues.at("tap", occurrence=3)

    def test_rectangular_grid_on_scaled_canvas(self):
        cells = Image.new("RGB",(3,2))
        cells.putpixel((2,1),(42,120,95))
        for width in (640,1920):
            im = Image.new("RGB",(width,width*9//16))
            c = Canvas(im,Theme.notebook(),0)
            g = Grid(17,21,109,51,2,3)
            g.paint(c,cells)
            xy = tuple(round(v*c.scale) for v in g.center(1,2))
            self.assertEqual(im.getpixel(xy),(42,120,95))
            with self.assertRaises(IndexError):
                g.center(-1,0)

    def test_rectangle_matches_polygon_brush_at_each_scale(self):
        for width in (640, 1920):
            for progress in (0, .45, 1):
                image = Image.new("RGB", (width, width * 9 // 16), "white")
                expected = image.copy()
                theme = Theme.notebook()
                canvas = Canvas(image, theme, 1)
                canvas.fill_rect(23, 14, 102, 31, progress=progress, color="red")
                Canvas(expected, theme, 1).brush_fill(
                    [(23, 14), (125, 14), (125, 45), (23, 45)],
                    progress=progress, color="red")
                canvas.fill_rect(15, 10, 0, 20, color="blue")
                canvas.fill_rect(15, 10, 20, 0, color="blue")
                self.assertEqual(image.tobytes(), expected.tobytes())
                with self.assertRaises(ValueError):
                    canvas.fill_rect(15, 10, -1, 20)

    def test_signed_bars_share_zero(self):
        im = Image.new("RGB",(1280,720),"white")
        canvas = Canvas(im,Theme.notebook(),0)
        bars = ValueBars(100,300,-1,2)
        bars.bar(canvas,50,-1,height=10,color="red")
        bars.bar(canvas,80,2,height=10,color="green")
        bars.bar(canvas,110,0,height=10,color="red")
        self.assertEqual(im.getpixel((150,50)),(255,0,0))
        self.assertEqual(im.getpixel((250,50)),(255,255,255))
        self.assertEqual(im.getpixel((350,80)),(0,128,0))
        self.assertEqual(im.getpixel((200,110)),(255,255,255))
