#!/usr/bin/env bash
# ==============================================================================
# easydl - 1-Click Installer for Linux & macOS
# ==============================================================================
set -e

BOLD='\033[1m'
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ┌──────────────────────────────────────────────────┐"
echo "  │        easydl - Installer (Linux & macOS)        │"
echo "  └──────────────────────────────────────────────────┘"
echo -e "${RESET}"

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3.8+ first.${RESET}"
    exit 1
fi
echo -e "${GREEN}✔ Python 3 found:${RESET} $(python3 --version)"

# 2. Check / Install ffmpeg and yt-dlp
OS_TYPE="$(uname -s)"
echo -e "\n${CYAN}➜ Checking system dependencies (ffmpeg, yt-dlp)...${RESET}"

install_ffmpeg() {
    if command -v ffmpeg &>/dev/null; then
        echo -e "${GREEN}✔ ffmpeg is already installed.${RESET}"
        return
    fi

    echo -e "${YELLOW}ffmpeg not found. Attempting to install...${RESET}"
    if [ "$OS_TYPE" = "Darwin" ]; then
        if command -v brew &>/dev/null; then
            brew install ffmpeg
        else
            echo -e "${RED}Homebrew not found. Please install ffmpeg with: brew install ffmpeg${RESET}"
        fi
    elif [ "$OS_TYPE" = "Linux" ]; then
        if command -v dnf &>/dev/null; then
            sudo dnf install -y ffmpeg
        elif command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y ffmpeg
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm ffmpeg
        else
            echo -e "${YELLOW}Please install ffmpeg manually with your package manager.${RESET}"
        fi
    fi
}

install_ffmpeg

# 3. Install Python dependencies
echo -e "\n${CYAN}➜ Installing Python dependencies (rich, yt-dlp)...${RESET}"
python3 -m pip install --upgrade --user rich yt-dlp

# 4. Install easydl executable
echo -e "\n${CYAN}➜ Installing easydl...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install via pip in editable/user mode
python3 -m pip install --user -e "$SCRIPT_DIR"

# Ensure ~/.local/bin fallback symlink exists
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
ln -sf "$SCRIPT_DIR/easydl.py" "$INSTALL_DIR/easydl"
chmod +x "$SCRIPT_DIR/easydl.py" "$INSTALL_DIR/easydl"

# Check PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}Note: $INSTALL_DIR is not in your current PATH.${RESET}"
    echo -e "Add this to your ~/.bashrc or ~/.zshrc:\n  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo -e "\n${GREEN}${BOLD}✨ easydl installation successfully completed!${RESET}"
echo -e "You can now run ${CYAN}easydl${RESET} in your terminal to launch the interactive menu."
