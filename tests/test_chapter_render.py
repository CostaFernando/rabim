import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ChapterRender(unittest.TestCase):
    def test_adjacent_ranges_stay_on_the_full_frame_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            episode = folder / "episode.py"
            episode.write_text(
                "from PIL import Image\nfrom rabim.notebook import Notebook\n"
                "class Sample(Notebook):\n"
                "    def frame(self,t,width):\n"
                "        return Image.new('RGB',(width,width*9//16),(round(t*200),0,0))\n"
                "scene=Sample(duration=.61,chapters=[(0,'one'),(.13,'two'),(.46,'three')])\n"
            )
            root = Path(__file__).resolve().parents[1]
            env = dict(os.environ, PYTHONPATH=str(root))
            def render(name, options):
                dest = folder / (name + ".mp4")
                subprocess.run([sys.executable,"-m","rabim",str(episode),"--preview","-o",str(dest),*options],
                               check=True,stdout=subprocess.DEVNULL,env=env)
                return subprocess.check_output(["ffmpeg","-v","error","-i",str(dest),"-vf","scale=1:1",
                                                "-f","rawvideo","-pix_fmt","rgb24","-"])
            full = render("full", [])
            excerpt = render("excerpt", ["--chapter","2:3"])
            # At 12 fps, t=.13 falls between frames 1 and 2.
            self.assertEqual(len(excerpt), len(full)-6)
            self.assertLessEqual(max(abs(a-b) for a,b in zip(excerpt,full[6:])), 3)
