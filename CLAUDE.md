# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A **local audio transcription tool** that downloads audio from a URL (YouTube, podcast feeds, etc.), transcribes it using a local AI model, and stores the result in a database for later search.

Two types of search on transcripts:
- **Full-text / keyword search** — via SQLite FTS
- **Semantic search** — via a vector database (Qdrant)

### Longer-term vision (not the focus right now)
A self-contained desktop application that anyone can download and run locally — point it at an audio file or URL, get a searchable transcript. A web version where users upload audio and search transcripts may come later but is not planned yet.

## Current Status

> **The project is being revived and restructured.** The old codebase targeted Linux + NVIDIA GPU (vllm, CUDA, etc.) and does not run on Apple Silicon. A clean rewrite is in progress targeting macOS Apple Silicon first.

## Target Environment

- **Platform:** macOS, Apple Silicon (M-series chip)
- **Transcription:** `mlx-whisper` (Apple MLX framework — fast, native Apple Silicon support, no CUDA needed)
- **Python:** 3.11+, managed via `.venv`

## Architecture (target)

### Data Flow
```
Audio URL (YouTube, podcast RSS, etc.)
  → yt-dlp: download audio file
  → mlx-whisper: transcribe → chunks with timestamps
  → SQLite (FTS5): store chunks for keyword search
  → Qdrant (vector DB): store embeddings for semantic search
```

### Key Technologies
| Layer | Tool | Notes |
|---|---|---|
| Audio fetch | yt-dlp | Handles YouTube, SoundCloud, Acast, etc. |
| Transcription | mlx-whisper | Optimized for Apple Silicon via MLX |
| Keyword search | SQLite FTS5 | Built into Python stdlib (`sqlite3`) |
| Semantic search | Qdrant | Runs via Docker on port 6333 |
| Embeddings | TBD | A small multilingual model (e.g. `sentence-transformers`) |

### SQLite Schema
- **sources** — title, url, type (podcast/youtube/file), date added
- **transcription_segments** — source_id, start_time, end_time, text

## Key Commands

### Python Environment
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Qdrant (Vector DB via Docker)
```bash
# First run — create container with persistent storage
docker run -p 6333:6333 --name qdrant -v $(pwd)/data/qdrant_db:/qdrant/storage qdrant/qdrant

# Subsequent runs
docker start qdrant        # background
docker start -a qdrant     # with output
docker stop qdrant
```

### Transcription (mlx-whisper)
```bash
# Basic usage
mlx_whisper --model mlx-community/whisper-large-v3-turbo --language fr <audio.mp3>
```

## Gitignored Paths
Audio files (`.mp3`, `.wav`), model weights, the `whisper.cpp` submodule, and the `data/` directory are gitignored and must be set up locally.
