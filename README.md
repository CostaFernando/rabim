# Rabim

Rabim is a Python library for composing hand-drawn videos from reusable drawing primitives, timed pages, and narrated scenes. Install it once, then render scripts from a separate video project. The script supplies the content, visual theme, and optional soundtrack. The CLI writes renders and speech caches relative to the working directory.

## Preview and render

Use Python 3.10+, Pillow, and FFmpeg. Notebook handwriting uses the bundled Caveat SemiBold font. The other default font paths and optional speech synthesis currently target macOS. Install from a local checkout with `python -m pip install -e /path/to/rabim`.

From your video project, save the following as `example.py`:

```python
from rabim.notebook import Notebook

scene = Notebook(duration=4)
page = scene.page(0, "How far is a kilometer?")
page.label(1, (100, 310), "1 kilometer = 1,000 meters", 52, reveal="handwrite", duration=1.4)
```

```sh
python -m rabim example.py --quality draft
python -m rabim example.py --quality production -o renders/distance.mp4
```

| Render profile | Output | H.264 encoding | Default file |
| --- | --- | --- | --- |
| `draft` (also `--preview`) | 640 × 360, 12 fps | veryfast, CRF 23 | `renders/example-preview.mp4` |
| `standard` (default) | 1280 × 720, 24 fps | fast, CRF 17 | `renders/example.mp4` |
| `production` | 1920 × 1080, 24 fps | fast, CRF 15 | `renders/example-1080p.mp4` |

Switch profiles on the same episode and soundtrack. All profiles keep cue times in seconds and produce a fast-start MP4. Notebook labels, handwriting and callouts draw at the output resolution. For a resolution-independent custom layer, use `page.layer(at, duration, draw, native=True)` and draw with Canvas primitives. The callback runs on demand when the render width changes, so capture loop values when defining it. Existing custom layers keep their 720p snapshot behavior. Raw Pillow coordinates inside native callbacks are in output pixels. A custom `Notebook.frame(time, width)` implementation owns its rasterization and must return an RGB image of the requested size.

## Create a timed notebook

Use `Notebook.page` for a fresh board, `page.label` for handwriting or monospace values, `page.callout` for a highlighted takeaway, and `page.layer` for a custom illustration drawn with the existing Canvas primitives. Layer times are relative to their page. Notebook pages use their own masthead, paper, and typography.

```sh
python -m rabim example.py --audio path/to/finished-soundtrack.m4a
```

A notebook renders silently by default. Supply a local audio file or a video containing the finished mix to use its audio stream. Use `Theme.notebook(accent="#913c25")` to customize the palette while keeping the notebook handwriting. Override `sans` or `mono` to choose another font.

## Choose a component

| To draw | Public API |
| --- | --- |
| A function with labeled axes, ticks and a formula | `scene.curve(fn, x=Axis(label, low, high, ticks), y=Axis(...), formula="…", at=cue)` |
| A point on that function with live numeric labels | `curve.point(x_value, at=cue)`. The first call places it. Subsequent calls animate from the previous value. |
| A custom visual | `scene.reveal(draw, at=cue)`. Compose the canvas primitives below inside `draw(canvas, progress)`. |

Choose a finite, continuous function on the displayed domain and a y range containing it. Omit ticks for endpoint and midpoint labels. Give point targets in chronological order, with room for each move to finish. Override a move with `duration=0.8` or the curve ink with `color="#31599a"`.

## Compose a custom reveal

```python
from rabim import Scene

scene = Scene("A directed edge", subtitle="Which way does the signal travel?")
beat = scene.cue("Follow the arrow from the input to the output.")

def connection(c, progress):
    c.text((260, 370), "Input")
    c.arrow((345, 370), (610, 370), progress=progress)
    c.text((640, 370), "Output")

scene.reveal(connection, at=beat)
```

Use `--voice Daniel` to select a macOS speech voice. Each `cue(words)` appends a spoken line. Bind several reveals to the same cue to start them together. A reveal can take `delay` and `duration` in seconds. Its progress runs from 0 to 1 and the completed drawing stays visible. Omit `at` to start at time zero.

Canvas coordinates use a 1280 × 720 page with the origin at the top left. The title and subtitle occupy the top 190 units. Draw layers in reading order.

- `text((x,y), words, size=26, face="sans", color=...)` anchors at left center by default. Faces include sans, serif and mono.
- `write_text((x,y), words, progress=p, size=26)` traces a line of text with the same font, color, and anchor options as `text`. On a notebook page, choose `page.label(..., reveal="handwrite", duration=1.4)`. The default label reveal is a horizontal wipe. Handwritten text uses the selected font’s glyphs when available. Missing `→`, `Σ`, and `⁻` are drawn as pen strokes.
- `canvas.text_width(words, size=26, face="sans")` measures the same advances in logical canvas coordinates. Use it to fit an equation or position a second phrase immediately after the first.
- `brush_fill(points, progress=p, color=...)` paints inside a polygon with alternating diagonal brushstrokes. For an outline, trace its closed perimeter with `path`.
- `path(points, progress=p, width=3, color=...)` reveals a fraction of the stroke length.
- `arrow(start, end, progress=p)`, `highlight(start, end, progress=p)` and `dot(xy, radius=8)` share the scene palette.

Set scene-wide defaults with `Scene(..., theme=Theme(accent="#913c25"), seed=9)`. The seed holds stroke variation steady across frames. Watch a preview through each cue before making the full render.

## Timed diagrams and chapter renders

Use `NarrationCues(alignment)` with recorded character timestamps. Resolve required cues at setup with `cues.at("look lower")`. Select a repeated phrase with `occurrence=2`. In a frame callback, `cues.progress(time, "look lower", duration=1.2)` returns a smooth reveal at the recorded onset.

`Grid(x, y, width, height, rows, columns)` uses zero-based row and column addresses. Paint a cell-sized RGB image with `grid.paint(canvas, image)`, draw a selection with `grid.highlight(canvas, row, col, color=ink)`, or use `grid.center(row, col)` to attach a connector. Bounds and centers use logical canvas coordinates.

Use `ValueBars(left=400, width=240, low=-2, high=4)` as a shared scale. Call `bars.bar(canvas, y, value, height=14, color=ink)` for each labeled row. All bars grow from the same zero baseline.

Notebook pages can be rendered independently. For a custom frame implementation, supply `chapters=[(0, "Opening"), (12.4, "Calculation")]` to the Notebook constructor. Select one chapter with `--chapter 2` or a consecutive range with `--chapter 2:4`. Frame times stay on the full episode clock. An optional full-length soundtrack is trimmed to the same interval.
