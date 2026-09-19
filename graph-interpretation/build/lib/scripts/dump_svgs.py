"""Dump all 8 sample SVGs to stdout, prefixed by a marker so we can grab them."""
from pathlib import Path
import sys

DIR = Path(__file__).parent
FILES = [
    "sample_km.svg",
    "sample_forest.svg",
    "sample_roc.svg",
    "sample_box.svg",
    "sample_scatter.svg",
    "sample_bar.svg",
    "sample_heatmap.svg",
    "sample_volcano.svg",
]

target_name = sys.argv[1] if len(sys.argv) > 1 else None
for name in FILES:
    if target_name and name != target_name:
        continue
    content = (DIR / name).read_text(encoding="utf-8")
    print(f"<<<{name}>>>")
    print(content)
    print(f"<<</{name}>>>")
