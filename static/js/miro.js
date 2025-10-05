/**
 * Miro board functionality
 */

/**
 * Load Miro board
 */
async function loadMiroBoard() {
    miroStatus.textContent = "Getting board information...";
    miroError.style.display = "none";
    
    try {
        const response = await fetch('/api/miro-board-info');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Set the iframe source to the embed URL
        miroBoard.src = data.embed_url;
        miroBoardContainer.style.display = "block";
        refreshMiroBtn.style.display = "inline-flex";
        miroStatus.textContent = `Board loaded: ${data.board_id}`;
        
        // Hide placeholder
        const placeholder = document.getElementById('miroPlaceholder');
        if (placeholder) {
            placeholder.style.display = "none";
        }
        
    } catch (error) {
        miroError.textContent = `Failed to load Miro board: ${error.message}`;
        miroError.style.display = "block";
        miroStatus.textContent = "Failed to load board";
    } finally {
    }
}

/**
 * Refresh Miro board
 */
function refreshMiroBoard() {
    if (miroBoard.src) {
        miroBoard.src = miroBoard.src; // Reload the iframe
        miroStatus.textContent = "Board refreshed";
    }
}

// Auto-load the board on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    loadMiroBoard();
});

// Set up event handlers
refreshMiroBtn.onclick = refreshMiroBoard;

// Optional: reset board button handler if present
document.addEventListener('DOMContentLoaded', () => {
    const resetBtn = document.getElementById('resetMiroBtn');
    if (resetBtn) {
        resetBtn.onclick = async () => {
            try {
                resetBtn.disabled = true;
                resetBtn.textContent = 'Resetting...';
                const resp = await fetch('/api/miro/reset', { method: 'POST' });
                if (!resp.ok) throw new Error(await resp.text());
                // After reset, refresh iframe
                refreshMiroBoard();
                miroStatus.textContent = 'Board reset';
            } catch (e) {
                miroError.textContent = `Failed to reset board: ${e.message}`;
                miroError.style.display = 'block';
            } finally {
                resetBtn.disabled = false;
                resetBtn.textContent = 'Reset Board';
            }
        };
    }
});