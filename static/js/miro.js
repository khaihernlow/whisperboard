/**
 * Miro board functionality
 */

/**
 * Load Miro board
 */
async function loadMiroBoard() {
    loadMiroBtn.disabled = true;
    loadMiroBtn.innerHTML = 'Loading...';
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
        loadMiroBtn.disabled = false;
        loadMiroBtn.innerHTML = 'Load Board';
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

// Set up event handlers
loadMiroBtn.onclick = loadMiroBoard;
refreshMiroBtn.onclick = refreshMiroBoard;
