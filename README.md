# easydl

```text
  ███████╗  █████╗  ███████╗ ██╗   ██╗ ██████╗  ██╗     
  ██╔════╝ ██╔══██╗ ██╔════╝ ╚██╗ ██╔╝ ██╔══██╗ ██║     
  █████╗   ███████║ ███████╗  ╚████╔╝  ██║  ██║ ██║     
  ██╔══╝   ██╔══██║ ╚════██║   ╚██╔╝   ██║  ██║ ██║     
  ███████╗ ██║  ██║ ███████║    ██║    ██████╔╝ ███████╗
  ╚══════╝ ╚═╝  ╚═╝ ╚══════╝    ╚═╝    ╚═════╝  ╚══════╝
```

<p align="center">
  <b>A friendly, Vibe-Coded, high-performance, cross-platform media downloader & library manager.</b><br>
  <i>Powered by <code>yt-dlp</code>, <code>spotdl</code>, <code>ffmpeg</code>, and <code>rich</code>.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-00f2fe?style=for-the-badge&logo=python&logoColor=black" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-4facfe?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/license-MIT-a8ff78?style=for-the-badge&logoColor=black" alt="MIT License" />
  <img src="https://img.shields.io/badge/powered%20by-yt--dlp%20%26%20spotdl-ffd200?style=for-the-badge&logoColor=black" alt="yt-dlp & spotdl" />
</p>

---

## ✨ Features

- 🎨 **Sleek Interactive TUI**: Beautiful modern visual interface powered by Rich with dynamic gradient banners and live badges.
- 🎵 **Multi-Platform Music Suite**: First-class support for **Spotify**, **Apple Music**, **YouTube Music**, and **SoundCloud**.
- 📁 **Automated Playlist & Album Folders**: Downloading any playlist or album (from Spotify, Apple Music, YouTube Music, SoundCloud, or YouTube) automatically creates a clean, dedicated subfolder named after the playlist!
- 🟢 **Dedicated Spotify Client (`spotdl`)**: Powered by `spotdl` for exact audio matching, audio fingerprinting, duration verification, high-res album covers, and full ID3 metadata tagging—preventing mismatched or random videos.
- 🍎 **Native Apple Music Support**: Download songs, albums, and curated playlists directly from Apple Music links with full tag preservation.
- 🔴 **YouTube Music & 🟠 SoundCloud**: Full native extraction of tracks, playlists, sets, and albums.
- 🎶 **Audiophile-Grade Formats**: One-click extraction to MP3 (320kbps), bit-perfect FLAC, OPUS, M4A, or uncompressed WAV with embedded album artwork and metadata tags.
- 🎬 **Crisp Video Downloads**: Easy resolution selector supporting 4K (2160p), 2K (1440p), 1080p Full HD, 720p, or Best Available with automated stream merging.
- 📋 **Smart Clipboard Detection**: Automatically detects URLs copied to your clipboard on launch across Linux (Wayland & X11), macOS, and Windows.
- 🔁 **Incremental Playlist Sync**: Keeps track of downloaded songs in `.easydl-archive.txt` so repeated sync runs only download newly added items without re-downloading.
- 🔍 **Interactive Media Library**: Search and launch your downloaded music and videos instantly using `fzf` or the built-in search picker.
- 🌍 **100% Cross-Platform**: Native notifications and file manager integrations for **Linux** (`notify-send`, `xdg-open`), **macOS** (Notification Center, Finder), and **Windows** (System Tray balloons, File Explorer).

---

## 📦 Requirements

Before installing `easydl`, ensure you have:
1. **Python 3.8 or newer**
2. **ffmpeg** (required for audio conversion and video stream muxing)
3. **yt-dlp** & **spotdl** (installed automatically by the package)
4. *(Optional)* **fzf** for instant interactive fuzzy media search

---

## 🚀 Installation

Choose your operating system below for 1-click or quick installation instructions:

### 🐧 Linux

#### Automated 1-Click Install:
Clone this repository and run the installer:
```bash
git clone https://github.com/kekobade/easydl.git
cd easydl
chmod +x install.sh
./install.sh
```

#### Manual Installation:
1. **Install ffmpeg:**
   - **Fedora:** `sudo dnf install -y ffmpeg`
   - **Ubuntu / Debian:** `sudo apt update && sudo apt install -y ffmpeg`
   - **Arch Linux:** `sudo pacman -S ffmpeg`

2. **Install `easydl` via pip:**
   ```bash
   pip install --user -e .
   ```
   *(Ensure `~/.local/bin` is in your `PATH`)*

---

### 🍏 macOS

#### Automated 1-Click Install:
```bash
git clone https://github.com/kekobade/easydl.git
cd easydl
chmod +x install.sh
./install.sh
```

#### Manual Installation:
1. **Install ffmpeg via Homebrew:**
   ```bash
   brew install ffmpeg
   ```

2. **Install `easydl`:**
   ```bash
   python3 -m pip install --user -e .
   ```

---

### 🪟 Windows

#### Automated 1-Click Install:
1. Download or clone this repository.
2. Double-click **`install.bat`** (or right-click `install.ps1` and select **Run with PowerShell**).
3. The installer will automatically verify Python, install `ffmpeg` via `winget`, and configure the `easydl` command.

#### Manual Installation:
1. **Install Python & ffmpeg (via PowerShell):**
   ```powershell
   winget install Python.Python.3.11
   winget install Gyan.FFmpeg
   ```
2. **Install `easydl`:**
   ```powershell
   cd easydl
   python -m pip install -e .
   ```
3. Run `easydl` in Command Prompt or PowerShell, or double-click `easydl.bat`!

---

## 💡 Usage

### 1. Interactive Menu Mode
Simply run:
```bash
easydl
```
This launches the full terminal UI where you can choose actions with single key presses (`1` through `8`, `c` for clipboard, `q` to quit).

### 2. Command-Line Direct Mode
`easydl` can also be used directly from your shell without opening the menu:

```bash
# Smart auto-prompt for any URL
easydl "https://youtu.be/dQw4w9WgXcQ"

# Download Spotify track, album, or playlist (auto-creates playlist folder)
easydl spotify "https://open.spotify.com/playlist/37i9dQZF1DZ06evO1duNex"

# Download Apple Music song, album, or playlist (auto-creates playlist folder)
easydl apple "https://music.apple.com/us/album/anti-deluxe/1440933849"

# Download YouTube Music track or album
easydl ytmusic "https://music.youtube.com/playlist?list=..."

# Download SoundCloud track or set
easydl soundcloud "https://soundcloud.com/artist/sets/..."

# Download audio track as FLAC or MP3
easydl audio -f flac "https://youtu.be/dQw4w9WgXcQ"

# Download video capped at 1080p
easydl video -q 1080 "https://youtu.be/dQw4w9WgXcQ"

# Sync a playlist incrementally into an auto-named folder (or custom folder)
easydl sync "https://youtube.com/playlist?list=..."

# Instantly download media URL currently in clipboard
easydl clipboard

# Search and launch downloaded media
easydl search

# Open your downloads folder in file manager
easydl open audio
easydl open video

# Update yt-dlp to the latest extractors
easydl update
```

---

## ⚙️ Configuration

`easydl` saves its configuration in standard OS configuration directories:
- **Linux:** `~/.config/easydl/easydl.json`
- **macOS:** `~/Library/Application Support/easydl/easydl.json`
- **Windows:** `%APPDATA%\easydl\easydl.json`

You can customize:
- `audio_dir`: Default music download directory (Default: `~/Music/easydl`)
- `video_dir`: Default video download directory (Default: `~/Videos/easydl`)
- `default_audio_fmt`: Preferred audio codec (`mp3`, `flac`, `opus`, `m4a`, `wav`)
- `default_video_res`: Preferred video resolution ceiling (`2160`, `1440`, `1080`, `720`, `480`, `best`)
- `embed_metadata`: Automatically write ID3 tags, artist, and album tags
- `embed_thumbnail`: Embed album / video thumbnail cover art directly into files
- `embed_subs`: Download and mux subtitles into video files
- `browser_cookies`: Read cookies from your browser (`firefox`, `chrome`, `brave`, `edge`) to bypass login or age-verification walls

You can adjust these settings directly inside `easydl` by pressing **`7`** (**Settings & Config**).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/kekobade/easydl/issues).

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
