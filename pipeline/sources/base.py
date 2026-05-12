from abc import ABC, abstractmethod
from typing import Optional
from typing_extensions import TypedDict, Required


class ArtworkRow(TypedDict, total=False):
    """Standard schema every museum source must produce."""
    # Required
    id: Required[int]
    source: Required[str]           # e.g. "harvard", "met"
    primary_image_url: Required[str]

    # Identification
    object_number: str
    title: str
    artwork_url: str                 # museum collection page URL

    # Dating
    dated: str                       # free-text, e.g. "c. 1637-1645"
    date_begin: Optional[int]
    date_end: Optional[int]
    century: str
    period: str

    # Material / technique
    medium: str
    technique: str
    classification: str

    # Geography / culture
    culture: str                     # artwork-level, e.g. "Dutch"
    division: str                    # e.g. "European and American Art"
    department: str

    # Artist (primary)
    artist_name: str
    artist_culture: str
    artist_display_date: str
    artist_birthplace: str
    artist_deathplace: str

    # Physical dimensions
    dimensions: str                  # raw string
    dim_height_cm: float
    dim_width_cm: float

    # Descriptive text
    description: str
    label_text: str
    credit_line: str

    # Quality signals
    access_level: int
    verification_level: int
    total_page_views: int
    total_unique_page_views: int

    # Full raw API response (stored as JSONB)
    raw: dict

    # Populated by the embedder, not the source
    embedding: list[float]
    embedding_type: str              # "multimodal" | "text"


class MuseumSource(ABC):
    """
    Abstract base for a museum data source.

    To add a new museum:
      1. Create pipeline/sources/<museum>.py
      2. Subclass MuseumSource, set source_id, implement fetch_all() and clean()
      3. Register in pipeline/ingest.py's SOURCES dict
    """

    source_id: str  # short slug used in the `source` DB column and cache filenames

    @abstractmethod
    def fetch_all(self) -> list[dict]:
        """Fetch all raw records from the museum. May be cached to disk."""
        ...

    @abstractmethod
    def clean(self, raw: list[dict]) -> list[ArtworkRow]:
        """
        Filter and transform raw records into ArtworkRow dicts.
        Must deduplicate on primary_image_url within the source.
        """
        ...
