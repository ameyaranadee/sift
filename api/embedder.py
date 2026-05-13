import base64
import logging
from typing import Optional

import httpx
from google import genai
from google.genai import types

from config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GEMINI_EMBEDDING_MODEL, IIIF_MAX_DIM

log = logging.getLogger(__name__)

_client = genai.Client(
    vertexai=True,
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
)

_QUERY_TASK = "task: retrieval query"


def _image_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/full/!{IIIF_MAX_DIM},{IIIF_MAX_DIM}/0/default.jpg"


def embed_query(query_text: str) -> Optional[list[float]]:
    try:
        response = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=types.Content(
                parts=[types.Part(text=f"{_QUERY_TASK} | {query_text}")]
            ),
        )
        return response.embeddings[0].values
    except Exception as exc:
        log.error("embed_query failed: %s", exc)
        return None


def embed_image_query(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[list[float]]:
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
        log.error("embed_image_query failed: %s", exc)
        return None


def embed_image_url_query(image_url: str) -> Optional[list[float]]:
    """Embed a publicly accessible image URL for reverse image search."""
    try:
        resp = httpx.get(_image_url(image_url), timeout=5, follow_redirects=True)
        resp.raise_for_status()
        return embed_image_query(resp.content, "image/jpeg")
    except Exception as exc:
        log.error("embed_image_url_query failed for %s: %s", image_url, exc)
        return None
