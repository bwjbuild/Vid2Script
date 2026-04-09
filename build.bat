@echo off
title Vid2Script — Build

echo.
echo ============================================================
echo  Vid2Script .exe Builder
echo ============================================================
echo.
echo  This script will:
echo    1. Check for ffmpeg/
echo    2. Install PyInstaller if needed
echo    3. Build the Vid2Script.exe
echo    4. Done!
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ── Check FFmpeg ──────────────────────────────────────────────
if not exist "ffmpeg\ffmpeg.exe" (
    echo.
    echo [ERROR] FFmpeg not found.
    echo.
    echo   Please run SETUP.bat FIRST to download FFmpeg,
    echo   then run this build.bat again.
    echo.
    pause
    exit /b 1
)

echo [OK] FFmpeg found
echo.

:: ── Install PyInstaller ───────────────────────────────────────
echo Installing PyInstaller...
echo.

:: Check if pip is available
where pip >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing pip first...
    python -m ensurepip --default-pip 2>nul
)

python -m pip install pyinstaller --quiet --upgrade 2>nul

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to install PyInstaller.
    echo   Run:  pip install pyinstaller
    echo   Then re-run this build.bat
    echo.
    pause
    exit /b 1
)

echo [OK] PyInstaller ready
echo.

:: ── Build ─────────────────────────────────────────────────────
echo Building Vid2Script.exe ...
echo.

:: Clean old builds
if exist "build\"   rmdir /s /q "build"   2>nul
if exist "dist\"    rmdir /s /q "dist"    2>nul

pyinstaller vid2script.spec --noconfirm --clean

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed. Check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [SUCCESS] Build complete!
echo ============================================================
echo.
echo   Your .exe is at:
echo   dist\Vid2Script\Vid2Script.exe
echo.
echo   Copy the entire dist\Vid2Script\ folder and share it.
echo   (FFmpeg is bundled inside — no installation needed)
echo.
pause
