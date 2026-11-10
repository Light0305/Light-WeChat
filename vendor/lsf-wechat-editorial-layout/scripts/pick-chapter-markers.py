"""Pick chapter markers without repeating styles until the pool is exhausted."""
import argparse
import json
import random
import secrets
from pathlib import Path


def letter_label(number):
    label = ""
    while number:
        number, index = divmod(number - 1, 26)
        label = chr(ord("A") + index) + label
    return label


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--mode", choices=("initialis", "numbers"), default="numbers")
parser.add_argument("--chapters", required=True, type=int, choices=range(1, 1000), metavar="1–999")
parser.add_argument("--seed", type=int, help="Reuse the seed to repeat a previous selection")
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
folder = root / "assets/chapter-markers" / args.mode
styles = json.loads((folder / "styles.json").read_text(encoding="utf-8"))
names = {style: json.loads((folder / style / "preset.json").read_text(encoding="utf-8"))["name"] for style in styles}
seed = args.seed if args.seed is not None else secrets.randbits(64)
randomizer = random.Random(seed)
letters = args.mode == "initialis"
available = []
previous = None
chapters = []
for number in range(1, args.chapters + 1):
    if not available:
        available = styles.copy()
    candidates = [style for style in available if style != previous] or available
    style = randomizer.choice(candidates)
    available.remove(style)
    label = letter_label(number) if letters else str(number)
    symbols = list(label) if letters else [label]
    paths = [folder / style / f"{symbol}.gif" for symbol in symbols]
    assets = [path.relative_to(root).as_posix() for path in paths if path.is_file()]
    chapter = {
        "label": label,
        "style": style,
        "name": names[style],
        "asset": assets[0] if len(symbols) == len(assets) == 1 else None,
    }
    if letters:
        if len(assets) != len(symbols):
            parser.error(f"Missing letter GIFs for {label} in style {names[style]}")
        chapter["assets"] = assets
    chapters.append(chapter)
    previous = style
print(json.dumps({"seed": seed, "chapters": chapters}, ensure_ascii=False, indent=2))
