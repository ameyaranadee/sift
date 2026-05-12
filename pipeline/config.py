import os
from dotenv import load_dotenv

load_dotenv()

HAM_API_KEY: str = os.environ["HAM_API_KEY"]
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]

# Vertex AI project — auth via Application Default Credentials.
# Run once: gcloud auth application-default login
GOOGLE_CLOUD_PROJECT: str = os.environ["GOOGLE_CLOUD_PROJECT"]
GOOGLE_CLOUD_LOCATION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIM = 3072

# Max image dimension when fetching via IIIF (keeps payloads reasonable)
IIIF_MAX_DIM = 800
