# 🚀 AI Code Debugger - Chrome Extension
AI Code Debugger is a lightweight Chrome extension designed to simplify and accelerate the debugging process in the era of AI-assisted coding. With the growing use of AI tools for code generation, developers often face challenges in validating code correctness, identifying hidden errors, and understanding whether the code is AI-generated or human-written. Our solution enables users to instantly analyze any code by simply copying it and clicking the “Analyze Clipboard” button. The extension securely sends the code to the Gemini API, which performs deep analysis to detect runtime errors, warnings, potential exceptions, and code quality issues. It also provides intelligent fix suggestions along with a probability score indicating whether the code is AI-generated. By eliminating IDE dependency and supporting all programming languages, AI Code Debugger offers a fast, transparent, and universal debugging experience that enhances developer productivity and trust in AI-generated code.

<img width="1920" height="977" alt="ss_2" src="https://github.com/user-attachments/assets/d798e31e-0e7b-4003-9f33-eef29e5463d2" />

MVP:
https://drive.google.com/drive/folders/1m6aDZ5KxO31Q9WtvxmxdqwAV4q9YH9S7?usp=sharing

---

## 🧩 Problem Statement

With the rapid rise of AI-generated code, developers lack quick tools to verify code correctness, quality, and authorship. Existing debuggers are IDE-dependent, language-specific, and do not provide AI-generated probability insights, leading to slower debugging and reduced trust in AI-assisted development.

---

## 💡 Solution Overview

AI Code Debugger enables developers to analyze any code snippet simply by copying it and clicking **“Analyze Clipboard”**. The extension sends the code to the **Gemini API**, which performs deep analysis and returns:

- Runtime errors and warnings  
- Intelligent fix suggestions  
- Code quality insights  
- AI-generated probability score  
- A structured, detailed analysis report  

All this happens directly inside the browser, without disrupting the developer’s workflow.

---

## ✨ Features

- 📋 Clipboard-based code analysis  
- 🌐 Supports all programming languages  
- 🐞 Runtime error and warning detection  
- 🛠 Intelligent fix suggestions  
- 🤖 AI-generated probability detection  
- 📄 Detailed analysis report generation  
- ⚡ Lightweight Chrome extension (no IDE required)

---

## 🏗 Architecture Overview

**User → Chrome Extension UI → Clipboard Reader → Gemini API (Google GenAI) → Analysis Engine → Results Dashboard → Report Generation**

The Gemini API acts as the central intelligence layer, while Google Cloud ensures secure API key handling.

---

## 🔧 Technologies Used

- **Gemini API (Google Generative AI)** – Core analysis engine  
- **Google Chrome Extensions API** – Browser integration  
- **Google Cloud Platform (GCP)** – Secure API key management  
- **JavaScript / HTML / CSS** – Extension frontend and logic  

---

## 📸 MVP (Minimum Viable Product)

The current MVP demonstrates:
- Working Chrome extension
- Clipboard-based code capture
- Successful Gemini API integration
- Display of errors, fixes, and AI probability
- Generation of a readable analysis report

This validates the feasibility and core value of the solution.

---

## 🚀 Installation & Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ai-code-debugger.git
  Open Chrome and go to:

2. Open Chrome and go to: chrome://extensions
3. Enable Developer Mode
4. Click Load Unpacked and select the project folder
5. Add your Gemini API key in the configuration file
6. Follow instructions in setup.sh
7. Copy any code → Click Analyze Clipboard → View results

## 🔮 Future Enhancements

1. IDE integration (VS Code, IntelliJ)
2. One-click auto-fix for detected issues
3. Multi-model analysis support
4. Enhanced AI-authorship confidence scoring
5. Team dashboards and analytics
6. Offline analysis for privacy-sensitive environments
7. Chrome Web Store deployment

