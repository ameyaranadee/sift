import base64
from typing import Optional

import httpx
from google import genai
from google.genai import types

from config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GEMINI_EMBEDDING_MODEL, IIIF_MAX_DIM

_client = genai.Client(
    vertexai=True,
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
)

# Task prefixes are embedded inline in the text per gemini-embedding-2's spec.
_DOC_TASK = "task: retrieval document"
_QUERY_TASK = "task: retrieval query"


def _image_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/full/!{IIIF_MAX_DIM},{IIIF_MAX_DIM}/0/default.jpg"


def _fetch_image(url: str) -> Optional[bytes]:
    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def build_text(row: dict) -> str:
    parts: list[str] = []

    if row.get("title"):
        parts.append(f"Title: {row['title']}")
    if row.get("artist_name"):
        parts.append(f"Artist: {row['artist_name']}")
    if row.get("artist_display_date"):
        parts.append(f"Active: {row['artist_display_date']}")

    culture = row.get("culture") or row.get("artist_culture")
    if culture:
        parts.append(f"Culture: {culture}")
    if row.get("division"):
        parts.append(f"Division: {row['division']}")

    for field, label in [
        ("dated", "Date"),
        ("century", "Century"),
        ("period", "Period"),
        ("medium", "Medium"),
        ("technique", "Technique"),
        ("classification", "Classification"),
        ("department", "Department"),
    ]:
        if row.get(field):
            parts.append(f"{label}: {row[field]}")

    for field in ("description", "label_text", "credit_line"):
        if row.get(field):
            parts.append(row[field])

    return "\n".join(parts)


def embed_artwork(row: dict) -> Optional[list[float]]:
    """Embed a cleaned artwork row (image + text) for storage."""
    text = f"{_DOC_TASK} | {build_text(row)}"
    content_parts: list[types.Part] = []

    base_url = row.get("primary_image_url")
    if base_url:
        image_bytes = _fetch_image(_image_url(base_url))
        if image_bytes:
            content_parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=base64.b64encode(image_bytes).decode(),
                    )
                )
            )

    content_parts.append(types.Part(text=text))

    try:
        response = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=types.Content(parts=content_parts),
        )
        return response.embeddings[0].values
    except Exception as exc:
        print(f"  [embedder] failed for id={row.get('id')}: {exc}")
        return None


def embed_query(query_text: str) -> Optional[list[float]]:
    """Embed a user search query (text-only)."""
    try:
        response = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=types.Content(
                parts=[types.Part(text=f"{_QUERY_TASK} | {query_text}")]
            ),
        )
        return response.embeddings[0].values
    except Exception as exc:
        print(f"  [embedder] query failed: {exc}")
        return None


def embed_image_query(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[list[float]]:
    """Embed an uploaded image for reverse image search."""
    try:
        response = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=base64.b64encode(image_bytes).decode(),
                        )
                    ),
                    types.Part(text=f"{_QUERY_TASK} | artwork"),
                ]
            ),
        )
        return response.embeddings[0].values
    except Exception as exc:
        print(f"  [embedder] image query failed: {exc}")
        return None
