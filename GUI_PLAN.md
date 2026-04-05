# GUI Implementation Plan

## Decisions Made

### Stack
- **Frontend:** SwiftUI (native macOS app)
- **Backend:** Python + FastAPI (wraps existing pipeline, no rewrite)
- **Bridge:** SwiftUI spawns uvicorn as a subprocess on launch, talks to it via HTTP on `localhost:8765`
- **Vector DB:** Qdrant in **embedded mode** (`QdrantClient(path=...)`) — no Docker, no separate process

### Why these choices
- SwiftUI for a first-class native macOS experience
- FastAPI because the Python ML stack (yt-dlp, mlx-whisper, sentence-transformers) has no viable Swift equivalent — rewriting would be pointless
- The HTTP overhead between Swift and FastAPI is negligible (microseconds) compared to minutes of transcription work
- Qdrant embedded replaces the Docker dependency; one-line change, same API
- Scale estimate: 200 × 2h podcasts ≈ 280K segments ≈ ~430MB vectors + ~150MB SQLite — manageable

---

## Architecture

```
SwiftUI App (macOS)
  ├── ServerProcess.swift  → spawns: uv run uvicorn src.server:app --port 8765
  ├── APIService.swift     → HTTP calls to localhost:8765
  └── Views                → Ingest / Sources / Search

FastAPI server (src/server.py)
  ├── GET  /health         → readiness probe (Swift polls this before first request)
  ├── POST /ingest         → SSE stream (progress events + error event)
  ├── GET  /sources        → list all sources
  ├── GET  /search/keyword?q=
  └── GET  /search/semantic?q=
```

---

## Phase 1: Python changes ✅ Done

| File | Change | Status |
|------|--------|--------|
| `src/config.py` | Switched to `QDRANT_PATH` (absolute, anchored to project root); removed `QDRANT_HOST`/`QDRANT_PORT` | ✅ |
| `src/database/vector_store.py` | `QdrantClient(path=QDRANT_PATH)` — embedded mode, no Docker | ✅ |
| `src/pipeline.py` | Added `on_progress: Callable[[str], None] = print` param; replaced all `print()` with `on_progress()` | ✅ |
| `src/database/sqlite_store.py` | Added `list_sources(db_path) -> list[dict]` | ✅ |
| `src/server.py` | **New file** — FastAPI app with 5 endpoints (see below) | ✅ |
| `requirements.txt` | Added `fastapi`, `uvicorn[standard]` | ✅ |

### Risks addressed in Phase 1
- **SSE deadlock on exception** — `run()` wrapped in `try/finally`; always puts `None` sentinel even on crash; pipeline errors sent as `event: error` SSE event
- **`asyncio.get_event_loop()` deprecated** — uses `asyncio.get_running_loop()` instead
- **Server readiness race condition** — `GET /health` endpoint added for Swift to poll before making real requests

### Key pattern for `/ingest` SSE streaming

```python
@app.post("/ingest")
async def ingest_endpoint(body: IngestRequest):
    msg_queue: queue.Queue[str | None] = queue.Queue()

    def on_progress(msg): msg_queue.put(msg)
    def run():
        try:
            pipeline.ingest(body.url, body.language, body.force,
                            body.initial_prompt, on_progress=on_progress)
        except Exception as e:
            msg_queue.put(f"__error__:{e}")
        finally:
            msg_queue.put(None)  # always unblocks the reader

    threading.Thread(target=run, daemon=True).start()

    async def stream():
        loop = asyncio.get_running_loop()
        while True:
            msg = await loop.run_in_executor(None, msg_queue.get)
            if msg is None: break
            if msg.startswith("__error__:"):
                yield f"event: error\ndata: {json.dumps({'message': msg[10:]})}\n\n"
            else:
                yield f"data: {json.dumps({'message': msg})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
```

### Verification commands
```bash
uv pip install -r requirements.txt
uv run uvicorn src.server:app --port 8765

curl http://localhost:8765/health
curl http://localhost:8765/sources
curl "http://localhost:8765/search/keyword?q=test"
curl "http://localhost:8765/search/semantic?q=test"
```

---

## Phase 2: SwiftUI app ⏳ Not started

New Xcode project at `PodcastExtractor/` (macOS App, SwiftUI, no CoreData).

```
PodcastExtractor/
├── PodcastExtractorApp.swift     # starts/stops server on app lifecycle
├── Services/
│   ├── ServerProcess.swift       # Process() wrapper for uvicorn subprocess
│   └── APIService.swift          # URLSession async/await wrappers
├── Models/
│   ├── Source.swift
│   └── SearchResult.swift
└── Views/
    ├── ContentView.swift         # TabView: Ingest | Sources | Search
    ├── IngestView.swift          # URL input, progress log (SSE), spinner
    ├── SourcesView.swift         # List of ingested sources
    └── SearchView.swift          # Query field, keyword/semantic toggle, results
```

### Risks to address in Phase 2

**1. `uv` not in subprocess PATH**
macOS app bundles don't inherit shell PATH — `uv` won't be found via a plain `Process()` call.
Fix: resolve `uv`'s absolute path at startup using a login shell:
```swift
// Step 1: find uv
let whichTask = Process()
whichTask.executableURL = URL(fileURLWithPath: "/bin/zsh")
whichTask.arguments = ["-l", "-c", "which uv"]
// capture stdout → uvPath (e.g. "/Users/you/.cargo/bin/uv")

// Step 2: launch server with absolute path
let serverTask = Process()
serverTask.executableURL = URL(fileURLWithPath: uvPath)
serverTask.arguments = ["run", "uvicorn", "src.server:app", "--port", "8765"]
serverTask.currentDirectoryURL = projectRoot
```

**2. Server readiness polling**
After spawning the process, poll `GET /health` before enabling the UI:
```swift
func waitUntilReady() async throws {
    for _ in 0..<20 {           // max ~2 seconds
        try? await Task.sleep(nanoseconds: 100_000_000)  // 100ms
        if let _ = try? await APIService.shared.health() { return }
    }
    throw ServerError.startupTimeout
}
```

**3. SSE error event handling**
```swift
for try await line in stream.lines {
    if line.hasPrefix("event: error") {
        // next "data:" line contains {"message": "..."} — show in UI
    } else if line.hasPrefix("data: ") {
        // append to progress log
    }
}
```

---

## Phase 3: Packaging (future)
- Bundle the FastAPI server as a standalone binary via **PyInstaller**
- Place it in `PodcastExtractor.app/Contents/Resources/server`
- Models (~2GB) download on first launch to `~/Library/Application Support/PodcastExtractor/`
- This is a later phase — for now, dev workflow uses `uv run uvicorn` directly
