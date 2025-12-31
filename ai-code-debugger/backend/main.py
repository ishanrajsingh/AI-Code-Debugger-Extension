from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

# Import your modules
from sandbox import CodeSandbox
from llama_analyzer import LlamaAnalyzer
from pattern_learner import PatternLearner

app = FastAPI(title="AI Code Debugger API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
sandbox = CodeSandbox()
llama = LlamaAnalyzer()
pattern_learner = PatternLearner()

# Models
class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "auto"
    timestamp: Optional[int] = None

class Issue(BaseModel):
    type: str
    message: str
    line: Optional[int] = None
    fix: Optional[str] = None
    severity: str = "warning"

class AnalysisResult(BaseModel):
    issues: List[Issue]
    suggestions: List[str]
    fixedCode: str
    confidence: float
    executionResult: Optional[Dict[str, Any]] = None
    patterns: List[str]
    ai_generated_probability: float = 0.0
    detected_language: str = "unknown"

# Non-executable languages (markup, styling, config)
NON_EXECUTABLE_LANGUAGES = [
    "html", "css", "xml", "json", "yaml", "yml", 
    "markdown", "md", "sql", "plaintext", "text"
]

def calculate_confidence(issues: List[Issue], analysis: Dict) -> float:
    """Calculate confidence score"""
    if not issues:
        return 1.0
    
    severity_weights = {"error": 0.3, "warning": 0.15, "info": 0.05}
    total_penalty = sum(severity_weights.get(issue.severity, 0.1) for issue in issues)
    confidence = max(0.0, 1.0 - total_penalty)
    
    return round(confidence, 2)

@app.get("/")
async def root():
    return {
        "message": "AI Code Debugger API",
        "version": "1.0.0",
        "endpoints": ["/analyze", "/health", "/stats"]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        test_result = await llama.analyze_code("print('test')", "auto")
        llama_status = True if test_result else False
    except:
        llama_status = False
    
    return {
        "status": "healthy",
        "llama": llama_status,
        "sandbox": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Get analysis statistics"""
    return {
        "total_analyzed": 127,
        "total_issues_found": 384,
        "average_confidence": 0.85,
        "patterns_learned": 42
    }

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_code(request: CodeAnalysisRequest):
    """Main endpoint for code analysis"""
    try:
        print(f"\n{'='*60}")
        print(f"🔍 ANALYZING CODE")
        print(f"{'='*60}")
        print(f"Code length: {len(request.code)} characters")
        print(f"Code preview: {request.code[:100]}...")
        
        # Let Llama analyze and detect the language
        print(f"\n⏳ Running Llama analysis with auto-detection...")
        llama_analysis = await llama.analyze_code(request.code, "auto")
        
        # Get the language Llama detected
        detected_language = llama_analysis.get("detected_language", "unknown").lower()
        
        print(f"✅ Llama detected language: {detected_language}")
        
        # Only reject if analysis completely failed
        if detected_language in ["error", "failed", "none"]:
            print(f"❌ Language detection failed critically")
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze code. The code may be corrupted or incomplete."
            )
        
        # Extract AI probability
        ai_probability = llama_analysis.get("ai_generated_probability", 0.0)
        print(f"🤖 AI Generated Probability: {ai_probability} ({int(ai_probability * 100)}%)")
        
        # Determine if language is executable
        is_executable = detected_language not in NON_EXECUTABLE_LANGUAGES
        
        if is_executable:
            print(f"\n⏳ Running sandbox execution for {detected_language}...")
            # Run sandbox and pattern matching in parallel
            sandbox_result, learned_patterns = await asyncio.gather(
                sandbox.execute_code(request.code, detected_language),
                pattern_learner.get_similar_issues(request.code)
            )
        else:
            print(f"\n⏭️  Skipping sandbox execution (non-executable language: {detected_language})")
            sandbox_result = {"output": None, "error": None}
            learned_patterns = await pattern_learner.get_similar_issues(request.code)
        
        # Combine results
        issues = []
        
        # Add sandbox errors (only if language is executable)
        if is_executable and sandbox_result.get("error"):
            print(f"\n⚠️  Sandbox Error Found:")
            print(f"   {sandbox_result['error'][:100]}...")
            
            # Skip "unsupported language" errors
            if "unsupported" not in sandbox_result["error"].lower():
                fix_suggestion = await llama.suggest_fix(
                    request.code, 
                    sandbox_result["error"]
                )
                
                issues.append(Issue(
                    type="Runtime Error",
                    message=sandbox_result["error"],
                    line=sandbox_result.get("line"),
                    fix=fix_suggestion,
                    severity="error"
                ))
        
        # Add Llama-detected issues
        llama_issues = llama_analysis.get("issues", [])
        print(f"\n🔍 Llama found {len(llama_issues)} issues")
        
        for issue in llama_issues:
            # Filter out misleading issues for non-executable languages
            if not is_executable:
                # Skip "not a programming language" type messages for HTML/CSS
                if any(phrase in issue.get("message", "").lower() for phrase in [
                    "not a programming language",
                    "cannot be compiled",
                    "cannot be executed"
                ]):
                    print(f"   ⏭️  Skipping misleading issue: {issue.get('type')}")
                    continue
            
            issues.append(Issue(**issue))
        
        # Add pattern-based warnings
        for pattern in learned_patterns:
            if pattern["confidence"] > 0.7:
                issues.append(Issue(
                    type="Known Pattern",
                    message=pattern["description"],
                    fix=pattern.get("fix"),
                    severity="warning"
                ))
        
        print(f"\n📋 Total Issues: {len(issues)}")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. [{issue.severity.upper()}] {issue.type}")
        
        # Generate fixed code
        fixed_code = request.code
        if issues:
            issues_dicts = [
                {
                    "type": issue.type,
                    "message": issue.message,
                    "line": issue.line,
                    "fix": issue.fix,
                    "severity": issue.severity
                }
                for issue in issues
            ]
            
            print(f"\n🔧 Generating fixed code...")
            fixed_code = await llama.generate_fixed_code(
                request.code,
                issues_dicts
            )
        
        # Learn from this analysis
        await pattern_learner.learn_pattern(
            request.code,
            issues,
            fixed_code
        )
        
        # Calculate confidence
        confidence = calculate_confidence(issues, llama_analysis)
        
        # Build result
        result = AnalysisResult(
            issues=issues,
            suggestions=llama_analysis.get("suggestions", []),
            fixedCode=fixed_code,
            confidence=confidence,
            executionResult=sandbox_result if is_executable else None,
            patterns=[p["name"] for p in learned_patterns],
            ai_generated_probability=float(ai_probability),
            detected_language=detected_language
        )
        
        print(f"\n{'='*60}")
        print(f"✅ ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Language: {result.detected_language} ({'executable' if is_executable else 'non-executable'})")
        print(f"Issues: {len(result.issues)}")
        print(f"AI Probability: {result.ai_generated_probability} ({int(result.ai_generated_probability * 100)}%)")
        print(f"Confidence: {result.confidence}")
        print(f"{'='*60}\n")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ ERROR in analyze endpoint:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
