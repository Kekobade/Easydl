@echo off
setlocal enabledelayedexpansion

echo ======================================================
echo           easydl - Windows 1-Click Installer
echo ======================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 was not found!
    echo Please install Python from https://www.python.org or via winget:
    echo    winget install Python.Python.3.11
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python is installed.
echo.

:: 2. Check / Install ffmpeg via winget
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] ffmpeg is not installed. Attempting installation via winget...
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [WARN] Could not install ffmpeg via winget automatically.
        echo Please install ffmpeg or run: winget install Gyan.FFmpeg
    )
) else (
    echo [OK] ffmpeg is already installed.
)

:: 3. Install Python requirements
echo.
echo [INFO] Installing required Python libraries (rich, yt-dlp, spotdl)...
python -m pip install --upgrade pip
python -m pip install --upgrade rich yt-dlp spotdl
python -m pip install -e "%~dp0"

echo.
echo ======================================================
echo       easydl installation completed successfully!
echo ======================================================
echo.
echo You can now run easydl in Command Prompt or PowerShell:
echo.
echo    easydl
echo.
pause
