const API_BASE_URL = 'http://localhost:8000';

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'CODE_PASTED') {
    analyzeCode(message.code, sender.tab.id);
  }
});

async function analyzeCode(code, tabId) {
  try {
    // Send to backend for analysis
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        language: detectLanguage(code),
        timestamp: Date.now()
      })
    });
    
    const result = await response.json();
    
    // Send results back to content script
    chrome.tabs.sendMessage(tabId, {
      type: 'ANALYSIS_COMPLETE',
      result: result
    });
    
    // Store in local storage for popup
    chrome.storage.local.set({
      lastAnalysis: {
        ...result,
        ai_generated_probability: result.ai_generated_probability || 0
      },
      lastCode: code,
      timestamp: Date.now()
    });
    
    // Update stats
    chrome.storage.local.get(['stats'], (data) => {
      const stats = data.stats || { analyzed: 0, issues: 0, timeSaved: 0 };
      stats.analyzed++;
      stats.issues += result.issues.length;
      stats.timeSaved += result.issues.length * 5; // 5 min per issue
      chrome.storage.local.set({ stats });
    });
    
  } catch (error) {
    console.error('Analysis failed:', error);
    chrome.tabs.sendMessage(tabId, {
      type: 'ANALYSIS_COMPLETE',
      result: {
        issues: [{
          type: 'Connection Error',
          message: 'Could not connect to analysis server. Make sure the backend is running.',
          fix: null,
          severity: 'error'
        }],
        suggestions: [],
        fixedCode: code,
        confidence: 0,
        ai_generated_probability: 0
      }
    });
  }
}

function detectLanguage(code) {
  if (code.includes('def ') || code.includes('import ')) return 'python';
  if (code.includes('function') || code.includes('const ') || code.includes('=>')) return 'javascript';
  if (code.includes('public class') || code.includes('System.out')) return 'java';
  if (code.includes('#include') || code.includes('std::')) return 'cpp';
  return 'python'; // default
}
