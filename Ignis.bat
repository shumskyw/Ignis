@echo off
type ascii_art.txt
echo.
echo Starting Ignis AI Web Server...
echo.
echo To run without opening browser automatically:
echo   python server.py --no-browser
echo.

cd /d %~dp0

REM Kill any existing processes on our ports
echo Checking for existing servers...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing process on port 8000: %%a
    taskkill /f /pid %%a >nul 2>&1
)

timeout /t 1 /nobreak > nul

echo Starting web server...
python server.py

echo.
echo Web server closed.
echo.
pause