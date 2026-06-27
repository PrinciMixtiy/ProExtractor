"""
Constants and magic numbers for the Pro Extractor desktop application.

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
MIN_WINDOW_WIDTH: Final[int] = 900
MIN_WINDOW_HEIGHT: Final[int] = 600

# Content and Cards
CONTENT_MARGIN: Final[int] = 16
CARD_SPACING: Final[int] = 8
BUTTON_HEIGHT: Final[int] = 28
INPUT_HEIGHT: Final[int] = 38

# Colors and Theme
ACCENT_COLOR: Final[str] = "#14b8a6"
ACCENT_HOVER_COLOR: Final[str] = "#0d9488"
SUCCESS_COLOR: Final[str] = "#22c55e"
WARNING_COLOR: Final[str] = "#f59e0b"
ERROR_COLOR: Final[str] = "#ef4444"
INFO_COLOR: Final[str] = "#3b82f6"

# Timeouts and Intervals
THEME_CHECK_INTERVAL: Final[int] = 5000  # milliseconds
SOCKET_TIMEOUT: Final[int] = 20  # seconds

# UI and Pagination Settings
DEFAULT_PAGE_SIZE: Final[int] = 30
MAX_CONCURRENT_LIMIT: Final[int] = 10
MIN_CONCURRENT_LIMIT: Final[int] = 1

# Queue Status Colors
QUEUE_WAITING_COLOR: Final[str] = "#f59e0b"  # Orange
QUEUE_ACTIVE_COLOR: Final[str] = "#22c55e"   # Green  
QUEUE_ERROR_COLOR: Final[str] = "#ef4444"    # Red
QUEUE_IDLE_COLOR: Final[str] = "#64748b"     # Gray

# UI Text Styles
QUEUE_STATUS_STYLE: Final[str] = "font-size: 12px; padding: 4px 8px; font-weight: 500;"
PAGE_LABEL_STYLE: Final[str] = "font-size: 12px; font-weight: 500; color: #64748b; background-color: transparent;"

# Network and Performance
FRAGMENT_RETRIES: Final[int] = 5

# Thumbnail
THUMBNAIL_DOWNLOAD_TIMEOUT: Final[int] = 10  # seconds
THUMBNAIL_EXTENSION: Final[str] = ".jpg"

# Directory Names
DATA_DIR_NAME: Final[str] = "data"
LOGS_DIR_NAME: Final[str] = "logs"

# Filename deduplication
MAX_FILENAME_ATTEMPTS: Final[int] = 1000

# Auto-resume
MAX_AUTO_RESUME_ATTEMPTS: Final[int] = 3

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

class Theme(Enum):
    """Theme enumeration."""
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"
