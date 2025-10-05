/**
 * Analysis functionality
 */

/**
 * Analyze conversation with Gemini AI
 */
async function analyzeConversation() {
    if (!currentBotId) {
        alert("No active bot. Please start a meeting first.");
        return;
    }
    
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";
    analysisStatus.textContent = "Analyzing conversation with Gemini AI...";
    
    try {
        const resp = await fetch(`/api/analyze-conversation/${currentBotId}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });
        
        const result = await resp.json();
        
        if (resp.ok && !result.error) {
            displayAnalysisResults(result);
            analysisStatus.textContent = "Analysis completed successfully!";
            analysisStatus.style.color = "#28a745";
        } else {
            analysisStatus.textContent = `Analysis failed: ${result.error || 'Unknown error'}`;
            analysisStatus.style.color = "#dc3545";
        }
    } catch (error) {
        analysisStatus.textContent = `Analysis failed: ${error.message}`;
        analysisStatus.style.color = "#dc3545";
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze";
    }
}

/**
 * Create Miro diagram from analysis
 */
async function createMiroDiagram() {
    if (!currentBotId) {
        alert("No active bot. Please start a meeting first.");
        return;
    }
    
    createDiagramBtn.disabled = true;
    createDiagramBtn.textContent = "Creating...";
    analysisStatus.textContent = "Creating Miro diagram...";
    
    try {
        const resp = await fetch(`/api/create-diagram/${currentBotId}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });
        
        const result = await resp.json();
        
        if (resp.ok && result.diagram && result.diagram.success) {
            analysisStatus.textContent = "Miro diagram created successfully!";
            analysisStatus.style.color = "#28a745";
            
            // Show the Miro board URL
            const miroLink = document.createElement("a");
            miroLink.href = result.diagram.board_url;
            miroLink.target = "_blank";
            miroLink.textContent = "Open Miro Board";
            miroLink.style.marginLeft = "10px";
            miroLink.style.color = "#007bff";
            
            analysisStatus.appendChild(miroLink);
            
            // Also display the analysis results
            if (result.analysis && !result.analysis.error) {
                displayAnalysisResults(result.analysis);
            }
            
            // Auto-refresh the embedded board if it's loaded
            if (miroBoardContainer.style.display !== "none" && miroBoard.src) {
                setTimeout(() => {
                    refreshMiroBoard();
                    miroStatus.textContent = "Board updated with new analysis";
                }, 2000); // Wait 2 seconds for the API to process
            }
        } else {
            const errorMsg = result.diagram?.error || result.error || 'Unknown error';
            analysisStatus.textContent = `Diagram creation failed: ${errorMsg}`;
            analysisStatus.style.color = "#dc3545";
        }
    } catch (error) {
        analysisStatus.textContent = `Diagram creation failed: ${error.message}`;
        analysisStatus.style.color = "#dc3545";
    } finally {
        createDiagramBtn.disabled = false;
        createDiagramBtn.textContent = "Create Diagram";
    }
}

/**
 * Display analysis results
 */
function displayAnalysisResults(analysis) {
    let html = "<div style='font-size: 0.9em;'>";
    
    if (analysis.topics && analysis.topics.length > 0) {
        html += "<h4>📋 Key Topics</h4><ul>";
        analysis.topics.slice(0, 5).forEach(topic => {
            html += `<li><strong>${topic.name}</strong> (${Math.round(topic.importance * 100)}% important)<br><small>${topic.description || ''}</small></li>`;
        });
        html += "</ul>";
    }
    
    if (analysis.decisions && analysis.decisions.length > 0) {
        html += "<h4>✅ Decisions Made</h4><ul>";
        analysis.decisions.slice(0, 3).forEach(decision => {
            html += `<li><strong>${decision.title}</strong><br><small>${decision.description || ''}</small></li>`;
        });
        html += "</ul>";
    }
    
    if (analysis.action_items && analysis.action_items.length > 0) {
        html += "<h4>📝 Action Items</h4><ul>";
        analysis.action_items.slice(0, 5).forEach(item => {
            const priority = item.priority === 'high' ? '🔴' : item.priority === 'medium' ? '🟡' : '🟢';
            html += `<li>${priority} <strong>${item.task}</strong> (${item.assignee || 'Unassigned'})</li>`;
        });
        html += "</ul>";
    }
    
    if (analysis.speakers && analysis.speakers.length > 0) {
        html += "<h4>👥 Speakers</h4><ul>";
        analysis.speakers.forEach(speaker => {
            html += `<li><strong>${speaker.name}</strong> - ${speaker.role || 'Participant'} (${Math.round(speaker.engagement * 100)}% engaged)</li>`;
        });
        html += "</ul>";
    }
    
    html += "</div>";
    
    analysisContent.innerHTML = html;
    analysisResults.style.display = "block";
}

// Set up event handlers
analyzeBtn.onclick = analyzeConversation;
createDiagramBtn.onclick = createMiroDiagram;
