// Hey Spotify - Frontend JavaScript

const API_BASE = '';

// State
let currentUser = null;
let mediaRecorder = null;
let audioChunks = [];
let mediaStream = null;

// DOM Elements
const loginSection = document.getElementById('login-section');
const appSection = document.getElementById('app-section');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const userInfo = document.getElementById('user-info');
const userName = document.getElementById('user-name');
const commandInput = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const micIcon = document.getElementById('mic-icon');
const recordingIndicator = document.getElementById('recording-indicator');
const transcribingIndicator = document.getElementById('transcribing-indicator');
const outputLog = document.getElementById('output-log');
const clearLogBtn = document.getElementById('clear-log-btn');
const quickActionBtns = document.querySelectorAll('.btn-action');
const nowPlayingCard = document.getElementById('now-playing-card');
const nowPlayingContent = document.getElementById('now-playing-content');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    loginBtn.addEventListener('click', () => {
        window.location.href = '/auth/login';
    });
    
    logoutBtn.addEventListener('click', async () => {
        await logout();
    });
    
    sendBtn.addEventListener('click', () => {
        handleCommand();
    });
    
    commandInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleCommand();
        }
    });
    
    clearLogBtn.addEventListener('click', () => {
        outputLog.innerHTML = '';
    });
    
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const command = btn.getAttribute('data-command');
            commandInput.value = command;
            handleCommand();
        });
    });
    
    // Voice input - hold to record
    micBtn.addEventListener('mousedown', startRecording);
    micBtn.addEventListener('mouseup', stopRecording);
    micBtn.addEventListener('mouseleave', (e) => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            stopRecording();
        }
    });
    
    // Touch support for mobile
    micBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });
    micBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = await response.json();
            showApp();
        } else {
            showLogin();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLogin();
    }
}

function showLogin() {
    loginSection.classList.remove('hidden');
    appSection.classList.add('hidden');
    userInfo.classList.add('hidden');
}

function showApp() {
    loginSection.classList.add('hidden');
    appSection.classList.remove('hidden');
    userInfo.classList.remove('hidden');
    userName.textContent = currentUser.display_name || currentUser.email || 'User';
}

async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout failed:', error);
    }
    currentUser = null;
    showLogin();
}

async function handleCommand() {
    const command = commandInput.value.trim();
    if (!command) return;
    
    logCommand(command);
    commandInput.value = '';
    
    try {
        const response = await executeCommand(command);
        logResponse(command, response, false);
        
        // Auto-refresh now playing for certain commands
        if (['play', 'pause', 'resume', 'next', 'previous', 'now playing'].some(cmd => command.includes(cmd))) {
            setTimeout(() => refreshNowPlaying(), 500);
        }
    } catch (error) {
        logResponse(command, error.message, true);
    }
}

async function executeCommand(command) {
    // Route all text commands through the assistant endpoint (uses LLM for natural language)
    const response = await fetch(`${API_BASE}/assistant/command`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            command: command
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Command failed');
    }
    
    const result = await response.json();
    
    // Return formatted message from backend
    if (!result.success) {
        throw new Error(result.message);
    }
    
    return result.message;
}

function formatDevices(devices) {
    if (devices.length === 0) {
        return '📱 No devices found. Open Spotify on a device to see it here.';
    }
    
    let output = `📱 Found ${devices.length} device(s):\n\n`;
    devices.forEach(device => {
        const active = device.is_active ? '✓ ' : '  ';
        output += `${active}${device.name} (${device.type})`;
        if (device.volume_percent !== null) {
            output += ` - ${device.volume_percent}%`;
        }
        output += '\n';
    });
    return output;
}

function formatNowPlaying(state) {
    if (!state.item) {
        return 'Nothing is currently playing';
    }
    
    const track = state.item;
    const artists = track.artists.map(a => a.name).join(', ');
    const status = state.is_playing ? '▶️ Playing' : '⏸️ Paused';
    
    return `${status}\n🎵 ${track.name}\n👤 ${artists}\n💿 ${track.album.name}\n📱 ${state.device.name}`;
}

function formatSearchResults(tracks) {
    if (tracks.length === 0) {
        return '🔍 No tracks found';
    }
    
    let output = `🔍 Found ${tracks.length} track(s):\n\n`;
    tracks.forEach((track, i) => {
        const artists = track.artists.map(a => a.name).join(', ');
        output += `${i + 1}. ${track.name} - ${artists}\n`;
    });
    return output;
}

function logCommand(command) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <div class="log-command">→ ${escapeHtml(command)}</div>
        <div class="log-response">Processing...</div>
    `;
    outputLog.insertBefore(entry, outputLog.firstChild);
}

function logResponse(command, response, isError) {
    const entries = outputLog.querySelectorAll('.log-entry');
    if (entries.length > 0) {
        const lastEntry = entries[0];
        const responseDiv = lastEntry.querySelector('.log-response');
        responseDiv.textContent = response;
        responseDiv.className = `log-response ${isError ? 'error' : 'success'}`;
        
        const time = document.createElement('div');
        time.className = 'log-time';
        time.textContent = new Date().toLocaleTimeString();
        lastEntry.appendChild(time);
    }
}

async function refreshNowPlaying() {
    try {
        const response = await fetch(`${API_BASE}/spotify/now-playing`, {
            credentials: 'include'
        });
        
        if (!response.ok) return;
        
        const state = await response.json();
        if (state && state.item) {
            displayNowPlaying(state);
        } else {
            nowPlayingCard.classList.add('hidden');
        }
    } catch (error) {
        console.error('Failed to refresh now playing:', error);
    }
}

function displayNowPlaying(state) {
    const track = state.item;
    const artists = track.artists.map(a => a.name).join(', ');
    const albumArt = track.album.images && track.album.images.length > 0 
        ? track.album.images[0].url 
        : '';
    
    nowPlayingContent.innerHTML = `
        ${albumArt ? `<img src="${albumArt}" alt="Album art" class="album-art">` : ''}
        <div class="track-info">
            <div class="track-name">${escapeHtml(track.name)}</div>
            <div class="track-artist">${escapeHtml(artists)}</div>
            <div class="track-device">
                ${state.is_playing ? '▶️' : '⏸️'} Playing on ${escapeHtml(state.device.name)}
            </div>
        </div>
    `;
    
    nowPlayingCard.classList.remove('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Voice Input Functions
async function startRecording() {
    if (!currentUser) return;
    
    try {
        // Request microphone permission
        if (!mediaStream) {
            mediaStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 48000
                } 
            });
        }
        
        // Initialize MediaRecorder
        audioChunks = [];
        mediaRecorder = new MediaRecorder(mediaStream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            // Create audio blob
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            // Send to backend
            await transcribeAudio(audioBlob);
        };
        
        // Start recording
        mediaRecorder.start();
        
        // Update UI
        micBtn.classList.add('recording');
        micIcon.textContent = '⏺️';
        recordingIndicator.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        
        let errorMsg = 'Failed to access microphone';
        if (error.name === 'NotAllowedError') {
            errorMsg = 'Microphone permission denied. Please enable it in your browser settings.';
        } else if (error.name === 'NotFoundError') {
            errorMsg = 'No microphone found. Please connect a microphone and try again.';
        }
        
        logResponse('voice', errorMsg, true);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        
        // Update UI
        micBtn.classList.remove('recording');
        micBtn.classList.add('processing');
        micIcon.textContent = '🎤';
        recordingIndicator.classList.add('hidden');
        transcribingIndicator.classList.remove('hidden');
    }
}

async function transcribeAudio(audioBlob) {
    try {
        // Validate audio size (25MB max)
        const maxSize = 25 * 1024 * 1024;
        if (audioBlob.size > maxSize) {
            throw new Error(`Audio file too large (${(audioBlob.size / 1024 / 1024).toFixed(1)}MB). Maximum is 25MB.`);
        }
        
        if (audioBlob.size === 0) {
            throw new Error('No audio recorded. Please hold the button and speak.');
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        // Send to backend with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout
        
        const response = await fetch(`${API_BASE}/voice/command`, {
            method: 'POST',
            credentials: 'include',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            let errorMsg = 'Transcription failed';
            try {
                const error = await response.json();
                errorMsg = error.detail || errorMsg;
            } catch {}
            
            // Handle specific error codes
            if (response.status === 401) {
                errorMsg = 'Please log in again';
                // Optionally redirect to login
            } else if (response.status === 413) {
                errorMsg = 'Audio file too large. Try recording a shorter message.';
            } else if (response.status === 500) {
                errorMsg = 'Server error. Please try again.';
            }
            
            throw new Error(errorMsg);
        }
        
        const result = await response.json();
        
        // Log the transcript
        logCommand(`🎤 "${result.transcript}"`);
        
        // Display result
        if (result.success) {
            logResponse(`voice: ${result.transcript}`, result.message, false);
        } else {
            logResponse(`voice: ${result.transcript}`, result.message, true);
        }
        
        // Show latency breakdown
        const latency = result.latency_breakdown;
        console.log('Voice command latency:', {
            transcribe: `${latency.transcribe_ms}ms`,
            execute: `${latency.execute_ms}ms`,
            total: `${latency.total_ms}ms`
        });
        
        // Auto-refresh now playing for relevant commands
        if (['play', 'pause', 'resume', 'next', 'previous', 'queue'].some(cmd => 
            result.transcript.toLowerCase().includes(cmd))) {
            setTimeout(() => refreshNowPlaying(), 500);
        }
        
    } catch (error) {
        console.error('Transcription error:', error);
        
        let errorMsg = error.message;
        
        // Handle network errors
        if (error.name === 'AbortError') {
            errorMsg = 'Request timed out. Please try again with a shorter recording.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMsg = 'Network error. Please check your connection and try again.';
        }
        
        logResponse('voice', `❌ ${errorMsg}`, true);
    } finally {
        // Reset UI
        micBtn.classList.remove('processing');
        transcribingIndicator.classList.add('hidden');
    }
}

// Auto-refresh now playing every 5 seconds
setInterval(() => {
    if (currentUser) {
        refreshNowPlaying();
    }
}, 5000);
