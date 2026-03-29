#!/usr/bin/env python3
"""Download Collins Scrabble Words (CSW21), merge with existing words.txt, and update metadata."""
from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CSW21_URL = "https://raw.githubusercontent.com/scrabblewords/scrabblewords/main/words/British/CSW21.txt"

ROOT = Path(__file__).resolve().parent.parent
WORDS_PATH = ROOT / "words.txt"
META_PATH = ROOT / "dict.meta.json"
SCRABBLE_DIR = ROOT / "data" / "scrabble"
CSW_CACHE_PATH = SCRABBLE_DIR / "csw21.txt"


def download_csw() -> Path:
    if CSW_CACHE_PATH.exists():
        print(f"  cached: {CSW_CACHE_PATH}")
        return CSW_CACHE_PATH
    SCRABBLE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  downloading from {CSW21_URL} ...")
    try:
        with urllib.request.urlopen(CSW21_URL) as resp, CSW_CACHE_PATH.open("wb") as f:
            shutil.copyfileobj(resp, f)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to download CSW21: {exc}") from exc
    print(f"  saved to {CSW_CACHE_PATH}")
    return CSW_CACHE_PATH


def read_words(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {line.strip() for line in text.splitlines() if line.strip()}


def normalize_scrabble_words(path: Path) -> set[str]:
    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Take only the first token (some formats have definitions after the word)
        token = stripped.split()[0]
        word = re.sub(r"[^a-z]", "", token.lower())
        if word:
            words.add(word)
    return words


def assert_sorted_unique(words: list[str]) -> None:
    for i in range(1, len(words)):
        if words[i - 1] >= words[i]:
            raise RuntimeError(
                f"Sorted-unique invariant failed at index {i}: '{words[i - 1]}' >= '{words[i]}'"
            )


def update_meta(total: int, csw_raw_count: int) -> None:
    meta: dict = {}
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))

    meta["additionalSources"] = [
        {
            "name": "csw21",
            "description": "Collins Scrabble Words 2021 (SOWPODS/International)",
            "url": CSW21_URL,
            "wordCountRaw": csw_raw_count,
        }
    ]
    meta.setdefault("stats", {})
    meta["stats"]["wordCount"] = total
    meta["stats"]["buildTimestamp"] = datetime.now(timezone.utc).isoformat()

    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    print("[1/4] Download CSW21")
    csw_path = download_csw()

    print("[2/4] Read word lists")
    if not WORDS_PATH.exists():
        raise RuntimeError(f"{WORDS_PATH} not found. Run `npm run dict:words` first.")
    existing = read_words(WORDS_PATH)
    scrabble = normalize_scrabble_words(csw_path)
    print(f"  existing words.txt: {len(existing):,}")
    print(f"  CSW21 (normalized): {len(scrabble):,}")

    print("[3/4] Merge + deduplicate")
    overlap = existing & scrabble
    csw_only = scrabble - existing
    scowl_only = existing - scrabble
    merged = sorted(existing | scrabble)
    assert_sorted_unique(merged)
    WORDS_PATH.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"  overlap:    {len(overlap):,}")
    print(f"  SCOWL-only: {len(scowl_only):,}")
    print(f"  CSW-only:   {len(csw_only):,}")
    print(f"  total:      {len(merged):,}")

    print("[4/4] Update metadata")
    update_meta(len(merged), len(scrabble))
    print(f"  updated {META_PATH}")

    print(f"\nDone. words.txt now has {len(merged):,} words.")
    print("Run `npm run dict:dawg` to rebuild the DAWG file.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc
