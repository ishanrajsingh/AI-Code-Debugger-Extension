// CSP-compliant external JavaScript for details page

// Load data from storage when page loads
chrome.storage.local.get(['detailsData'], (result) => {
  console.log('Details data:', result);
  if (result.detailsData) {
    const { lastAnalysis, lastCode } = result.detailsData;
    displayAnalysis(lastAnalysis, lastCode);
  } else {
    console.error('No details data found');
    document.getElementById('issuesList').innerHTML = '<p style="text-align: center; color: #6b7280; padding: 40px;">No analysis data available</p>';
  }
});

function displayAnalysis(analysis, code) {
  console.log('Displaying analysis:', analysis);
  
  // Show AI probability
  const aiProb = analysis.ai_generated_probability || 0;
  if (aiProb > 0) {
    const percent = Math.round(aiProb * 100);
    document.getElementById('aiProbSection').style.display = 'block';
    document.getElementById('aiProbCircle').textContent = percent + '%';
    
    let label;
    if (percent < 30) label = 'Likely Human Code';
    else if (percent < 60) label = 'Possibly AI-Generated';
    else if (percent < 85) label = 'Likely AI-Generated';
    else label = 'Very Likely AI-Generated';
    
    document.getElementById('aiProbLabel').textContent = label;
  }

  // Summary stats
  const issues = analysis.issues || [];
  document.getElementById('totalIssues').textContent = issues.length;
  const errors = issues.filter(i => i.severity === 'error').length;
  const warnings = issues.filter(i => i.severity === 'warning').length;
  document.getElementById('errorCount').textContent = errors;
  document.getElementById('warningCount').textContent = warnings;

  // Issues list
  if (issues.length === 0) {
    document.getElementById('issuesList').innerHTML = '<p style="text-align: center; color: #10b981; padding: 40px; font-size: 18px;">✅ No issues found! Your code looks great.</p>';
  } else {
    const issuesHtml = issues.map((issue, index) => `
      <div class="issue-card ${issue.severity || 'warning'}">
        <div class="issue-header">
          <div class="issue-type">${index + 1}. ${escapeHtml(issue.type)}</div>
          <span class="severity-badge ${issue.severity || 'warning'}">${issue.severity || 'warning'}</span>
        </div>
        <div class="issue-message">${escapeHtml(issue.message)}</div>
        ${issue.fix ? `
          <div class="issue-fix">
            <div class="issue-fix-label">💡 Suggested Fix:</div>
            <pre>${escapeHtml(issue.fix)}</pre>
          </div>
        ` : ''}
      </div>
    `).join('');
    
    document.getElementById('issuesList').innerHTML = issuesHtml;
  }

  // Original code
  document.getElementById('originalCode').textContent = code || 'No code available';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function copyReport() {
  chrome.storage.local.get(['detailsData'], (result) => {
    if (result.detailsData) {
      const { lastAnalysis } = result.detailsData;
      const issues = lastAnalysis.issues || [];
      const report = `AI Code Debugger - Analysis Report
===========================================

Total Issues: ${issues.length}
AI Probability: ${Math.round((lastAnalysis.ai_generated_probability || 0) * 100)}%

Issues:
${issues.map((issue, i) => `${i + 1}. [${(issue.severity || 'warning').toUpperCase()}] ${issue.type}
   ${issue.message}
   ${issue.fix ? 'Fix: ' + issue.fix : ''}`).join('\n\n')}
`;
      
      navigator.clipboard.writeText(report).then(() => {
        alert('📋 Report copied to clipboard!');
      }).catch(err => {
        console.error('Copy failed:', err);
        alert('❌ Failed to copy report');
      });
    }
  });
}

// Add event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Close button
  const closeBtn = document.querySelector('[data-action="close"]');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      window.close();
    });
  }

  // Copy button
  const copyBtn = document.querySelector('[data-action="copy"]');
  if (copyBtn) {
    copyBtn.addEventListener('click', copyReport);
  }
});
