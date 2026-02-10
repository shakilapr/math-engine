# MathEngine

A comprehensive math tutoring engine with Python backend and React frontend.

## Features
- **Step-by-step solutions** with student-friendly explanations
- **Cross-verification** using SymPy, NumPy, and mpmath
- **Multi-provider LLM support** (Gemini, Claude, DeepSeek, OpenAI)
- **Visualization** of functions and data
- **LaTeX & Image input** support

## Setup

### Backend
1. Install [Conda](https://docs.conda.io/en/latest/).
2. Create the environment:
   ```bash
   cd backend
   conda env create -f environment.yml
   conda activate mathengine
   ```
3. Set up .env:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
4. Run the server:
   ```bash
   python main.py
   ```
   Server runs at `http://localhost:8000`.

### Frontend
1. Install [Bun](https://bun.sh/).
2. Install dependencies:
   ```bash
   cd frontend
   bun install
   ```
3. Run dev server:
   ```bash
   bun run dev
   ```
   App runs at `http://localhost:5173`.

## Architecture
- **Backend**: FastAPI, SymPy, NumPy, Matplotlib
- **Frontend**: React, Vite, TailwindCSS, Shadcn UI
- **LLM**: Abstract provider layer for model flexibility
