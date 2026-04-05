"""
FastAPI server that wraps the CLI pipeline for the macOS GUI.

Run with:
    uv run uvicorn src.server:app --port 8765
"""

import asyncio
import json
import queue
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src import embedder
from src.config import DB_PATH
from src.database import sqlite_store, vector_store
from src import pipeline

app = FastAPI()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Readiness probe — Swift polls this after spawning the server process."""
    return {"status": "ok"}


# ── Ingest (SSE) ──────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    url: str
    language: str | None = None
    force: bool = False
    initial_prompt: str | None = None


@app.post("/ingest")
async def ingest_endpoint(body: IngestRequest):
    """
    Run the ingest pipeline and stream progress messages as Server-Sent Events.

    Event types:
      (default) — progress message string
      error     — pipeline raised an exception; data contains {"message": "..."}
    """
    msg_queue: queue.Queue[str | None] = queue.Queue()

    def on_progress(msg: str) -> None:
        msg_queue.put(msg)

    def run() -> None:
        try:
            pipeline.ingest(
                body.url,
                body.language,
                body.force,
                body.initial_prompt,
                on_progress=on_progress,
            )
        except Exception as e:
            msg_queue.put(f"__error__:{e}")
        finally:
            # Always unblock the async reader, even if an exception was raised
            msg_queue.put(None)

    threading.Thread(target=run, daemon=True).start()

    async def stream():
        loop = asyncio.get_running_loop()
        while True:
            msg = await loop.run_in_executor(None, msg_queue.get)
            if msg is None:
                break
            if msg.startswith("__error__:"):
                yield f"event: error\ndata: {json.dumps({'message': msg[10:]})}\n\n"
            else:
                yield f"data: {json.dumps({'message': msg})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Sources ───────────────────────────────────────────────────────────────────

@app.get("/sources")
async def sources_endpoint():
    """List all ingested sources, most recent first."""
    return sqlite_store.list_sources(DB_PATH)


# ── Search ────────────────────────────────────────────────────────────────────

@app.get("/search/keyword")
async def search_keyword_endpoint(q: str = Query(..., min_length=1), limit: int = 10):
    """Full-text keyword search across all transcription segments."""
    return sqlite_store.search_keyword(DB_PATH, q, limit=limit)


@app.get("/search/semantic")
async def search_semantic_endpoint(q: str = Query(..., min_length=1), limit: int = 10):
    """Semantic similarity search using the same embedding model as ingest."""
    try:
        query_vector = embedder.embed_texts([q])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")
    return vector_store.search_semantic(query_vector, limit=limit)
