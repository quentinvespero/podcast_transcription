import os

# ── Storage paths ────────────────────────────────────────────────────────────
# Anchor all paths to the project root so the script works regardless of cwd.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR  = os.path.join(_PROJECT_ROOT, "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
DB_PATH   = os.path.join(DATA_DIR, "transcriptions.db")

# ── Qdrant (vector database) ─────────────────────────────────────────────────
QDRANT_PATH       = os.path.join(DATA_DIR, "qdrant_db")
QDRANT_COLLECTION = "segments"

# ── Transcription ────────────────────────────────────────────────────────────
TRANSCRIPTION_MODEL = "mlx-community/whisper-large-v3-turbo"

# ── Embeddings ───────────────────────────────────────────────────────────────
# Multilingual MiniLM: compact (~420 MB), covers French, English, and more.
# Produces 384-dimensional vectors — keep EMBEDDING_DIMENSION in sync.
EMBEDDING_MODEL     = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384
