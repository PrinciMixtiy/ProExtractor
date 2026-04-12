"""
Constants and magic numbers for Video Downloader Desktop.

This module centralizes all constant values used throughout the application
to improve maintainability and reduce magic numbers.
"""

from typing import Final
from enum import Enum

# Application metadata
APP_NAME: Final[str] = "PRO EXTRACTOR"
APP_VERSION: Final[str] = "1.0.0"
ORG_NAME: Final[str] = "Princi"

# UI Dimensions
MIN_WINDOW_WIDTH: Final[int] = 1100
MIN_WINDOW_HEIGHT: Final[int] = 700
DEFAULT_WINDOW_WIDTH: Final[int] = 1200
DEFAULT_WINDOW_HEIGHT: Final[int] = 800

# Header and Sidebar
HEADER_HEIGHT: Final[int] = 70
SIDEBAR_WIDTH: Final[int] = 280
SIDEBAR_COLLAPSED_WIDTH: Final[int] = 60
SIDEBAR_BUTTON_HEIGHT: Final[int] = 50
SIDEBAR_ICON_SIZE: Final[int] = 22

# Content and Cards
CONTENT_MARGIN: Final[int] = 32
CARD_SPACING: Final[int] = 16
CARD_CORNER_RADIUS: Final[int] = 12
THUMBNAIL_HEIGHT: Final[int] = 200
BUTTON_HEIGHT: Final[int] = 40
INPUT_HEIGHT: Final[int] = 36

# Progress and Status
PROGRESS_BAR_HEIGHT: Final[int] = 6
STATUS_ICON_SIZE: Final[int] = 16
ANIMATION_DURATION: Final[int] = 300

# Colors and Theme
ACCENT_COLOR: Final[str] = "#14b8a6"
ACCENT_HOVER_COLOR: Final[str] = "#0d9488"
SUCCESS_COLOR: Final[str] = "#22c55e"
WARNING_COLOR: Final[str] = "#f59e0b"
ERROR_COLOR: Final[str] = "#ef4444"
INFO_COLOR: Final[str] = "#3b82f6"

# Timeouts and Intervals
THEME_CHECK_INTERVAL: Final[int] = 5000  # milliseconds
HTTP_TIMEOUT: Final[int] = 30  # seconds
SOCKET_TIMEOUT: Final[int] = 20  # seconds
RETRY_DELAY: Final[int] = 1000  # milliseconds
WORKER_TIMEOUT: Final[int] = 300  # seconds

# Download Settings
DEFAULT_MAX_CONCURRENT: Final[int] = 3
DEFAULT_RETRIES: Final[int] = 5
DEFAULT_CHUNK_SIZE: Final[int] = 8192
DEFAULT_QUALITY: Final[str] = "highest"
DEFAULT_FORMAT: Final[str] = "mp4"

# UI and Pagination Settings
DEFAULT_PAGE_SIZE: Final[int] = 30
MAX_PAGE_SIZE: Final[int] = 100
MIN_PAGE_SIZE: Final[int] = 10
MAX_CONCURRENT_LIMIT: Final[int] = 10
MIN_CONCURRENT_LIMIT: Final[int] = 1

# Queue Status Colors
QUEUE_WAITING_COLOR: Final[str] = "#f59e0b"  # Orange
QUEUE_ACTIVE_COLOR: Final[str] = "#22c55e"   # Green  
QUEUE_ERROR_COLOR: Final[str] = "#ef4444"    # Red
QUEUE_IDLE_COLOR: Final[str] = "#64748b"     # Gray

# UI Text Styles
QUEUE_STATUS_STYLE: Final[str] = "font-size: 12px; padding: 4px 8px; font-weight: 500;"
PAGE_LABEL_STYLE: Final[str] = "font-weight: 500; color: #64748b;"

# File and Path Limits
MAX_FILENAME_LENGTH: Final[int] = 255
MAX_URL_LENGTH: Final[int] = 2048
MAX_TITLE_LENGTH: Final[int] = 200

# Network and Performance
MAX_RETRIES: Final[int] = 5
FRAGMENT_RETRIES: Final[int] = 5
CONNECTION_TIMEOUT: Final[int] = 30
READ_TIMEOUT: Final[int] = 30

# File Size Limits (bytes)
MAX_FILE_SIZE: Final[int] = 5 * 1024 * 1024 * 1024  # 5GB
THUMBNAIL_MAX_SIZE: Final[int] = 1024 * 1024  # 1MB

# Supported Formats
SUPPORTED_VIDEO_FORMATS: Final[tuple] = ("mp4", "webm", "mkv", "avi", "mov")
SUPPORTED_AUDIO_FORMATS: Final[tuple] = ("mp3", "m4a", "wav", "flac", "ogg")
SUPPORTED_IMAGE_FORMATS: Final[tuple] = ("jpg", "jpeg", "png", "webp")

# Filename Pattern Tags
FILENAME_TAGS: Final[dict] = {
    "title": "Video title",
    "id": "Video ID",
    "author": "Channel name",
    "duration": "Video duration"
}

# Error Messages
ERROR_MESSAGES: Final[dict] = {
    "ffmpeg_not_found": "FFmpeg not found! Please install it and add it to your PATH.",
    "invalid_url": "Invalid URL provided. Please check and try again.",
    "download_failed": "Download failed. Please check your internet connection.",
    "file_not_found": "File not found. The download may have been cancelled.",
    "permission_denied": "Permission denied. Please check folder permissions.",
    "disk_full": "Disk full. Please free up space and try again.",
    "network_error": "Network error. Please check your internet connection."
}

# Status Messages
STATUS_MESSAGES: Final[dict] = {
    "fetching_info": "Fetching video information...",
    "download_queued": "Download queued",
    "download_started": "Download started",
    "download_paused": "Download paused",
    "download_completed": "Download completed",
    "download_failed": "Download failed",
    "download_cancelled": "Download cancelled",
    "processing": "Processing...",
    "merging": "Merging video and audio...",
    "extracting_audio": "Extracting audio...",
    "generating_thumbnail": "Generating thumbnail...",
    "downloading_subtitle": "Downloading subtitle..."
}

class DownloadStatus(Enum):
    """Download status enumeration."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROCESSING = "processing"

class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Theme(Enum):
    """Theme enumeration."""
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"

class Quality(Enum):
    """Video quality enumeration."""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"

# Regular Expressions
YOUTUBE_URL_PATTERN: Final[str] = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
PLAYLIST_PATTERN: Final[str] = r'[?&]list=([a-zA-Z0-9_-]+)'
VIDEO_ID_PATTERN: Final[str] = r'(?:v=|\/|embed\/)([0-9A-Za-z_-]{11})'

# File Extensions
THUMBNAIL_EXTENSION: Final[str] = ".jpg"
CONFIG_EXTENSION: Final[str] = ".json"
LOG_EXTENSION: Final[str] = ".log"

# Directory Names
DATA_DIR_NAME: Final[str] = "data"
CACHE_DIR_NAME: Final[str] = "cache"
TEMP_DIR_NAME: Final[str] = "temp"
LOGS_DIR_NAME: Final[str] = "logs"
ASSETS_DIR_NAME: Final[str] = "assets"
ICONS_DIR_NAME: Final[str] = "icons"

# MIME Types
THUMBNAIL_MIME_TYPE: Final[str] = "image/jpeg"
VIDEO_MIME_TYPE: Final[str] = "video/mp4"
AUDIO_MIME_TYPE: Final[str] = "audio/mpeg"

# Keyboard Shortcuts
SHORTCUTS: Final[dict] = {
    "new_download": "Ctrl+N",
    "open_folder": "Ctrl+O",
    "settings": "Ctrl+,",
    "quit": "Ctrl+Q",
    "minimize": "Ctrl+M",
    "about": "F1"
}
