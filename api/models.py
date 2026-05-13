from pydantic import BaseModel


class ArtworkResult(BaseModel):
    id: int
    title: str | None
    artist_name: str | None
    culture: str | None
    division: str | None
    dated: str | None
    century: str | None
    medium: str | None
    classification: str | None
    primary_image_url: str | None
    artwork_url: str | None
    similarity: float


class ArtworkDetail(BaseModel):
    id: int
    object_number: str | None
    title: str | None
    dated: str | None
    date_begin: int | None
    date_end: int | None
    century: str | None
    period: str | None
    medium: str | None
    technique: str | None
    classification: str | None
    culture: str | None
    division: str | None
    department: str | None
    artist_name: str | None
    artist_culture: str | None
    artist_display_date: str | None
    artist_birthplace: str | None
    artist_deathplace: str | None
    dimensions: str | None
    dim_height_cm: float | None
    dim_width_cm: float | None
    description: str | None
    label_text: str | None
    credit_line: str | None
    primary_image_url: str | None
    artwork_url: str | None
    source: str | None


class SearchResponse(BaseModel):
    results: list[ArtworkResult]
    count: int
