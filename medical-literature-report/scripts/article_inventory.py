#!/usr/bin/env python3
"""Inventory and mechanically verify medical literature-report files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pdf(path: Path) -> dict:
    result = {"valid_pdf_header": path.read_bytes()[:5] == b"%PDF-"}
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        result["pages"] = len(reader.pages)
        result["encrypted"] = bool(reader.is_encrypted)
        metadata = reader.metadata or {}
        result["pdf_title"] = str(metadata.get("/Title") or "")
    except ImportError:
        result["pdf_note"] = "Install pypdf for page count and metadata checks."
    except Exception as exc:  # Continue so other files are still inventoried.
        result["pdf_error"] = str(exc)
    return result


def inspect_office(path: Path) -> dict:
    result = {"valid_zip": False}
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            result["valid_zip"] = bad_member is None
            result["bad_member"] = bad_member
            if path.suffix.lower() == ".pptx":
                slide_pattern = re.compile(r"^ppt/slides/slide\d+\.xml$")
                result["slides"] = sum(
                    1 for name in archive.namelist() if slide_pattern.match(name)
                )
                media = [
                    item
                    for item in archive.infolist()
                    if item.filename.startswith("ppt/media/") and not item.is_dir()
                ]
                result["media_files"] = len(media)
                result["zero_byte_media"] = sum(
                    1 for item in media if item.file_size == 0
                )
    except Exception as exc:
        result["zip_error"] = str(exc)
    return result


def inspect(path: Path) -> dict:
    item = {"path": str(path.resolve()), "exists": path.is_file()}
    if not item["exists"]:
        return item

    item.update({"bytes": path.stat().st_size, "sha256": sha256(path)})
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        item.update(inspect_pdf(path))
    elif suffix in {".pptx", ".docx", ".xlsx"}:
        item.update(inspect_office(path))
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Files to inventory")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    report = {"files": [inspect(Path(value)) for value in args.paths]}
    report["all_exist"] = all(item["exists"] for item in report["files"])
    report["all_nonempty"] = all(
        item.get("bytes", 0) > 0 for item in report["files"]
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report["all_exist"] and report["all_nonempty"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
