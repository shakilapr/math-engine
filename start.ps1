Write-Host "Starting MathEngine..." -ForegroundColor Cyan

Start-Process -FilePath "cmd" -ArgumentList "/k cd backend && python main.py" -WindowStyle Normal
Start-Process -FilePath "cmd" -ArgumentList "/k cd frontend && bun run dev" -WindowStyle Normal

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
