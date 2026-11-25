import argparse
import hashlib
import math
import runpy
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from . import Canvas, Scene
from .notebook import Notebook


@dataclass(frozen=True)
class RenderProfile:
    width: int
    fps: int
    preset: str
    crf: int
    suffix: str


PROFILES = {
    "draft": RenderProfile(640, 12, "veryfast", 23, "-preview.mp4"),
    "standard": RenderProfile(1280, 24, "fast", 17, ".mp4"),
    "production": RenderProfile(1920, 24, "fast", 15, "-1080p.mp4"),
}


def narration(scene, folder, voice):
    cache = Path(".rabim/audio")
    cache.mkdir(parents=True, exist_ok=True)
    starts = {None: 0}
    rate = 22050
    audio = folder / "speech.wav"
    with wave.open(str(audio), "wb") as track:
        track.setparams((1, 2, rate, 0, "NONE", ""))
        for cue in scene.cues:
            key = hashlib.sha256(
                repr((cue.words, voice, 155, rate)).encode()
            ).hexdigest()
            clip = cache / (key + ".pcm")
            if not clip.exists():
                speech = folder / "voice.aiff"
                subprocess.run(
                    [
                        "say",
                        "-v",
                        voice,
                        "-r",
                        "155",
                        "-o",
                        str(speech),
                        "--",
                        cue.words,
                    ],
                    check=True,
                )
                pcm = subprocess.check_output(
                    [
                        "ffmpeg",
                        "-loglevel",
                        "error",
                        "-i",
                        str(speech),
                        "-ac",
                        "1",
                        "-ar",
                        str(rate),
                        "-f",
                        "s16le",
                        "-",
                    ]
                )
                if not pcm:
                    raise RuntimeError(
                        "macOS say returned empty audio. Check voice access."
                    )
                with tempfile.NamedTemporaryFile(dir=cache, delete=False) as out:
                    out.write(pcm)
                Path(out.name).replace(clip)
            starts[cue] = track.tell() / rate
            track.writeframes(clip.read_bytes())
            track.writeframes(bytes(2 * round(0.28 * rate)))
        end = max(
            (
                starts[at] + delay + duration
                for at, delay, duration, _, _ in scene.layers
            ),
            default=0,
        )
        hold = max(0, end - track.tell() / rate) + 0.75
        track.writeframes(bytes(2 * math.ceil(hold * rate)))
        seconds = track.tell() / rate
    return audio, starts, seconds


def frame(scene, starts, time, width):
    image = Image.new("RGB", (width, width * 9 // 16), scene.theme.paper)
    c = Canvas(image, scene.theme, scene.seed)
    c.text((72, 77), scene.title, size=68, face="serif")
    c.text((75, 149), scene.subtitle, size=27, color=c.theme.muted)
    c.path([(74, 187), (1206, 187)], width=1, color=c.theme.grid)
    c.highlight((75, 187), (159, 187), width=4, color=c.theme.accent)
    active = {}
    for i, (cue, delay, duration, draw, track) in enumerate(scene.layers):
        elapsed = time - starts[cue] - delay
        if elapsed >= 0:
            active[("layer", i) if track is None else ("track", track)] = (
                draw,
                min(1, elapsed / duration) if duration else 1,
            )
    for draw, p in active.values():
        draw(c, p)
    return image


def main():
    parser = argparse.ArgumentParser(description="Render a Rabim Python episode")
    parser.add_argument("episode", type=Path)
    quality = parser.add_mutually_exclusive_group()
    quality.add_argument("--quality", choices=PROFILES, default="standard")
    quality.add_argument("--preview", dest="quality", action="store_const", const="draft",
                         help="alias for --quality draft")
    parser.add_argument("--voice", default="Samantha")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--audio", type=Path, help="Optional finished soundtrack for a timed notebook")
    args = parser.parse_args()
    scene = runpy.run_path(str(args.episode))["scene"]
    if not isinstance(scene, (Notebook, Scene)):
        parser.error("episode must export a Rabim Scene named scene")
    if args.audio and not isinstance(scene, Notebook):
        parser.error("--audio needs a timed notebook episode")
    profile = PROFILES[args.quality]
    width, fps = profile.width, profile.fps
    output = args.output or Path("renders") / (args.episode.stem + profile.suffix)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        folder = Path(tmp)
        if isinstance(scene, Notebook):
            audio, seconds = args.audio, scene.duration
        else:
            audio, starts, seconds = narration(scene, folder, args.voice)
        video = folder / "encoded.mp4"
        command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{width * 9 // 16}",
            "-r",
            str(fps),
            "-i",
            "-",
            *(["-i", str(audio)] if audio else []),
            "-map", "0:v:0",
            *(["-map", "1:a:0", "-af", "apad", "-shortest"] if audio else []),
            "-c:v",
            "libx264",
            "-preset",
            profile.preset,
            "-crf",
            str(profile.crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(video),
        ]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            for i in range(math.ceil(seconds * fps)):
                if isinstance(scene, Notebook):
                    img = scene.frame(i / fps, width)
                    if img.size != (width, width * 9 // 16) or img.mode != "RGB":
                        raise ValueError(f"Notebook.frame must return an RGB image at {width} × {width * 9 // 16}")
                    encoder.stdin.write(img.tobytes())
                    continue
                img = frame(scene, starts, i / fps, width * 2)
                encoder.stdin.write(
                    img.resize(
                        (width, width * 9 // 16), Image.Resampling.LANCZOS
                    ).tobytes()
                )
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("FFmpeg encoding failed")
        video.replace(output)
    print(output)


if __name__ == "__main__":
    main()
