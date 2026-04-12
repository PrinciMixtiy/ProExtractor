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
- **FFmpeg Integration**: For high-quality video merging and audio extraction
- **Configurable Filename Patterns**: Use tags like {title}, {id}, {author}, {duration}
- **Retry Mechanism**: Automatic retries on failure with exponential backoff

## Architecture

### Core Components

- **`main.py`**: Application entry point with FFmpeg dependency checking
- **`core/constants.py`**: Centralized constants, enums (DownloadStatus, Theme, Quality), and configuration values
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
- **`generate_build.py`**: Automated build script for creating standalone executables

### Design Patterns

- **MVC Architecture**: Clear separation between UI and business logic
- **Worker Thread Pattern**: Non-blocking downloads using QThread with proper signal-slot communication
- **Debounced Persistence**: History saves are batched to avoid UI freezes during large playlist operations
- **Virtualized Lists**: UI widgets created only for visible history pages to manage memory with large playlists

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required for video processing)
- Git (for cloning the repository)

### Dependencies

The application requires the following Python packages:

```
PySide6==6.11.0
yt-dlp
darkdetect
requests
```

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd YoutubeDownloader/desktop
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

5. **Install AtomicParsley** (Recommended for MP4 thumbnails):

    **On Ubuntu/Debian**:
    ```bash
    sudo apt update
    sudo apt install atomicparsley
    ```

    **On macOS**:
    ```bash
    brew install atomicparsley
    ```

    **On Windows**:
    - Download from official repository
    - Add to system PATH

    **Verify installation**:
    ```bash
    AtomicParsley --version
    ```

## Running the Application

### Development Mode

```bash
# Navigate to desktop directory
cd desktop

# Activate virtual environment (if not already active)
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run the application
python main.py
```

### Production Distribution

To generate a standalone executable (no Python required on target machine):

```bash
# Optional: Install PyInstaller manually or let the script handle it
python generate_build.py
```

The executable will be located in the `dist/` folder.

## Configuration

### Settings Tabs

The application settings are organized into three tabs:

1. **General**: Default download folder, filename pattern, theme (Auto/Light/Dark), language
2. **Downloads**: Concurrent downloads limit, retry attempts, default quality/format, subtitle options
3. **Advanced**: FFmpeg path configuration, custom data directory

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

### Default Directories

- **Configuration**: `~/.config/pro-extractor/` (Linux/macOS) or `%APPDATA%/pro-extractor` (Windows)
- **Data**: Application's `desktop/data/` directory (or custom path if configured)
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
desktop/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── styles.py           # Theme and styling system
├── core/               # Core business logic
│   ├── constants.py    # Constants and enums
│   ├── config.py     # Configuration management
│   ├── downloader.py   # Download engine with yt-dlp
│   ├── worker.py       # Thread workers for async operations
│   └── storage.py      # History persistence with debounced saves
├── ui/                 # User interface
│   ├── main_window.py  # Main application window
│   ├── sidebar.py      # Navigation sidebar
│   ├── settings.py     # Settings UI (General/Downloads/Advanced tabs)
│   ├── widgets.py      # Custom UI components
│   └── icons.py        # Icon management
├── assets/             # Static assets
├── data/               # Application data (history.json)
└── resources/          # Additional resources
```


### Contributing Guidelines

1. Follow PEP 8 style guidelines
2. Add type hints to new code
3. Update `core/constants.py` for any new magic numbers
4. Use the existing worker pattern for async operations
5. Follow the signal-slot pattern for UI updates from background threads
6. Use debounced saves for any new persistent data to avoid UI freezes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **yt-dlp**: For YouTube video extraction
- **PySide6**: For the Qt6 Python bindings
- **darkdetect**: For automatic theme detection
- **FFmpeg**: For video processing capabilities
