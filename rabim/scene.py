from dataclasses import dataclass
from math import isfinite

from .drawing import Theme


@dataclass(frozen=True, eq=False)
class Cue:
    words: str


class Scene:
    def __init__(self, title, *, subtitle="", theme=None, seed=17):
        self.title = title
        self.subtitle = subtitle
        self.theme = theme or Theme()
        self.seed = seed
        self.cues = []
        self.layers = []

    def cue(self, words):
        """Append one spoken beat. Its measured audio sets the next cue's start."""
        if not words.strip():
            raise ValueError("A cue needs narration")
        cue = Cue(words)
        self.cues.append(cue)
        return cue

    def reveal(self, draw, *, at=None, duration=None, delay=0, track=None):
        """draw(canvas, progress) is called in insertion order and persists at 1."""
        duration = self.theme.reveal if duration is None else duration
        if at is not None and at not in self.cues:
            raise ValueError("Use a cue from this scene")
        if not all(isfinite(v) and v >= 0 for v in (duration, delay)):
            raise ValueError("Timing must be finite and nonnegative")
        self.layers.append((at, delay, duration, draw, track))

    def curve(self, function, **options):
        from .curve import LabeledCurve

        return LabeledCurve(self, function, **options)
