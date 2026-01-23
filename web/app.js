// Hey Spotify - Frontend JavaScript

const API_BASE = '';

// State
let currentUser = null;

// DOM Elements
const loginSection = document.getElementById('login-section');
const appSection = document.getElementById('app-section');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const userInfo = document.getElementById('user-info');
const userName = document.getElementById('user-name');
const commandInput = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');
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
    const cmd = command.toLowerCase();
    
    // Parse command and route to appropriate endpoint
    if (cmd === 'devices') {
        const response = await fetch(`${API_BASE}/spotify/devices`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        const devices = await response.json();
        return formatDevices(devices);
    }
    
    if (cmd === 'now playing' || cmd === 'what\'s playing') {
        const response = await fetch(`${API_BASE}/spotify/now-playing`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        const state = await response.json();
        return state ? formatNowPlaying(state) : 'Nothing is currently playing';
    }
    
    if (cmd === 'pause') {
        const response = await fetch(`${API_BASE}/spotify/pause`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        return '⏸️ Playback paused';
    }
    
    if (cmd === 'resume') {
        const response = await fetch(`${API_BASE}/spotify/resume`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        return '▶️ Playback resumed';
    }
    
    if (cmd === 'next') {
        const response = await fetch(`${API_BASE}/spotify/next`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        return '⏭️ Skipped to next track';
    }
    
    if (cmd === 'previous') {
        const response = await fetch(`${API_BASE}/spotify/previous`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        return '⏮️ Skipped to previous track';
    }
    
    if (cmd.startsWith('play ')) {
        const query = command.substring(5).trim();
        const response = await fetch(`${API_BASE}/spotify/play?query=${encodeURIComponent(query)}`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to play');
        }
        return `🎵 Playing: ${query}`;
    }
    
    if (cmd.startsWith('queue ')) {
        const query = command.substring(6).trim();
        const response = await fetch(`${API_BASE}/spotify/queue?query=${encodeURIComponent(query)}`, {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to queue');
        }
        return `➕ Queued: ${query}`;
    }
    
    if (cmd.startsWith('search ')) {
        const query = command.substring(7).trim();
        const response = await fetch(`${API_BASE}/spotify/search/tracks?q=${encodeURIComponent(query)}&limit=5`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error(await response.text());
        const tracks = await response.json();
        return formatSearchResults(tracks);
    }
    
    throw new Error('Unknown command. Try: play <song>, pause, resume, devices, now playing, queue <song>, search <query>');
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

// Auto-refresh now playing every 5 seconds
setInterval(() => {
    if (currentUser) {
        refreshNowPlaying();
    }
}, 5000);
