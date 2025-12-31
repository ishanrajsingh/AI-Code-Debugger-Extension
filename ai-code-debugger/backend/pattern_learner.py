import json
import hashlib
from typing import List, Dict, Any
from datetime import datetime
import asyncio

class PatternLearner:
    """Learn from past debugging patterns"""
    
    def __init__(self):
        self.patterns = []  # In production, use PostgreSQL
        self.stats = {
            "total_analyzed": 0,
            "total_issues_found": 0,
            "patterns_learned": 0
        }
    
    async def learn_pattern(self, code: str, issues: List[Any], fixed_code: str):
        """Learn from this debugging session"""
        
        if not issues:
            return
        
        pattern = {
            "code_hash": hashlib.md5(code.encode()).hexdigest()[:8],
            "issue_types": [issue.type for issue in issues],
            "timestamp": datetime.now().isoformat(),
            "issue_count": len(issues),
            "fixes_applied": [issue.fix for issue in issues if issue.fix]
        }
        
        self.patterns.append(pattern)
        self.stats["patterns_learned"] += 1
        self.stats["total_analyzed"] += 1
        self.stats["total_issues_found"] += len(issues)
        
        # In production: Store in PostgreSQL
        # await self.db.store_pattern(pattern)
    
    async def get_similar_issues(self, code: str) -> List[Dict[str, Any]]:
        """Find similar issues from past patterns"""
        
        results = []
        
        # Simple pattern matching (in production, use embeddings)
        for pattern in self.patterns[-100:]:  # Last 100 patterns
            similarity = self._calculate_similarity(code, pattern)
            
            if similarity > 0.7:
                results.append({
                    "name": f"Pattern {pattern['code_hash']}",
                    "description": f"Similar to {pattern['issue_count']} previous issues",
                    "confidence": similarity,
                    "fix": pattern["fixes_applied"][0] if pattern["fixes_applied"] else None
                })
        
        return results
    
    def _calculate_similarity(self, code: str, pattern: Dict) -> float:
        """Calculate code similarity (simplified)"""
        # In production: Use embeddings and cosine similarity
        return 0.5  # Placeholder
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return self.stats
    
    async def is_healthy(self) -> bool:
        """Health check"""
        return True
