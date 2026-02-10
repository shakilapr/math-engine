@echo off
echo Starting MathEngine...

start "MathEngine Backend" cmd /k "cd backend && python main.py"
start "MathEngine Frontend" cmd /k "cd frontend && bun run dev"

echo Services started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
