@echo off
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "%~dp0python\python.exe" (
        set "PYTHON=%~dp0python\python.exe"
    ) else (
        echo.
        echo Vid2Script requires Python but it was not found.
        echo.
        echo Run SETUP.bat first to download Python + FFmpeg automatically.
        echo.
        pause
        exit /b 1
    )
) else (
    set "PYTHON=python"
)

cd /d "%~dp0"
%PYTHON% vid2script.py
pause