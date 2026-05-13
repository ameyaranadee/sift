import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]

GOOGLE_CLOUD_PROJECT: str = os.environ["GOOGLE_CLOUD_PROJECT"]
GOOGLE_CLOUD_LOCATION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

GEMINI_EMBEDDING_MODEL = "gemini-embedding-2-preview"
IIIF_MAX_DIM = 800
