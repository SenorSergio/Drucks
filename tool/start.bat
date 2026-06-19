@echo off
REM Druckts? Idea-to-Print — start the configurator service.
REM Double-click this file, then open http://127.0.0.1:8000/konfigurator.html
cd /d "%~dp0"
echo Starting Druckts? Konfigurator ...
echo Open this in your browser:  http://127.0.0.1:8000/konfigurator.html
echo (Press Ctrl+C or close this window to stop.)
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
