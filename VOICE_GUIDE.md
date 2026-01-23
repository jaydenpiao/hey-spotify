# Voice Input Guide

Complete guide for using voice commands with Hey Spotify.

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Edge, Firefox, or Safari)
- Working microphone
- Internet connection (for Whisper API)
- OpenAI API key configured in `.env`

### First Time Setup

1. **Grant Microphone Permission**
   - When you first click the 🎤 button, your browser will ask for permission
   - Click "Allow" to enable voice input
   - This permission persists for future sessions

2. **Test Your Microphone**
   - Hold the mic button and say "devices"
   - If it works, you'll see your Spotify devices listed
   - If not, see Troubleshooting below

## How to Use

### Push-to-Talk

**Desktop:**
1. Click and **hold** the 🎤 microphone button
2. Speak your command clearly
3. Release the button when done
4. Wait 1-2 seconds for transcription
5. Command executes automatically

**Mobile/Touch:**
1. Touch and **hold** the 🎤 button
2. Speak your command
3. Lift your finger
4. Wait for transcription

### Voice States

| Icon | State | Description |
|------|-------|-------------|
| 🎤 | Ready | Click to start recording |
| ⏺️ | Recording | Speak your command |
| 🔴 | Recording... | Visual indicator showing active recording |
| ⏳ | Transcribing... | Processing your audio |

## Supported Commands

All text commands work via voice:

### Playback
- "play kanye west"
- "play upbeat indie music"
- "pause"
- "resume"
- "next track"
- "previous track"

### Queue
- "queue bohemian rhapsody"
- "add dancing queen to queue"

### Information
- "what's playing"
- "now playing"
- "show devices"
- "list my devices"

### Search
- "search for taylor swift"
- "find bruno mars songs"

## Tips for Best Results

### ✅ Do This
- **Speak clearly** - Enunciate your words
- **Normal pace** - Not too fast, not too slow
- **Quiet environment** - Minimize background noise
- **Short commands** - Keep it under 10 seconds
- **Hold steadily** - Don't release too early
- **Be specific** - "play happy by pharrell" works better than "play that happy song"

### ❌ Avoid This
- Speaking too fast or mumbling
- Recording in loud environments
- Very long commands (>15 seconds)
- Releasing button while still speaking
- Yelling or whispering

## Technical Details

### Audio Specifications
- **Format:** WebM Opus (browser default)
- **Sample Rate:** 48kHz
- **Channels:** Mono
- **Processing:** Echo cancellation + noise suppression enabled
- **Max Length:** ~2 minutes (25MB limit)

### Transcript Processing
The app automatically normalizes voice transcripts to improve matching:
- **Removes punctuation** ("Pause." → "pause")
- **Normalizes case** ("PAUSE" → "pause")
- **Trims whitespace** ("  pause  " → "pause")

This ensures Whisper's punctuation doesn't break commands!

### Latency Breakdown
Typical timings for a 3-second voice command:

| Stage | Time | Description |
|-------|------|-------------|
| Audio Capture | <50ms | Browser records audio |
| Upload | 100-300ms | Send to server |
| Whisper API | 500-1500ms | OpenAI transcription |
| Command Execute | 200-500ms | Spotify API call |
| **Total** | **<2s** | End-to-end latency |

### Browser Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Excellent | Recommended |
| Edge | ✅ Excellent | Chromium-based |
| Firefox | ✅ Good | Works well |
| Safari | ✅ Good | macOS/iOS |
| Opera | ✅ Good | Chromium-based |
| Mobile Chrome | ✅ Good | Touch support |
| Mobile Safari | ✅ Good | Touch support |

## Troubleshooting

### Permission Denied
**Symptom:** "Microphone permission denied" error

**Solution:**
1. Click the 🔒 lock icon in address bar
2. Find "Microphone" permission
3. Change to "Allow"
4. Reload the page

### No Microphone Found
**Symptom:** "No microphone found" error

**Solution:**
1. Check physical connection
2. Test in other apps (e.g., Voice Recorder)
3. Check system settings:
   - **Windows:** Settings → Privacy → Microphone
   - **macOS:** System Preferences → Security & Privacy → Microphone
   - **Linux:** Check `pavucontrol` input devices
4. Try a different browser

### Poor Transcription Accuracy
**Symptom:** Commands transcribed incorrectly

**Solutions:**
- **Speak more clearly** - Enunciate each word
- **Reduce background noise** - Move to quieter area
- **Check microphone** - Ensure it's not muted or too far away
- **Try headset mic** - Usually better quality than laptop mics
- **Slow down slightly** - Give Whisper time to process
- **Use common words** - "play" works better than "put on"

### "Request timed out"
**Symptom:** Error after 30 seconds

**Solution:**
- Check internet connection
- Try shorter recordings (<10 seconds)
- Verify OpenAI API is accessible
- Check server logs for details

### "Audio file too large"
**Symptom:** Upload fails with 413 error

**Solution:**
- Keep recordings under 2 minutes
- Release button sooner
- If consistent, check browser recording settings

### Transcription Succeeds But Command Fails
**Symptom:** Correct transcript but "command not found"

**Solution:**
- Check command syntax in logs
- Try the text version first to verify command works
- Use simpler phrasing (e.g., "play X" not "can you play X")

## Privacy & Security

### What Gets Recorded
- **Audio:** Your voice command (typically 2-5 seconds)
- **Transcript:** Text version from Whisper
- **Metadata:** Timestamp, duration, latency

### What Doesn't Get Recorded
- Audio is **not saved** on the server
- No permanent recording storage
- Audio is deleted after transcription

### Data Flow
1. Browser records audio (stays local until you release button)
2. Audio sent to your backend server
3. Backend forwards to OpenAI Whisper API
4. Whisper returns transcript
5. Audio is discarded (not saved)
6. Transcript used to execute command

### OpenAI Data Usage
- OpenAI may use audio for API improvement (per their terms)
- Audio is not associated with your Spotify account
- See [OpenAI's Privacy Policy](https://openai.com/privacy) for details

## Advanced Usage

### Keyboard Shortcut (Future)
Coming in a future update: Press and hold `Space` to activate voice input without clicking.

### Custom Wake Word (Milestone 3)
Upcoming feature: "Hey Spotify" wake word for hands-free activation.

## Cost Estimate

OpenAI Whisper pricing: **$0.006 per minute**

Typical usage:
- 3-second command = $0.0003 (less than a cent)
- 100 commands/day = $0.03/day = $0.90/month
- 1000 commands/day = $0.30/day = $9/month

Very affordable for personal use!

## Feedback

If voice input isn't working:
1. Check browser console (F12) for errors
2. Look at server logs for backend errors
3. Test with simple commands first ("pause", "devices")
4. Try text version to isolate issue
5. Open a GitHub issue with details

## FAQ

**Q: Can I use this while music is playing?**  
A: Yes, but you may need to pause first or use headphones to avoid feedback.

**Q: Does it work offline?**  
A: No, Whisper API requires internet connection.

**Q: What languages are supported?**  
A: Currently English only, but Whisper supports 90+ languages. Easy to add!

**Q: Can I use a different speech-to-text service?**  
A: Yes! The architecture is modular. Just replace `services/voice/whisper.py`.

**Q: Why is it slower than Siri?**  
A: We wait for full command before processing. Streaming transcription (future) will improve this.

**Q: Can I adjust sensitivity/quality?**  
A: Not yet, but you can modify MediaRecorder settings in `web/app.js`.
