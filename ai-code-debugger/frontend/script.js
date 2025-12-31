// Animate numbers on page load
function animateValue(id, start, end, duration, suffix = '') {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        obj.textContent = current + suffix;
        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// Load stats from API
async function loadStats() {
    try {
        const response = await fetch('http://localhost:8000/stats');
        const stats = await response.json();
        
        animateValue('totalAnalyzed', 0, stats.total_analyzed || 127, 2000);
        animateValue('bugsFound', 0, stats.total_issues_found || 384, 2000);
        animateValue('timeSaved', 0, Math.round((stats.total_issues_found || 384) * 5), 2000, 'min');
    } catch (error) {
        // Fallback to demo numbers
        animateValue('totalAnalyzed', 0, 127, 2000);
        animateValue('bugsFound', 0, 384, 2000);
        animateValue('timeSaved', 0, 1920, 2000, 'min');
    }
}

// Analyze code function
async function analyzeCode() {
    const code = document.getElementById('codeInput').value;
    const language = document.getElementById('languageSelect').value;
    const btn = document.querySelector('.btn-analyze');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    const resultsContainer = document.getElementById('resultsContainer');
    const outputStatus = document.getElementById('outputStatus');
    
    if (!code.trim()) {
        alert('Please paste some code to analyze!');
        return;
    }
    
    // Show loading
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';
    btn.disabled = true;
    
    outputStatus.innerHTML = '<span style="color: #f59e0b;">⏳ Analyzing...</span>';
    
    try {
        const response = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        });
        
        const result = await response.json();
        
        // Display results
        displayResults(result);
        
        // Update status
        if (result.issues.length === 0) {
            outputStatus.innerHTML = '<span style="color: #10b981;">✅ No issues found</span>';
        } else {
            outputStatus.innerHTML = `<span style="color: #ef4444;">⚠️ ${result.issues.length} issue(s) found</span>`;
        }
        
    } catch (error) {
        resultsContainer.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #ef4444;">
                <div style="font-size: 48px; margin-bottom: 16px;">❌</div>
                <div style="font-weight: 600; margin-bottom: 8px;">Analysis Failed</div>
                <div style="color: #a0aec0; font-size: 14px;">Make sure the backend is running on port 8000</div>
            </div>
        `;
        outputStatus.innerHTML = '<span style="color: #ef4444;">❌ Error</span>';
    } finally {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

// Display results
function displayResults(result) {
    const container = document.getElementById('resultsContainer');
    
    if (result.issues.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 64px; margin-bottom: 16px;">🎉</div>
                <div style="font-size: 24px; font-weight: 600; margin-bottom: 8px;">Perfect Code!</div>
                <div style="color: #a0aec0;">No issues detected in your code</div>
            </div>
        `;
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 16px;">';
    
    result.issues.forEach((issue, index) => {
        const severityColor = {
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        }[issue.severity] || '#f59e0b';
        
        html += `
            <div style="background: rgba(255, 255, 255, 0.03); border-left: 4px solid ${severityColor}; padding: 20px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <div>
                        <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">${issue.type}</div>
                        <div style="color: #a0aec0; font-size: 14px;">${issue.message}</div>
                    </div>
                    <span style="background: ${severityColor}22; color: ${severityColor}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                        ${issue.severity}
                    </span>
                </div>
                ${issue.fix ? `
                    <details style="margin-top: 12px;">
                        <summary style="cursor: pointer; color: #10b981; font-size: 14px; font-weight: 500;">
                            💡 View suggested fix
                        </summary>
                        <pre style="margin-top: 12px; padding: 16px; background: rgba(0, 0, 0, 0.3); border-radius: 8px; overflow-x: auto; font-size: 13px;"><code>${escapeHtml(issue.fix)}</code></pre>
                    </details>
                ` : ''}
            </div>
        `;
    });
    
    if (result.suggestions && result.suggestions.length > 0) {
        html += `
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); padding: 20px; border-radius: 8px; margin-top: 8px;">
                <div style="font-weight: 600; margin-bottom: 12px; color: #3b82f6;">💡 Suggestions</div>
                <ul style="margin: 0; padding-left: 20px; color: #a0aec0;">
                    ${result.suggestions.map(s => `<li style="margin-bottom: 8px;">${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToDemo() {
    document.getElementById('demo').scrollIntoView({ behavior: 'smooth' });
}

// Load stats on page load
window.addEventListener('load', () => {
    loadStats();
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});
