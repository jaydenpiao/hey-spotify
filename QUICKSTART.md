# Quick Start Guide

Get Hey Spotify running in 5 minutes!

## 1. Set Up Virtual Environment

```bash
cd hey-spotify

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

## 2. Install Dependencies

```bash
pip install -e .
```

## 3. Create `.env` file

Create a `.env` file in the root directory with:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
SECRET_KEY=your_secret_key_here
DATABASE_PATH=./hey_spotify.db
HOST=0.0.0.0
PORT=8000
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**⚠️ Important:** Use `127.0.0.1` (not `localhost`) - this is a [Spotify requirement](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri) as of April 2025.

## 4. Get Spotify Credentials

1. Go to https://developer.spotify.com/dashboard
2. Click "Create an App"
3. Copy your Client ID and Client Secret
4. Click "Edit Settings"
5. Add Redirect URI: `http://127.0.0.1:8000/auth/callback` (**Must use 127.0.0.1, not localhost**)
6. Save

Paste the credentials into your `.env` file.

## 5. Run the Server

```bash
uvicorn apps.api.main:app --reload
```

## 6. Use the App

1. Open http://127.0.0.1:8000
2. Click "Login with Spotify"
3. Try commands like:
   - `devices`
   - `play kanye west`
   - `now playing`
   - `pause`
   - `queue bohemian rhapsody`

## Troubleshooting

**"No active device"**: Open Spotify on any device and start playing something.

**OAuth errors**: 
- Verify redirect URI in Spotify Dashboard is `http://127.0.0.1:8000/auth/callback` (not localhost)
- Check `.env` file has matching `SPOTIFY_REDIRECT_URI`
- Restart server after changing environment variables

## Run Tests

```bash
pytest
```

That's it! You're ready to control Spotify with text commands. 🎵
