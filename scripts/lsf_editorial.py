#!/usr/bin/env python3
"""Apply the published editorial choices on top of the vendored LSF layout.

The vendor tree stays unmodified. This script records the rotation, frames
screenshots, and can build a footer sticker from a QR image the user supplies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SKILL_ROOT = Path(__file__).resolve().parents[1]
VENDOR = SKILL_ROOT / "vendor" / "lsf-wechat-editorial-layout"
SELECTION_PATH = SKILL_ROOT / "assets" / "lsf-editorial" / "selection.json"
STATE_PATH = SKILL_ROOT / "runtime" / "lsf-editorial-rotation.json"
AURA_PATH = VENDOR / "assets" / "style-picker" / "backgrounds" / "aura-presets.json"
FOOTER_SIZE = (900, 450)
FOOTER_GIF = SKILL_ROOT / "assets" / "brand" / "chuan-lab-footer.gif"


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def selection() -> dict:
    return read_json(SELECTION_PATH)


def intro_names() -> dict[str, str]:
    names = {item["id"]: item["name"] for item in read_json(VENDOR / "assets/style-picker/catalog.json")["intro"]}
    for item in read_json(VENDOR / "assets/design-how/catalog.json"):
        names[item["number"]] = item["name"]
    return names


def background_entries() -> list[dict]:
    excluded = set(selection()["backgrounds"]["exclude"])
    return [item for item in read_json(VENDOR / "assets/style-picker/catalog.json")["backgrounds"]
            if item["id"] not in excluded]


def load_state(path: Path) -> dict:
    if path.is_file():
        data = read_json(path)
        data.setdefault("order", [])
        data.setdefault("assigned", {})
        return data
    return {"order": [], "assigned": {}}


def article_key(article: Path) -> str:
    return article.resolve().name


def stable_seed(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def take_unique(count: int, pool: list[str], rng: random.Random) -> list[str]:
    if not pool:
        raise ValueError("背景池是空的")
    bag: list[str] = []
    last = None
    chosen = []
    while len(chosen) < count:
        if not bag:
            bag = pool.copy()
            rng.shuffle(bag)
            if last is not None and len(bag) > 1 and bag[0] == last:
                bag.append(bag.pop(0))
        last = bag.pop(0)
        chosen.append(last)
    return chosen


def pick_chapters(mode: str, count: int, seed: int) -> dict:
    script = VENDOR / "scripts" / "pick-chapter-markers.py"
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(script), "--mode", mode, "--chapters", str(count), "--seed", str(seed)],
        check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(completed.stdout)


def copy_chapter_markers(article: Path, picked: dict) -> list[dict]:
    destination = article / "images" / "chapter-markers"
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for chapter in picked["chapters"]:
        assets = chapter.get("assets") or ([chapter["asset"]] if chapter.get("asset") else [])
        files = []
        for asset in assets:
            source = VENDOR / asset
            target = destination / f"{chapter['label']}-{source.name}"
            shutil.copy2(source, target)
            files.append(target.relative_to(article).as_posix())
        copied.append({
            "label": chapter["label"], "style": chapter["style"], "name": chapter["name"], "files": files,
        })
    return copied


def copy_footer(article: Path) -> None:
    source = FOOTER_GIF
    if not source.is_file():
        return
    destination = article / "images" / "chuan-lab-footer.gif"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source, destination)


def assign_article(article: Path, screenshots: list[str], chapters: int = 0, reseed: bool = False,
                   render: bool = True, state_path: Path = STATE_PATH) -> dict:
    article = article.resolve()
    if not article.is_dir():
        raise FileNotFoundError(article)
    chosen = selection()
    names = intro_names()
    missing = [item for item in chosen["intro"]["ids"] if item not in names]
    if missing:
        raise KeyError("署名动效编号没有对应名称: " + ", ".join(missing))
    key = article_key(article)
    state = load_state(state_path)
    if key not in state["assigned"]:
        index = len(state["order"])
        seed = stable_seed(key)
        state["order"].append(key)
        state["assigned"][key] = {
            "intro_id": chosen["intro"]["ids"][index % len(chosen["intro"]["ids"])],
            "chapter_mode": chosen["chapters"]["modes"][index % len(chosen["chapters"]["modes"])],
            "background_seed": seed,
            "chapter_seed": seed,
        }
        write_json(state_path, state)
    slot = state["assigned"][key]
    if reseed:
        seed = random.SystemRandom().randrange(1, 2**63)
        slot["background_seed"] = seed
        slot["chapter_seed"] = seed
        write_json(state_path, state)
    entries = {item["id"]: item for item in background_entries()}
    background_ids = take_unique(len(screenshots), list(entries), random.Random(slot["background_seed"]))
    framed = []
    for path, background_id in zip(screenshots, background_ids):
        source = Path(path)
        if not source.is_absolute():
            source = article / source
        record = {
            "source": Path(path).as_posix() if not Path(path).is_absolute() else source.relative_to(article).as_posix(),
            "id": background_id,
            "name": entries[background_id]["name"],
        }
        if render:
            if not source.is_file():
                raise FileNotFoundError(source)
            target = article / "images" / "backgrounds" / f"{source.stem}-{background_id}.png"
            frame_screenshot(source, background_id, target)
            record["file"] = target.relative_to(article).as_posix()
        framed.append(record)
    mode = slot["chapter_mode"]
    motion = {
        "author": chosen["author"],
        "intro": {"id": slot["intro_id"], "name": names[slot["intro_id"]]},
        "chapters": {
            "mode": mode,
            "name": "动态字母" if mode == "initialis" else "动态数字",
            "seed": slot["chapter_seed"],
        },
        "backgrounds": framed,
        "footer": "images/chuan-lab-footer.gif",
    }
    copy_footer(article)
    if chapters:
        motion["chapters"]["markers"] = copy_chapter_markers(
            article, pick_chapters(mode, chapters, int(slot["chapter_seed"])))
    elif (article / "editorial-motion.json").is_file() and not reseed:
        previous = read_json(article / "editorial-motion.json")
        if previous.get("chapters", {}).get("markers"):
            motion["chapters"]["markers"] = previous["chapters"]["markers"]
    write_json(article / "editorial-motion.json", motion)
    return motion


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def cover_image(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.convert("RGB").resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                                          Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def numpy():
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("Screenshot backgrounds need NumPy. Install numpy, then run this command again.") from error
    return np


def soft_light(base, source, alpha):
    np = numpy()
    blended = np.where(
        source <= 0.5,
        base - (1 - 2 * source) * base * (1 - base),
        base + (2 * source - 1) * (np.where(base <= 0.25, ((16 * base - 12) * base + 4) * base, np.sqrt(base)) - base),
    )
    return blended * alpha + base * (1 - alpha)


def source_over(base, base_alpha, color, alpha):
    np = numpy()
    src_alpha = alpha[..., None]
    dst_alpha = base_alpha[..., None]
    out_alpha = src_alpha + dst_alpha * (1 - src_alpha)
    out = (color * src_alpha + base * dst_alpha * (1 - src_alpha)) / np.maximum(out_alpha, 1e-6)
    return out, out_alpha[..., 0]


def radial_alpha(width: int, height: int, layer: dict):
    np = numpy()
    yy, xx = np.mgrid[0:height, 0:width]
    center_x = width * layer["x"] / 100
    center_y = height * layer["y"] / 100
    radius = max(width, height) * layer["size"] / 100
    distance = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2) / max(radius, 1)
    strength = np.interp(distance, [0, 0.42, 0.78, 1], [1, 0.72, 0.22, 0], left=1, right=0)
    return (layer["opacity"] / 100) * strength


def blur_alpha(alpha, radius: float):
    np = numpy()
    if radius <= 0.5:
        return alpha
    image = Image.fromarray(np.clip(alpha * 255, 0, 255).astype(np.uint8), "L")
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255


def grain_alpha(width: int, height: int, amount: float):
    np = numpy()
    def imul(left: int, right: int) -> int:
        result = (left * right) & 0xFFFFFFFF
        return result - 0x100000000 if result >= 0x80000000 else result

    seed = 1297
    values = np.empty(96 * 96, dtype=np.uint8)
    for index in range(values.size):
        seed = (imul(seed, 1664525) + 1013904223) & 0xFFFFFFFF
        values[index] = 255 if seed >> 31 else 0
    tile = values.reshape(96, 96)
    scale = max(1, round(width / 400))
    if scale > 1:
        tile = np.repeat(np.repeat(tile, scale, axis=0), scale, axis=1)
    repeats = (int(np.ceil(height / tile.shape[0])), int(np.ceil(width / tile.shape[1])))
    tiled = np.tile(tile, repeats)[:height, :width]
    color = tiled.astype(np.float32) / 255
    alpha = np.full((height, width), round(8 + amount * 0.62) / 255, dtype=np.float32)
    return color, alpha


def paint_aura(preset: dict, width: int, height: int) -> Image.Image:
    np = numpy()
    color = np.array(hex_rgb(preset["base"]), dtype=np.float32) / 255
    image = np.empty((height, width, 3), dtype=np.float32)
    image[:] = color
    alpha = np.ones((height, width), dtype=np.float32)
    for layer in preset["layers"]:
        layer_alpha = blur_alpha(radial_alpha(width, height, layer), min(width, height) * layer["blur"] * 0.0016)
        layer_color = np.array(hex_rgb(layer["color"]), dtype=np.float32) / 255
        if layer["blend"] == "soft-light":
            image = soft_light(image, layer_color, layer_alpha[..., None])
        else:
            image, alpha = source_over(image, alpha, layer_color, layer_alpha)
    if preset.get("grain"):
        grain_color, grain_opacity = grain_alpha(width, height, preset["grain"])
        image = soft_light(image, grain_color[..., None], grain_opacity[..., None])
    return Image.fromarray(np.clip(image * 255, 0, 255).astype(np.uint8), "RGB")


def background_canvas(background_id: str, width: int, height: int) -> Image.Image:
    entry = next(item for item in read_json(VENDOR / "assets/style-picker/catalog.json")["backgrounds"]
                 if item["id"] == background_id)
    if "artwork" in entry:
        artwork = Image.open(VENDOR / "assets/style-picker/backgrounds" / entry["artwork"])
        return cover_image(artwork, width, height)
    presets = read_json(AURA_PATH)
    return paint_aura(presets[entry["aura"]], width, height)


def frame_screenshot(source: Path, background_id: str, destination: Path) -> None:
    shot = Image.open(source).convert("RGBA")
    border = min(shot.width, shot.height) * 0.08
    scale = min(1200 / (shot.width + 2 * border), 4096 / (shot.height + 2 * border))
    width = round((shot.width + 2 * border) * scale)
    height = round((shot.height + 2 * border) * scale)
    inset = border * scale
    radius = min(shot.width, shot.height) * scale * 0.03
    outer = min(32, radius + inset / 3)
    canvas = background_canvas(background_id, width, height).convert("RGBA")
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=outer, fill=255)
    framed = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    framed.paste(canvas, mask=mask)
    shot_w = round(shot.width * scale)
    shot_h = round(shot.height * scale)
    box = (round(inset), round(inset), round(inset + shot_w), round(inset + shot_h))
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if background_id == "01":
        color = (255, 184, 107, 170)
        blur = inset * 1.2
        offset = (0, 0)
    else:
        color = (5, 20, 24, 82)
        blur = inset * 0.85
        offset = (0, inset * 0.2)
    ImageDraw.Draw(shadow).rounded_rectangle(
        (box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1]),
        radius=radius, fill=color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(0.5, blur)))
    framed.alpha_composite(shadow)
    plate = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    plate_mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(plate_mask).rounded_rectangle(box, radius=radius, fill=255)
    white = Image.new("RGBA", (shot_w, shot_h), (255, 255, 255, 255))
    white.alpha_composite(shot.resize((shot_w, shot_h), Image.Resampling.LANCZOS))
    plate.paste(white, box[:2])
    framed.paste(plate, mask=plate_mask)
    clipped = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    clipped.paste(framed, mask=mask)
    destination.parent.mkdir(parents=True, exist_ok=True)
    clipped.save(destination, "PNG")


def wordmark_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeuib.ttf", "segoeuisb.ttf", "arialbd.ttf", "arial.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_tracked_line(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
                      y: float, width: int, tracking: float) -> None:
    widths = [font.getlength(character) for character in text]
    x = (width - (sum(widths) + tracking * (len(text) - 1))) / 2
    for character, glyph_width in zip(text, widths):
        draw.text((x, y), character, font=font, fill=(0, 0, 0, 255))
        x += glyph_width + tracking


def wordmark_lines() -> tuple[str, ...]:
    text = str(selection()["footer"].get("center_text") or selection().get("author") or "ChuanLab").strip()
    if " " in text:
        first, rest = text.split(None, 1)
        return (first, rest)
    split = re.fullmatch(r"([A-Z][a-z]+)([A-Z][a-z]+)", text)
    if split:
        return (split.group(1), split.group(2))
    return (text,)


def draw_wordmark(image: Image.Image) -> None:
    lines = wordmark_lines()
    draw = ImageDraw.Draw(image)
    size = 72
    font = wordmark_font(size)
    while size > 28:
        font = wordmark_font(size)
        widest = max(sum(font.getlength(character) for character in line) + size * 0.04 * (len(line) - 1)
                     for line in lines)
        block = size * len(lines) + size * 0.12 * (len(lines) - 1)
        if widest <= image.width * 0.50 and block <= image.height * 0.42:
            break
        size -= 2
    tracking = size * 0.04
    gap = size * 0.12
    ascent = font.getbbox(lines[0])
    line_height = ascent[3] - ascent[1]
    block = line_height * len(lines) + gap * (len(lines) - 1)
    y = (image.height - block) / 2 - ascent[1]
    for line in lines:
        draw_tracked_line(draw, line, font, y, image.width, tracking)
        y += line_height + gap


def footer_destinations() -> list[Path]:
    return [FOOTER_GIF]


def pad_qr(image: Image.Image) -> Image.Image:
    side = max(image.width, image.height)
    tile = Image.new("RGBA", (side + 64, side + 64), (255, 255, 255, 255))
    tile.paste(image, ((tile.width - image.width) // 2, (tile.height - image.height) // 2))
    return tile


def build_footer(qr_path: Path, poster_only: bool = False) -> Path:
    qr = pad_qr(Image.open(qr_path).convert("RGBA"))
    ring = Image.open(VENDOR / "assets/footer-motion/ai-sticker-ring/ai-sticker-ring.gif")
    width, height = FOOTER_SIZE
    ring_size = height - 28
    qr_size = ring_size - 36
    qr_image = qr.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    left = 36
    right = width - qr_size - 48

    def compose(frame: Image.Image) -> Image.Image:
        canvas = Image.new("RGBA", FOOTER_SIZE, (255, 255, 255, 255))
        mark = frame.convert("RGBA").resize((ring_size, ring_size), Image.Resampling.LANCZOS)
        draw_wordmark(mark)
        canvas.alpha_composite(mark, (left, (height - ring_size) // 2))
        canvas.alpha_composite(qr_image, (right, (height - qr_size) // 2))
        return canvas

    ring.seek(0)
    poster = compose(ring).convert("RGB")
    poster_paths = [path.with_suffix(".png") for path in footer_destinations()]
    for path in poster_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        poster.save(path, "PNG")
    if poster_only:
        return poster_paths[0]
    palette = poster.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    frames = []
    durations = []
    for index in range(ring.n_frames):
        ring.seek(index)
        frames.append(compose(ring).convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE))
        durations.append(ring.info.get("duration", 100))
    primary = footer_destinations()[0]
    frames[0].save(primary, save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   disposal=2, optimize=False)
    for path in footer_destinations()[1:]:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(primary, path)
    return primary


def build_preview(output: Path) -> None:
    mimetypes.add_type("image/webp", ".webp")
    author = str(selection().get("author") or "ChuanLab")
    sys.path.insert(0, str(VENDOR / "scripts"))
    sys.argv = ["build-style-preview.py", "--author", author, "--output", str(output)]
    import runpy
    runpy.run_path(str(VENDOR / "scripts" / "build-style-preview.py"), run_name="__main__")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    assign = commands.add_parser("assign")
    assign.add_argument("article", type=Path)
    assign.add_argument("--chapters", type=int, default=0)
    assign.add_argument("--screenshot", action="append", default=[])
    assign.add_argument("--reseed", action="store_true")
    assign.add_argument("--no-render", action="store_true")
    assign.add_argument("--state", type=Path, default=STATE_PATH)
    preview = commands.add_parser("preview")
    preview.add_argument("--output", type=Path, required=True)
    footer = commands.add_parser("footer")
    footer.add_argument("--qr", type=Path, required=True, help="Square QR image supplied by the account owner")
    footer.add_argument("--poster-only", action="store_true")
    shot = commands.add_parser("render-screenshot")
    shot.add_argument("source", type=Path)
    shot.add_argument("background", help="背景编号，例如 02")
    shot.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "assign":
        motion = assign_article(args.article, args.screenshot, args.chapters, args.reseed,
                                not args.no_render, args.state)
        print(json.dumps(motion, ensure_ascii=False, indent=2))
    elif args.command == "preview":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        build_preview(args.output)
        print(args.output)
    elif args.command == "footer":
        print(build_footer(args.qr, args.poster_only))
    else:
        frame_screenshot(args.source, args.background, args.output)
        print(args.output)


if __name__ == "__main__":
    main()
