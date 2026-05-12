"""
Source-agnostic ingestion orchestrator.

Usage:
    python ingest.py --source harvard               # full run / resume
    python ingest.py --source harvard --skip-fetch  # skip re-fetching raw data

To add a new museum: implement MuseumSource in sources/<museum>.py and
register it in sources/__init__.py.
"""

import argparse
import json
import time
from pathlib import Path

from sources import SOURCES
from embedder import embed_artwork
from db import upsert_artworks, already_embedded_ids

CACHE_DIR = Path(__file__).parent.parent / "cache"


def _checkpoint_path(source_id: str) -> Path:
    return CACHE_DIR / f"{source_id}_checkpoint.json"


def _load_checkpoint(source_id: str) -> int:
    p = _checkpoint_path(source_id)
    return json.loads(p.read_text()).get("index", 0) if p.exists() else 0


def _save_checkpoint(source_id: str, index: int) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _checkpoint_path(source_id).write_text(json.dumps({"index": index}))


def run(source_name: str, skip_fetch: bool) -> None:
    if source_name not in SOURCES:
        raise ValueError(f"Unknown source '{source_name}'. Available: {list(SOURCES)}")

    source = SOURCES[source_name]()
    print(f"=== Sift ingest: {source_name} ===\n")

    raw = source.fetch_all(use_cache=skip_fetch)

    print("Cleaning…")
    rows = source.clean(raw)
    print(f"After cleaning: {len(rows):,} artworks\n")

    # Embed + upsert
    start = _load_checkpoint(source_name)
    done_ids = already_embedded_ids()
    if start > 0 or done_ids:
        print(f"Resuming from index {start} ({len(done_ids):,} already embedded)\n")

    batch: list[dict] = []
    BATCH_SIZE = 50

    for i, row in enumerate(rows):
        if i < start or row["id"] in done_ids:
            continue

        embedding = embed_artwork(row)
        if embedding is not None:
            row["embedding"] = embedding
            row["embedding_type"] = "multimodal" if row.get("primary_image_url") else "text"

        batch.append(row)

        if len(batch) >= BATCH_SIZE:
            upsert_artworks(batch)
            _save_checkpoint(source_name, i + 1)
            print(f"  [{i + 1:,}/{len(rows):,}] upserted {len(batch)} rows")
            batch = []
            time.sleep(0.05)

    if batch:
        upsert_artworks(batch)
        _save_checkpoint(source_name, len(rows))
        print(f"  [{len(rows):,}/{len(rows):,}] upserted final {len(batch)} rows")

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=list(SOURCES), help="Museum source to ingest")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached raw data")
    args = parser.parse_args()
    run(args.source, skip_fetch=args.skip_fetch)
