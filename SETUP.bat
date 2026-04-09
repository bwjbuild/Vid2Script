@echo off
echo.
echo Vid2Script Setup — downloading required tools...
echo.

set PYTHON_ZIP=python-3.12.8-embed-amd64.zip
set PYTHON_URL=https://www.nic.funet.fi/pub/misc/python.org/ Distributions/python-3.12.8/python-3.12.8-embed-amd64.zip
set PYTHON_URL_ALT=https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip
set FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%python"
set "FFMPEG_DIR=%SCRIPT_DIR%ffmpeg"
set "PYTHON_ZIP_PATH=%SCRIPT_DIR%%PYTHON_ZIP%"

:: ── Check if already set up ──────────────────────────────────────────────────
if exist "%PYTHON_DIR%\python.exe" (
    if exist "%FFMPEG_DIR%\ffmpeg.exe" (
        echo Python and FFmpeg are already set up.
        echo Run vid2script.bat to start!
        echo.
        pause
        exit /b 0
    )
)

:: ── Download Python Embeddable ───────────────────────────────────────────────
echo Downloading Python 3.12 (Embeddable)...
echo This may take a minute...
echo.
curl -L -o "%PYTHON_ZIP_PATH%" "%PYTHON_URL%" 2>nul
if not exist "%PYTHON_ZIP_PATH%" (
    echo First URL failed, trying alternate...
    curl -L -o "%PYTHON_ZIP_PATH%" "%PYTHON_URL_ALT%" 2>nul
)

if not exist "%PYTHON_ZIP_PATH%" (
    echo.
    echo [FAILED] Could not download Python.
    echo Please download manually:
    echo   %PYTHON_URL_ALT%
    echo.
    echo Save the ZIP next to this SETUP.bat, then run SETUP.bat again.
    echo.
    pause
    exit /b 1
)

echo Extracting Python...
powershell -Command "Expand-Archive -Force '%PYTHON_ZIP_PATH%' '%SCRIPT_DIR%'"
del /f "%PYTHON_ZIP_PATH%" 2>nul

:: Remove python312._pth restriction to allow imports
set "PTH_FILE=%PYTHON_DIR%\python312._pth"
if exist "%PTH_FILE%" (
    powershell -Command "(Get-Content '%PTH_FILE%') -replace '#import site', 'import site' | Set-Content '%PTH_FILE%'"
)

:: ── Download FFmpeg ──────────────────────────────────────────────────────────
echo.
echo Downloading FFmpeg (this may take a few minutes...)...
echo.
curl -L -o "%SCRIPT_DIR%ffmpeg.zip" "%FFMPEG_URL%" 2>nul

if not exist "%SCRIPT_DIR%ffmpeg.zip" (
    echo.
    echo [FAILED] Could not download FFmpeg.
    echo Please download manually:
    echo   %FFMPEG_URL%
    echo.
    echo Save the ZIP next to this SETUP.bat, then run SETUP.bat again.
    echo.
    pause
    exit /b 1
)

echo Extracting FFmpeg...
powershell -Command "Expand-Archive -Force '%SCRIPT_DIR%ffmpeg.zip' '%SCRIPT_DIR%ffmpeg_extract'"
:: Move ffmpeg.exe from nested folder to ffmpeg/
for /r "%SCRIPT_DIR%ffmpeg_extract" %%f in (ffmpeg.exe) do (
    if exist "%%f" (
        move /y "%%f" "%FFMPEG_DIR%\ffmpeg.exe" >nul
    )
)
rmdir /s /q "%SCRIPT_DIR%ffmpeg_extract" 2>nul
del /f "%SCRIPT_DIR%ffmpeg.zip" 2>nul

:: ── Done ────────────────────────────────────────────────────────────────────
echo.
if exist "%PYTHON_DIR%\python.exe" (
    if exist "%FFMPEG_DIR%\ffmpeg.exe" (
        echo [OK] Python ready!
        echo [OK] FFmpeg ready!
        echo.
        echo Setup complete! Run vid2script.bat to start.
    ) else (
        echo [WARNING] FFmpeg not found. Please extract ffmpeg.exe to:
        echo   %FFMPEG_DIR%
    )
) else (
    echo [WARNING] Python not found. Please extract Python to:
    echo   %PYTHON_DIR%
)
echo.
pause
