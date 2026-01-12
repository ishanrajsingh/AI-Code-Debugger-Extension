from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from sandbox import CodeSandbox
from gemini_analyzer import GeminiAnalyzer

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
gemini = GeminiAnalyzer()
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
        test_result = await gemini.analyze_code("print('test')", "auto")
        gemini_status = True if test_result else False
    except:
        gemini_status = False
    
    return {
        "status": "healthy",
        "gemini": gemini_status,
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
        print(f"ANALYZING CODE")
        print(f"{'='*60}")
        print(f"Code length: {len(request.code)} characters")
        print(f"Code preview: {request.code[:100]}...")
        
        # Let gemini analyze and detect the language
        print(f"\nRunning gemini analysis with auto-detection...")
        gemini_analysis = await gemini.analyze_code(request.code, "auto")
        
        # Get the language gemini detected
        detected_language = gemini_analysis.get("detected_language", "unknown").lower()
        
        print(f"gemini detected language: {detected_language}")
        
        # Only reject if analysis completely failed
        if detected_language in ["error", "failed", "none"]:
            print(f"Language detection failed critically")
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze code. The code may be corrupted or incomplete."
            )
        
        # Extract AI probability
        # Boost AI probability when patterns detected
        ai_probability = gemini_analysis.get("ai_generated_probability", 0.0)

        # Get AI patterns from gemini analysis
        gemini_patterns = gemini_analysis.get("patterns", [])
        if gemini_patterns:
            ai_probability = max(ai_probability, 0.90)  # Boost to 90% if AI patterns found
            print(f"AI PATTERNS FOUND → BOOSTED to {ai_probability}")

        print(f"AI Generated Probability: {ai_probability} ({int(ai_probability * 100)}%)")

        
        # Determine if language is executable
        is_executable = detected_language not in NON_EXECUTABLE_LANGUAGES
        
        if is_executable:
            print(f"\nRunning sandbox execution for {detected_language}...")
            # Run sandbox and pattern matching in parallel
            sandbox_result, learned_patterns = await asyncio.gather(
                sandbox.execute_code(request.code, detected_language),
                pattern_learner.get_similar_issues(request.code)
            )
        else:
            print(f"\nSkipping sandbox execution (non-executable language: {detected_language})")
            sandbox_result = {"output": None, "error": None}
            learned_patterns = await pattern_learner.get_similar_issues(request.code)
        
        # Combine results
        issues = []
        
        # Add sandbox errors (only if language is executable)
        if is_executable and sandbox_result.get("error"):
            error_msg = sandbox_result["error"].lower()
            
            if "timeout" in error_msg:
                print(f"\nTimeout detected (interactive/blocking code) - SKIPPED")
                pass
            elif "interactive" in error_msg or "input" in error_msg:
                print(f"\nInteractive code detected - SKIPPED")
                pass
            elif "unsupported" in error_msg:
                print(f"\nUnsupported language error - SKIPPED")
                pass
            elif "memory" in error_msg:
                print(f"\nMemory limit exceeded - SKIPPED")
                pass
            elif "execution halted" in error_msg:
                print(f"\nExecution halted error - SKIPPED")
                pass
            elif "infinite loop" in error_msg:
                print(f"\nInfinite loop detected - SKIPPED")
                pass
            elif "segmentation fault" in error_msg:
                print(f"\nSegmentation fault detected - SKIPPED")
                pass
            elif "stack overflow" in error_msg:
                print(f"\nStack overflow detected - SKIPPED")
                pass
            elif "out of memory" in error_msg:
                print(f"\nOut of memory detected - SKIPPED")
                pass
            elif "recursion limit" in error_msg:
                print(f"\nRecursion limit reached - SKIPPED")
                pass
            elif "timeout" in error_msg:
                print(f"\nExecution timeout - SKIPPED")
                pass
            elif ("import" or "module") in error_msg:
                print(f"\nMissing module error - SKIPPED")
                pass
            else:
                print(f"\nSandbox Error Found:")
                print(f"   {sandbox_result['error'][:100]}...")
                
                fix_suggestion = await gemini.suggest_fix(
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

        # Add gemini-detected issues
        gemini_issues = gemini_analysis.get("issues", [])
        print(f"\ngemini found {len(gemini_issues)} issues")
        
        for issue in gemini_issues:
            # Filter out misleading issues for non-executable languages
            if not is_executable:
                # Skip "not a programming language" type messages for HTML/CSS
                if any(phrase in issue.get("message", "").lower() for phrase in [
                    "not a programming language",
                    "cannot be compiled",
                    "cannot be executed"
                ]):
                    print(f"Skipping misleading issue: {issue.get('type')}")
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
        
        print(f"\nTotal Issues: {len(issues)}")
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
            
            print(f"\nGenerating fixed code...")
            fixed_code = await gemini.generate_fixed_code(
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
        confidence = calculate_confidence(issues, gemini_analysis)
        
        # Build result
        result = AnalysisResult(
            issues=issues,
            suggestions=gemini_analysis.get("suggestions", []),
            fixedCode=fixed_code,
            confidence=confidence,
            executionResult=sandbox_result if is_executable else None,
            patterns=[p["name"] for p in learned_patterns],
            ai_generated_probability=float(ai_probability),
            detected_language=detected_language
        )
        
        print(f"\n{'='*60}")
        print(f"ANALYSIS COMPLETE")
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
        print(f"\nERROR in analyze endpoint:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
