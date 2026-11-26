# Using Rabim

Start with the runnable notebook in [Preview and render](README.md#preview-and-render). Install Rabim in the Python environment that runs the episode and make sure FFmpeg is on PATH. Keep the episode script and its assets in the video project. Run the CLI from that directory. The script must expose a module-level variable named `scene`.

## Choose an authoring workflow

- For an existing voiceover or finished mix, use a [timed notebook](README.md#create-a-timed-notebook) and pass the mix with `--audio`. Page start times use episode seconds. Labels and layers use seconds relative to their page. Subtract the page start when placing a cue taken from a full-episode alignment.
- For a script that generates its own narration using macOS speech, use [Scene and spoken cues](README.md#compose-a-custom-reveal).
- For recorded phrase timing, grid cells, and signed bars, use the [timed diagram primitives](README.md#timed-diagrams-and-chapter-renders). The [diagram tests](tests/test_timed_diagrams.py) show the alignment input and coordinate conventions. Phrase occurrences start at one and grid indices start at zero.

## Check the render

Run `python -m rabim episode.py --quality draft` while iterating. For a local change, add `--chapter 2` or an inclusive range such as `--chapter 2:4`. Inspect the reveal against the spoken phrase and check labels and connectors at the intended viewing size. Use `--quality production` for final output and supply the same soundtrack used for the preview.

## Change the package

Keep lesson-specific text, data and layouts in the episode script. Put reusable drawing or timing behavior in Rabim and document public API changes in the README. From the checkout run `python -m unittest discover -s tests -v`. The chapter test renders and decodes a short MP4 with FFmpeg to check frame timing.
