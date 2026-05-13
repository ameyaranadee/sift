import logging
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import get_artwork, get_random_artworks, search_artworks
from embedder import embed_image_query, embed_query
from models import ArtworkDetail, ArtworkResult, SearchResponse

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Sift API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


class TextSearchRequest(BaseModel):
    q: str
    limit: int = Field(20, ge=1, le=100)
    threshold: float = Field(0.3, ge=0.0, le=1.0)
    classification: Optional[str] = None
    century: Optional[str] = None
    culture: Optional[str] = None
    division: Optional[str] = None


@app.get("/artworks/random", response_model=SearchResponse)
def get_random(limit: int = Query(20, ge=1, le=100)):
    rows = get_random_artworks(limit)
    return SearchResponse(results=[ArtworkResult(**r) for r in rows], count=len(rows))


@app.get("/artworks/{artwork_id}", response_model=ArtworkDetail)
def get_artwork_detail(artwork_id: int):
    row = get_artwork(artwork_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return ArtworkDetail(**row)


@app.post("/search/text", response_model=SearchResponse)
def search_by_text(req: TextSearchRequest):
    embedding = embed_query(req.q)
    if embedding is None:
        raise HTTPException(status_code=502, detail="Embedding service unavailable")
    rows = search_artworks(
        embedding,
        limit=req.limit,
        threshold=req.threshold,
        classification=req.classification,
        century=req.century,
        culture=req.culture,
        division=req.division,
    )
    return SearchResponse(results=[ArtworkResult(**r) for r in rows], count=len(rows))


@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    limit: int = Query(20, ge=1, le=100),
    threshold: float = Query(0.3, ge=0.0, le=1.0),
    classification: Optional[str] = Query(None),
    century: Optional[str] = Query(None),
    culture: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
):
    data = await image.read()
    mime = image.content_type or "image/jpeg"
    if not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    embedding = embed_image_query(data, mime)
    if embedding is None:
        raise HTTPException(status_code=502, detail="Embedding service unavailable")
    rows = search_artworks(
        embedding,
        limit=limit,
        threshold=threshold,
        classification=classification,
        century=century,
        culture=culture,
        division=division,
    )
    return SearchResponse(results=[ArtworkResult(**r) for r in rows], count=len(rows))
