# Project Progress

## Pipeline Status


| Step                    | Status               | Notes                                                                    |
| ----------------------- | -------------------- | ------------------------------------------------------------------------ |
| Audio download          | Implemented          | yt-dlp, converts to MP3 via ffmpeg, tested on YouTube                    |
| Transcription           | Implemented          | mlx-whisper (Apple Silicon), segment timestamps, auto language detect    |
| SQLite storage          | Implemented & tested | FTS5, sources + segments schema, deduplication via status field          |
| Embeddings              | Implemented          | sentence-transformers, module-level model cache                          |
| Qdrant / vector storage | Implemented          | Qdrant client, cosine similarity, SQLite segment IDs as Qdrant point IDs |
| Keyword search          | Implemented          | FTS5 via `search keyword` CLI command                                    |
| Semantic search         | Implemented          | Qdrant via `search semantic` CLI command                                 |
| End-to-end pipeline     | Implemented          | `ingest` orchestrates all 4 steps; full run not yet confirmed            |


## What's Missing / Known Gaps

- **End-to-end test** — the full `ingest` → both searches flow has not been run yet
- **Qdrant orphan cleanup** — force re-ingest wipes SQLite rows but leaves stale Qdrant points
- **RSS/podcast feed support** — yt-dlp handles it in theory but untested
- **UI** — CLI only; no desktop or web interface yet

## Milestone Log

- 2026-03-30 — Full pipeline code complete: download → transcribe → SQLite → Qdrant → search

