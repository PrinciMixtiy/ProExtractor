# PRO EXTRACTOR

A modern desktop application for downloading YouTube videos and playlists with a sleek dark/light theme interface.

## Features

- **Video & Playlist Downloads**: Download individual videos or entire YouTube playlists
- **Multiple Quality Options**: Choose from various video qualities (Highest, 1080p, 720p, 480p, 360p, Lowest)
- **Audio-only Downloads**: Extract audio in MP3 or M4A formats
- **Thumbnail Embedding**: Option to embed thumbnails in downloaded video files
- **Subtitle Support**: Auto-generate subtitles with language selection
- **Dark/Light Theme**: Automatic theme detection with manual override options (Auto, Light, Dark)
- **Download History**: Persistent history of all downloads with pagination support
- **Concurrent Downloads**: Configurable simultaneous downloads (1-10 max)
- **Production Logging**: Detailed logs saved to the user data directory for easy troubleshooting
- **Progress Tracking**: Real-time download progress with speed and ETA
- **FFmpeg Integration**: Bundled FFmpeg for video merging, audio extraction, and thumbnail embedding (no separate install needed for builds)
- **Configurable Filename Patterns**: Use tags like {title}, {id}, {author}, {duration}
- **Retry Mechanism**: Automatic retries on failure with exponential backoff
- **Browser Cookies**: Support for using browser cookies for authentication

## Architecture

### Core Components

- **`main.py`**: Application entry point with FFmpeg dependency checking
- **`core/constants.py`**: Centralized constants, enums (DownloadStatus, Theme), and configuration values
- **`core/downloader.py`**: Core download logic using yt-dlp with retry mechanism
- **`core/worker.py`**: Thread workers (InfoWorker, DownloadWorker) for non-blocking operations
- **`core/storage.py`**: History management with debounced JSON persistence
- **`core/config.py`**: Configuration manager with JSON persistence and environment variable support
- **`ui/main_window.py`**: Main application window with download queue management
- **`ui/sidebar.py`**: Navigation sidebar with collapsible buttons
- **`ui/settings.py`**: Settings interface with General, Downloads, and Advanced tabs
- **`ui/widgets.py`**: Custom UI components (VideoInfoCard, TaskItem, PaginationWidget, etc.)
- **`ui/icons.py`**: Icon management
- **`styles.py`**: Dynamic theming system with dark/light support
- **`core/utils.py`**: Shared utilities like centralized filename sanitization
- **`core/ffmpeg_manager.py`**: FFmpeg path resolution for bundled and system installs
- **`generate_build.py`**: Automated build script with FFmpeg bundling support

### Design Patterns

- **MVC Architecture**: Clear separation between UI and business logic
- **Worker Thread Pattern**: Non-blocking downloads using QThread with proper signal-slot communication
- **Debounced Persistence**: History saves are batched to avoid UI freezes during large playlist operations
- **Virtualized Lists**: UI widgets created only for visible history pages to manage memory with large playlists

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- FFmpeg (bundled in builds; system install required for development)
- Git (for cloning the repository)

### Dependencies

The application requires the following Python packages:

```
PySide6==6.11.0
yt-dlp
darkdetect
requests
secretstorage
cryptography
Pillow
```

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ProExtractor
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**:
   
   **On Ubuntu/Debian**:
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
   
   **On macOS**:
   ```bash
   brew install ffmpeg
   ```
   
   **On Windows**:
   - Download from https://ffmpeg.org/download.html
   - Add to system PATH
   
   **Verify installation**:
   ```bash
   ffmpeg -version
   ```

## Running the Application

### Development Mode

```bash
# Navigate to project directory
cd ProExtractor

# Activate virtual environment (if not already active)
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run the application
python main.py
```

### Production Distribution

To generate a standalone executable (no Python or FFmpeg required on target machine):

```bash
# Optional: Install PyInstaller manually or let the script handle it
python generate_build.py
```

The build script will:
1. Download the appropriate FFmpeg binary for your platform (Windows/macOS/Linux)
2. Bundle FFmpeg into the executable
3. Configure yt-dlp to use the bundled FFmpeg automatically

The executable will be located in the `dist/` folder.

**Note**: First build may take longer due to FFmpeg download (~100MB). Subsequent builds reuse the cached FFmpeg in `resources/ffmpeg/`.

## Configuration

### Settings Tabs

The application settings are organized into four tabs:

1. **General**: Default download folder, filename pattern, theme (Auto/Light/Dark), language
2. **Downloads**: Concurrent downloads limit, retry attempts, default quality/format, subtitle options
3. **Authentication**: Browser cookie source for accessing restricted content, per-site cookie settings
4. **Advanced**: FFmpeg path configuration (auto-detects bundled FFmpeg), custom data and log directories

### Configuration File

Settings are stored in JSON format:

- **Windows**: `%APPDATA%/pro-extractor/config.json`
- **macOS/Linux**: `~/.config/pro-extractor/config.json`

### Environment Variables

The following environment variables can override configuration values:

- `YOUTUBE_DOWNLOADER_GENERAL_DEFAULT_DOWNLOAD_FOLDER`: Override default download folder
- `YOUTUBE_DOWNLOADER_GENERAL_THEME`: Override theme setting (auto, light, dark)
- `YOUTUBE_DOWNLOADER_DOWNLOADS_MAX_CONCURRENT`: Override max concurrent downloads
- `YOUTUBE_DOWNLOADER_DOWNLOADS_RETRIES_ON_FAILURE`: Override retry attempts
- `YOUTUBE_DOWNLOADER_ADVANCED_FFMPEG_PATH`: Override FFmpeg executable path
- `YOUTUBE_DOWNLOADER_PATHS_DATA_DIR`: Override data directory path
- `YOUTUBE_DOWNLOADER_PATHS_LOG_DIR`: Override log directory path

### Default Directories

- **Configuration**: `~/.config/pro-extractor/` (Linux/macOS) or `%APPDATA%/pro-extractor` (Windows)
- **Data**: Application's `data/` directory (or custom path if configured)
- **Thumbnails**: `~/Desktop/YoutubeThumbnails` (default, created at runtime)

## Troubleshooting

### Common Issues

1. **FFmpeg not found**:
   - Ensure FFmpeg is installed and in system PATH
   - Or set custom path in Settings > Advanced > FFmpeg Path
   - Restart the application after installation

2. **Import errors**:
   - Verify virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **UI not rendering**:
   - Check PySide6 installation
   - Update graphics drivers

4. **Download failures**:
   - Check internet connection
   - Verify YouTube URL is valid
   - Check yt-dlp updates: `pip install --upgrade yt-dlp`
   - Increase retry attempts in Settings > Downloads

5. **Permission errors**:
   - Ensure write permissions to download directory
   - Check directory ownership

6. **Large playlist memory usage**:
   - The app uses virtualized lists and debounced saves to manage large playlists
   - If issues persist, try reducing concurrent downloads in settings

## Development

### Project Structure

```
ProExtractor/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── styles.py            # Theme and styling system
├── generate_build.py    # Build script for standalone executable
├── core/                # Core business logic
│   ├── __init__.py
│   ├── constants.py     # Constants and enums
│   ├── config.py        # Configuration management
│   ├── downloader.py    # Download engine with yt-dlp
│   ├── ffmpeg_manager.py # FFmpeg path resolution for bundled/system installs
│   ├── worker.py        # Thread workers for async operations
│   ├── storage.py       # History persistence with debounced saves
│   └── utils.py         # Shared utilities
├── ui/                  # User interface
│   ├── __init__.py
│   ├── main_window.py   # Main application window
│   ├── sidebar.py       # Navigation sidebar
│   ├── settings.py      # Settings UI (General/Downloads/Advanced tabs)
│   ├── widgets.py       # Custom UI components
│   └── icons.py         # Icon management
├── assets/              # Static assets (icons)
├── data/                # Application data (history.json)
└── resources/           # Additional resources
```


### Contributing Guidelines

1. Follow PEP 8 style guidelines
2. Add type hints to new code
3. Update `core/constants.py` for any new magic numbers
4. Use the existing worker pattern for async operations
5. Follow the signal-slot pattern for UI updates from background threads
6. Use debounced saves for any new persistent data to avoid UI freezes

## License

This project is licensed under GNU General Public License v3.0 - see the LICENSE file for details.

## Acknowledgments

- **yt-dlp**: For YouTube video extraction
- **PySide6**: For the Qt6 Python bindings
- **darkdetect**: For automatic theme detection
- **FFmpeg**: For video processing capabilities
- **secretstorage**: For secure credential storage
- **cryptography**: For encryption
- **Pillow**: Build icon files
