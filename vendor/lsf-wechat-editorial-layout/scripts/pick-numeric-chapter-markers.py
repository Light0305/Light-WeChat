"""Keep the existing numeric picker command available."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("pick-chapter-markers.py")), run_name="__main__")
