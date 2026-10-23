#!/usr/bin/env python3
from pathlib import Path
import tomllib

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUT = ROOT / "static" / "og"
FONTS = Path(__file__).resolve().parent / "fonts"
SANS = ImageFont.truetype(FONTS / "inter-latin-500-normal.ttf", 28)
SANS_SMALL = ImageFont.truetype(FONTS / "inter-latin-500-normal.ttf", 22)

WIDTH = 1200
HEIGHT = 630
PAPER = (246, 244, 239)
INK = (26, 27, 38)
MUTED = (92, 92, 92)
MARGIN = 88


def slug_for(path: Path, data: dict) -> str:
    explicit = data.get("slug")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if path.name == "index.md":
        return path.parent.name
    return path.stem


def wrap(text: str, font: ImageFont.FreeTypeFont, limit: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = current + " " + word
        if font.getlength(trial) <= limit:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fitted_title(text: str, limit: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for size in range(72, 34, -2):
        font = ImageFont.truetype(FONTS / "source-serif-4-latin-600-normal.ttf", size)
        lines = wrap(text, font, limit)
        if len(lines) <= 5 and all(font.getlength(line) <= limit for line in lines):
            return font, lines
    font = ImageFont.truetype(FONTS / "source-serif-4-latin-600-normal.ttf", 34)
    return font, wrap(text, font, limit)[:6]


def draw_card(title: str, dest: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 14, HEIGHT), fill=INK)
    draw.text((MARGIN, 78), "Adam Jarvis", font=SANS, fill=MUTED)
    font, lines = fitted_title(title, WIDTH - MARGIN * 2)
    line_height = int(font.size * 1.18)
    block = line_height * len(lines)
    y = (HEIGHT - block) // 2 + 10
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=INK)
        y += line_height
    draw.text((MARGIN, HEIGHT - 92), "jarvis.gg", font=SANS_SMALL, fill=MUTED)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, "PNG")


def pages():
    for path in sorted(CONTENT.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text()
        if not text.startswith("+++"):
            continue
        _, front, _ = text.split("+++", 2)
        data = tomllib.loads(front)
        if data.get("draft") is True:
            continue
        extra = data.get("extra") or {}
        if extra.get("hero"):
            continue
        title = data.get("title") or "Adam Jarvis"
        yield slug_for(path, data), str(title)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    draw_card("Adam Jarvis", OUT / "default.png")
    seen = set()
    for slug, title in pages():
        if slug in seen:
            raise SystemExit(f"duplicate share-image slug: {slug}")
        seen.add(slug)
        draw_card(title, OUT / f"{slug}.png")


if __name__ == "__main__":
    main()
