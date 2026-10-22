# ==============================================================================
# easydl - PowerShell 1-Click Installer for Windows
# ==============================================================================
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "        easydl - Windows PowerShell Installer         " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python 3 was not found in your PATH." -ForegroundColor Red
    Write-Host "Installing Python via winget..." -ForegroundColor Yellow
    winget install Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
    Write-Host "Please restart your PowerShell window after Python installation finishes." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[OK] Python is installed." -ForegroundColor Green

# 2. Check ffmpeg
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCmd) {
    Write-Host "[INFO] ffmpeg is missing. Installing via winget..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "[OK] ffmpeg is already installed." -ForegroundColor Green
}

# 3. Install Python dependencies
Write-Host "`n[INFO] Installing Python packages (rich, yt-dlp, spotdl)..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install --upgrade rich yt-dlp spotdl
python -m pip install -e "$PSScriptRoot"

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "     easydl installation completed successfully!     " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "You can now run easydl in any terminal by typing: easydl" -ForegroundColor Yellow
Write-Host ""
