import google.generativeai as genai
from typing import List, Dict, Any
import json
import re


class GeminiAnalyzer:
    """AI-powered code analysis using Gemini"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for potential issues"""

        prompt = f"""
Analyze this {language} code for potential issues, bugs, and improvements.

Code:
{code}

Provide analysis in JSON format:
{{
  "issues": [
    {{
      "type": "Issue Type",
      "message": "Detailed description",
      "line": null,
      "fix": null,
      "severity": "error | warning | info"
    }}
  ],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "ai_generated_probability": 0.0
}}
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Extract JSON safely
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group())

            return {
                "issues": [],
                "suggestions": [],
                "ai_generated_probability": 0.0
            }

        except Exception as e:
            return {
                "issues": [],
                "suggestions": [],
                "ai_generated_probability": 0.0,
                "error": str(e)
            }

    async def suggest_fix(self, code: str, error: str) -> str | None:
        """Generate fix suggestion for specific error"""

        prompt = f"""
Given this code and error, provide a concise fix (code only, no explanations).

Error:
{error}

Code:
{code}

Provide only the corrected code snippet (max 5 lines):
"""

        try:
            response = self.model.generate_content(prompt)
            fix = response.text.strip()

            # Remove markdown code blocks safely
            fix = re.sub(r"```[\w]*", "", fix)
            fix = fix.replace("```", "").strip()

            return fix

        except Exception:
            return None

    async def generate_fixed_code(self, code: str, issues: List[Dict[str, Any]]) -> str:
        """Generate completely fixed version of code"""

        issues_text = "\n".join(
            [f"- {issue.get('type')}: {issue.get('message')}" for issue in issues[:5]]
        )

        prompt = f"""
Fix all issues in this code. Return ONLY the corrected code.

Issues:
{issues_text}

Original code:
{code}

Fixed code:
"""

        try:
            response = self.model.generate_content(prompt)
            fixed = response.text.strip()

            # Remove markdown formatting
            fixed = re.sub(r"```[\w]*", "", fixed)
            fixed = fixed.replace("```", "").strip()

            return fixed if fixed else code

        except Exception:
            return code

    async def is_healthy(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            print("🔍 Testing Gemini API connection...")
            response = self.model.generate_content("Hello")
            print("✅ Gemini response:", response.text[:100])
            return True
        except Exception as e:
            print(f"❌ Gemini API failed: {type(e).__name__}: {str(e)}")
            return False

