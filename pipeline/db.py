import logging
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

log = logging.getLogger(__name__)
_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def upsert_artworks(rows: list[dict]) -> None:
    client = get_client()
    batch_size = 50  # ~5MB payload cap per Supabase REST request
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            client.table("artworks").upsert(batch, on_conflict="id").execute()
        except Exception as exc:
            log.error("upsert failed for batch starting at %d: %s", i, exc)


def already_embedded_ids() -> set[int]:
    """Return IDs of artworks that already have an embedding (for resumable runs)."""
    client = get_client()
    ids: set[int] = set()
    page, page_size = 0, 1000
    while True:
        resp = (
            client.table("artworks")
            .select("id")
            .not_.is_("embedding", "null")
            .range(page * page_size, (page + 1) * page_size - 1)
            .execute()
        )
        batch = resp.data or []
        for row in batch:
            ids.add(row["id"])
        if len(batch) < page_size:
            break
        page += 1
    return ids
