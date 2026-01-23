# Implementation Tasks

This document tracks the implementation progress for the Hey Spotify voice assistant.

## Milestone 0: Text Command MVP ✅ COMPLETE

### Task 1: Project Setup + FastAPI Skeleton ✅
- [x] Create `pyproject.toml` with dependencies
- [x] Set up core config (`core/config.py`) reading from `.env`
- [x] Create FastAPI app in `apps/api/main.py`
- [x] Add health check router (`/healthz`)
- [x] Implement request ID middleware
- [x] Implement timing middleware for `Server-Timing` headers
- [x] Set up JSON structured logging with request_id, path, latency_ms
- [x] Create `.env.example` with required variables
- [x] Add `.gitignore` for Python, .env, *.db

**Status:** ✅ Complete

### Task 2: Spotify OAuth PKCE Flow ✅
- [x] Implement PKCE helper (`services/auth/pkce.py`)
- [x] Create SQLite schema (`storage/models.py`)
- [x] Implement token store (`services/auth/token_store.py`)
- [x] Build OAuth flow (`services/auth/spotify_oauth.py`)
- [x] Create auth router (`apps/api/routers/auth.py`)
  - [x] `GET /auth/login`
  - [x] `GET /auth/callback`
  - [x] `GET /auth/me`
  - [x] `POST /auth/logout`
- [x] Add session management via cookies

**Status:** ✅ Complete

### Task 3: Spotify API Client with Retries + Rate Limiting ✅
- [x] Create Spotify HTTP client (`services/spotify/client.py`)
  - [x] httpx.AsyncClient with timeout (10s)
  - [x] Exponential backoff on 5xx errors (max 3 retries)
  - [x] Handle 429 rate limits with `Retry-After`
  - [x] Automatic token refresh on 401
  - [x] Structured logging for all requests
- [x] Define Pydantic models (`services/spotify/models.py`)
- [x] Add error types (`core/errors.py`)
- [x] Implement backoff utilities (`core/rate_limit.py`)

**Status:** ✅ Complete

### Task 4: Spotify Playback + Device Endpoints ✅
- [x] Implement device service (`services/spotify/devices.py`)
  - [x] `get_devices()` - List available devices
  - [x] `transfer_playback()` - Switch active device
  - [x] `get_active_device()` - Get current device
- [x] Implement playback service (`services/spotify/playback.py`)
  - [x] `get_current_playback()` - Get now playing
  - [x] `play()` - Start playback
  - [x] `pause()` - Pause playback
  - [x] `resume()` - Resume playback
  - [x] `skip_next()` - Next track
  - [x] `skip_previous()` - Previous track
  - [x] `add_to_queue()` - Queue track
  - [x] `set_volume()` - Set volume
- [x] Implement search service (`services/spotify/search.py`)
  - [x] `search_tracks()` - Search for tracks
  - [x] `search_artists()` - Search for artists
- [x] Create Spotify router (`apps/api/routers/spotify.py`)
  - [x] `GET /spotify/devices`
  - [x] `GET /spotify/now-playing`
  - [x] `POST /spotify/play`
  - [x] `POST /spotify/pause`
  - [x] `POST /spotify/resume`
  - [x] `POST /spotify/next`
  - [x] `POST /spotify/previous`
  - [x] `POST /spotify/queue`
  - [x] `GET /spotify/search/tracks`
- [x] Handle "no active device" errors gracefully

**Status:** ✅ Complete

### Task 5: Web UI (Text Command Console) ✅
- [x] Create single-page web UI (`web/index.html`)
  - [x] Login button → redirects to `/auth/login`
  - [x] Command input field
  - [x] Quick action buttons
  - [x] Output log showing JSON responses
  - [x] Display current user info
  - [x] Now playing display
- [x] Add JavaScript (`web/app.js`)
  - [x] Fetch API calls to backend
  - [x] Command parser and router
  - [x] Response formatting
  - [x] Auto-refresh now playing
- [x] Add CSS (`web/styles.css`)
  - [x] Spotify-inspired dark theme
  - [x] Responsive design
- [x] Serve static files from FastAPI

**Status:** ✅ Complete

### Task 6: Intent System Foundation (Rules-Based) ✅
- [x] Define intent JSON schema (`services/intent/schema.py`)
  - [x] Intent types enum
  - [x] IntentArgs model
  - [x] Intent model with validation
  - [x] IntentResponse model
- [x] Implement rule-based parser (`services/intent/rules.py`)
  - [x] Regex patterns for all commands
  - [x] Query extraction
  - [x] Intent confidence scoring
- [x] Create LLM compiler stub (`services/intent/llm_compiler.py`)
- [x] Add example utterances (`services/intent/examples.yaml`)
- [x] Create assistant resolver (`services/assistant/resolver.py`)
  - [x] Query to Spotify URI resolution
- [x] Create executor (`services/assistant/executor.py`)
  - [x] Execute all intent types
  - [x] Error handling
  - [x] Response formatting
- [x] Create orchestrator (`services/assistant/orchestrator.py`)
  - [x] End-to-end command flow
  - [x] Logging and monitoring
- [x] Add assistant router (`apps/api/routers/assistant.py`)
  - [x] `POST /assistant/command`

**Status:** ✅ Complete

### Task 7: Documentation + Demo ✅
- [x] Write comprehensive README.md
  - [x] Prerequisites
  - [x] Setup instructions
  - [x] Spotify app creation guide
  - [x] Usage examples
  - [x] Architecture diagram
  - [x] API documentation
  - [x] Troubleshooting guide
  - [x] Roadmap
- [x] Create TASKS.md with detailed checklist
- [x] Add docstrings to all public functions
- [x] Create demo script

**Status:** ✅ Complete

---

## Milestone 1: Push-to-Talk Voice ✅ COMPLETE

### Task 8: Web Audio Capture ✅
- [x] Add MediaRecorder API integration
- [x] Push-to-talk button in UI
- [x] Audio recording and chunking (WebM Opus)
- [x] Touch support for mobile

### Task 9: Whisper Integration ✅
- [x] OpenAI Whisper API client (`services/voice/whisper.py`)
- [x] Audio file upload handling
- [x] Transcription error handling
- [x] Latency measurement (<2s p95)

### Task 10: Voice Router ✅
- [x] Voice endpoint (`apps/api/routers/voice.py`)
- [x] `POST /voice/transcribe` - Upload audio
- [x] `POST /voice/command` - Audio → transcript → execute
- [x] Latency breakdown tracking

### Task 11: UI Updates ✅
- [x] Microphone button with recording indicator
- [x] Recording/transcribing state indicators
- [x] Voice response display in output log
- [x] Latency metrics in console
- [x] Error handling with user-friendly messages

**Status:** ✅ Complete

---

## Milestone 2: LLM Intent Compiler 🔮

### Task 12: OpenAI Integration
- [ ] Implement `services/intent/llm_compiler.py`
- [ ] GPT-4 API client with structured output
- [ ] Prompt engineering for intent extraction
- [ ] JSON schema validation

### Task 13: Intent Prompt Engineering
- [ ] Create system prompt for intent parsing
- [ ] Add few-shot examples from `examples.yaml`
- [ ] Test with edge cases
- [ ] Fallback to rules if LLM fails

### Task 14: Disambiguation
- [ ] Handle ambiguous queries
- [ ] Multi-step conversations
- [ ] Context management

---

## Milestone 3: Wake Word Detection 🔮

### Task 15: Porcupine Integration
- [ ] Add Porcupine WASM to web client
- [ ] Wake word detection ("Hey Spotify")
- [ ] Streaming audio pipeline
- [ ] Wake word activation UI

### Task 16: Always-On Pipeline
- [ ] Background mic listening
- [ ] Wake word → record → transcribe
- [ ] Privacy controls

---

## Milestone 4: Production Scalability 🔮

### Task 17: Caching Layer
- [ ] Redis for token caching
- [ ] Device list caching (short TTL)
- [ ] Search result caching

### Task 18: Observability
- [ ] OpenTelemetry integration
- [ ] Distributed tracing spans
- [ ] Metrics export (Prometheus)
- [ ] Dashboard (Grafana)

### Task 19: Reliability
- [ ] Circuit breakers
- [ ] Idempotency keys
- [ ] Queue for async operations
- [ ] Health checks with dependencies

### Task 20: Testing & Benchmarks
- [ ] Load testing scripts (Locust)
- [ ] Latency benchmarks
- [ ] Integration tests
- [ ] E2E tests with Playwright

---

## Current Status

**Milestone 0:** ✅ Complete (7/7 tasks)  
**Milestone 1:** ✅ Complete (4/4 tasks)  
**Milestone 2:** 🔮 Planned (0/3 tasks)  
**Milestone 3:** 🔮 Planned (0/2 tasks)  
**Milestone 4:** 🔮 Planned (0/4 tasks)

**Total Progress:** 11/20 tasks complete (55%)

---

## Notes

- All Milestone 0 tasks are complete and tested
- The architecture is designed to easily accommodate future milestones
- Intent system has both rules (M0) and LLM (M2) paths ready
- Rate limiting and retries are production-grade from day 1
- Next priority: Milestone 1 (voice input)
