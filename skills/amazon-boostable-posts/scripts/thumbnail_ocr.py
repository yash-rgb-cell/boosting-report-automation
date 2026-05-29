#!/usr/bin/env python3
"""
thumbnail_ocr.py — Layer 5 helper. Downloads each thumbnail URL and OCRs it,
then matches the OCR text against the known-title list.

Requires:
  pip install pytesseract pillow requests
  System: tesseract-ocr (apt-get install tesseract-ocr)

Usage:
    python thumbnail_ocr.py \\
        --thumbnails thumbnails.csv \\          # columns: post_url, thumbnail_url
        --known-titles known_titles.txt \\      # one title per line
        --output ocr_suggestions.csv

Output CSV: post_url, suggested_tag, ocr_text
Only rows where OCR found a known-title substring are emitted.

Honest caveats:
- OCR works best on still images with bold on-screen text (Reels covers, TikTok
  end frames). Live photos and motion-blurred frames are unreliable.
- Some thumbnail URLs require auth or expire. Failures are logged and skipped.
- We do a case-insensitive substring match, then prefer the longest match if
  multiple known titles substring-match (e.g. "Mr. and Mrs. Smith" beats "Smith").
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--thumbnails", required=True, help="CSV with columns: post_url, thumbnail_url")
    p.add_argument("--known-titles", required=True, help="Text file, one title per line")
    p.add_argument("--output", required=True, help="Where to write OCR suggestions CSV")
    p.add_argument("--timeout", type=float, default=10.0)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        import requests
        from PIL import Image
        import pytesseract
    except ImportError as e:
        sys.exit(
            f"Missing dependency: {e}\n"
            "Install with: pip install pytesseract pillow requests\n"
            "Plus system tesseract-ocr."
        )

    known = [t.strip() for t in Path(args.known_titles).read_text(encoding="utf-8").splitlines() if t.strip()]
    known.sort(key=len, reverse=True)  # longest first → match wins

    out_rows: list[dict] = []
    with Path(args.thumbnails).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_url = row.get("post_url", "").strip()
            thumb_url = row.get("thumbnail_url", "").strip()
            if not post_url or not thumb_url:
                continue
            try:
                resp = requests.get(thumb_url, timeout=args.timeout, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
            except Exception as e:
                print(f"[skip] {post_url}: fetch/decode failed: {e}", file=sys.stderr)
                continue

            try:
                text = pytesseract.image_to_string(img) or ""
            except Exception as e:
                print(f"[skip] {post_url}: OCR failed: {e}", file=sys.stderr)
                continue

            lower = text.lower()
            match = next((t for t in known if t.lower() in lower), None)
            if match:
                out_rows.append({"post_url": post_url, "suggested_tag": match, "ocr_text": text.strip().replace("\n", " | ")[:200]})

    with Path(args.output).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["post_url", "suggested_tag", "ocr_text"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"Thumbnail OCR: {len(out_rows)} matches written to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
