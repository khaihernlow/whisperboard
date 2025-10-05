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
    
    if (typeof analyzeBtn !== 'undefined' && analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";
    }
    analysisStatus.textContent = "Analyzing conversation with Gemini AI...";
    
    try {
        const resp = await fetch(`/api/analyze-conversation/${currentBotId}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });
        
        const result = await resp.json();
        
        if (resp.ok && !result.error) {
            displayAnalysisResults(result);
            analysisStatus.textContent = "Analysis completed successfully! Creating diagram...";
            analysisStatus.style.color = "#28a745";

            // Auto-create Miro diagram after successful analysis
            await autoCreateDiagramAndRefresh(result);
        } else {
            analysisStatus.textContent = `Analysis failed: ${result.error || 'Unknown error'}`;
            analysisStatus.style.color = "#dc3545";
        }
    } catch (error) {
        analysisStatus.textContent = `Analysis failed: ${error.message}`;
        analysisStatus.style.color = "#dc3545";
    } finally {
        if (typeof analyzeBtn !== 'undefined' && analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Analyze";
        }
    }
}

/**
 * Create Miro diagram from analysis (manual trigger - no longer exposed in UI)
 */
async function createMiroDiagram() {
    if (!currentBotId) {
        alert("No active bot. Please start a meeting first.");
        return;
    }
    
    if (typeof createDiagramBtn !== 'undefined' && createDiagramBtn) {
        createDiagramBtn.disabled = true;
        createDiagramBtn.textContent = "Creating...";
    }
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
            
            // No iframe refresh needed; Miro updates shortly on its own
        } else {
            const errorMsg = result.diagram?.error || result.error || 'Unknown error';
            analysisStatus.textContent = `Diagram creation failed: ${errorMsg}`;
            analysisStatus.style.color = "#dc3545";
        }
    } catch (error) {
        analysisStatus.textContent = `Diagram creation failed: ${error.message}`;
        analysisStatus.style.color = "#dc3545";
    } finally {
        if (typeof createDiagramBtn !== 'undefined' && createDiagramBtn) {
            createDiagramBtn.disabled = false;
            createDiagramBtn.textContent = "Create Diagram";
        }
    }
}

/**
 * Automatically create diagram and load/refresh Miro board
 */
async function autoCreateDiagramAndRefresh(latestAnalysis) {
    try {
        analysisStatus.textContent = "Creating Miro diagram...";
        const resp = await fetch(`/api/create-diagram/${currentBotId}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });

        const result = await resp.json();

        if (resp.ok && result.diagram && result.diagram.success) {
            analysisStatus.textContent = "Miro diagram created successfully!";
            analysisStatus.style.color = "#28a745";

            if (result.analysis && !result.analysis.error) {
                displayAnalysisResults(result.analysis);
            } else if (latestAnalysis) {
                displayAnalysisResults(latestAnalysis);
            }

            // Load board if not already visible; avoid forced refreshes
            if (miroBoardContainer.style.display === "none" || !miroBoard.src) {
                await loadMiroBoard();
                miroStatus.textContent = "Board loaded";
            }
        } else {
            const errorMsg = result.diagram?.error || result.error || 'Unknown error';
            analysisStatus.textContent = `Diagram creation failed: ${errorMsg}`;
            analysisStatus.style.color = "#dc3545";
        }
    } catch (error) {
        analysisStatus.textContent = `Diagram creation failed: ${error.message}`;
        analysisStatus.style.color = "#dc3545";
    }
}

/**
 * Display analysis results
 */
function displayAnalysisResults(analysis) {
    let html = "<div style='font-size: 0.9em;'>";

    if (analysis.summary && (analysis.summary.frame_name || analysis.summary.blurb)) {
        html += `<h4>🎯 ${analysis.summary.frame_name || 'Conversation'}</h4>`;
        if (analysis.summary.blurb) {
            html += `<p>${analysis.summary.blurb}</p>`;
        }
    }

    if (analysis.topics && analysis.topics.length > 0) {
        html += "<h4>📋 Topics</h4><ul>";
        analysis.topics.slice(0, 6).forEach(t => {
            const name = t.label || t.name || 'Topic';
            const imp = typeof t.importance === 'number' ? ` (${Math.round(t.importance*100)}%)` : '';
            html += `<li><strong>${name}</strong>${imp}<br><small>${t.description || ''}</small></li>`;
        });
        html += "</ul>";
    }

    if (analysis.insights && analysis.insights.length > 0) {
        html += "<h4>🧠 Insights</h4><ul>";
        analysis.insights.slice(0, 6).forEach(i => {
            const ev = (i.evidence && i.evidence.length) ? ` <small>(${i.evidence.slice(0,2).join(', ')})</small>` : '';
            html += `<li><strong>${i.label || 'Insight'}</strong>${ev}</li>`;
        });
        html += "</ul>";
    }

    if (analysis.decisions && analysis.decisions.length > 0) {
        html += "<h4>✅ Decisions</h4><ul>";
        analysis.decisions.slice(0, 5).forEach(d => {
            const why = (d.rationale && d.rationale.length) ? ` <small>Why: ${d.rationale.slice(0,2).join(', ')}</small>` : '';
            html += `<li><strong>${d.label || d.title || 'Decision'}</strong>${why}</li>`;
        });
        html += "</ul>";
    }

    if (analysis.actions && analysis.actions.length > 0) {
        html += "<h4>📝 Actions</h4><ul>";
        analysis.actions.slice(0, 6).forEach(a => {
            const owner = a.owner || 'TBD';
            const due = a.due || 'TBD';
            html += `<li><strong>${a.label || 'Action'}</strong> <small>(${owner} · ${due})</small></li>`;
        });
        html += "</ul>";
    }

    if (analysis.relationships && analysis.relationships.length > 0) {
        html += "<h4>🔗 Relationships</h4><ul>";
        analysis.relationships.slice(0, 8).forEach(r => {
            html += `<li><code>${r.from}</code> → <code>${r.to}</code> <small>(${r.type || 'rel'})</small></li>`;
        });
        html += "</ul>";
    }

    html += "</div>";

    analysisContent.innerHTML = html;
    analysisResults.style.display = "block";
}

// Expose a trigger function for scheduled auto-analysis
async function triggerAutoAnalysis() {
    if (!currentBotId) return;
    // Only run if transcript likely updated since last run is not strictly necessary; backend can decide
    await analyzeConversation();
}
