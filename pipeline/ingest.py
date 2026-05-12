"""
Source-agnostic ingestion orchestrator.

Usage:
    python ingest.py --source harvard               # full run / resume
    python ingest.py --source harvard --skip-fetch  # skip re-fetching raw data

Logs go to cache/logs/ingest_<source>_<timestamp>.log and to stdout.

To add a new museum: implement MuseumSource in sources/<museum>.py and
register it in sources/__init__.py.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from sources import SOURCES
from embedder import embed_artwork
from db import upsert_artworks, already_embedded_ids

CACHE_DIR = Path(__file__).parent.parent / "cache"
LOG_DIR = CACHE_DIR / "logs"


def setup_logging(source_name: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"ingest_{source_name}_{timestamp}.log"

    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # Root logger — all modules that use logging.getLogger(__name__) inherit this
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("ingest")
    logger.info("Logging to %s", log_file)
    return logger


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

    log = setup_logging(source_name)
    log.info("=== Sift ingest: %s ===", source_name)

    source = SOURCES[source_name]()

    # 1. Fetch
    raw = source.fetch_all(use_cache=skip_fetch)

    # 2. Clean
    log.info("Cleaning…")
    rows = source.clean(raw)
    log.info("After cleaning: %s artworks", f"{len(rows):,}")

    # 3. Embed + upsert (resumable)
    start = _load_checkpoint(source_name)
    done_ids = already_embedded_ids()
    if start > 0 or done_ids:
        log.info("Resuming from index %s (%s already embedded)", f"{start:,}", f"{len(done_ids):,}")

    batch: list[dict] = []
    BATCH_SIZE = 50
    failed = 0

    for i, row in enumerate(rows):
        if i < start or row["id"] in done_ids:
            continue

        embedding = embed_artwork(row)
        if embedding is not None:
            row["embedding"] = embedding
            row["embedding_type"] = "multimodal" if row.get("primary_image_url") else "text"
        else:
            failed += 1

        batch.append(row)

        if len(batch) >= BATCH_SIZE:
            upsert_artworks(batch)
            _save_checkpoint(source_name, i + 1)
            log.info("[%s/%s] upserted %d rows (%d embed failures so far)",
                     f"{i + 1:,}", f"{len(rows):,}", len(batch), failed)
            batch = []
            time.sleep(0.05)

    if batch:
        upsert_artworks(batch)
        _save_checkpoint(source_name, len(rows))
        log.info("[%s/%s] upserted final %d rows", f"{len(rows):,}", f"{len(rows):,}", len(batch))

    log.info("Done. Total embed failures: %d", failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=list(SOURCES), help="Museum source to ingest")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached raw data")
    args = parser.parse_args()
    run(args.source, skip_fetch=args.skip_fetch)
