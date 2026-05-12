"""
Harvard Art Museums source.

Data: ~248k objects via the public browse endpoint.
After cleaning: ~127k artworks with valid 2D images.

Cleaning logic:
  - Must have primaryimageurl
  - dimensions must parse to H×W in cm
  - H in [1, 200] cm, W in [1, 250] cm  (excludes coins, scrolls, wall-size works)
  - Deduplicate on primaryimageurl
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Optional

import aiohttp

from sources.base import ArtworkRow, MuseumSource

log = logging.getLogger(__name__)

BROWSE_URL = "https://harvardartmuseums.org/browse"
CONCURRENCY = 10
CACHE_FILE = Path(__file__).parent.parent.parent / "cache" / "harvard_raw.json"

DIMS_RE = re.compile(
    r"([0-9]+\.?[0-9]*) ?x ?(?:W\.)? ?([0-9]+\.?[0-9]*) ?(?:x [0-9.]+)? ?cm",
    re.IGNORECASE,
)
DIM_H_MIN, DIM_H_MAX = 1.0, 200.0
DIM_W_MIN, DIM_W_MAX = 1.0, 250.0
ARTIST_ROLES = {"Artist", "Artist after", "Maker", "Attributed to"}


class HarvardSource(MuseumSource):
    source_id = "harvard"

    def fetch_all(self, use_cache: bool = True) -> list[dict]:
        if use_cache and CACHE_FILE.exists():
            log.info("Loading cached Harvard data from %s", CACHE_FILE)
            return json.loads(CACHE_FILE.read_text())

        log.info("Fetching all records from Harvard Art Museums (async)…")
        records = asyncio.run(self._fetch_async())

        deduped = list({r["id"]: r for r in records}.values())
        log.info("Fetched %s records → %s after id-dedup → caching", f"{len(records):,}", f"{len(deduped):,}")
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(deduped))
        return deduped

    async def _fetch_async(self) -> list[dict]:
        records: list[dict] = []
        sema = asyncio.Semaphore(CONCURRENCY)
        connector = aiohttp.TCPConnector(limit=CONCURRENCY)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            first = await self._load_page(session, 0)
            meta = first.get("info", {})
            n_pages: int = meta.get("pages", 1)
            total: int = meta.get("totalrecords", 0)
            log.info("%s objects across %s pages", f"{total:,}", f"{n_pages:,}")
            records.extend(first.get("records", []))

            async def task(offset: int) -> None:
                async with sema:
                    data = await self._load_page(session, offset)
                    records.extend(data.get("records", []))

            tasks = [asyncio.create_task(task(i * 100)) for i in range(1, n_pages)]
            done = 0
            for coro in asyncio.as_completed(tasks):
                await coro
                done += 1
                if done % 200 == 0:
                    log.info("%s/%s pages fetched…", f"{done:,}", f"{n_pages - 1:,}")

        return records

    async def _load_page(self, session: aiohttp.ClientSession, offset: int) -> dict:
        try:
            async with session.get(
                BROWSE_URL, params={"load_amount": 100, "offset": offset}
            ) as resp:
                return await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Page fetch failed at offset=%d: %s", offset, exc)
            return {}

    def clean(self, raw: list[dict]) -> list[ArtworkRow]:
        seen_images: set[str] = set()
        out: list[ArtworkRow] = []

        for rec in raw:
            image_url = rec.get("primaryimageurl")
            if not image_url:
                continue

            dims = self._parse_dims(rec.get("dimensions"))
            if dims is None:
                continue
            h, w = dims
            if not (DIM_H_MIN <= h <= DIM_H_MAX and DIM_W_MIN <= w <= DIM_W_MAX):
                continue

            if image_url in seen_images:
                continue
            seen_images.add(image_url)

            out.append(self._transform(rec, h, w))

        return out

    def _transform(self, rec: dict, h: float, w: float) -> ArtworkRow:
        people: list[dict] = rec.get("people") or []
        artist = next((p for p in people if p.get("role") in ARTIST_ROLES), {})

        return ArtworkRow(
            id=rec["id"],
            source=self.source_id,
            object_number=rec.get("objectnumber"),
            title=rec.get("title"),
            artwork_url=rec.get("url"),
            dated=rec.get("dated"),
            date_begin=self._safe_int(rec.get("datebegin")),
            date_end=self._safe_int(rec.get("dateend")),
            century=rec.get("century"),
            period=rec.get("period"),
            medium=rec.get("medium"),
            technique=rec.get("technique"),
            classification=rec.get("classification"),
            culture=rec.get("culture"),
            division=rec.get("division"),
            department=rec.get("department"),
            artist_name=artist.get("displayname") or artist.get("name"),
            artist_culture=artist.get("culture"),
            artist_display_date=artist.get("displaydate"),
            artist_birthplace=artist.get("birthplace"),
            artist_deathplace=artist.get("deathplace"),
            dimensions=rec.get("dimensions"),
            dim_height_cm=h,
            dim_width_cm=w,
            primary_image_url=rec.get("primaryimageurl"),
            description=rec.get("description"),
            label_text=rec.get("labeltext"),
            credit_line=rec.get("creditline"),
            access_level=rec.get("accesslevel"),
            verification_level=rec.get("verificationlevel"),
            total_page_views=rec.get("totalpageviews"),
            total_unique_page_views=rec.get("totaluniquepageviews"),
            raw=rec,
        )

    @staticmethod
    def _parse_dims(dimensions: Optional[str]) -> Optional[tuple[float, float]]:
        if not dimensions:
            return None
        m = DIMS_RE.search(dimensions)
        return (float(m.group(1)), float(m.group(2))) if m else None

    @staticmethod
    def _safe_int(v) -> Optional[int]:
        try:
            return max(int(v), 0)
        except (TypeError, ValueError):
            return None
