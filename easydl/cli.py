#!/usr/bin/env python3
"""
  ███████╗  █████╗  ███████╗ ██╗   ██╗ ██████╗  ██╗     
  ██╔════╝ ██╔══██╗ ██╔════╝ ╚██╗ ██╔╝ ██╔══██╗ ██║     
  █████╗   ███████║ ███████╗  ╚████╔╝  ██║  ██║ ██║     
  ██╔══╝   ██╔══██║ ╚════██║   ╚██╔╝   ██║  ██║ ██║     
  ███████╗ ██║  ██║ ███████║    ██║    ██████╔╝ ███████╗
  ╚══════╝ ╚═╝  ╚═╝ ╚══════╝    ╚═╝    ╚═════╝  ╚══════╝

easydl - A friendly, cross-platform media downloader & library manager.
Supports YouTube, Spotify, SoundCloud, Bandcamp, Bilibili, and more!
Powered by yt-dlp, ffmpeg, rich, and fzf.
Compatible with Windows, macOS, and Linux.
"""

import sys
import os
import re
import json
import base64
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich import box
    from rich.align import Align
except ImportError:
    print("Error: 'rich' library is required. Install with: pip install rich")
    sys.exit(1)

VERSION = "2.3.0"

# ---------- Cross-Platform Paths ----------
def get_config_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "easydl"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "easydl.json"
BASH_CONFIG_FILE = CONFIG_DIR / "easydl.conf"

console = Console()

# ---------- Default Configuration ----------
DEFAULT_CONFIG = {
    "audio_dir": str(Path.home() / "Music" / "easydl"),
    "video_dir": str(Path.home() / "Videos" / "easydl"),
    "default_audio_fmt": "mp3",
    "default_video_res": "1080",
    "notifications": True,
    "embed_metadata": True,
    "embed_thumbnail": True,
    "embed_subs": False,
    "browser_cookies": "",
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception:
            pass
    else:
        save_config(config)
    return config

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        with open(BASH_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("# easydl configuration file\n")
            f.write(f'AUDIO_DIR="{config.get("audio_dir", "")}"\n')
            f.write(f'VIDEO_DIR="{config.get("video_dir", "")}"\n')
            f.write(f'DEFAULT_AUDIO_FMT="{config.get("default_audio_fmt", "mp3")}"\n')
            f.write(f'DEFAULT_VIDEO_RES="{config.get("default_video_res", "1080")}"\n')
            f.write(f'NOTIFICATIONS="{"true" if config.get("notifications") else "false"}"\n')
            f.write(f'EMBED_METADATA="{"true" if config.get("embed_metadata") else "false"}"\n')
            f.write(f'EMBED_THUMBNAIL="{"true" if config.get("embed_thumbnail") else "false"}"\n')
            f.write(f'EMBED_SUBS="{"true" if config.get("embed_subs") else "false"}"\n')
            f.write(f'BROWSER_COOKIES="{config.get("browser_cookies", "")}"\n')
    except Exception as e:
        console.print(f"[red]Failed to save config: {e}[/red]")

# ---------- Cross-Platform System Helpers ----------
def open_path(p):
    """Open a folder or file in the native file manager / default viewer."""
    target = str(p)
    try:
        if sys.platform == "win32":
            os.startfile(target)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        console.print(f"[dim]Could not open {target}: {e}[/dim]")

def get_ytdlp_version():
    try:
        res = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "Not Found"

def get_media_counts(audio_dir, video_dir):
    audio_count = 0
    video_count = 0
    p_audio = Path(audio_dir)
    p_video = Path(video_dir)
    if p_audio.exists():
        audio_count = sum(1 for f in p_audio.rglob("*") if f.is_file() and f.suffix.lower() in [".mp3", ".flac", ".opus", ".m4a", ".wav", ".aac", ".ogg"])
    if p_video.exists():
        video_count = sum(1 for f in p_video.rglob("*") if f.is_file() and f.suffix.lower() in [".mp4", ".mkv", ".webm", ".avi", ".mov"])
    return audio_count, video_count

def send_notification(title, msg, icon="media-playback-start", config=None):
    if config and not config.get("notifications", True):
        return
    try:
        if sys.platform == "darwin":
            escaped_msg = msg.replace('"', '\\"')
            escaped_title = title.replace('"', '\\"')
            script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
            subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "win32":
            ps_script = (
                f"[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null; "
                f"$n = New-Object System.Windows.Forms.NotifyIcon; "
                f"$n.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$n.Visible = $true; "
                f"$n.ShowBalloonTip(3000, '{title}', '{msg}', [System.Windows.Forms.ToolTipIcon]::Info)"
            )
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-a", "easydl", "-i", icon, title, msg], stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_clipboard_url():
    # 1. Try tkinter (built into standard library on Windows/macOS/Linux)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        if text:
            match = re.search(r"https?://[^\s\"\'<>]+", text.strip())
            if match:
                return match.group(0)
    except Exception:
        pass

    # 2. Try OS CLI clipboard utilities
    if sys.platform == "darwin":
        tools = [["pbpaste"]]
    elif sys.platform == "win32":
        tools = [["powershell", "-NoProfile", "-Command", "Get-Clipboard"]]
    else:
        tools = [
            ["wl-paste"],
            ["xclip", "-o", "-selection", "clipboard"],
            ["xsel", "-b", "-o"]
        ]

    for cmd in tools:
        if shutil.which(cmd[0]):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
                if res.returncode == 0:
                    text = res.stdout.strip()
                    match = re.search(r"https?://[^\s\"\'<>]+", text)
                    if match:
                        return match.group(0)
            except Exception:
                continue
    return None

def check_dependencies():
    missing = []
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp")
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")

    if missing:
        console.print(f"[bold yellow]⚠️ Missing required dependencies: {', '.join(missing)}[/bold yellow]\n")

        # Auto-installer prompts based on detected OS
        if sys.platform == "win32":
            if shutil.which("winget"):
                if Confirm.ask("Would you like to install them now with winget?"):
                    if "yt-dlp" in missing:
                        subprocess.run(["winget", "install", "--id", "yt-dlp.yt-dlp", "-e", "--accept-source-agreements", "--accept-package-agreements"])
                    if "ffmpeg" in missing:
                        subprocess.run(["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements", "--accept-package-agreements"])
            elif shutil.which("scoop"):
                if Confirm.ask("Would you like to install them now with scoop?"):
                    subprocess.run(["scoop", "install"] + missing)
            elif shutil.which("choco"):
                if Confirm.ask("Would you like to install them now with chocolatey?"):
                    subprocess.run(["choco", "install", "-y"] + missing)
            else:
                console.print("[dim]Install with: winget install yt-dlp Gyan.FFmpeg[/dim]")
        elif sys.platform == "darwin":
            if shutil.which("brew"):
                if Confirm.ask("Would you like to install them now with Homebrew?"):
                    subprocess.run(["brew", "install"] + missing)
            else:
                console.print("[dim]Install with: brew install yt-dlp ffmpeg[/dim]")
        else:
            if shutil.which("dnf"):
                if Confirm.ask("Would you like to install them now with dnf?"):
                    if "ffmpeg" in missing:
                        subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"])
                    if "yt-dlp" in missing:
                        subprocess.run(["sudo", "dnf", "install", "-y", "yt-dlp"]) or subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"])
            elif shutil.which("apt"):
                if Confirm.ask("Would you like to install them now with apt?"):
                    subprocess.run(["sudo", "apt", "update"])
                    if "ffmpeg" in missing:
                        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
                    if "yt-dlp" in missing:
                        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"])
            elif shutil.which("pacman"):
                if Confirm.ask("Would you like to install them now with pacman?"):
                    subprocess.run(["sudo", "pacman", "-S", "--noconfirm"] + missing)

        still_missing = [d for d in ["yt-dlp", "ffmpeg"] if not shutil.which(d)]
        if still_missing:
            console.print(f"\n[bold red]easydl cannot continue without {', '.join(still_missing)}. Exiting.[/bold red]")
            if sys.platform == "win32":
                console.print("[yellow]Quick Windows fix: run 'winget install yt-dlp Gyan.FFmpeg' in PowerShell.[/yellow]")
            elif sys.platform == "darwin":
                console.print("[yellow]Quick macOS fix: run 'brew install yt-dlp ffmpeg' in Terminal.[/yellow]")
            else:
                console.print("[yellow]Quick Linux fix: install yt-dlp and ffmpeg using your package manager.[/yellow]")
            sys.exit(1)

# ---------- Music Platforms & Sanitization Helpers ----------
def sanitize_folder_name(name):
    """Sanitize playlist/album name for safe folder creation across OSes."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", str(name)).strip()
    clean = re.sub(r'^[. ]+', '', clean)
    clean = clean.strip()
    return clean or "Playlist"

PLATFORM_META = {
    "spotify": {"name": "Spotify", "color": "#1db954", "icon": "🟢"},
    "apple_music": {"name": "Apple Music", "color": "#fc3c44", "icon": "🍎"},
    "ytmusic": {"name": "YouTube Music", "color": "#ff0000", "icon": "🔴"},
    "youtube": {"name": "YouTube", "color": "#ff0000", "icon": "▶️"},
    "soundcloud": {"name": "SoundCloud", "color": "#ff5500", "icon": "🟠"},
    "bandcamp": {"name": "Bandcamp", "color": "#629aa9", "icon": "🟣"},
    "generic": {"name": "Web Media", "color": "#00f2fe", "icon": "🌐"},
}

def detect_platform(url):
    s = str(url).lower()
    if is_spotify_url(s):
        return "spotify"
    elif is_apple_music_url(s):
        return "apple_music"
    elif "music.youtube.com" in s:
        return "ytmusic"
    elif "youtube.com" in s or "youtu.be" in s:
        return "youtube"
    elif "soundcloud.com" in s:
        return "soundcloud"
    elif "bandcamp.com" in s:
        return "bandcamp"
    return "generic"

# ---------- Spotify Support ----------
def is_spotify_url(url):
    return bool(re.search(r"(open\.spotify\.com/(track|album|playlist|artist)/|spotify:(track|album|playlist|artist):)", str(url)))

def parse_spotify(url):
    """Extract tracks and metadata from any Spotify link using public embed metadata."""
    console.print("[dim]Parsing Spotify metadata...[/dim]")
    m = re.search(r"(track|album|playlist|artist)[/:]([a-zA-Z0-9]+)", str(url))
    if not m:
        return None, "Invalid Spotify URL format."
    kind, item_id = m.group(1), m.group(2)

    def fetch_embed(c_id):
        embed_url = f"https://open.spotify.com/embed/{kind}/{c_id}"
        req = urllib.request.Request(
            embed_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                return response.read().decode("utf-8", errors="ignore"), 200
        except urllib.error.HTTPError as e:
            return "", e.code
        except Exception:
            if shutil.which("curl"):
                try:
                    proc = subprocess.run(
                        ["curl", "-s", "-L", embed_url, "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"],
                        capture_output=True, text=True, timeout=12
                    )
                    return proc.stdout, 200 if proc.stdout else 500
                except Exception:
                    pass
            return "", 500

    def is_valid_embed(content, status_code):
        if status_code != 200 or not content:
            return False
        if '"status":404' in content or '"status": 404' in content or '"status":500' in content or '"status": 500' in content:
            return False
        if "Page not found" in content:
            return False
        try:
            m_chk = re.search(r"<script id=\"__NEXT_DATA__\" type=\"application/json\">([^<]+)</script>", content)
            if not m_chk:
                return False
            d_chk = json.loads(m_chk.group(1))
            ent_chk = d_chk.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
            return bool(ent_chk and (ent_chk.get("title") or ent_chk.get("name")))
        except Exception:
            return False

    html, code = fetch_embed(item_id)
    # Check for typo (e.g. 0 vs O, 1 vs l/I) if not valid
    if not is_valid_embed(html, code):
        corrected = False
        probes = 0
        for idx_ch, ch in enumerate(item_id):
            if probes >= 4:
                break
            replacements = []
            if ch in ["0", "O"]:
                replacements.append("O" if ch == "0" else "0")
            elif ch in ["1", "l", "I"]:
                replacements.extend([r for r in ["1", "l", "I"] if r != ch])
            for r_ch in replacements:
                if probes >= 4:
                    break
                probes += 1
                cand_id = item_id[:idx_ch] + r_ch + item_id[idx_ch+1:]
                cand_html, cand_code = fetch_embed(cand_id)
                if is_valid_embed(cand_html, cand_code):
                    html, code, item_id = cand_html, cand_code, cand_id
                    corrected = True
                    console.print(f"[bold green]✔ Auto-corrected URL ID typo ({ch} ➜ {r_ch}): {cand_id}[/bold green]")
                    break
            if corrected:
                break

    if not is_valid_embed(html, code):
        return None, "Spotify item not found (HTTP 404). The playlist or track may be private or removed. Check for typos (e.g., 0 vs O)."

    if not html:
        return None, f"Failed to retrieve Spotify metadata (HTTP {code}). Check your network connection."

    m_json = re.search(r"<script id=\"__NEXT_DATA__\" type=\"application/json\">([^<]+)</script>", html)
    if not m_json:
        return None, "Could not locate structured metadata in Spotify embed."

    try:
        data = json.loads(m_json.group(1))
        page_props = data.get("props", {}).get("pageProps", {})
        if page_props.get("status") == 404:
            return None, "Spotify item does not exist or is set to private (HTTP 404)."
        entity = page_props.get("state", {}).get("data", {}).get("entity", {})
    except Exception as e:
        return None, f"Error decoding Spotify JSON data: {e}"

    if not entity:
        return None, "Spotify entity data is empty or invalid."

    entity_type = entity.get("type", kind)
    title = entity.get("title") or entity.get("name") or "Unknown"
    subtitle = entity.get("subtitle") or ""

    artists_list = [a.get("name", "") for a in entity.get("artists", []) if a.get("name")]
    entity_artist = ", ".join(artists_list) or subtitle or "Various Artists"

    tracks = []
    raw_tracklist = entity.get("trackList", [])
    if raw_tracklist:
        for t in raw_tracklist:
            t_title = t.get("title") or t.get("name")
            if not t_title:
                continue
            t_artist = t.get("subtitle") or entity_artist
            t_album = title if entity_type == "album" else ""
            tracks.append({
                "title": t_title,
                "artist": t_artist,
                "album": t_album,
                "duration_ms": t.get("duration", 0)
            })
    elif entity_type == "track":
        tracks.append({
            "title": title,
            "artist": entity_artist,
            "album": entity.get("album", {}).get("name", "") or title,
            "duration_ms": entity.get("duration", 0)
        })

    if not tracks:
        return None, "No playable tracks found in Spotify collection."

    return {
        "type": entity_type,
        "title": title,
        "artist": entity_artist,
        "tracks": tracks
    }, None

def download_spotify(url, fmt=None, out_dir=None, config=None):
    if not config:
        config = load_config()
    fmt = fmt or config.get("default_audio_fmt", "mp3")
    base_out = Path(out_dir or config.get("audio_dir", Path.home() / "Music" / "easydl"))

    meta, err = parse_spotify(url)
    if not meta or not meta.get("tracks"):
        console.print(f"[bold red]Could not retrieve Spotify track details: {err or 'Unknown error'}[/bold red]")
        return 1

    tracks = meta["tracks"]
    total = len(tracks)

    info_card = Panel(
        f"[bold #1db954]Spotify {meta['type'].upper()}:[/] [bold white]{meta['title']}[/]\n"
        f"[dim]Artist:[/] [cyan]{meta['artist'] or 'Various'}[/]  │  [dim]Total Tracks:[/] [yellow]{total}[/]",
        border_style="#1db954",
        box=box.ROUNDED,
        title="[bold #1db954]🟢 Spotify Media Detected[/]"
    )
    console.print(info_card)

    dest_folder = base_out
    if meta["type"] in ["album", "playlist"] or total > 1:
        safe_name = sanitize_folder_name(meta["title"])
        dest_folder = base_out / safe_name
        console.print(f"  [dim]📁 Dedicated folder:[/] [bold cyan]{dest_folder}[/]")
    dest_folder.mkdir(parents=True, exist_ok=True)

    archive_file = dest_folder / ".easydl-archive.txt"
    downloaded_set = set()
    if archive_file.exists():
        try:
            with open(archive_file, "r", encoding="utf-8") as f:
                downloaded_set = {line.strip() for line in f if line.strip()}
        except Exception:
            pass

    success_count = 0
    for idx, t in enumerate(tracks, start=1):
        track_key = f"{t['artist']} - {t['title']}"
        track_tag = f"[{idx}/{total}]"

        if track_key in downloaded_set:
            console.print(f"  {track_tag} [dim]Already downloaded, skipping:[/] [white]{track_key}[/]")
            success_count += 1
            continue

        console.print(f"\n[bold #00f2fe]➜ {track_tag} Fetching:[/] [bold white]{t['title']}[/] [dim]by {t['artist']}[/]")
        query = f"ytsearch1:{t['artist']} - {t['title']} audio" if t.get('artist') else f"ytsearch1:{t['title']} audio"

        out_template = str(dest_folder / f"{idx:02d} - %(title)s.%(ext)s") if total > 1 else str(dest_folder / "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", fmt,
            "--audio-quality", "0",
            "--no-playlist",
            "-o", out_template,
        ]
        cmd.extend(build_base_ytdlp_args(config))
        cmd.append(query)

        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            success_count += 1
            try:
                with open(archive_file, "a", encoding="utf-8") as f:
                    f.write(f"{track_key}\n")
            except Exception:
                pass
        else:
            console.print(f"  [red]Failed to fetch track:[/] {t['title']}")

    if success_count > 0:
        done_card = Panel(
            f"[bold #00e676]✔ Successfully fetched {success_count}/{total} track(s)![/]\n[white]Saved to:[/] [cyan]{dest_folder}[/]",
            border_style="#00e676",
            box=box.ROUNDED,
            title="[bold #00e676]✨ Spotify Download Complete[/]"
        )
        console.print(done_card)
        send_notification("Spotify Download Complete", f"Saved {success_count} track(s) to {dest_folder.name}", "audio-x-generic", config)
        return 0
    else:
        console.print("[bold red]Failed to download tracks from Spotify collection.[/bold red]")
        return 1

# ---------- Apple Music Support ----------
def is_apple_music_url(url):
    return bool(re.search(r"(music|itunes)\.apple\.com/", str(url)))

def parse_apple_music(url):
    """Extract tracks and metadata from Apple Music link."""
    console.print("[dim]Parsing Apple Music metadata...[/dim]")
    url_clean = str(url).strip()
    req = urllib.request.Request(
        url_clean,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    html = ""
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return None, f"Apple Music returned HTTP {e.code}: {e.reason}"
    except Exception as e:
        if shutil.which("curl"):
            try:
                proc = subprocess.run(
                    ["curl", "-s", "-L", url_clean, "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"],
                    capture_output=True, text=True, timeout=12
                )
                html = proc.stdout
            except Exception:
                return None, f"Failed to connect to Apple Music: {e}"
        else:
            return None, f"Failed to connect to Apple Music: {e}"

    if not html:
        return None, "Empty response from Apple Music."

    # Check for single song query (?i=12345)
    song_id_match = re.search(r"[?&]i=(\d+)", url_clean)
    target_track_id = song_id_match.group(1) if song_id_match else None
    is_song_url = "/song/" in url_clean or bool(target_track_id)

    # 1. Parse serialized-server-data (best for playlists and albums)
    m_server = re.search(r"<script type=\"application/json\" id=\"serialized-server-data\">([^<]+)</script>", html)
    if m_server:
        try:
            s_data = json.loads(m_server.group(1))
            items_arr = s_data.get("data", []) if isinstance(s_data, dict) else s_data
            if items_arr and isinstance(items_arr, list):
                main_item = items_arr[0]
                d = main_item.get("data", {})
                
                collection_title = ""
                seo_title = d.get("seoData", {}).get("pageTitle", "")
                if seo_title:
                    collection_title = re.sub(r"\s*-\s*(Playlist|Album|Song).*", "", seo_title, flags=re.I).strip()
                    collection_title = collection_title.lstrip("\u200e").strip()

                tracks = []
                sections = d.get("sections", [])
                for sec in sections:
                    for itm in sec.get("items", []):
                        t_id = str(itm.get("id", ""))
                        if "track-lockup" in t_id or "song" in t_id or (itm.get("title") and itm.get("subtitleLinks")):
                            t_title = itm.get("title", "").strip()
                            t_artists = [a.get("title") for a in itm.get("subtitleLinks", []) if a.get("title")]
                            t_artist = ", ".join(t_artists)
                            t_album = ""
                            if itm.get("tertiaryLinks"):
                                t_album = itm["tertiaryLinks"][0].get("title", "")
                            
                            nums = re.findall(r"\d{6,}", t_id)
                            item_adam_id = nums[-1] if nums else None
                            if target_track_id and item_adam_id and target_track_id != item_adam_id:
                                continue

                            if t_title:
                                tracks.append({
                                    "title": t_title,
                                    "artist": t_artist,
                                    "album": t_album or collection_title
                                })
                
                if tracks:
                    if is_song_url and len(tracks) >= 1:
                        chosen = tracks[0]
                        return {
                            "type": "track",
                            "title": chosen["title"],
                            "artist": chosen["artist"],
                            "tracks": [chosen]
                        }, None

                    c_type = "album" if "album" in url_clean.lower() else "playlist"
                    c_artist = tracks[0]["artist"] if c_type == "album" else "Various Artists"
                    return {
                        "type": c_type,
                        "title": collection_title or "Apple Music Collection",
                        "artist": c_artist,
                        "tracks": tracks
                    }, None
        except Exception:
            pass

    # 2. Schema JSON-LD Fallback
    m_schema = re.search(r"<script id=\"?schema:[^\">]+\"? type=\"application/ld\+json\">([^<]+)</script>", html)
    if m_schema:
        try:
            sch = json.loads(m_schema.group(1))
            stype = sch.get("@type", "")
            sname = sch.get("name", "").lstrip("\u200e").strip()
            by_artist = sch.get("byArtist", [])
            sartist = by_artist[0].get("name", "") if by_artist and isinstance(by_artist, list) else ""
            
            raw_tracks = sch.get("tracks", [])
            if raw_tracks:
                tracks = []
                for rt in raw_tracks:
                    rt_name = rt.get("name", "")
                    if rt_name:
                        tracks.append({
                            "title": rt_name,
                            "artist": sartist,
                            "album": sname
                        })
                return {
                    "type": "album" if "Album" in stype else "playlist",
                    "title": sname,
                    "artist": sartist,
                    "tracks": tracks
                }, None
            elif stype in ["MusicRecording", "MusicComposition"] or is_song_url:
                og_t = re.search(r"<meta property=\"og:title\" content=\"([^\"]+)\"", html)
                title_cand = sname
                artist_cand = sartist
                if og_t:
                    og_match = re.match(r"(.*?)\s+by\s+(.*?)\s+on\s+Apple\s+Music", og_t.group(1), re.I)
                    if og_match:
                        title_cand = og_match.group(1).strip()
                        artist_cand = og_match.group(2).strip()
                return {
                    "type": "track",
                    "title": title_cand,
                    "artist": artist_cand,
                    "tracks": [{"title": title_cand, "artist": artist_cand, "album": ""}]
                }, None
        except Exception:
            pass

    return None, "Could not extract tracks from Apple Music link. Please check if link is valid and public."

def download_apple_music(url, fmt=None, out_dir=None, config=None):
    if not config:
        config = load_config()
    fmt = fmt or config.get("default_audio_fmt", "mp3")
    base_out = Path(out_dir or config.get("audio_dir", Path.home() / "Music" / "easydl"))

    meta, err = parse_apple_music(url)
    if not meta or not meta.get("tracks"):
        console.print(f"[bold red]Could not retrieve Apple Music tracks: {err or 'Unknown error'}[/bold red]")
        return 1

    tracks = meta["tracks"]
    total = len(tracks)

    info_card = Panel(
        f"[bold #fc3c44]Apple Music {meta['type'].upper()}:[/] [bold white]{meta['title']}[/]\n"
        f"[dim]Artist:[/] [cyan]{meta['artist'] or 'Various'}[/]  │  [dim]Total Tracks:[/] [yellow]{total}[/]",
        border_style="#fc3c44",
        box=box.ROUNDED,
        title="[bold #fc3c44]🍎 Apple Music Media Detected[/]"
    )
    console.print(info_card)

    dest_folder = base_out
    if meta["type"] in ["album", "playlist"] or total > 1:
        safe_name = sanitize_folder_name(meta["title"])
        dest_folder = base_out / safe_name
        console.print(f"  [dim]📁 Dedicated folder:[/] [bold cyan]{dest_folder}[/]")
    dest_folder.mkdir(parents=True, exist_ok=True)

    archive_file = dest_folder / ".easydl-archive.txt"
    downloaded_set = set()
    if archive_file.exists():
        try:
            with open(archive_file, "r", encoding="utf-8") as f:
                downloaded_set = {line.strip() for line in f if line.strip()}
        except Exception:
            pass

    success_count = 0
    for idx, t in enumerate(tracks, start=1):
        track_key = f"{t['artist']} - {t['title']}"
        track_tag = f"[{idx}/{total}]"

        if track_key in downloaded_set:
            console.print(f"  {track_tag} [dim]Already downloaded, skipping:[/] [white]{track_key}[/]")
            success_count += 1
            continue

        console.print(f"\n[bold #00f2fe]➜ {track_tag} Fetching:[/] [bold white]{t['title']}[/] [dim]by {t['artist']}[/]")
        query = f"ytsearch1:{t['artist']} - {t['title']} audio" if t.get('artist') else f"ytsearch1:{t['title']} audio"

        out_template = str(dest_folder / f"{idx:02d} - %(title)s.%(ext)s") if total > 1 else str(dest_folder / "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", fmt,
            "--audio-quality", "0",
            "--no-playlist",
            "-o", out_template,
        ]
        cmd.extend(build_base_ytdlp_args(config))
        cmd.append(query)

        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            success_count += 1
            try:
                with open(archive_file, "a", encoding="utf-8") as f:
                    f.write(f"{track_key}\n")
            except Exception:
                pass
        else:
            console.print(f"  [red]Failed to fetch track:[/] {t['title']}")

    if success_count > 0:
        done_card = Panel(
            f"[bold #00e676]✔ Successfully fetched {success_count}/{total} track(s)![/]\n[white]Saved to:[/] [cyan]{dest_folder}[/]",
            border_style="#00e676",
            box=box.ROUNDED,
            title="[bold #00e676]✨ Apple Music Download Complete[/]"
        )
        console.print(done_card)
        send_notification("Apple Music Download Complete", f"Saved {success_count} track(s) to {dest_folder.name}", "audio-x-generic", config)
        return 0
    else:
        console.print("[bold red]Failed to download tracks from Apple Music collection.[/bold red]")
        return 1

# ---------- Visual Components ----------
def render_banner(config):
    console.clear()
    banner_lines = [
        "███████╗  █████╗  ███████╗ ██╗   ██╗ ██████╗  ██╗     ",
        "██╔════╝ ██╔══██╗ ██╔════╝ ╚██╗ ██╔╝ ██╔══██╗ ██║     ",
        "█████╗   ███████║ ███████╗  ╚████╔╝  ██║  ██║ ██║     ",
        "██╔══╝   ██╔══██║ ╚════██║   ╚██╔╝   ██║  ██║ ██║     ",
        "███████╗ ██║  ██║ ███████║    ██║    ██████╔╝ ███████╗",
        "╚══════╝ ╚═╝  ╚═╝ ╚══════╝    ╚═╝    ╚═════╝  ╚══════╝",
    ]

    gradient_colors = ["#00f2fe", "#26d0ce", "#4facfe", "#6b73ff", "#9b51e0", "#e056fd"]
    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = gradient_colors[i % len(gradient_colors)]
        styled_banner.append(line + "\n", style=f"bold {color}")

    panel = Panel(
        Align.center(styled_banner),
        border_style="#4facfe",
        box=box.ROUNDED,
        subtitle="[bold #e056fd]⚡ Next-Gen Media Downloader (Spotify, Apple Music, YouTube, SoundCloud)[/]",
        subtitle_align="right"
    )
    console.print(panel)

    # Compact Badges bar
    ytdlp_ver = get_ytdlp_version()
    audio_cnt, video_cnt = get_media_counts(config["audio_dir"], config["video_dir"])

    badges = Text()
    badges.append(f" 🏷️ v{VERSION} ", style="bold black on #00f2fe")
    badges.append(" ")
    badges.append(f" 📦 yt-dlp: {ytdlp_ver} ", style="bold black on #4facfe")
    badges.append(" ")
    badges.append(f" 🎵 Music: {audio_cnt} ", style="bold black on #a8ff78")
    badges.append(" ")
    badges.append(f" 🎬 Videos: {video_cnt} ", style="bold black on #ffd200")
    console.print(Align.center(badges))
    console.print()

def show_clipboard_banner(clip_url):
    if not clip_url:
        return
    text = Text()
    plat = detect_platform(clip_url)
    pmeta = PLATFORM_META.get(plat, PLATFORM_META["generic"])
    icon = pmeta["icon"] + " "
    prefix = f"[{pmeta['name']}] "
    text.append(icon, style=f"bold {pmeta['color']}")
    text.append(prefix, style=f"bold {pmeta['color']}")
    text.append(clip_url, style="bold white underline")
    text.append("\n💡 Press ", style="dim")
    text.append("[c]", style="bold #00f2fe")
    text.append(" to download from clipboard immediately, or choose a menu option below.", style="dim")

    clip_panel = Panel(
        text,
        title="[bold #00f2fe]📋 Clipboard Media URL Detected[/bold #00f2fe]",
        border_style=pmeta["color"],
        box=box.ROUNDED,
        padding=(0, 2)
    )
    console.print(clip_panel)
    console.print()

def prompt_url_smart(prompt_label="media URL"):
    clip_url = get_clipboard_url()
    if clip_url:
        plat = detect_platform(clip_url)
        pmeta = PLATFORM_META.get(plat, PLATFORM_META["generic"])
        console.print(f"  [dim]Detected {pmeta['icon']} {pmeta['name']} in clipboard:[/] [bold cyan]{clip_url}[/]")
        use_clip = Confirm.ask("  Use this URL?", default=True)
        if use_clip:
            return clip_url
    url = Prompt.ask(f"  [bold]Enter {prompt_label}[/]")
    return url.strip()

def build_base_ytdlp_args(config):
    args = ["--no-mtime", "--continue"]
    # Provide JS runtime if available (node, deno, bun) to prevent YouTube extraction warnings
    for rt in ["node", "deno", "bun"]:
        if shutil.which(rt):
            args.extend(["--js-runtimes", rt])
            break
    if config.get("embed_metadata", True):
        args.extend(["--add-metadata", "--embed-metadata"])
    if config.get("embed_thumbnail", True):
        args.append("--embed-thumbnail")
    if config.get("browser_cookies"):
        args.extend(["--cookies-from-browser", config["browser_cookies"]])
    return args

# ---------- Download Actions ----------
def download_audio(url, fmt=None, out_dir=None, config=None):
    if not config:
        config = load_config()

    if is_spotify_url(url):
        return download_spotify(url, fmt=fmt, out_dir=out_dir, config=config)
    if is_apple_music_url(url):
        return download_apple_music(url, fmt=fmt, out_dir=out_dir, config=config)

    fmt = fmt or config.get("default_audio_fmt", "mp3")
    base_out = Path(out_dir or config.get("audio_dir", Path.home() / "Music" / "easydl"))
    base_out.mkdir(parents=True, exist_ok=True)

    plat = detect_platform(url)
    pmeta = PLATFORM_META.get(plat, PLATFORM_META["generic"])
    if plat in ["ytmusic", "soundcloud", "bandcamp", "youtube"]:
        console.print(Panel(f"[bold {pmeta['color']}]{pmeta['name']} Media[/]\n[white]{url}[/]", title=f"[bold {pmeta['color']}]{pmeta['icon']} {pmeta['name']} Detected[/]", box=box.ROUNDED, border_style=pmeta['color']))

    console.print(f"\n[bold #00f2fe]➜ Initiating audio download ({fmt.upper()}, best quality)...[/]")
    console.print(f"[dim]Destination: {base_out}[/dim]")
    console.print("[dim]Playlists/Albums will automatically create dedicated folders.[/dim]\n")

    # Conditional template creates a dedicated folder for playlists
    out_template = str(base_out / "%(playlist_title&{}/|)s%(playlist_index&{:02d} - |)s%(title)s.%(ext)s")

    cmd = ["yt-dlp"]
    cmd.extend(build_base_ytdlp_args(config))
    cmd.extend([
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", fmt,
        "--audio-quality", "0",
        "-o", out_template,
        url
    ])

    ret = subprocess.run(cmd)
    if ret.returncode == 0:
        card = Panel(
            f"[bold #00e676]✔ Download Succeeded![/]\n[white]Saved to:[/] [cyan]{base_out}[/]",
            border_style="#00e676",
            box=box.ROUNDED,
            title="[bold #00e676]✨ Audio Download Complete[/]"
        )
        console.print(card)
        send_notification("Audio Download Complete", f"Saved to {base_out}", "audio-x-generic", config)
    else:
        console.print(f"\n[bold #ff1744]✘ Download failed. Please check the URL and internet connection.[/]")
        send_notification("Download Failed", f"Failed: {url}", "dialog-error", config)
    return ret.returncode

def download_video(url, res=None, out_dir=None, config=None):
    if not config:
        config = load_config()

    if is_spotify_url(url):
        console.print("[yellow]Spotify links are audio-only. Switching to audio extraction...[/yellow]")
        return download_spotify(url, out_dir=config["audio_dir"], config=config)
    if is_apple_music_url(url):
        console.print("[yellow]Apple Music links are audio-only. Switching to audio extraction...[/yellow]")
        return download_apple_music(url, out_dir=config["audio_dir"], config=config)

    res = res or config.get("default_video_res", "1080")
    out_dir = Path(out_dir or config.get("video_dir", Path.home() / "Videos" / "easydl"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if res == "best":
        fmt_string = "bestvideo+bestaudio/best"
        console.print(f"\n[bold #00f2fe]➜ Initiating video download (Best available quality)...[/]")
    else:
        fmt_string = f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"
        console.print(f"\n[bold #00f2fe]➜ Initiating video download (up to {res}p)...[/]")
    console.print(f"[dim]Destination: {out_dir}[/dim]\n")

    cmd = ["yt-dlp"]
    cmd.extend(build_base_ytdlp_args(config))

    if config.get("embed_subs", False):
        cmd.extend(["--write-subs", "--sub-langs", "en.*,ja,all", "--embed-subs"])

    out_template = str(out_dir / "%(playlist_title&{}/|)s%(playlist_index&{:02d} - |)s%(title)s.%(ext)s")

    cmd.extend([
        "-f", fmt_string,
        "--merge-output-format", "mp4",
        "-o", out_template,
        url
    ])

    ret = subprocess.run(cmd)
    if ret.returncode == 0:
        card = Panel(
            f"[bold #00e676]✔ Video Download Succeeded![/]\n[white]Saved to:[/] [cyan]{out_dir}[/]",
            border_style="#00e676",
            box=box.ROUNDED,
            title="[bold #00e676]✨ Video Download Complete[/]"
        )
        console.print(card)
        send_notification("Video Download Complete", f"Saved to {out_dir}", "video-x-generic", config)
    else:
        console.print(f"\n[bold #ff1744]✘ Download failed. Please check URL and resolution.[/]")
        send_notification("Download Failed", f"Failed: {url}", "dialog-error", config)
    return ret.returncode

def sync_playlist(url, folder_name=None, media_type="audio", config=None):
    if not config:
        config = load_config()

    if is_spotify_url(url):
        return download_spotify(url, out_dir=config["audio_dir"], config=config)
    if is_apple_music_url(url):
        return download_apple_music(url, out_dir=config["audio_dir"], config=config)

    base_dir = Path(config["video_dir"]) if media_type == "video" else Path(config["audio_dir"])
    
    if folder_name:
        safe_folder = sanitize_folder_name(folder_name)
        sync_dir = base_dir / safe_folder
        sync_dir.mkdir(parents=True, exist_ok=True)
        archive_file = sync_dir / ".easydl-archive.txt"
        out_template = str(sync_dir / "%(playlist_index)02d - %(title)s.%(ext)s")
    else:
        sync_dir = base_dir
        archive_file = base_dir / ".easydl-archive.txt"
        # Organizes into playlist folder automatically
        out_template = str(base_dir / "%(playlist_title&{}/|)s%(playlist_index&{:02d} - |)s%(title)s.%(ext)s")

    console.print(f"\n[bold #00f2fe]➜ Syncing playlist into:[/] [cyan]{sync_dir}[/]")
    console.print(f"[dim]Archive Tracker: {archive_file} (skips tracks already present)[/dim]\n")

    cmd = ["yt-dlp"]
    cmd.extend(build_base_ytdlp_args(config))

    if media_type == "video":
        res = config.get("default_video_res", "1080")
        fmt = "bestvideo+bestaudio/best" if res == "best" else f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"
        cmd.extend([
            "-f", fmt,
            "--merge-output-format", "mp4",
            "--download-archive", str(archive_file),
            "--yes-playlist",
            "-o", out_template,
            url
        ])
    else:
        fmt = config.get("default_audio_fmt", "mp3")
        cmd.extend([
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", fmt,
            "--audio-quality", "0",
            "--download-archive", str(archive_file),
            "--yes-playlist",
            "-o", out_template,
            url
        ])

    ret = subprocess.run(cmd)
    if ret.returncode == 0:
        card = Panel(
            f"[bold #00e676]✔ Playlist Sync Complete![/]\n[white]Saved to:[/] [cyan]{sync_dir}[/]",
            border_style="#00e676",
            box=box.ROUNDED,
            title="[bold #00e676]✨ Playlist Synced[/]"
        )
        console.print(card)
        send_notification("Playlist Synced", f"Synced to {sync_dir.name}", "media-playlist", config)
    else:
        console.print(f"\n[bold #ff1744]✘ Playlist sync encountered errors.[/]")
    return ret.returncode

# ---------- Search & Library (Cross-Platform) ----------
def do_search(config):
    audio_dir = Path(config["audio_dir"])
    video_dir = Path(config["video_dir"])

    extensions = {".mp3", ".flac", ".mp4", ".mkv", ".webm", ".m4a", ".opus", ".wav", ".aac", ".ogg"}
    files = []
    for p in [audio_dir, video_dir]:
        if p.exists():
            files.extend([f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in extensions])
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not files:
        console.print("[yellow]No downloaded media found yet in Music or Video directories.[/yellow]")
        input("\nPress Enter to return...")
        return

    # Check for fzf
    if shutil.which("fzf"):
        console.print("[bold #00f2fe]Launching interactive Media Search with fzf...[/]")
        try:
            fzf_cmd = [
                "fzf",
                "--prompt=🔍 Search Media > ",
                "--header=[ENTER] Play Media  |  [ESC] Exit",
                "--color=pointer:#00f2fe,header:#e056fd,prompt:#4facfe"
            ]
            file_list_input = "\n".join(str(f) for f in files)
            p = subprocess.Popen(fzf_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            stdout, _ = p.communicate(input=file_list_input)
            selected = stdout.strip()
            if selected:
                console.print(f"[bold green]▶ Opening:[/] [cyan]{selected}[/]")
                open_path(selected)
            return
        except Exception as e:
            console.print(f"[dim]fzf search failed, using fallback list: {e}[/dim]")

    # Built-in search fallback
    console.print("[bold #00f2fe]Recently Downloaded Media:[/bold #00f2fe]\n")
    max_show = min(15, len(files))
    for idx, f in enumerate(files[:max_show], 1):
        console.print(f"  [bold cyan]{idx}[/] • {f.name} [dim]({f.parent.name})[/dim]")

    console.print("\n  [dim]Enter a number to open, or enter a text filter, or press Enter to return.[/dim]")
    sel = Prompt.ask("  Select").strip()
    if sel.isdigit() and 1 <= int(sel) <= max_show:
        open_path(files[int(sel) - 1])
    elif sel:
        matches = [f for f in files if sel.lower() in f.name.lower()]
        if matches:
            console.print(f"[bold green]▶ Opening:[/] [cyan]{matches[0].name}[/]")
            open_path(matches[0])
        else:
            console.print("[yellow]No matching file found.[/yellow]")
            input("\nPress Enter to return...")

# ---------- Interactive Menus ----------
def menu_audio(config):
    render_banner(config)
    console.print("  [bold #00f2fe]🎵 Download Audio / Music[/]")
    console.print("  [dim]Supports Spotify, Apple Music, YouTube Music, SoundCloud, Bandcamp, YouTube[/dim]\n")
    url = prompt_url_smart("audio, song, album, or playlist URL")
    if not url:
        return

    if is_spotify_url(url):
        download_spotify(url, config=config)
        input("\nPress Enter to return...")
        return

    if is_apple_music_url(url):
        download_apple_music(url, config=config)
        input("\nPress Enter to return...")
        return

    table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=True, header_style="bold #00f2fe")
    table.add_column("Key", justify="center", style="bold cyan", width=5)
    table.add_column("Format", style="bold white", width=12)
    table.add_column("Details", style="grey78")
    table.add_row("1", "MP3", "Universal standard, compatible with every player (320kbps)")
    table.add_row("2", "FLAC", "Lossless audio extracted bit-perfect from source")
    table.add_row("3", "OPUS", "Modern audiophile codec with superb compression")
    table.add_row("4", "M4A", "Native AAC format for Apple & Android ecosystems")
    table.add_row("5", "WAV", "Uncompressed raw PCM waveform")
    console.print(table)

    choice = Prompt.ask("  Choose format", choices=["1", "2", "3", "4", "5"], default="1")
    fmt_map = {"1": "mp3", "2": "flac", "3": "opus", "4": "m4a", "5": "wav"}
    download_audio(url, fmt=fmt_map.get(choice, "mp3"), config=config)
    input("\nPress Enter to return...")

def menu_video(config):
    render_banner(config)
    console.print("  [bold #00f2fe]🎬 Download Video[/]\n")
    url = prompt_url_smart("video URL")
    if not url:
        return

    if is_spotify_url(url):
        download_spotify(url, config=config)
        input("\nPress Enter to return...")
        return

    if is_apple_music_url(url):
        download_apple_music(url, config=config)
        input("\nPress Enter to return...")
        return

    table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=True, header_style="bold #00f2fe")
    table.add_column("Key", justify="center", style="bold cyan", width=5)
    table.add_column("Resolution", style="bold white", width=16)
    table.add_column("Details", style="grey78")
    table.add_row("1", "2160p (4K UHD)", "Ultra High Definition")
    table.add_row("2", "1440p (2K QHD)", "Quad HD for high-DPI displays")
    table.add_row("3", "1080p (Full HD)", "Standard crisp HD (Default)")
    table.add_row("4", "720p (HD)", "Fast download, compact size")
    table.add_row("5", "480p (SD)", "Standard definition for data savings")
    table.add_row("6", "Best Available", "Maximum resolution available, no ceiling")
    table.add_row("7", "Inspect Streams", "Run yt-dlp -F to view all codecs & stream IDs")
    console.print(table)

    choice = Prompt.ask("  Pick resolution", choices=["1", "2", "3", "4", "5", "6", "7"], default="3")
    res_map = {"1": "2160", "2": "1440", "3": "1080", "4": "720", "5": "480", "6": "best"}

    if choice == "7":
        console.print(f"\n[bold #00f2fe]Fetching stream table for {url}...[/]\n")
        subprocess.run(["yt-dlp", "-F", url])
        custom_fmt = Prompt.ask("\nEnter desired format ID or resolution (e.g. 1080 or 137+140)")
        if custom_fmt:
            download_video(url, res=custom_fmt, config=config)
    else:
        download_video(url, res=res_map[choice], config=config)

    input("\nPress Enter to return...")

def menu_playlist(config):
    render_banner(config)
    console.print("  [bold #00f2fe]🔁 Sync Playlist or Album (Auto-Folder)[/]")
    console.print("  [dim]Smart incremental download: creates dedicated folder & skips already fetched tracks.[/dim]\n")
    url = prompt_url_smart("playlist or album URL (Spotify, Apple Music, YT Music, SoundCloud, YouTube)")
    if not url:
        return

    if is_spotify_url(url):
        download_spotify(url, config=config)
        input("\nPress Enter to return...")
        return

    if is_apple_music_url(url):
        download_apple_music(url, config=config)
        input("\nPress Enter to return...")
        return

    folder = Prompt.ask("  Enter folder name (press Enter to auto-name from playlist title)", default="")
    media_type = Prompt.ask("  Playlist Media Type", choices=["audio", "video"], default="audio")
    sync_playlist(url, folder or None, media_type=media_type, config=config)
    input("\nPress Enter to return...")

def menu_clipboard_direct(config):
    render_banner(config)
    clip_url = get_clipboard_url()
    if not clip_url:
        console.print("[yellow]No media URL detected in system clipboard.[/yellow]")
        input("\nPress Enter to return...")
        return

    if is_spotify_url(clip_url):
        download_spotify(clip_url, config=config)
        input("\nPress Enter to return...")
        return

    if is_apple_music_url(clip_url):
        download_apple_music(clip_url, config=config)
        input("\nPress Enter to return...")
        return

    plat = detect_platform(clip_url)
    pmeta = PLATFORM_META.get(plat, PLATFORM_META["generic"])
    console.print(Panel(f"[bold cyan]{clip_url}[/]", title=f"[bold {pmeta['color']}]{pmeta['icon']} {pmeta['name']} Detected[/]", box=box.ROUNDED, border_style=pmeta["color"]))
    table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=False)
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Action", style="bold white")
    table.add_row("1", f"🎵 Download Audio ({config['default_audio_fmt'].upper()})")
    table.add_row("2", f"🎬 Download Video ({config['default_video_res']}p)")
    table.add_row("3", "🎬 Download Video (Best Available)")
    table.add_row("c", "Cancel")
    console.print(table)

    choice = Prompt.ask("  Choice", choices=["1", "2", "3", "c"], default="1")
    if choice == "1":
        download_audio(clip_url, config=config)
    elif choice == "2":
        download_video(clip_url, res=config["default_video_res"], config=config)
    elif choice == "3":
        download_video(clip_url, res="best", config=config)
    input("\nPress Enter to return...")

def menu_settings(config):
    while True:
        render_banner(config)
        console.print("  [bold #00f2fe]🔧  Settings & Preferences[/]")
        console.print(f"  [dim]Config stored at: {CONFIG_FILE}[/dim]\n")

        table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=True, header_style="bold #00f2fe")
        table.add_column("Key", justify="center", style="bold cyan", width=5)
        table.add_column("Setting", style="bold white", width=22)
        table.add_column("Current Value", style="bold")
        table.add_column("Description", style="grey78")

        notify_val = "[bold #00e676]ENABLED[/]" if config["notifications"] else "[dim]DISABLED[/]"
        subs_val = "[bold #00e676]ENABLED[/]" if config["embed_subs"] else "[dim]DISABLED[/]"
        cookies_val = f"[bold magenta]{config['browser_cookies']}[/]" if config["browser_cookies"] else "[dim]None[/]"

        table.add_row("1", "Desktop Notifications", notify_val, "System alerts upon download completion")
        table.add_row("2", "Default Audio Format", f"[cyan]{config['default_audio_fmt'].upper()}[/]", "Default format for quick audio downloads")
        table.add_row("3", "Default Video Res", f"[cyan]{config['default_video_res']}p[/]", "Default resolution ceiling for videos")
        table.add_row("4", "Embed Subtitles", subs_val, "Download and embed multilingual subs")
        table.add_row("5", "Browser Cookies", cookies_val, "Bypass age-restriction / login prompts")
        table.add_row("6", "Audio Directory", f"[blue]{config['audio_dir']}[/]", "Root folder for audio downloads")
        table.add_row("7", "Video Directory", f"[blue]{config['video_dir']}[/]", "Root folder for video downloads")
        table.add_row("b", "Back to Main Menu", "", "")
        console.print(table)

        choice = Prompt.ask("  Select setting to change", choices=["1", "2", "3", "4", "5", "6", "7", "b"], default="b")
        if choice == "1":
            config["notifications"] = not config["notifications"]
        elif choice == "2":
            config["default_audio_fmt"] = Prompt.ask("Choose audio format", choices=["mp3", "flac", "opus", "m4a", "wav"], default="mp3")
        elif choice == "3":
            config["default_video_res"] = Prompt.ask("Choose video resolution", choices=["2160", "1440", "1080", "720", "480", "best"], default="1080")
        elif choice == "4":
            config["embed_subs"] = not config["embed_subs"]
        elif choice == "5":
            config["browser_cookies"] = Prompt.ask("Choose browser cookies", choices=["", "firefox", "brave", "chrome", "chromium", "edge"], default="")
        elif choice == "6":
            new_path = Prompt.ask("Enter new Audio path", default=config["audio_dir"])
            config["audio_dir"] = str(Path(new_path).expanduser().resolve())
        elif choice == "7":
            new_path = Prompt.ask("Enter new Video path", default=config["video_dir"])
            config["video_dir"] = str(Path(new_path).expanduser().resolve())
        elif choice.lower() == "b":
            break

        save_config(config)

def menu_open_folders(config):
    render_banner(config)
    console.print("  [bold #00f2fe]📂 Open Media Folders[/]\n")
    table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=False)
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Action", style="bold white")
    table.add_row("1", f"Open Music Directory ({config['audio_dir']})")
    table.add_row("2", f"Open Video Directory ({config['video_dir']})")
    table.add_row("3", "Open Both")
    table.add_row("b", "Back")
    console.print(table)

    choice = Prompt.ask("  Choice", choices=["1", "2", "3", "b"], default="1")
    if choice == "1":
        open_path(config["audio_dir"])
    elif choice == "2":
        open_path(config["video_dir"])
    elif choice == "3":
        open_path(config["audio_dir"])
        open_path(config["video_dir"])

def do_update():
    console.clear()
    console.print(Panel("[bold #00f2fe]🔄 Checking and Updating yt-dlp...[/]", box=box.ROUNDED))
    res = subprocess.run(["yt-dlp", "-U"])
    if res.returncode != 0:
        console.print("\n[dim]Trying pip user update...[/dim]")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    console.print("\n[bold #00e676]Update check finished![/]")
    input("\nPress Enter to return...")

# ---------- Main Menu Loop ----------
def main_menu():
    config = load_config()
    check_dependencies()

    while True:
        render_banner(config)
        clip_url = get_clipboard_url()
        show_clipboard_banner(clip_url)

        table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=True, header_style="bold #00f2fe", expand=True)
        table.add_column("Key", justify="center", style="bold cyan", width=5)
        table.add_column("Action", style="bold white", width=25)
        table.add_column("Description", style="grey78")

        table.add_row("1", "🎵  Download Audio", "Spotify, Apple Music, YouTube Music, SoundCloud")
        table.add_row("2", "🎬  Download Video", "4K, 1440p, 1080p, 720p, or Best available")
        table.add_row("3", "🔁  Sync Playlist / Album", "Auto-folders: Spotify, Apple Music, YT Music, SoundCloud")
        table.add_row("4", "📋  From Clipboard", "Instantly fetch media from copied URL")
        table.add_row("5", "🔍  Media Library (fzf)", "Fuzzy search & instantly play downloaded media")
        table.add_row("6", "📂  Open Folders", "Open Music or Video folder in file manager")
        table.add_row("7", "🔧  Settings & Config", "Format, quality, cookies, notifications, paths")
        table.add_row("8", "🔄  Update yt-dlp", "Update extractors to latest release")
        table.add_row("q", "🚪  Exit", "Leave easydl")

        console.print(table)
        choice = Prompt.ask("  Choose an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "c", "q"], default="1")

        if choice == "1":
            menu_audio(config)
        elif choice == "2":
            menu_video(config)
        elif choice == "3":
            menu_playlist(config)
        elif choice in ["4", "c"]:
            menu_clipboard_direct(config)
        elif choice == "5":
            do_search(config)
        elif choice == "6":
            menu_open_folders(config)
        elif choice == "7":
            menu_settings(config)
            config = load_config()
        elif choice == "8":
            do_update()
        elif choice.lower() == "q":
            console.print("\n[bold #00e676]✨ Thank you for using easydl! Have a wonderful day.[/]\n")
            break

# ---------- CLI Argument Mode ----------
def cli_help():
    panel = Panel(f"""[bold #00f2fe]easydl[/] - A friendly, cross-platform media downloader & library manager

[bold white]USAGE:[/]
  easydl                                    Start interactive visual menu
  easydl [URL]                              Smart download prompt for URL
  easydl audio [OPTIONS] <URL>              Download audio (Spotify, Apple Music, YT Music, SoundCloud)
  easydl video [OPTIONS] <URL>              Download video directly
  easydl sync [OPTIONS] <URL> [FOLDER]      Sync playlist / album with auto-folder creation
  easydl spotify <URL>                      Download Spotify track/album/playlist into organized folder
  easydl apple <URL>                        Download Apple Music song/album/playlist into organized folder
  easydl ytmusic <URL>                      Download YouTube Music track/album/playlist
  easydl soundcloud <URL>                   Download SoundCloud track/set
  easydl clipboard                          Download whatever is in clipboard
  easydl search                             Fuzzy find & play downloaded files (fzf)
  easydl open [audio|video]                 Open downloads directory in file manager
  easydl update                             Update yt-dlp to latest release
  easydl config                             Print current configuration

[bold white]COMMAND ALIASES:[/]
  a, audio <url>                            Download audio (all music platforms)
  v, video <url>                            Download video
  s, sync, playlist <url> [folder]          Sync playlist / album into folder
  am, apple, applemusic <url>               Apple Music downloader
  sp, spotify <url>                         Spotify downloader
  ytm, ytmusic <url>                        YouTube Music downloader
  sc, soundcloud <url>                      SoundCloud downloader
  c, clip, clipboard                        Process URL in clipboard
  f, search                                 Launch library search

[bold white]OPTIONS:[/]
  -f, --format FORMAT                       Audio format: mp3, flac, opus, m4a, wav
  -q, --quality RES                         Video quality: 2160, 1440, 1080, 720, 480, best
  -o, --output DIR                          Custom output directory
  -b, --browser BROWSER                     Cookies from browser (firefox, brave, chrome, edge)
      --subs                                Download and embed subtitles
      --no-notify                           Disable desktop notification
  -h, --help                                Show this manual
  -V, --version                             Show version info

[bold white]EXAMPLES:[/]
  easydl "https://open.spotify.com/playlist/37i9dQZF1DZ06evO1duNex"
  easydl "https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb"
  easydl "https://music.youtube.com/playlist?list=..."
  easydl "https://soundcloud.com/octobersveryown/sets/..."
  easydl audio -f flac "https://youtu.be/..."
  easydl video -q 1080 "https://youtu.be/..."
  easydl sync "https://youtube.com/playlist?list=..."
  easydl clipboard""",
        title=f"[bold #00f2fe]easydl v{VERSION}[/]",
        border_style="#4facfe",
        box=box.ROUNDED
    )
    console.print(panel)

def run_cli():
    config = load_config()
    check_dependencies()
    args = sys.argv[1:]

    if not args or args[0] in ["-i", "--interactive"]:
        main_menu()
        return

    cmd = args[0]
    rest = args[1:]

    if cmd in ["-h", "--help", "help"]:
        cli_help()
        return

    if cmd in ["-V", "--version", "version"]:
        console.print(f"[bold #00f2fe]easydl[/] version [bold white]{VERSION}[/]")
        return

    if cmd in ["-u", "update"]:
        do_update()
        return

    if cmd in ["-f", "search"]:
        do_search(config)
        return

    if cmd in ["-c", "clip", "clipboard"]:
        clip_url = get_clipboard_url()
        if not clip_url:
            console.print("[bold red]Error: No media URL detected in clipboard.[/]")
            sys.exit(1)
        menu_clipboard_direct(config)
        return

    if cmd == "open":
        target = rest[0] if rest else "audio"
        p = config["video_dir"] if target == "video" else config["audio_dir"]
        open_path(p)
        return

    if cmd == "config":
        console.print(Panel(json.dumps(config, indent=2), title="[bold #00f2fe]Current Configuration[/]", box=box.ROUNDED))
        return

    if cmd in ["spotify", "sp"]:
        target_url = rest[0] if rest else prompt_url_smart("Spotify URL")
        sys.exit(download_spotify(target_url, config=config))

    if cmd in ["apple", "applemusic", "am"]:
        target_url = rest[0] if rest else prompt_url_smart("Apple Music URL")
        sys.exit(download_apple_music(target_url, config=config))

    if cmd in ["ytmusic", "ytm", "youtube-music"]:
        target_url = rest[0] if rest else prompt_url_smart("YouTube Music URL")
        sys.exit(download_audio(target_url, config=config))

    if cmd in ["soundcloud", "sc"]:
        target_url = rest[0] if rest else prompt_url_smart("SoundCloud URL")
        sys.exit(download_audio(target_url, config=config))

    if cmd in ["a", "audio"]:
        fmt = config["default_audio_fmt"]
        out = config["audio_dir"]
        url = None
        i = 0
        while i < len(rest):
            arg = rest[i]
            if arg in ["-f", "--format"] and i + 1 < len(rest):
                fmt = rest[i+1]
                i += 2
            elif arg in ["-o", "--output"] and i + 1 < len(rest):
                out = rest[i+1]
                i += 2
            elif arg in ["-b", "--browser"] and i + 1 < len(rest):
                config["browser_cookies"] = rest[i+1]
                i += 2
            elif arg == "--no-notify":
                config["notifications"] = False
                i += 1
            elif not arg.startswith("-"):
                url = arg
                i += 1
            else:
                i += 1
        if not url:
            url = prompt_url_smart("audio URL")
        if is_spotify_url(url):
            sys.exit(download_spotify(url, fmt=fmt, out_dir=out, config=config))
        if is_apple_music_url(url):
            sys.exit(download_apple_music(url, fmt=fmt, out_dir=out, config=config))
        sys.exit(download_audio(url, fmt=fmt, out_dir=out, config=config))

    if cmd in ["v", "video"]:
        res = config["default_video_res"]
        out = config["video_dir"]
        url = None
        i = 0
        while i < len(rest):
            arg = rest[i]
            if arg in ["-q", "--quality"] and i + 1 < len(rest):
                res = rest[i+1]
                i += 2
            elif arg in ["-o", "--output"] and i + 1 < len(rest):
                out = rest[i+1]
                i += 2
            elif arg in ["-b", "--browser"] and i + 1 < len(rest):
                config["browser_cookies"] = rest[i+1]
                i += 2
            elif arg == "--subs":
                config["embed_subs"] = True
                i += 1
            elif arg == "--no-notify":
                config["notifications"] = False
                i += 1
            elif not arg.startswith("-"):
                url = arg
                i += 1
            else:
                i += 1
        if not url:
            url = prompt_url_smart("video URL")
        if is_spotify_url(url):
            sys.exit(download_spotify(url, out_dir=config["audio_dir"], config=config))
        if is_apple_music_url(url):
            sys.exit(download_apple_music(url, out_dir=config["audio_dir"], config=config))
        sys.exit(download_video(url, res=res, out_dir=out, config=config))

    if cmd in ["s", "sync", "playlist"]:
        media_type = "audio"
        url = None
        folder = None
        for arg in rest:
            if arg.startswith("http"):
                url = arg
            elif arg in ["video", "audio"]:
                media_type = arg
            elif not arg.startswith("-"):
                folder = arg
        if not url:
            url = prompt_url_smart("playlist or album URL")
        if is_spotify_url(url):
            sys.exit(download_spotify(url, out_dir=config["audio_dir"], config=config))
        if is_apple_music_url(url):
            sys.exit(download_apple_music(url, out_dir=config["audio_dir"], config=config))
        sys.exit(sync_playlist(url, folder, media_type=media_type, config=config))

    if cmd.startswith("http://") or cmd.startswith("https://") or cmd.startswith("spotify:"):
        raw_url = cmd
        if is_spotify_url(raw_url):
            sys.exit(download_spotify(raw_url, config=config))
        if is_apple_music_url(raw_url):
            sys.exit(download_apple_music(raw_url, config=config))

        render_banner(config)
        plat = detect_platform(raw_url)
        pmeta = PLATFORM_META.get(plat, PLATFORM_META["generic"])
        console.print(Panel(f"[bold cyan]{raw_url}[/]", title=f"[bold {pmeta['color']}]{pmeta['icon']} {pmeta['name']} URL Provided[/]", box=box.ROUNDED, border_style=pmeta["color"]))
        table = Table(box=box.ROUNDED, border_style="#4facfe", show_header=False)
        table.add_column("Key", style="bold cyan", width=4)
        table.add_column("Action", style="bold white")
        table.add_row("1", f"🎵 Download Audio ({config['default_audio_fmt'].upper()})")
        table.add_row("2", f"🎬 Download Video ({config['default_video_res']}p)")
        table.add_row("3", "🎬 Download Video (Best Available)")
        table.add_row("4", "🔁 Sync as Playlist")
        console.print(table)
        ch = Prompt.ask("Choose action", choices=["1", "2", "3", "4"], default="1")
        if ch == "1":
            sys.exit(download_audio(raw_url, config=config))
        elif ch == "2":
            sys.exit(download_video(raw_url, res=config["default_video_res"], config=config))
        elif ch == "3":
            sys.exit(download_video(raw_url, res="best", config=config))
        elif ch == "4":
            f_name = Prompt.ask("Folder name (press Enter for auto-named folder)", default="")
            sys.exit(sync_playlist(raw_url, f_name or None, config=config))

    console.print(f"[bold red]Unknown command: {cmd}[/]")
    console.print("Run [bold cyan]easydl --help[/] for usage instructions.")
    sys.exit(1)

def main():
    try:
        run_cli()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Operation cancelled by user.[/dim]")
        sys.exit(0)

if __name__ == "__main__":
    main()
