/**
 * Main application JavaScript
 */

// DOM elements
const log = document.getElementById("log");
const meetingUrl = document.getElementById("meetingUrl");
const btn = document.getElementById("startBtn");
const leaveBtn = document.getElementById("leaveBtn");
const statusValue = document.getElementById("statusValue");
const statusDot = document.getElementById("statusDot");
const joiningBanner = document.getElementById("joiningBanner");
const zoomBanner = document.getElementById("zoomBanner");

// Analysis controls
const analyzeBtn = document.getElementById("analyzeBtn");
const createDiagramBtn = document.getElementById("createDiagramBtn");
const analysisStatus = document.getElementById("analysisStatus");
const analysisResults = document.getElementById("analysisResults");
const analysisContent = document.getElementById("analysisContent");

// Miro controls
const loadMiroBtn = document.getElementById("loadMiroBtn");
const refreshMiroBtn = document.getElementById("refreshMiroBtn");
const miroStatus = document.getElementById("miroStatus");
const miroBoardContainer = document.getElementById("miroBoardContainer");
const miroBoard = document.getElementById("miroBoard");
const miroError = document.getElementById("miroError");

// Application state
let lastStatusTimestamp = null;
let currentBotId = null;
let pollingInterval = null;
let lastTranscriptTime = 0;

/**
 * Update bot status display
 */
function updateStatus(state, eventType = null, timestamp = null) {
    // If we have a timestamp, check if it's newer than the last one
    if (timestamp && lastStatusTimestamp) {
        const newTime = new Date(timestamp);
        const lastTime = new Date(lastStatusTimestamp);
        if (newTime <= lastTime) {
            // Ignore older status updates
            return;
        }
    }
    
    // Update the last timestamp if provided
    if (timestamp) {
        lastStatusTimestamp = timestamp;
    }

    // Update status text and dot
    statusValue.textContent = state;
    statusValue.className = "status-value";
    
    // Reset status dot classes
    statusDot.className = "status-dot";
    
    // Show/hide joining banner
    if (state === "joining") {
        joiningBanner.style.display = "block";
    } else {
        joiningBanner.style.display = "none";
    }
    
    // Show/hide leave button based on state
    if (state === "joined_not_recording" || state === "joined_recording") {
        leaveBtn.style.display = "inline-flex";
    } else {
        leaveBtn.style.display = "none";
    }
    
    // Add appropriate CSS class and status dot based on state
    if (state === "ended" || state === "fatal_error" || state === "data_deleted") {
        statusValue.classList.add("status-ended");
        statusDot.classList.add("error");
        btn.disabled = false;
        btn.innerHTML = 'Launch Bot';
        currentBotId = null;
        stopPolling();

    } else if (state === "joined_recording") {
        statusValue.classList.add("status-running");
        statusDot.classList.add("active");
    } else if (state === "ready" || state === "joining" || state === "joined_not_recording" || 
               state === "leaving" || state === "post_processing" || state === "waiting_room") {
        statusValue.classList.add("status-starting");
        statusDot.classList.add("starting");
    }
}

/**
 * Leave bot from meeting
 */
async function leaveBot() {
    if (!currentBotId) return;
    
    leaveBtn.disabled = true;
    leaveBtn.innerHTML = 'Leaving...';
    stopPolling(); // Stop polling when leaving
    
    try {
        const resp = await fetch(`/api/leave/${currentBotId}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });
        
        if (!resp.ok) {
            alert("Failed to leave: " + (await resp.text()));
            leaveBtn.disabled = false;
            leaveBtn.innerHTML = 'Leave Meeting';
            startPolling(); // Restart polling if leave failed
        } else {
            // Successfully left, reset UI
            btn.disabled = false;
            btn.innerHTML = 'Launch Bot';
            currentBotId = null;
            updateStatus("ended");
        }
    } catch (error) {
        alert("Failed to leave: " + error.message);
        leaveBtn.disabled = false;
        leaveBtn.innerHTML = 'Leave Meeting';
        startPolling(); // Restart polling if leave failed
    }
}

/**
 * Poll bot status
 */
async function pollBotStatus() {
    if (!currentBotId) return;
    
    try {
        const resp = await fetch(`/api/bot-status/${currentBotId}`);
        if (resp.ok) {
            const botData = await resp.json();
            updateStatus(botData.state);
        }
    } catch (error) {
        console.error("Error polling bot status:", error);
    }
}

/**
 * Poll transcripts
 */
async function pollTranscripts() {
    if (!currentBotId) return;
    
    try {
        const resp = await fetch(`/api/transcripts/${currentBotId}`);
        if (resp.ok) {
            const data = await resp.json();
            // The API returns an array directly, not wrapped in a 'transcripts' property
            if (Array.isArray(data)) {
                data.forEach(transcript => {
                    if (transcript.timestamp_ms > lastTranscriptTime) {
                        const ts = new Date(transcript.timestamp_ms).toLocaleTimeString();
                        log.textContent += `[${ts}] ${transcript.speaker_name}: ${transcript.transcription.transcript}\n`;
                        log.scrollTop = log.scrollHeight;
                        lastTranscriptTime = transcript.timestamp_ms;
                    }
                });
            }
        }
    } catch (error) {
        console.error("Error polling transcripts:", error);
    }
}

/**
 * Start polling for status and transcripts
 */
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(async () => {
        await pollBotStatus();
        await pollTranscripts();
    }, 2000); // Poll every 2 seconds
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

/**
 * Launch bot
 */
btn.onclick = async () => {
    const url = meetingUrl.value.trim();
    if (!url) { 
        alert("Enter a meeting URL"); 
        return; 
    }

    btn.disabled = true;
    btn.innerHTML = 'Launching...';
    updateStatus("ready");

    const resp = await fetch("/api/launch", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({meeting_url: url}),
    });

    if (resp.ok) {
        const {bot_id} = await resp.json();
        updateStatus("joining");
        btn.disabled = true;
        btn.innerHTML = 'Launched';
        // reset the leave button
        leaveBtn.disabled = false;
        leaveBtn.innerHTML = 'Leave Meeting';
        currentBotId = bot_id;
        
        // Start polling for status and transcripts
        startPolling();
    } else {
        alert("Failed: " + (await resp.text()));
        btn.disabled = false;
        btn.innerHTML = 'Launch Bot';
        updateStatus("fatal_error");
    }
};

// Tab functionality
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Remove active class from all buttons and panels
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked button and corresponding panel
            btn.classList.add('active');
            document.getElementById(targetTab + 'Tab').classList.add('active');
        });
    });
}

// Initialize tabs when DOM is loaded
document.addEventListener('DOMContentLoaded', initTabs);

// Set up event handlers
leaveBtn.onclick = leaveBot;
