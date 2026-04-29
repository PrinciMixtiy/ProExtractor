# Pro Extractor - User Guide

A simple, powerful desktop app for downloading YouTube videos and playlists.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Downloading Videos](#downloading-videos)
- [Downloading Playlists](#downloading-playlists)
- [Managing Downloads](#managing-downloads)
- [Settings](#settings)
- [Download History](#download-history)
- [Tips & Troubleshooting](#tips--troubleshooting)

---

## Getting Started

### Installation

**Option 1: Download Pre-built Version (Recommended)**

Download the latest release for your operating system from the releases page. No additional software required—everything is included.

**Option 2: Run from Source (Advanced Users)**

See `README.md` for developer setup instructions.

### First Launch

When you open Pro Extractor for the first time:

1. The app automatically detects your system's light/dark theme
2. A default download folder is set (you can change this in Settings)
3. You're ready to start downloading

---

## Downloading Videos

### Quick Download

1. **Paste a URL** — Copy any YouTube video link and paste it into the search bar at the top
2. **Press Enter or click the Download button** — The app will fetch video information
3. **Choose your options** — Select quality, format, and other options in the video card that appears
4. **Click Download** — The video joins your download queue

### Video Options

| Option | Description |
|--------|-------------|
| **Quality** | Choose from Highest, 1080p, 720p, 480p, 360p, or Lowest |
| **Format** | MP4 (video), MP3 (audio only), or M4A (audio only) |
| **Subtitles** | Auto-generate subtitles in your preferred language |
| **Thumbnail** | Embed the video thumbnail in the downloaded file |

**Tip:** The thumbnail option only works with video formats (MP4), not audio-only downloads.

---

## Downloading Playlists

### How to Download a Playlist

1. **Paste the playlist URL** — Any YouTube playlist link works
2. **Press Enter** — The app loads all videos in the playlist
3. **Review the playlist** — You'll see all videos listed with checkboxes
4. **Select videos** — Check/uncheck individual videos, or use "Select All" / "Clear All"
5. **Set download options** — Choose quality, format, and subtitle preferences
6. **Click Download** — Selected videos are added to your queue

### Playlist Controls

- **Select All** — Check every video in the playlist
- **Clear All** — Uncheck all videos
- **Individual checkboxes** — Choose specific videos you want
- **Pagination** — Large playlists are split into pages for easier browsing

---

## Managing Downloads

### The Download Queue

Active and pending downloads appear in the main task list. Each download shows:

- **Title** — Video name
- **Progress bar** — Visual progress indicator
- **Percentage** — Exact download completion %
- **Speed** — Current download speed
- **ETA** — Estimated time remaining
- **Status** — Waiting, Downloading, Processing, Complete, or Error

### Queue Colors

| Color | Meaning |
|-------|---------|
| **Gray** | Waiting in queue |
| **Blue** | Currently downloading |
| **Green** | Completed successfully |
| **Red** | Error occurred |

### Actions

- **Cancel** — Stop an active or queued download
- **Retry** — Attempt to re-download a failed item
- **Open Folder** — Jump to the download location (available after completion)

### Concurrent Downloads

By default, Pro Extractor downloads **3 videos at once**. You can change this in Settings → Downloads (range: 1–10).

---

## Settings

Access settings by clicking **Settings** in the left sidebar.

### General Tab

| Setting | Description |
|---------|-------------|
| **Download Folder** | Where downloaded files are saved. Click "Browse" to change. |
| **Filename Pattern** | How files are named. Available tags: `{title}`, `{id}`, `{author}`, `{duration}`. Default: `{title}` |
| **Theme** | Auto (follows system), Light, or Dark |
| **Language** | Preferred language for subtitles and UI |

**Filename Example:**
- Pattern: `{author} - {title}`
- Result: `ChannelName - Video Title.mp4`

### Downloads Tab

| Setting | Description |
|---------|-------------|
| **Concurrent Downloads** | How many videos download simultaneously (1–10) |
| **Retry Attempts** | How many times to retry failed downloads (0–10) |
| **Default Quality** | Pre-selected quality for new downloads |
| **Default Format** | Pre-selected format (MP4/MP3/M4A) |
| **Subtitles** | Enable/disable subtitles by default |
| **Subtitle Languages** | Comma-separated list of preferred subtitle languages (e.g., `en,es,fr`) |

### Authentication Tab

Use this if you need to download age-restricted or private videos.

| Setting | Description |
|---------|-------------|
| **Browser Cookies** | Select which browser to use cookies from (Chrome, Firefox, Edge, Safari) |
| **Per-Site Settings** | Configure different browsers for different websites |

**Note:** You must be logged into YouTube in the selected browser for this to work.

### Advanced Tab

| Setting | Description |
|---------|-------------|
| **FFmpeg Path** | Usually auto-detected. Only change if you know what you're doing. |
| **Data Directory** | Where app data (history) is stored |
| **Log Directory** | Where log files are saved |

---

## Download History

All completed downloads are saved in your history. Access it by clicking **History** in the sidebar.

### History Features

- **Search** — Find past downloads by title
- **Pagination** — Browse through large history lists (20 items per page)
- **Re-download** — Click the download icon to download again
- **Open Location** — Click the folder icon to open the file location
- **Clear History** — Remove all history entries (does not delete files)

### History Storage

History is saved automatically and persists between app restarts. The data is stored in:

- **Windows:** `%APPDATA%/pro-extractor/`
- **macOS/Linux:** `~/.config/pro-extractor/`

---

## Tips & Troubleshooting

### Tips

**Download Speed**
- Lower quality = faster downloads
- Fewer concurrent downloads = more bandwidth per file
- Downloads may pause briefly when merging audio/video—this is normal

**Organizing Files**
- Use the `{author}` tag in filenames to group videos by creator
- Change your download folder per project/playlist

**Age-Restricted Content**
- Enable browser cookie authentication in Settings → Authentication
- Make sure you're logged into YouTube in that browser

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "FFmpeg not found" error | If using a pre-built version, try re-downloading. If running from source, install FFmpeg (see README.md). |
| Download fails immediately | Check your internet connection. Try increasing retry attempts in Settings. |
| Video won't play after download | Try a different quality setting. Some formats require specific players. |
| Slow download speeds | Reduce concurrent downloads in Settings, or choose a lower quality. |
| Subtitles not appearing | Make sure the video has subtitles available. Check your language codes in Settings. |
| App won't start | Check that your system meets requirements. View logs via Help → View Logs. |

### Getting Help

1. **View Logs** — Go to Help → View Logs to see detailed error information
2. **Check for Updates** — Make sure you're using the latest version
3. **Report Issues** — Include log files when reporting problems

### Log Files

Logs are helpful for troubleshooting. They are stored at:

- **Windows:** `%APPDATA%/pro-extractor/logs/`
- **macOS:** `~/Library/Logs/pro-extractor/`
- **Linux:** `~/.config/pro-extractor/logs/`

Logs are automatically cleaned up after 7 days.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + V` | Paste URL into search bar (when search is focused) |
| `Enter` | Submit URL / Start download |
| `Esc` | Cancel current dialog or clear search |

---

## Supported Sites

Pro Extractor uses yt-dlp under the hood, supporting hundreds of sites beyond YouTube. While optimized for YouTube, you can try pasting URLs from:

- YouTube (primary support)
- YouTube Music
- YouTube Shorts
- Other yt-dlp supported sites (experimental)

---

*Last updated: See git commit history for latest changes*
