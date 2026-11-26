"""Bind animation timing to phrases in a recorded narration."""
from math import isfinite


class NarrationCues:
    def __init__(self, alignment):
        characters = alignment["characters"]
        starts = tuple(alignment["character_start_times_seconds"])
        if len(characters) != len(starts) or any(len(c) != 1 for c in characters):
            raise ValueError("Expected one timestamp per character")
        if any(not isfinite(t) or t < 0 for t in starts) or any(a > b for a, b in zip(starts, starts[1:])):
            raise ValueError("Character times must be finite, nonnegative and ordered")
        self._text = "".join(characters)
        self._times = starts
        self._resolved = {}

    def at(self, phrase, *, occurrence=1):
        """Return the onset of the selected exact phrase, in seconds."""
        if not phrase or not isinstance(occurrence, int) or occurrence < 1:
            raise ValueError("Supply a nonempty phrase and a positive occurrence")
        key = (phrase, occurrence)
        if key not in self._resolved:
            start = 0
            for _ in range(occurrence):
                index = self._text.find(phrase, start)
                if index < 0:
                    raise ValueError(f"Narration has no occurrence {occurrence} of {phrase!r}")
                start = index + len(phrase)
            self._resolved[key] = self._times[index]
        return self._resolved[key]

    def progress(self, time, phrase, *, duration=0.8, delay=0, occurrence=1):
        """Smoothstep reveal relative to the selected phrase; zero duration is a cut."""
        if not isfinite(duration) or duration < 0:
            raise ValueError("Reveal duration must be finite and nonnegative")
        elapsed = time - self.at(phrase, occurrence=occurrence) - delay
        if duration == 0:
            return float(elapsed >= 0)
        u = max(0, min(1, elapsed / duration))
        return u * u * (3 - 2 * u)
