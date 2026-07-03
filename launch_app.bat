@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Missing virtual environment at .venv\Scripts\python.exe
    echo Please create it first or run the setup steps.
    pause
    exit /b 1
)

start "Crop Catalyst Backend" cmd /k "cd /d \"%~dp0\" && .\.venv\Scripts\python.exe backend.py"
start "Crop Catalyst Frontend" cmd /k "cd /d \"%~dp0\" && .\.venv\Scripts\python.exe -m http.server 8000"

rem Give the servers a moment to start
timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:8000/index.html

echo Crop Catalyst launched.
echo Backend: http://127.0.0.1:5000/health
echo Frontend: http://127.0.0.1:8000/index.html
pause
