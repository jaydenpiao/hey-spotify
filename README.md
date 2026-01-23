# 🎵 Hey Spotify

A Siri-like voice assistant for Spotify with OAuth PKCE authentication, intelligent intent parsing, and production-grade reliability features.

**Current Status:** Milestone 1 Complete ✅ (Push to Talk Command MVP)

https://github.com/user-attachments/assets/0d1917b1-2f22-4458-bd47-33e58501e113


https://github.com/user-attachments/assets/0228aebb-78cd-4d01-8c20-246c6ca60a33

## Features (Milestone 0)

- 🔐 **Spotify OAuth PKCE Flow** - Secure authentication
- 🎮 **Playback Control** - Play, pause, resume, skip, queue
- 📱 **Device Management** - List and switch between Spotify devices
- 🔍 **Search & Play** - Search tracks and start playback instantly
- 🎯 **Intent System** - Rules-based command parsing (LLM upgrade in M2)
- ⚡ **Rate Limit Handling** - Exponential backoff + Retry-After compliance
- 📊 **Production Logging** - Structured JSON logs with request IDs
- 🌐 **Web UI** - Beautiful command console interface

## Prerequisites

- **Python 3.11+**
- **Spotify Premium Account** (required for playback control)
- **Spotify Developer App** (free to create)

## Setup

### 1. Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create an App"
3. Fill in app name and description
4. Once created, note your **Client ID** and **Client Secret**
5. Click "Edit Settings"
6. Add redirect URI: `http://127.0.0.1:8000/auth/callback` (**Important:** Must use `127.0.0.1`, not `localhost` - [Spotify requirement](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri))
7. Save settings

### 2. Set Up Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd hey-spotify

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

## 3. Install Dependencies

```bash
# Install package in development mode
pip install -e .
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate a secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env with your credentials
# Required values:
# - SPOTIFY_CLIENT_ID (from step 1)
# - SPOTIFY_CLIENT_SECRET (from step 1)
# - SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback (must match Spotify Dashboard)
# - SECRET_KEY (paste the generated key above)
```

### 5. Run the Server

```bash
# Start the FastAPI server
uvicorn apps.api.main:app --reload

# Or use Python directly
python -m apps.api.main
```

Server will start at: **http://127.0.0.1:8000**

## Usage

### Web UI

1. Open http://127.0.0.1:8000 in your browser
2. Click "Login with Spotify"
3. Authorize the app
4. Start using commands!

### Voice Input (Milestone 1) 🎤

**Push-to-Talk:**
1. Hold down the microphone button (🎤)
2. Speak your command clearly
3. Release the button
4. Wait for transcription and execution

**Supported Commands:** Same as text commands (play, pause, queue, etc.)

**Browser Support:**
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari (macOS/iOS)

**Tips for Best Results:**
- Speak clearly and not too fast
- Minimize background noise
- Keep commands concise (< 10 seconds)
- Ensure microphone permission is granted

### Supported Commands

| Command | Description | Example |
|---------|-------------|---------|
| `play <query>` | Search and play a track | `play bohemian rhapsody` |
| `pause` | Pause playback | `pause` |
| `resume` | Resume playback | `resume` |
| `next` | Skip to next track | `next` |
| `previous` | Go to previous track | `previous` |
| `queue <query>` | Add track to queue | `queue dancing queen` |
| `devices` | List available devices | `devices` |
| `now playing` | Show current track | `now playing` |
| `search <query>` | Search for tracks | `search taylor swift` |

### Example Session

```
→ devices
  Found 2 devices: MacBook Pro (active), iPhone (inactive)

→ play kanye west stronger
  🎵 Playing: kanye west stronger

→ now playing
  ▶️ Playing
  🎵 Stronger
  👤 Kanye West
  💿 Graduation
  📱 MacBook Pro

→ pause
  ⏸️ Playback paused

→ queue bohemian rhapsody
  ➕ Queued: bohemian rhapsody
```

## API Documentation

Once the server is running, visit:
- **Interactive API Docs:** http://127.0.0.1:8000/docs
- **Alternative Docs:** http://127.0.0.1:8000/redoc

### Key Endpoints

#### Authentication
- `GET /auth/login` - Initiate OAuth flow
- `GET /auth/callback` - OAuth callback
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

#### Spotify Control
- `GET /spotify/devices` - List devices
- `GET /spotify/now-playing` - Current playback state
- `POST /spotify/play?query=...` - Play track
- `POST /spotify/pause` - Pause playback
- `POST /spotify/resume` - Resume playback
- `POST /spotify/queue?query=...` - Add to queue
- `GET /spotify/search/tracks?q=...` - Search tracks

#### Assistant (High-level)
- `POST /assistant/command` - Execute natural language command

## Architecture

```
┌─────────────────┐
│   Web Client    │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │
    HTTP Requests
         │
┌────────▼────────────────────────────────────────┐
│              FastAPI Backend                    │
│  ┌──────────────────────────────────────────┐   │
│  │  Middleware (Request ID, Timing, Logs)   │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐   ┌─────────────┐   │
│  │   Auth   │  │ Spotify  │   │  Assistant  │   │
│  │  Router  │  │  Router  │   │   Router    │   │
│  └────┬─────┘  └────┬─────┘   └──────┬──────┘   │
│       │             │                │          │
│  ┌────▼─────────────▼────────────────▼──────┐   │
│  │          Service Layer                   │   │
│  │  • OAuth PKCE                            │   │
│  │  • Spotify Client (retries/backoff)      │   │
│  │  • Intent Parser (rules → LLM in M2)     │   │
│  │  • Executor                              │   │
│  └──────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────┐  │
│  │       Storage (SQLite)                    │  │
│  │  • Users, Tokens, OAuth Sessions          │  │
│  └───────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────┘
                   │
              Spotify API
                   │
        ┌──────────▼──────────┐
        │   Spotify Servers   │
        └─────────────────────┘
```

## Project Structure

```
hey-spotify/
├── apps/api/               # FastAPI application
│   ├── main.py            # App entry point
│   ├── middleware/        # Request ID, timing
│   └── routers/           # Auth, Spotify, Assistant endpoints
├── core/                  # Core utilities
│   ├── config.py          # Settings management
│   ├── logging.py         # Structured JSON logging
│   ├── errors.py          # Custom exceptions
│   └── rate_limit.py      # Backoff utilities
├── services/              # Business logic
│   ├── auth/              # OAuth PKCE, token management
│   ├── spotify/           # Spotify API client
│   ├── intent/            # Intent parsing (rules + LLM)
│   └── assistant/         # Orchestrator, executor
├── storage/               # Database layer
│   ├── sqlite.py          # SQLite connection
│   └── models.py          # Data models
├── web/                   # Web UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── tests/                 # Unit tests
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Code Quality

The project follows these best practices:
- ✅ Type hints throughout
- ✅ Pydantic models for validation
- ✅ Structured logging with request IDs
- ✅ Exponential backoff for retries
- ✅ Rate limit compliance (429 + Retry-After)
- ✅ Clean separation of concerns
- ✅ Async/await for I/O operations

## Roadmap

### ✅ Milestone 0: Text Command MVP (COMPLETE)
- OAuth PKCE authentication
- Playback control endpoints
- Device management
- Web UI command console

### ✅ Milestone 1: Push-to-Talk Voice (COMPLETE)
- Web audio capture (MediaRecorder API)
- OpenAI Whisper API integration
- End-to-end voice → transcript → action
- Latency instrumentation (<2s p95)
- Error handling for mic permissions and network failures

### 🔮 Milestone 2: LLM Intent Compiler
- OpenAI GPT-4 with structured output
- Replace regex rules with natural language understanding
- Disambiguation handling
- Context-aware commands

### 🔮 Milestone 3: Wake Word Detection
- Porcupine integration (web WASM)
- "Hey Spotify" hotword activation
- Streaming audio pipeline

### 🔮 Milestone 4: Production Scalability
- Redis caching for tokens/devices
- OpenTelemetry distributed tracing
- Circuit breakers
- Load testing & benchmarks

## Troubleshooting

### "No active device" Error

**Problem:** Spotify needs an active device to control playback.

**Solution:**
1. Open Spotify on any device (desktop, mobile, web player)
2. Start playing something
3. Try the command again

### OAuth Callback Issues

**Problem:** Redirect URI mismatch

**Solution:**
1. Verify redirect URI in Spotify Dashboard matches exactly: `http://127.0.0.1:8000/auth/callback` (must use `127.0.0.1`, not `localhost`)
2. Check `.env` file has correct `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback`
3. Restart server after changing environment variables

**Note:** As of April 2025, Spotify [no longer allows `localhost`](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri) in redirect URIs. You must use the loopback IP `127.0.0.1`.

### Microphone Issues (Voice Input)

**Problem:** "Microphone permission denied"

**Solution:**
1. Click the camera/microphone icon in your browser's address bar
2. Allow microphone access for http://127.0.0.1:8000
3. Reload the page
4. Try recording again

**Problem:** "No microphone found"

**Solution:**
1. Check that a microphone is connected
2. Verify it works in other applications
3. Check browser settings (Settings → Privacy → Microphone)
4. Try a different browser

**Problem:** Voice commands not transcribed correctly

**Solution:**
1. Speak more clearly and slowly
2. Move to a quieter environment
3. Check microphone is not muted
4. Try holding the mic button closer to your face
5. Ensure you have a stable internet connection (Whisper API requires network)

**See also:** [VOICE_GUIDE.md](VOICE_GUIDE.md) for comprehensive voice input documentation

### Rate Limiting

The app automatically handles Spotify's rate limits with exponential backoff and respects the `Retry-After` header. You'll see warnings in logs if rate limited.

## Security Notes

- ✅ OAuth state parameter prevents CSRF
- ✅ PKCE prevents authorization code interception
- ✅ HTTPOnly cookies for session management
- ✅ Tokens stored locally (consider encryption for production)
- ✅ Environment variables for secrets
- ⚠️ For production: Add HTTPS, rate limiting per user, token encryption

## Contributing

This is a personal project, but feel free to fork and extend! Areas for improvement:
- Add more intent patterns
- Implement context/conversation state
- Add TTS for responses
- Support playlists and albums
- Multi-user support with proper DB

## License

MIT License - See LICENSE file for details

## Resume Line

> "Built full-stack Spotify voice assistant with OAuth PKCE authentication, push-to-talk voice input (MediaRecorder + OpenAI Whisper), and intelligent command execution. Implemented production-grade features: exponential backoff for API rate limits, structured JSON logging with request IDs, and end-to-end latency instrumentation (<2s p95). Modular architecture supports text and voice input with graceful error handling for microphone permissions and network failures."

## Credits

Built following best practices from:
- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- OAuth 2.0 PKCE specification
