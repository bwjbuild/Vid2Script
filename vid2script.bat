@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo Python was not found.
    echo Install Python 3.10+ and run:
    echo   pip install yt-dlp
    echo.
    pause
    exit /b 1
)

python vid2script.py
pause
