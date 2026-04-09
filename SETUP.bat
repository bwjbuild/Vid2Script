@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Vid2Script - Setup

set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "FFMPEG_DIR=%SCRIPT_DIR%ffmpeg"
set "OUTPUT_DIR=%SCRIPT_DIR%output"
set "LOG_DIR=%SCRIPT_DIR%logs"

set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "TMP_ZIP=%TEMP%\vid2script_ffmpeg.zip"
set "TMP_DIR=%TEMP%\vid2script_ffmpeg_extract"

echo.
echo ============================================================
echo  Vid2Script Setup
echo ============================================================
echo.

echo [1/4] Preparing folders...
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if exist "%FFMPEG_DIR%\ffmpeg.exe" if exist "%FFMPEG_DIR%\ffprobe.exe" (
    echo [OK] FFmpeg already present.
    goto :success
)

echo [2/4] Checking curl availability...
where curl >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] curl was not found on this machine.
    echo Please install curl (or use Windows 10/11 with built-in curl) and retry.
    goto :fail
)

echo [3/4] Downloading FFmpeg...
curl -L --fail --retry 3 --retry-delay 2 -o "%TMP_ZIP%" "%FFMPEG_URL%"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to download FFmpeg.
    echo URL: %FFMPEG_URL%
    goto :fail
)

echo [4/4] Extracting FFmpeg binaries...
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%" >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TMP_ZIP%' -DestinationPath '%TMP_DIR%' -Force"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to extract FFmpeg archive.
    goto :cleanup_fail
)

for /r "%TMP_DIR%" %%f in (ffmpeg.exe) do copy /y "%%f" "%FFMPEG_DIR%\ffmpeg.exe" >nul
for /r "%TMP_DIR%" %%f in (ffprobe.exe) do copy /y "%%f" "%FFMPEG_DIR%\ffprobe.exe" >nul

if not exist "%FFMPEG_DIR%\ffmpeg.exe" (
    echo.
    echo [ERROR] ffmpeg.exe was not found after extraction.
    goto :cleanup_fail
)

if not exist "%FFMPEG_DIR%\ffprobe.exe" (
    echo.
    echo [ERROR] ffprobe.exe was not found after extraction.
    goto :cleanup_fail
)

goto :cleanup_success

:cleanup_success
if exist "%TMP_ZIP%" del /f /q "%TMP_ZIP%" >nul 2>nul
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%" >nul 2>nul
goto :success

:cleanup_fail
if exist "%TMP_ZIP%" del /f /q "%TMP_ZIP%" >nul 2>nul
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%" >nul 2>nul
goto :fail

:success
echo.
echo [SUCCESS] Setup complete.
echo FFmpeg binaries:
echo   %FFMPEG_DIR%\ffmpeg.exe
echo   %FFMPEG_DIR%\ffprobe.exe
set "EXIT_CODE=0"
goto :done

:fail
set "EXIT_CODE=1"

echo.
echo Setup failed.

goto :done

:done
if "%NO_PAUSE%"=="1" exit /b %EXIT_CODE%
pause
exit /b %EXIT_CODE%
