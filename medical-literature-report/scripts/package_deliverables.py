#!/usr/bin/env python3
"""Copy literature-report deliverables into a hash-verified folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CATEGORY_FOLDERS = {
    "articles": "01_articles",
    "presentations": "02_presentations",
    "translations": "03_translations",
    "supplements": "04_supplements",
    "source_notes": "05_source_notes",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    candidate = Path(value)
    if not value or candidate.name != value or value in {".", ".."}:
        raise ValueError(f"Unsafe destination file name: {value!r}")
    return value


def package(manifest: Path, destination: Path, overwrite: bool) -> dict:
    config = json.loads(manifest.read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    results = []

    unknown = sorted(set(config) - set(CATEGORY_FOLDERS))
    if unknown:
        raise ValueError(f"Unknown manifest categories: {', '.join(unknown)}")

    for category, folder_name in CATEGORY_FOLDERS.items():
        items = config.get(category, [])
        if not isinstance(items, list):
            raise TypeError(f"Manifest category {category!r} must be a list")
        if not items:
            continue

        category_path = destination / folder_name
        category_path.mkdir(parents=True, exist_ok=True)
        for item in items:
            if not isinstance(item, dict) or "source" not in item:
                raise ValueError(f"Invalid item in category {category!r}: {item!r}")
            source = Path(item["source"]).expanduser().resolve()
            if not source.is_file():
                raise FileNotFoundError(f"Source file not found: {source}")
            name = safe_name(str(item.get("name") or source.name))
            target = category_path / name
            if target.exists() and not overwrite:
                raise FileExistsError(
                    f"Target already exists: {target}. Use --overwrite to replace it."
                )

            shutil.copy2(source, target)
            source_hash = sha256(source)
            target_hash = sha256(target)
            results.append(
                {
                    "category": category,
                    "source": str(source),
                    "target": str(target.resolve()),
                    "bytes": target.stat().st_size,
                    "sha256": target_hash,
                    "hash_match": source_hash == target_hash,
                }
            )

    report = {
        "destination": str(destination.resolve()),
        "file_count": len(results),
        "all_hashes_match": all(item["hash_match"] for item in results),
        "files": results,
    }
    report_path = destination / "package_inventory.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", help="JSON manifest path")
    parser.add_argument("destination", help="Destination folder")
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace existing destination files"
    )
    args = parser.parse_args()

    report = package(
        Path(args.manifest).expanduser().resolve(),
        Path(args.destination).expanduser().resolve(),
        args.overwrite,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_hashes_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
