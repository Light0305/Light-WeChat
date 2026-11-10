"""Prepare a disposable INITIĀLIS copy with Cinzel numeral outlines."""
import argparse
import json
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("upstream", type=Path, help="Source INITIĀLIS checkout")
parser.add_argument("destination", type=Path, help="New directory for the numeric renderer")
args = parser.parse_args()

base = Path(__file__).resolve().parent
font_path = Path("render/fonts/caps/cinzel-900.json")
caps = json.loads((args.upstream / font_path).read_text(encoding="utf-8"))
digits = json.loads((base / "cinzel-900-digits.json").read_text(encoding="utf-8"))
if caps["upm"] != digits.pop("upm"):
    parser.error("Cinzel outline units do not match; use the documented INITIĀLIS revision")

args.destination.mkdir(parents=True, exist_ok=False)
for name in ("lib", "render", "src"):
    shutil.copytree(args.upstream / name, args.destination / name)
for name in ("LICENSE", "THIRD-PARTY.md"):
    shutil.copy2(args.upstream / name, args.destination / name)
(args.destination / font_path).write_text(json.dumps({**caps, **digits}), encoding="utf-8")
shutil.copy2(base / "Cinzel-OFL.txt", args.destination / "Cinzel-OFL.txt")
print(args.destination.resolve())
