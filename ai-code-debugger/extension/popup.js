const API_BASE_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadLastAnalysis();
  
  document.getElementById('analyzeBtn').addEventListener('click', analyzeClipboard);
});

async function loadStats() {
  chrome.storage.local.get(['stats', 'lastAnalysis'], (result) => {
    const stats = result.stats || { analyzed: 0, issues: 0, timeSaved: 0 };
    const lastAnalysis = result.lastAnalysis || {};
    
    animateValue(document.getElementById('totalAnalyzed'), 0, stats.analyzed, 1000, '');
    animateValue(document.getElementById('issuesFound'), 0, stats.issues, 1000, '');
    animateValue(document.getElementById('timesSaved'), 0, Math.round(stats.timeSaved), 1000, '');
    
    // Show AI chance from last analysis
    const aiProb = lastAnalysis.ai_generated_probability || 0;
    const aiPercent = Math.round(aiProb * 100);
    animateValue(document.getElementById('aiChance'), 0, aiPercent, 1000, '%');
  });
}

async function loadLastAnalysis() {
  chrome.storage.local.get(['lastAnalysis', 'lastCode', 'timestamp'], (result) => {
    if (result.lastAnalysis) {
      const analysis = result.lastAnalysis;
      const container = document.getElementById('lastAnalysis');
      const aiProbContainer = document.getElementById('aiProbabilityContainer');
      
      console.log('📂 Loading analysis from storage');
      console.log('   Timestamp:', result.timestamp);
      console.log('   Issues:', analysis.issues?.length);
      console.log('   AI Prob:', analysis.ai_generated_probability);
      
      const timeAgo = getTimeAgo(result.timestamp);
      document.getElementById('activityBadge').textContent = timeAgo;
      
      // Show AI Probability if available
      const aiProb = analysis.ai_generated_probability || 0;
      
      if (aiProb > 0) {
        aiProbContainer.style.display = 'block';
        updateAIProbability(aiProb);
      } else {
        aiProbContainer.style.display = 'none';
      }
      
      // Show issues
      const issues = analysis.issues || [];
      const issuesHtml = issues.slice(0, 3).map(issue => `
        <div class="issue-item">
          <strong>${escapeHtml(issue.type)}</strong>
          <p>${escapeHtml(issue.message)}</p>
        </div>
      `).join('');
      
      const viewAllButton = issues.length > 3 ? `
        <button class="view-all-btn" data-action="viewAll">
          <span>View All ${issues.length} Issues →</span>
        </button>
      ` : '';
      
      container.innerHTML = `
        <div class="analysis-result">
          <div class="status-badge ${issues.length === 0 ? 'success' : 'warning'}">
            ${issues.length === 0 ? '✅ No Issues' : `⚠️ ${issues.length} Issue(s)`}
          </div>
          ${issues.length === 0 ? `
            <div style="text-align: center; padding: 24px; color: #10b981; font-size: 16px;">
              <div style="font-size: 48px; margin-bottom: 12px;">✨</div>
              <div style="font-weight: 600;">Code looks great!</div>
            </div>
          ` : issuesHtml}
          ${viewAllButton}
        </div>
      `;
      
      // Add event listener
      if (issues.length > 3) {
        const viewBtn = container.querySelector('[data-action="viewAll"]');
        if (viewBtn) {
          viewBtn.addEventListener('click', viewAllIssues);
        }
      }
    } else {
      console.log('📂 No analysis in storage');
    }
  });
}




// View all issues in new tab
function viewAllIssues(event) {
  event.preventDefault();
  chrome.storage.local.get(['lastAnalysis', 'lastCode'], (result) => {
    if (result.lastAnalysis) {
      console.log('Opening details with data:', result);
      // Store data for details page
      chrome.storage.local.set({ detailsData: result }, () => {
        // Open details page
        chrome.tabs.create({ 
          url: chrome.runtime.getURL('details.html')
        });
      });
    }
  });
}

// Update AI probability display
function updateAIProbability(probability) {
  const percent = Math.round(probability * 100);
  const percentElem = document.getElementById('aiProbPercent');
  const labelElem = document.getElementById('aiProbLabel');
  const fillElem = document.getElementById('aiProbFill');
  
  console.log('Updating AI probability to:', percent + '%');
  
  // Animate percentage
  let currentPercent = 0;
  const increment = Math.ceil(percent / 30);
  const timer = setInterval(() => {
    currentPercent += increment;
    if (currentPercent >= percent) {
      currentPercent = percent;
      clearInterval(timer);
    }
    percentElem.textContent = currentPercent + '%';
  }, 30);
  
  // Update progress bar
  setTimeout(() => {
    fillElem.style.width = percent + '%';
  }, 100);
  
  // Update label based on probability
  let label, className;
  if (percent < 30) {
    label = 'Likely Human';
    className = 'low';
  } else if (percent < 60) {
    label = 'Possibly AI';
    className = 'medium';
  } else if (percent < 85) {
    label = 'Likely AI';
    className = 'high';
  } else {
    label = 'Very Likely AI';
    className = 'very-high';
  }
  
  labelElem.textContent = label;
  labelElem.className = 'ai-prob-label-text ' + className;
}

async function analyzeClipboard() {
  const btn = document.getElementById('analyzeBtn');
  const btnText = btn.querySelector('span');
  const container = document.getElementById('lastAnalysis');
  
  btn.disabled = true;
  btnText.textContent = 'Analyzing...';
  
  // Clear previous results immediately
  container.innerHTML = `
    <div style="text-align: center; padding: 32px; color: #6b7280;">
      <div style="font-size: 48px; margin-bottom: 16px;">⏳</div>
      <div style="font-weight: 600; font-size: 16px;">Analyzing code...</div>
      <div style="font-size: 14px; margin-top: 8px; opacity: 0.7;">This may take a few seconds</div>
    </div>
  `;
  
  try {
    // Read clipboard
    const text = await navigator.clipboard.readText();
    
    if (!text || text.trim().length === 0) {
      showError('Clipboard is empty! Copy some code first.');
      btn.disabled = false;
      btnText.textContent = 'Analyze Clipboard';
      return;
    }
    
    console.log('📋 Clipboard content length:', text.length);
    console.log('📋 First 100 chars:', text.substring(0, 100));
    
    // Check if this is the same code as last time
    const lastCode = await new Promise(resolve => {
      chrome.storage.local.get(['lastCode'], result => resolve(result.lastCode));
    });
    
    if (lastCode === text) {
      console.log('⚠️ Same code as before - forcing re-analysis anyway');
    }
    
    // Force new analysis with timestamp to prevent caching
    const timestamp = Date.now();
    console.log(`🔄 Starting fresh analysis at ${timestamp}`);
    
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'  // Prevent caching
      },
      body: JSON.stringify({
        code: text,
        language: 'auto',
        timestamp: timestamp
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      if (response.status === 400 && errorData.detail) {
        showError(errorData.detail);
      } else {
        showError('Analysis failed: ' + (errorData.detail || 'Unknown error'));
      }
      btn.disabled = false;
      btnText.textContent = 'Analyze Clipboard';
      return;
    }
    
    const result = await response.json();
    
    console.log('✅ Analysis complete!');
    console.log('🌐 Language:', result.detected_language);
    console.log('🤖 AI Probability:', result.ai_generated_probability);
    console.log('🐛 Issues:', result.issues?.length || 0);
    
    // Update stats
    chrome.storage.local.get(['stats'], (data) => {
      const stats = data.stats || { analyzed: 0, issues: 0, timeSaved: 0 };
      stats.analyzed++;
      stats.issues += (result.issues || []).length;
      stats.timeSaved += (result.issues || []).length * 5;
      chrome.storage.local.set({ stats }, () => {
        console.log('📊 Stats updated:', stats);
      });
    });
    
    // Store NEW result with timestamp
    const analysisData = {
      issues: result.issues || [],
      suggestions: result.suggestions || [],
      fixedCode: result.fixedCode || text,
      confidence: result.confidence || 0,
      ai_generated_probability: result.ai_generated_probability || 0,
      detected_language: result.detected_language || 'unknown',
      timestamp: timestamp  // Add timestamp
    };
    
    console.log('💾 Storing new analysis data:', analysisData);
    
    // Force update storage
    chrome.storage.local.set({
      lastAnalysis: analysisData,
      lastCode: text,
      timestamp: timestamp
    }, () => {
      console.log('✅ Storage updated');
      // Force reload to show new data
      loadLastAnalysis();
      loadStats();
    });
    
  } catch (error) {
    console.error('❌ Analysis error:', error);
    showError('Failed to connect to backend. Make sure the server is running on port 8000.');
  } finally {
    btn.disabled = false;
    btnText.textContent = 'Analyze Clipboard';
  }
}


function showError(message) {
  const container = document.getElementById('lastAnalysis');
  container.innerHTML = `
    <div class="error-message">
      <div style="font-size: 32px; margin-bottom: 8px;">❌</div>
      <div style="font-weight: 600; margin-bottom: 4px;">Error</div>
      <div style="font-size: 14px; opacity: 0.9;">${escapeHtml(message)}</div>
    </div>
  `;
}

function showSuccess(message) {
  const container = document.getElementById('lastAnalysis');
  const existingContent = container.innerHTML;
  
  // Show success message temporarily
  container.innerHTML = `
    <div class="success-message">
      <div style="font-size: 32px; margin-bottom: 8px;">✅</div>
      <div style="font-weight: 600; color: #10b981;">${escapeHtml(message)}</div>
    </div>
  `;
  
  // Restore content after 2 seconds
  setTimeout(() => {
    loadLastAnalysis();
  }, 2000);
}

function openDashboard() {
  chrome.tabs.create({ url: 'http://localhost:3000' });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function animateValue(element, start, end, duration, suffix = '') {
  if (!element) return;
  
  const range = end - start;
  if (range === 0) {
    element.textContent = end + suffix;
    return;
  }
  
  const increment = end > start ? 1 : -1;
  const stepTime = Math.abs(Math.floor(duration / range));
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    element.textContent = current + suffix;
    if (current === end) {
      clearInterval(timer);
    }
  }, stepTime);
}

function getTimeAgo(timestamp) {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return 'today';
}
