# Rabim

Rabim is a Python library for composing hand-drawn videos from reusable drawing primitives, timed pages, and narrated scenes. Install it once, then render scripts from a separate video project. The script supplies the content, visual theme, and optional soundtrack. The CLI writes renders and speech caches relative to the working directory.

## Preview and render

Use Python 3.10+, Pillow, and FFmpeg. Notebook handwriting uses the bundled Caveat SemiBold font. The other default font paths and optional speech synthesis currently target macOS. Install from a local checkout with `python -m pip install -e /path/to/rabim`.

From your video project, save the following as `example.py`:

```python
from rabim.notebook import Notebook

scene = Notebook(duration=4)
page = scene.page(0, "How far is a kilometer?")
page.label(1, (100, 310), "1 kilometer = 1,000 meters", 52, mono=True)
```

```sh
python -m rabim example.py --preview
python -m rabim example.py -o renders/distance.mp4
```

Full renders use 1280 × 720 at 24 fps. Preview uses 640 × 360 at 12 fps.

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
- `path(points, progress=p, width=3, color=...)` reveals a fraction of the stroke length.
- `arrow(start, end, progress=p)`, `highlight(start, end, progress=p)` and `dot(xy, radius=8)` share the scene palette.

Set scene-wide defaults with `Scene(..., theme=Theme(accent="#913c25"), seed=9)`. The seed holds stroke variation steady across frames. Watch a preview through each cue before making the full render.
