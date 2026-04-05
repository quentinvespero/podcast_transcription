import os

from src import downloader, embedder, transcriber
from src.config import AUDIO_DIR, DB_PATH
from src.database import sqlite_store, vector_store
from src.utils import normalize_url


def ingest(url: str, language: str | None = None, force: bool = False, initial_prompt: str | None = None) -> None:
    """
    Full ingest pipeline for a single audio URL:
      1. Download audio via yt-dlp
      2. Transcribe with mlx-whisper
      3. Store segments in SQLite (keyword search)
      4. Embed segments and store in Qdrant (semantic search)

    Args:
        url:            Any URL supported by yt-dlp (YouTube, SoundCloud, etc.)
        language:       ISO 639-1 language hint for Whisper (e.g. "fr", "en").
                        None = auto-detect (slightly slower).
        force:          Re-download and re-transcribe even if already processed.
        initial_prompt: Optional context hint for Whisper (e.g. "React, TypeScript").
                        See transcriber.transcribe() for details.
    """
    url = normalize_url(url)

    # Ensure storage directories exist before any file operations
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    sqlite_store.init_db(DB_PATH)

    # ── Deduplication check ───────────────────────────────────────────────────
    if not force:
        status = sqlite_store.get_source_status(DB_PATH, url)
        if status == "complete":
            print(f"[skip] {url} already ingested. Use --force to re-process.")
            return

    if force:
        # Wipe existing data so the pipeline runs fresh.
        # Note: orphaned Qdrant points are not removed (acceptable for local use).
        sqlite_store.delete_source(DB_PATH, url)

    # ── 1. Download ──────────────────────────────────────────────────────────
    print(f"[1/4] Downloading audio from {url} …")
    audio_info = downloader.download_audio(url, AUDIO_DIR)
    print(f"      ✓ {audio_info['title']}")

    # ── 2. Transcribe ────────────────────────────────────────────────────────
    print("[2/4] Transcribing …")
    segments = transcriber.transcribe(audio_info["file_path"], language=language, initial_prompt=initial_prompt)
    print(f"      ✓ {len(segments)} segments")

    # ── 3. SQLite ────────────────────────────────────────────────────────────
    print("[3/4] Storing in SQLite …")
    source_id   = sqlite_store.insert_source(DB_PATH, audio_info["title"], url)
    segment_ids = sqlite_store.insert_segments(DB_PATH, source_id, segments)
    print(f"      ✓ source_id={source_id}, {len(segment_ids)} segments")

    # ── 4. Qdrant ────────────────────────────────────────────────────────────
    print("[4/4] Generating embeddings and storing in Qdrant …")
    texts    = [s["text"] for s in segments]
    vectors  = embedder.embed_texts(texts)
    payloads = [
        {
            "source_id":    source_id,
            "source_title": audio_info["title"],
            "source_url":   url,
            "start_time":   s["start"],
            "end_time":     s["end"],
            "text":         s["text"],
        }
        for s in segments
    ]
    vector_store.insert_segments(segment_ids, vectors, payloads)
    print(f"      ✓ {len(segment_ids)} embeddings stored")

    sqlite_store.mark_source_complete(DB_PATH, source_id)
    print("\nDone!")
