/**
 * Utility functions
 */

/**
 * Check if URL is a Zoom meeting
 */
function checkZoomUrl() {
    const url = meetingUrl.value.trim().toLowerCase();
    if (url.includes('zoom.us') || url.includes('zoom.com')) {
        zoomBanner.style.display = "block";
    } else {
        zoomBanner.style.display = "none";
    }
}

/**
 * Save meeting URL to localStorage
 */
function saveMeetingUrl() {
    const url = meetingUrl.value.trim();
    if (url) {
        localStorage.setItem('attendee_meeting_url', url);
    }
}

/**
 * Load meeting URL from localStorage
 */
function loadMeetingUrl() {
    const savedUrl = localStorage.getItem('attendee_meeting_url');
    if (savedUrl) {
        meetingUrl.value = savedUrl;
        checkZoomUrl(); // Check if it's a Zoom URL
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load saved URL on page load
    loadMeetingUrl();

    // Check for Zoom URL and save when user types
    meetingUrl.addEventListener('input', () => {
        checkZoomUrl();
        saveMeetingUrl();
    });
    
    meetingUrl.addEventListener('paste', () => {
        setTimeout(() => {
            checkZoomUrl();
            saveMeetingUrl();
        }, 0);
    });
});
