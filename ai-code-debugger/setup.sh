#!/bin/bash

echo "🚀 Setting up AI Code Debugger"

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
echo "⚠️  Please add your GEMINI_API_KEY to backend/.env"

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo "✅ Backend running on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo ""
echo "📦 To install Chrome extension:"
echo "1. Open Chrome -> chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the 'extension' folder"
echo ""
echo "🎉 Done! Paste some code to test it!"
