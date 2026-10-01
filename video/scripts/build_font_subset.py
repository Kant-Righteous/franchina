"""Subset Noto Sans SC to the characters used by the video.

Usage:
    python scripts/build_font_subset.py path/to/NotoSansSC[wght].ttf

Source font: https://github.com/google/fonts/tree/main/ofl/notosanssc (SIL OFL 1.1).
Requires fonttools and brotli. Re-run after adding new Chinese text.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "fonts" / "NotoSansSC-subset.woff2"

ASCII = "".join(chr(c) for c in range(0x20, 0x7F))
EXTRA = "，。、：；！？（）《》【】“”‘’…—·→←€¥$éèàçôûÉ⇄"


def used_characters() -> str:
    chars = set(ASCII + EXTRA)
    for pattern in ("src/**/*.ts", "src/**/*.tsx", "src/**/*.json"):
        for path in ROOT.glob(pattern):
            chars.update(path.read_text(encoding="utf-8"))
    return "".join(sorted(c for c in chars if c.isprintable()))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    text = used_characters()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    font = subset.load_font(sys.argv[1], options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    subset.save_font(font, str(OUT), options)
    print(f"{len(text)} characters -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
