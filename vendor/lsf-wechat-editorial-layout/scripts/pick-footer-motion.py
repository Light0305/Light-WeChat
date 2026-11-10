"""Pick one GIF from the article's shortlisted footer palettes."""

import argparse
import json
import random
from pathlib import Path


library = Path(__file__).resolve().parents[1] / "assets" / "footer-motion" / "planet-rocket"
catalog = json.loads((library / "palette-index.json").read_text(encoding="utf-8"))
palettes = {palette["id"]: palette for palette in catalog}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("ids", nargs="+", choices=palettes, help="palette IDs matched to the article")
args = parser.parse_args()
selected = palettes[random.choice(list(dict.fromkeys(args.ids)))]
gif_path = library / selected["file"]
if not gif_path.is_file():
    parser.error(f"missing GIF: {gif_path}")
print(json.dumps({"id": selected["id"], "name": selected["name"], "path": str(gif_path)}, ensure_ascii=False))
