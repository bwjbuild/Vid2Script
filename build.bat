@echo off
setlocal EnableExtensions
title Vid2Script - Build

set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================================
echo  Vid2Script Windows Build
echo ============================================================
echo.

call "%SCRIPT_DIR%SETUP.bat" --no-pause
if errorlevel 1 goto :fail

set "BOOTSTRAP_PY="
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3.12 -c "import sys" >nul 2>nul
    if %ERRORLEVEL%==0 set "BOOTSTRAP_PY=py -3.12"
)

if not defined BOOTSTRAP_PY (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 set "BOOTSTRAP_PY=python"
)

if not defined BOOTSTRAP_PY (
    echo [ERROR] Python 3.10+ not found.
    echo Install Python from https://www.python.org/downloads/windows/ and retry.
    goto :fail
)

%BOOTSTRAP_PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required.
    goto :fail
)

if not exist ".venv-build\Scripts\python.exe" (
    echo Creating build virtual environment...
    %BOOTSTRAP_PY% -m venv .venv-build
    if errorlevel 1 goto :fail
)

set "PYTHON=.venv-build\Scripts\python.exe"

echo Installing build dependencies...
%PYTHON% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PYTHON% -m pip install -r requirements-build.txt
if errorlevel 1 goto :fail

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Building single-file EXE...
%PYTHON% -m PyInstaller vid2script.spec --noconfirm --clean
if errorlevel 1 goto :fail

if not exist "dist\Vid2Script.exe" (
    echo [ERROR] Build output not found: dist\Vid2Script.exe
    goto :fail
)

echo.
echo [SUCCESS] Build completed.
echo EXE path:
echo   dist\Vid2Script.exe
echo.
echo You can share this single EXE directly.
set "EXIT_CODE=0"
goto :done

:fail
set "EXIT_CODE=1"
echo.
echo Build failed.

goto :done

:done
if "%NO_PAUSE%"=="1" exit /b %EXIT_CODE%
pause
exit /b %EXIT_CODE%
