#!/usr/bin/env python
"""Extract text from a text-based PDF into a compact Markdown file.

The script tries PyMuPDF, pypdf, then pdfplumber. It does not perform OCR.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SECTION_RE = re.compile(
    r"^\s*(abstract|summary|introduction|background|methods?|materials and methods|"
    r"results?|discussion|conclusion|conclusions|figures?|tables?|supplementary)\s*$",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if SECTION_RE.match(stripped):
            lines.append(f"\n## {stripped.title()}\n")
        else:
            lines.append(stripped)
    return "\n".join(lines).strip()


def extract_with_pymupdf(path: Path, max_pages: int | None) -> list[str]:
    import fitz  # type: ignore

    pages: list[str] = []
    with fitz.open(path) as doc:
        limit = min(len(doc), max_pages) if max_pages else len(doc)
        for idx in range(limit):
            pages.append(doc[idx].get_text("text") or "")
    return pages


def extract_with_pypdf(path: Path, max_pages: int | None) -> list[str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    limit = min(len(reader.pages), max_pages) if max_pages else len(reader.pages)
    return [(reader.pages[idx].extract_text() or "") for idx in range(limit)]


def extract_with_pdfplumber(path: Path, max_pages: int | None) -> list[str]:
    import pdfplumber  # type: ignore

    pages: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        limit = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)
        for idx in range(limit):
            pages.append(pdf.pages[idx].extract_text() or "")
    return pages


def extract_pages(path: Path, max_pages: int | None) -> tuple[str, list[str]]:
    extractors = [
        ("pymupdf", extract_with_pymupdf),
        ("pypdf", extract_with_pypdf),
        ("pdfplumber", extract_with_pdfplumber),
    ]
    errors = []
    for name, extractor in extractors:
        try:
            pages = extractor(path, max_pages)
            if any(page.strip() for page in pages):
                return name, pages
            errors.append(f"{name}: no text extracted")
        except Exception as exc:  # pragma: no cover - runtime dependency fallback
            errors.append(f"{name}: {exc}")
    raise RuntimeError("Unable to extract text. " + " | ".join(errors))


def build_markdown(path: Path, engine: str, pages: list[str]) -> str:
    parts = [
        f"# Extracted PDF Text: {path.stem}",
        "",
        f"- Source file: `{path}`",
        f"- Extraction engine: `{engine}`",
        f"- Pages extracted: {len(pages)}",
        "",
    ]
    for idx, page in enumerate(pages, start=1):
        text = clean_text(page)
        if text:
            parts.extend([f"## Page {idx}", "", text, ""])
    return "\n".join(parts).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Path to a text-based PDF article")
    parser.add_argument("--out", type=Path, help="Output Markdown path")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page limit")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    out = args.out or args.pdf.with_suffix(".extracted.md")
    engine, pages = extract_pages(args.pdf, args.max_pages)
    markdown = build_markdown(args.pdf, engine, pages)
    out.write_text(markdown, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
