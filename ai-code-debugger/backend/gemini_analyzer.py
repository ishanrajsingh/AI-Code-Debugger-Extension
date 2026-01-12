import os
import json
import google.generativeai as genai
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found! Create a .env file with your API key.")
else:
    print("Gemini API key loaded.")
genai.configure(api_key=gemini_api_key)
gemini_client = genai.GenerativeModel('gemini-2.5-flash-lite')

class GeminiAnalyzer:
    """Analyzes code using Gemini 2.0 Flash via Google AI Studio"""

    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and auto-detect language"""

        prompt = f"""
You are an expert code reviewer and language detector.

Code:
{code}

Return ONLY valid JSON:
{{
  "detected_language": "python",
  "issues": [
    {{
      "type": "Issue Name",
      "message": "Description",
      "line": 1,
      "severity": "error|warning|info",
      "fix": "Fixed code"
    }}
  ],
  "suggestions": ["Improvement idea"],
  "ai_generated_probability": 0.15
}}
"""

        try:
            print(f"Sending to Gemini for analysis...")
            
            response = await gemini_client.generate_content_async(prompt)
            response_text = response.text.strip()

            # Remove markdown fences safely
            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "")
                response_text = response_text.replace("```", "").strip()

            result = json.loads(response_text)

            # Normalize language
            detected_lang = result.get("detected_language", "unknown").lower().strip()
            lang_map = {
                "htm": "html",
                "js": "javascript",
                "ts": "typescript",
                "py": "python",
                "c++": "cpp",
                "c#": "csharp",
                "golang": "go",
                "shell": "bash",
                "sh": "bash",
            }
            result["detected_language"] = lang_map.get(detected_lang, detected_lang)

            # Get AI probability from Gemini or fallback to pattern detection
            ai_prob = result.get("ai_generated_probability", 0.0)
            
            if ai_prob == 0.0 or "ai_generated_probability" not in result:
                print(f"Gemini didn't provide AI probability, using pattern detection...")
                ai_prob = self._detect_ai_patterns(code)
                result["ai_generated_probability"] = ai_prob
            
            print(f"Detected: {result['detected_language']}")
            print(f"AI Probability: {ai_prob:.2f} ({int(ai_prob * 100)}%)")
            print(f"{self._get_ai_reasoning(code, ai_prob)}")

            return result

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            ai_prob = self._detect_ai_patterns(code)
            return {
                "detected_language": self._fallback_detect(code),
                "issues": [],
                "suggestions": ["Unable to parse model response"],
                "ai_generated_probability": ai_prob,
            }

        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                "detected_language": self._fallback_detect(code),
                "issues": [],
                "suggestions": [],
                "ai_generated_probability": 0.0,
            }

    # ---------- ALL HELPER METHODS SAME AS BEFORE ---------- #

    def _extract_language_from_text(self, text: str, code: str) -> str:
        text = text.lower()
        for lang in ["html", "css", "javascript", "python", "java", "cpp", "typescript", "php", "ruby", "go", "rust"]:
            if lang in text:
                return lang
        return self._fallback_detect(code)

    def _fallback_detect(self, code: str) -> str:
        c = code.lower()
        if "<html" in c or "<div" in c:
            return "html"
        if "def " in c or "import " in c:
            return "python"
        if "function" in c or "=>" in c or "const " in c:
            return "javascript"
        if "#include" in c:
            return "cpp"
        if "public class" in c:
            return "java"
        if "select " in c and " from " in c:
            return "sql"
        if c.startswith("#!/bin/bash"):
            return "bash"
        return "plaintext"

    def _get_ai_reasoning(self, code: str, probability: float) -> str:
        """Get human-readable reasoning for AI probability"""
        c = code.lower()
        patterns = []

        if "here's" in c or "here is" in c:
            patterns.append("teaching comments ('here's')")
        if "this function" in c:
            patterns.append("explanatory comments")
        if "todo:" in c or "fixme:" in c:
            patterns.append("TODO/FIXME comments")
        if "example usage" in c or "# example:" in c:
            patterns.append("example markers")
        if "def factorial" in c or "def fibonacci" in c:
            patterns.append("demo algorithms")
        if c.count("result") > 2 or c.count("data") > 2 or c.count("temp") > 2:
            patterns.append("excessive generic variables")
        if "your_api_key" in c or "example.com" in c:
            patterns.append("placeholder values")

        if not patterns:
            return "No AI patterns detected"
        
        return f"AI patterns found: {', '.join(patterns)}"

    def _detect_ai_patterns(self, code: str) -> float:
        """Improved pattern-based AI detection"""
        c = code.lower()
        total_score = 0
        found_patterns = []

        patterns = {
            # STRONG indicators (3 points)
            "here's a": 3,
            "here's how": 3,
            "here is a": 3,
            "this function does": 3,
            "example usage:": 3,
            "example usage": 2,
            "def factorial": 3,
            "def fibonacci": 3,
            "your_api_key": 3,
            "api_key_here": 3,
            
            # MEDIUM indicators (2 points)
            "this function": 2,
            "# example:": 2,
            "// example:": 2,
            "example.com": 2,
            "placeholder": 2,
            "note:": 1.5,
            "important:": 1.5,
            
            # WEAK indicators (1 point)
            "# todo:": 1,
            "// todo:": 1,
            "fixme:": 1,
        }

        for pattern, weight in patterns.items():
            if pattern in c:
                total_score += weight
                found_patterns.append(f"'{pattern}' ({weight}pt)")

        generic_vars = ["result", "data", "temp", "value", "item", "obj"]
        generic_count = sum(c.count(var) for var in generic_vars)
        
        if generic_count > 5:
            total_score += 2
            found_patterns.append(f"generic vars x{generic_count} (2pt)")
        elif generic_count > 3:
            total_score += 1
            found_patterns.append(f"generic vars x{generic_count} (1pt)")

        if '"""' in code:
            docstring_count = code.count('"""')
            if docstring_count >= 2:
                total_score += 1
                found_patterns.append(f"docstrings (1pt)")

        if total_score >= 10:
            probability = 0.85
        elif total_score >= 7:
            probability = 0.75
        elif total_score >= 5:
            probability = 0.6
        elif total_score >= 3:
            probability = 0.4
        elif total_score >= 1:
            probability = 0.25
        else:
            probability = 0.1

        if found_patterns:
            print(f"Pattern detection: {', '.join(found_patterns)}")
            print(f"Total score: {total_score} points → {probability:.2f} ({int(probability * 100)}%)")
        else:
            print(f"No AI patterns detected → default low (0.1)")

        return probability

    async def suggest_fix(self, code: str, error: str) -> str | None:
        prompt = f"""
Fix this error in the code.

Code:
{code}

Error:
{error}

Return ONLY corrected code.
"""

        try:
            response = await gemini_client.generate_content_async(prompt)
            fix = response.text.strip()
            fix = fix.replace("```", "").strip()
            return fix

        except Exception:
            return None

    async def generate_fixed_code(self, code: str, issues: List[Dict[str, Any]]) -> str:
        issues_text = "\n".join(
            [f"- {issue.get('type')}: {issue.get('message')}" for issue in issues]
        )

        prompt = f"""
Fix all issues in this code.

Original code:
{code}

Issues:
{issues_text}

Return ONLY corrected code.
"""

        try:
            response = await gemini_client.generate_content_async(prompt)
            fixed = response.text.strip()
            fixed = fixed.replace("```", "").strip()
            return fixed if fixed else code

        except Exception:
            return code
