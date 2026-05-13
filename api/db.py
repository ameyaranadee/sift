from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


_DETAIL_COLUMNS = ",".join([
    "id", "object_number", "title", "dated", "date_begin", "date_end",
    "century", "period", "medium", "technique", "classification",
    "culture", "division", "department",
    "artist_name", "artist_culture", "artist_display_date",
    "artist_birthplace", "artist_deathplace",
    "dimensions", "dim_height_cm", "dim_width_cm",
    "description", "label_text", "credit_line",
    "primary_image_url", "artwork_url", "source",
])


def get_artwork(artwork_id: int) -> dict | None:
    client = get_client()
    resp = (
        client.table("artworks")
        .select(_DETAIL_COLUMNS)
        .eq("id", artwork_id)
        .limit(1)
        .execute()
    )
    data = resp.data or []
    return data[0] if data else None


def get_random_artworks(count: int = 20) -> list[dict]:
    client = get_client()
    resp = client.rpc("random_artworks", {"count": count}).execute()
    return resp.data or []


def search_artworks(
    embedding: list[float],
    limit: int = 20,
    threshold: float = 0.3,
    classification: str | None = None,
    century: str | None = None,
    culture: str | None = None,
    division: str | None = None,
) -> list[dict]:
    client = get_client()
    params = {
        "query_embedding": embedding,
        "match_count": limit,
        "match_threshold": threshold,
        "filter_classification": classification,
        "filter_century": century,
        "filter_culture": culture,
        "filter_division": division,
    }
    resp = client.rpc("search_artworks", params).execute()
    return resp.data or []
