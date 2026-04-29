"""
Help and troubleshooting dialogs for Pro Extractor.

This module provides in-app troubleshooting assistance, error explanations
with actionable fixes, and log viewing capabilities.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QGridLayout, QTabWidget,
    QFileDialog, QMessageBox, QSpacerItem, QSizePolicy,
    QApplication, QWidget
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont
from styles import get_theme_colors
from ui.icons import get_icon
from core.constants import APP_NAME
from pathlib import Path
import logging
import sys
import os
import subprocess


class ErrorAnalyzer:
    """Analyzes error messages and provides actionable solutions."""
    
    ERROR_PATTERNS = {
        "network": {
            "patterns": [
                "network", "connection", "timeout", "unreachable",
                "failed to establish", "ssl", "certificate", "urlopen",
                "no route to host", "connection refused", "dns",
                "error fetching", "failed to resolve", "name resolution",
                "temporary failure", "transport error", "httpsconnection",
                "unable to download", "giving up after"
            ],
            "title": "Network Connection Issue",
            "description": "The app cannot reach the video server. This could be due to:",
            "causes": [
                "Internet connection is down or unstable",
                "YouTube servers are temporarily unavailable",
                "Firewall or antivirus is blocking the connection",
                "DNS resolution is failing"
            ],
            "solutions": [
                "Check your internet connection and try again",
                "Wait a few minutes and retry (servers may be busy)",
                "Temporarily disable VPN/proxy if using one",
                "Check firewall settings and allow Pro Extractor",
                "Try using a different network (mobile hotspot)",
                "Restart your router/modem"
            ],
            "icon": "search.png"
        },
        "rate_limit": {
            "patterns": [
                "rate limit", "429", "too many requests", "throttled",
                "slow down", "retry after", "exceeded"
            ],
            "title": "Rate Limited by YouTube",
            "description": "YouTube has temporarily limited your download speed or blocked requests.",
            "causes": [
                "Too many downloads in a short time period",
                "Large playlist causing many sequential requests",
                "IP address flagged for high activity"
            ],
            "solutions": [
                "Wait 10-15 minutes before trying again",
                "Reduce concurrent downloads in Settings → Downloads",
                "Try enabling browser cookies (Settings → Authentication)",
                "Consider using a VPN to change your IP address",
                "Download smaller batches at a time"
            ],
            "icon": "pause.png"
        },
        "permission": {
            "patterns": [
                "permission denied", "access denied", "forbidden", "403",
                "unauthorized", "private video", "not available", "restricted"
            ],
            "title": "Access Denied or Private Video",
            "description": "The video cannot be accessed. This may be due to:",
            "causes": [
                "Video is private or age-restricted",
                "Video has been removed or region-blocked",
                "You need to be logged in to view this content",
                "Channel requires membership/subscription"
            ],
            "solutions": [
                "Check if the video plays in your browser",
                "If private: ask the owner for access",
                "If age-restricted: enable browser cookies in Settings → Authentication",
                "If login required: select your browser in cookie settings",
                "Try a different video from the same channel"
            ],
            "icon": "info.png"
        },
        "ffmpeg": {
            "patterns": [
                "ffmpeg", "encoder", "codec", "conversion failed",
                "postprocessor", "merge", "mux", "post-process"
            ],
            "title": "Video Processing Error (FFmpeg)",
            "description": "The video downloaded but could not be processed or merged.",
            "causes": [
                "FFmpeg is missing or incorrectly installed",
                "Corrupted download requiring manual cleanup",
                "Unsupported video format combination",
                "Insufficient disk space during processing"
            ],
            "solutions": [
                "Ensure FFmpeg is installed: check Settings → Advanced",
                "Restart the app and try again",
                "Try downloading in a different format (MP4 instead of audio)",
                "Disable 'Extract Thumbnails' option temporarily",
                "Free up disk space (at least 2x the video size needed)",
                "Try a lower quality setting"
            ],
            "icon": "settings.png"
        },
        "disk_space": {
            "patterns": [
                "no space", "disk full", "insufficient space", "write error",
                "out of space", "storage", "cannot write", "i/o error"
            ],
            "title": "Insufficient Disk Space",
            "description": "Your download drive is running out of free space.",
            "causes": [
                "Download folder disk is nearly full",
                "Video file larger than expected",
                "Temporary files consuming space"
            ],
            "solutions": [
                "Free up disk space or choose a different download folder",
                "Change download location in Settings → General",
                "Clear completed downloads from history",
                "Empty your Recycle Bin/Trash",
                "Download to an external drive with more space"
            ],
            "icon": "folder.png"
        },
        "invalid_url": {
            "patterns": [
                "invalid url", "url error", "bad url", "malformed",
                "not a valid url", "unsupported url", "cannot download",
                "incomplete youtube id", "truncated", "looks truncated",
                "invalidurlerror", "invalid url exception"
            ],
            "title": "Invalid or Unsupported URL",
            "description": "The provided URL cannot be processed.",
            "causes": [
                "URL is malformed or incomplete",
                "Platform is not supported (only YouTube officially supported)",
                "Video has been deleted or is unavailable",
                "URL is a channel/playlist page without video ID"
            ],
            "solutions": [
                "Copy the full video URL from your browser's address bar",
                "Ensure the video is from youtube.com or youtu.be",
                "Check that the video hasn't been deleted",
                "For playlists: use the playlist URL, not individual videos",
                "Try refreshing the video page and copying the URL again"
            ],
            "icon": "link.png"
        },
        "yt_dlp": {
            "patterns": [
                "yt-dlp", "ytdlp", "extractor", "signature", "cipher",
                "unable to extract", "formats", "player response"
            ],
            "title": "YouTube Extraction Error",
            "description": "The video format information could not be extracted.",
            "causes": [
                "YouTube changed their website structure",
                "yt-dlp library is outdated",
                "Video uses a new streaming format"
            ],
            "solutions": [
                "Update yt-dlp: pip install --upgrade yt-dlp",
                "Restart the application after updating",
                "Try a different video from the same channel",
                "Check the View Logs button for more details",
                "Report the issue if it persists across multiple videos"
            ],
            "icon": "retry.png"
        },
        "cancelled": {
            "patterns": [
                "cancelled", "canceled", "user interrupt", "stopped"
            ],
            "title": "Download Cancelled",
            "description": "The download was cancelled by user action.",
            "causes": [
                "You clicked Cancel or Pause during download",
                "Application was closed during download",
                "System shutdown interrupted the process"
            ],
            "solutions": [
                "Click the Resume/Retry button to continue",
                "Partial downloads can usually be resumed",
                "If resuming fails, delete the partial file and retry"
            ],
            "icon": "pause.png"
        }
    }
    
    @classmethod
    def analyze(cls, error_message: str) -> dict:
        """Analyze error message and return matching solution data."""
        error_lower = error_message.lower()
        
        for category, data in cls.ERROR_PATTERNS.items():
            for pattern in data["patterns"]:
                if pattern in error_lower:
                    return {
                        "category": category,
                        **data
                    }
        
        # Default/fallback for unrecognized errors
        return {
            "category": "unknown",
            "title": "Unknown Error",
            "description": "An unexpected error occurred during download.",
            "causes": [
                "Unknown technical issue",
                "Temporary software glitch"
            ],
            "solutions": [
                "Click Retry to attempt the download again",
                "Check your internet connection",
                "Restart the application",
                "View the logs for technical details",
                "Report the issue if it persists"
            ],
            "icon": "warning.png"
        }


class TroubleshootingDialog(QDialog):
    """Dialog showing actionable troubleshooting for errors."""
    
    def __init__(self, error_message: str, parent=None, context: str = ""):
        super().__init__(parent)
        self.error_message = error_message
        self.context = context  # Human-readable label for what operation failed
        self.analysis = ErrorAnalyzer.analyze(error_message)
        self._setup_ui()
        self._apply_theme()
        
    def _setup_ui(self):
        self.setWindowTitle("Troubleshooting Help")
        self.setMinimumSize(550, 450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        colors = get_theme_colors()
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon(self.analysis.get("icon", "help.png"), colors['accent']).pixmap(32, 32))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.analysis["title"])
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['text_primary']};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Error message display
        error_frame = QFrame()
        error_frame.setObjectName("ErrorFrame")
        error_frame.setStyleSheet(f"""
            #ErrorFrame {{
                background-color: {colors['bg_dark']};
                border-left: 3px solid #f43f5e;
                border-radius: 4px;
                padding: 12px;
            }}
        """)
        error_layout = QVBoxLayout(error_frame)
        
        # Show operation context (e.g. "Download Failed") if provided,
        # otherwise fall back to the generic label.
        header_text = self.context if self.context else "Error Details:"
        error_header = QLabel(header_text)
        error_header.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {colors['text_secondary']};")
        error_layout.addWidget(error_header)
        
        error_text = QLabel(self.error_message)
        error_text.setWordWrap(True)
        error_text.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        error_layout.addWidget(error_text)
        
        layout.addWidget(error_frame)
        
        # Description
        desc_label = QLabel(self.analysis["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: 13px; color: {colors['text_primary']};")
        layout.addWidget(desc_label)
        
        # Possible Causes
        causes_header = QLabel("Possible Causes:")
        causes_header.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {colors['text_primary']};")
        layout.addWidget(causes_header)
        
        causes_text = "\n".join(f"• {cause}" for cause in self.analysis["causes"])
        causes_label = QLabel(causes_text)
        causes_label.setStyleSheet(f"font-size: 12px; color: {colors['text_secondary']}; padding-left: 8px;")
        layout.addWidget(causes_label)
        
        # Solutions section
        solutions_header = QLabel("Recommended Solutions:")
        solutions_header.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {colors['text_primary']};")
        layout.addWidget(solutions_header)
        
        # Solutions with numbered steps
        for i, solution in enumerate(self.analysis["solutions"], 1):
            solution_row = QHBoxLayout()
            solution_row.setSpacing(8)
            
            num_label = QLabel(f"{i}.")
            num_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {colors['accent']};")
            num_label.setFixedWidth(20)
            solution_row.addWidget(num_label)
            
            sol_label = QLabel(solution)
            sol_label.setWordWrap(True)
            sol_label.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
            solution_row.addWidget(sol_label, 1)
            
            layout.addLayout(solution_row)
        
        layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.view_logs_btn = QPushButton(" View Logs")
        self.view_logs_btn.setIcon(get_icon("folder.png", colors['text_secondary']))
        self.view_logs_btn.setIconSize(QSize(16, 16))
        self.view_logs_btn.setFixedHeight(36)
        self.view_logs_btn.clicked.connect(self._open_logs)
        button_layout.addWidget(self.view_logs_btn)
        
        button_layout.addStretch()
        
        self.retry_btn = QPushButton(" Retry Download")
        self.retry_btn.setIcon(get_icon("retry.png", "#ffffff"))
        self.retry_btn.setIconSize(QSize(16, 16))
        self.retry_btn.setFixedHeight(36)
        self.retry_btn.setObjectName("PrimaryButton")
        self.retry_btn.clicked.connect(self._on_retry)
        button_layout.addWidget(self.retry_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedHeight(36)
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_theme(self):
        colors = get_theme_colors()
        
        primary_btn_style = f"""
            QPushButton#PrimaryButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {colors['accent_hover']};
            }}
        """
        
        secondary_btn_style = f"""
            QPushButton {{
                background-color: {colors['bg_dark']};
                color: {colors['text_primary']};
                border: 1px solid {colors['outer_border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['outer_border']};
            }}
        """
        
        self.setStyleSheet(primary_btn_style + secondary_btn_style)
        
    def _open_logs(self):
        """Open logs folder in file manager or show log viewer."""
        try:
            # Determine log directory
            if sys.platform == 'win32':
                log_dir = Path(os.environ.get('APPDATA', '.')) / APP_NAME / "logs"
            elif sys.platform == 'darwin':
                log_dir = Path.home() / "Library" / "Logs" / APP_NAME
            else:
                log_dir = Path.home() / ".config" / APP_NAME / "logs"
            
            if log_dir.exists():
                # Open folder in system file manager
                if sys.platform == 'win32':
                    subprocess.run(['explorer', str(log_dir)])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', str(log_dir)])
                else:
                    subprocess.run(['xdg-open', str(log_dir)])
            else:
                QMessageBox.information(self, "Logs Not Found", 
                                       f"Log directory does not exist yet:\n{log_dir}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open logs: {str(e)}")
    
    def _on_retry(self):
        """Signal to retry the download."""
        self.done(100)  # Custom return code for retry


class LogViewerDialog(QDialog):
    """Dialog for viewing application logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._apply_theme()
        self._load_logs()
        
        # Scroll to bottom after dialog is fully rendered (longer delay for layout)
        QTimer.singleShot(300, self._scroll_to_bottom)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        colors = get_theme_colors()
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Application Logs")
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {colors['text_primary']};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(get_icon("retry.png", colors['text_secondary']))
        refresh_btn.setIconSize(QSize(14, 14))
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_and_scroll)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton(" Export")
        export_btn.setIcon(get_icon("download.png", colors['text_secondary']))
        export_btn.setIconSize(QSize(14, 14))
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self._export_logs)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Log display
        info_label = QLabel("These logs can help diagnose issues. Use the Export button to save for reporting.")
        info_label.setStyleSheet(f"font-size: 11px; color: {colors['text_secondary']};")
        layout.addWidget(info_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['bg_dark']};
                color: {colors['text_primary']};
                border: 1px solid {colors['outer_border']};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.log_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
    def _apply_theme(self):
        colors = get_theme_colors()
        btn_style = f"""
            QPushButton {{
                background-color: {colors['bg_dark']};
                color: {colors['text_primary']};
                border: 1px solid {colors['outer_border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['outer_border']};
            }}
        """
        self.setStyleSheet(btn_style)
        
    def _load_logs(self):
        """Load recent log entries."""
        try:
            # Determine log directory
            if sys.platform == 'win32':
                log_dir = Path(os.environ.get('APPDATA', '.')) / APP_NAME / "logs"
            elif sys.platform == 'darwin':
                log_dir = Path.home() / "Library" / "Logs" / APP_NAME
            else:
                log_dir = Path.home() / ".config" / APP_NAME / "logs"
            
            if not log_dir.exists():
                self.log_text.setPlainText("No logs found. Log directory does not exist yet.")
                return
            
            # Get log files sorted chronologically (oldest first)
            log_files = sorted(log_dir.glob("app-*.log"))  # Oldest first
            
            if not log_files:
                self.log_text.setPlainText("No log files found.")
                return
            
            # Load last 500 lines from most recent files (process oldest first, newest last)
            all_lines = []
            for log_file in log_files[-3:]:  # Last 3 days (most recent files)
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                        all_lines.extend([f"=== {log_file.name} ===\n"])
                        all_lines.extend(lines[-200:])  # Last 200 lines per file
                except Exception as e:
                    all_lines.append(f"Error reading {log_file.name}: {e}\n")
            
            content = "".join(all_lines[-500:])  # Keep last 500 total lines
            self.log_text.setPlainText(content)
            
        except Exception as e:
            self.log_text.setPlainText(f"Error loading logs: {str(e)}")
    
    def _scroll_to_bottom(self):
        """Scroll log view to the bottom (most recent entries)."""
        def do_scroll():
            # Move cursor to end
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
            # Ensure cursor is visible
            self.log_text.ensureCursorVisible()
            
            # Also set scrollbar to max
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Multiple retries at increasing intervals to catch final layout
        for delay in [0, 100, 300, 500]:
            QTimer.singleShot(delay, do_scroll)
    
    def _refresh_and_scroll(self):
        """Reload logs and scroll to bottom (for refresh button)."""
        self._load_logs()
        self._scroll_to_bottom()
    
    def _export_logs(self):
        """Export logs to a file."""
        try:
            # Determine log directory
            if sys.platform == 'win32':
                log_dir = Path(os.environ.get('APPDATA', '.')) / APP_NAME / "logs"
            elif sys.platform == 'darwin':
                log_dir = Path.home() / "Library" / "Logs" / APP_NAME
            else:
                log_dir = Path.home() / ".config" / APP_NAME / "logs"
            
            if not log_dir.exists():
                QMessageBox.warning(self, "No Logs", "No log files found to export.")
                return
            
            # Let user choose save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Logs",
                str(Path.home() / "pro-extractor-logs.txt"),
                "Text Files (*.txt);;All Files (*.*)"
            )
            
            if not file_path:
                return
            
            # Collect all log content
            all_content = []
            for log_file in sorted(log_dir.glob("app-*.log")):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        all_content.append(f"\n{'='*60}\n")
                        all_content.append(f"{log_file.name}\n")
                        all_content.append(f"{'='*60}\n\n")
                        all_content.append(f.read())
                except Exception as e:
                    all_content.append(f"Error reading {log_file.name}: {e}\n")
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("".join(all_content))
            
            QMessageBox.information(self, "Export Complete", 
                                   f"Logs exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export logs: {str(e)}")


def show_troubleshooting(parent, error_message: str, context: str = "") -> bool:
    """Show troubleshooting dialog and return True if user wants to retry.
    
    Args:
        parent: Parent widget.
        error_message: The raw backend error string (used for pattern matching).
        context: Optional human-readable label shown in the dialog to explain
                 what operation failed (e.g. "Video Info Fetch Failed").
                 Kept separate from error_message so it doesn't corrupt analysis.
    """
    dialog = TroubleshootingDialog(error_message, parent, context=context)
    result = dialog.exec()
    return result == 100  # 100 is retry code


def show_log_viewer(parent=None):
    """Show the log viewer dialog."""
    dialog = LogViewerDialog(parent)
    dialog.exec()


class LegalDialog(QDialog):
    """Dialog displaying Legal and Compliance Documents."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Legal & Compliance")
        self.setMinimumSize(650, 550)
        self._setup_ui()
        self._apply_theme()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        colors = get_theme_colors()
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("info.png", colors['accent']).pixmap(32, 32))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Legal & Compliance Documents")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['text_primary']};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignTop)
        
        # Section 1: Terms of Service
        tos_section = self._create_section(
            "Terms of Service",
            "By using Pro Extractor, you agree to the following terms:",
            [
                "Pro Extractor is provided 'as is' without warranties of any kind.",
                "Users are solely responsible for ensuring their use complies with applicable laws in their jurisdiction.",
                "The application is intended for personal, non-commercial use only.",
                "You agree not to use this software for any unlawful purpose or to infringe upon the rights of others.",
                "We reserve the right to modify these terms at any time. Continued use constitutes acceptance of changes."
            ],
            colors
        )
        content_layout.addWidget(tos_section)
        
        # Section 2: Copyright Disclaimer
        copyright_section = self._create_section(
            "Copyright Disclaimer",
            "Important information regarding downloaded content:",
            [
                "Users bear full responsibility for the content they choose to download.",
                "Pro Extractor does not host, store, or distribute any media content.",
                "It is the user's responsibility to respect copyright laws and intellectual property rights.",
                "Only download content that you have the legal right to access and save.",
                "Unauthorized downloading of copyrighted material may violate laws in your country."
            ],
            colors
        )
        content_layout.addWidget(copyright_section)
        
        # Section 3: YouTube Terms Compliance
        youtube_section = self._create_section(
            "YouTube Terms of Service Compliance",
            "This application operates in accordance with YouTube's terms:",
            [
                "Pro Extractor uses yt-dlp, an open-source library for extracting video information.",
                "We do not circumvent any technical protection measures implemented by YouTube.",
                "Downloaded content should not be redistributed, sold, or used for commercial purposes.",
                "Users must comply with YouTube's Terms of Service available at youtube.com/t/terms.",
                "This tool is intended for personal archival and offline viewing purposes only."
            ],
            colors
        )
        content_layout.addWidget(youtube_section)
        
        # Section 4: Privacy Policy
        privacy_section = self._create_section(
            "Privacy Policy",
            "Your privacy is important to us. Our commitment to you:",
            [
                "All data storage is local-only. No data is transmitted to external servers.",
                "Download history is stored locally on your device for your convenience.",
                "Application logs are kept locally and are not shared with any third parties.",
                "No personal information is collected, transmitted, or sold.",
                "You can clear your history and logs at any time through the application settings.",
                "We do not use cookies, analytics, or tracking of any kind."
            ],
            colors
        )
        content_layout.addWidget(privacy_section)
        
        # Acceptance notice
        accept_frame = QFrame()
        accept_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_dark']};
                border-left: 3px solid {colors['accent']};
                border-radius: 4px;
                padding: 12px;
            }}
        """)
        accept_layout = QVBoxLayout(accept_frame)
        
        accept_label = QLabel(
            "By continuing to use Pro Extractor, you acknowledge that you have read, "
            "understood, and agree to be bound by these Legal and Compliance Documents."
        )
        accept_label.setWordWrap(True)
        accept_label.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        accept_layout.addWidget(accept_label)
        
        content_layout.addWidget(accept_frame)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("I Understand")
        close_btn.setFixedHeight(40)
        close_btn.setObjectName("PrimaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
    def _create_section(self, title: str, description: str, bullets: list, colors: dict) -> QFrame:
        """Create a styled section with title, description, and bullet points."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['outer_border']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
        layout.addWidget(title_lbl)
        
        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        layout.addWidget(desc_lbl)
        
        # Bullet points
        for bullet in bullets:
            row = QHBoxLayout()
            row.setSpacing(8)
            
            bullet_lbl = QLabel("•")
            bullet_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
            row.addWidget(bullet_lbl)
            
            text_lbl = QLabel(bullet)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"font-size: 12px; color: {colors['text_secondary']};")
            row.addWidget(text_lbl, 1)
            
            layout.addLayout(row)
        
        return section
        
    def _apply_theme(self):
        colors = get_theme_colors()
        
        btn_style = f"""
            QPushButton#PrimaryButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {colors['accent_hover']};
            }}
        """
        self.setStyleSheet(btn_style)


def show_legal(parent=None):
    """Show the legal and compliance dialog."""
    dialog = LegalDialog(parent)
    dialog.exec()


class SettingsHelpDialog(QDialog):
    """Dialog displaying contextual help documentation for Settings."""

    def __init__(self, parent=None, initial_tab=0):
        super().__init__(parent)
        self.setWindowTitle("Settings Help")
        self.setMinimumSize(700, 550)
        self.initial_tab = initial_tab
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        colors = get_theme_colors()

        # Header
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setPixmap(get_icon("info.png", colors['accent']).pixmap(32, 32))
        header_layout.addWidget(icon_label)

        title_label = QLabel("Settings Help & Documentation")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['text_primary']};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Tab widget for different help sections
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Create help tabs
        self._create_general_help_tab()
        self._create_downloads_help_tab()
        self._create_authentication_help_tab()
        self._create_advanced_help_tab()

        layout.addWidget(self.tab_widget)

        # Set initial tab
        self.tab_widget.setCurrentIndex(self.initial_tab)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _create_help_scroll_area(self, content_widget):
        """Create a scroll area for help content."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(content_widget)
        return scroll

    def _create_help_section(self, title: str, description: str, bullets: list = None) -> QFrame:
        """Create a styled help section."""
        colors = get_theme_colors()

        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['outer_border']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
        layout.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        layout.addWidget(desc_lbl)

        # Bullet points
        if bullets:
            for bullet in bullets:
                row = QHBoxLayout()
                row.setSpacing(8)

                bullet_lbl = QLabel("")
                bullet_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
                row.addWidget(bullet_lbl)

                text_lbl = QLabel(bullet)
                text_lbl.setWordWrap(True)
                text_lbl.setStyleSheet(f"font-size: 12px; color: {colors['text_secondary']};")
                row.addWidget(text_lbl, 1)

                layout.addLayout(row)

        return section

    def _create_general_help_tab(self):
        """Create General settings help tab."""
        colors = get_theme_colors()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignTop)

        # Download Folder section
        folder_section = self._create_help_section(
            "Default Download Folder",
            "Choose where downloaded videos are saved by default.",
            [
                "Use the browse button to select a folder on your computer",
                "All downloads will be saved to this location unless changed per download",
                "Ensure the folder has sufficient free space for your downloads"
            ]
        )
        layout.addWidget(folder_section)

        # Filename Pattern section
        pattern_section = self._create_help_section(
            "Filename Pattern",
            "Customize how downloaded files are named using dynamic tags.",
            [
                "{title} - Video title",
                "{uploader} - Channel/creator name",
                "{upload_date} - Upload date (YYYYMMDD format)",
                "{id} - Video ID",
                "{resolution} - Video quality (e.g., 1080p)"
            ]
        )
        layout.addWidget(pattern_section)

        # Theme section
        theme_section = self._create_help_section(
            "Appearance Theme",
            "Select the visual theme for the application.",
            [
                "Auto - Follows your system theme preference",
                "Light - Bright interface with dark text",
                "Dark - Dark interface with light text (easier on eyes in low light)"
            ]
        )
        layout.addWidget(theme_section)

        # Language section
        lang_section = self._create_help_section(
            "Interface Language",
            "Choose the display language for the application interface.",
            [
                "Available languages: English, Spanish, French, German, Chinese",
                "Changing this affects menus, buttons, and labels",
                "Downloaded content language is controlled separately in Downloads settings"
            ]
        )
        layout.addWidget(lang_section)

        layout.addStretch()

        scroll = self._create_help_scroll_area(content)
        self.tab_widget.addTab(scroll, "General")

    def _create_downloads_help_tab(self):
        """Create Downloads settings help tab."""
        colors = get_theme_colors()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignTop)

        # Concurrent Downloads section
        concurrent_section = self._create_help_section(
            "Download Limits",
            "Control how many downloads run simultaneously.",
            [
                "Max Concurrent Downloads: How many videos download at the same time (1-8)",
                "Higher values use more bandwidth but complete batches faster",
                "Lower values reduce network strain and are gentler on servers",
                "Retries on Failure: How many times to retry failed downloads"
            ]
        )
        layout.addWidget(concurrent_section)

        # Download Options section
        options_section = self._create_help_section(
            "Download Options",
            "Additional features for downloaded content.",
            [
                "Auto-resume downloads - Continue interrupted downloads automatically",
                "Embed thumbnails - Add video thumbnail as cover art in the file",
                "Auto-generate subtitles - Download subtitles if available",
                "Default Subtitle Language - Preferred language code (en, es, fr, etc.)"
            ]
        )
        layout.addWidget(options_section)

        # Quality and Format section
        quality_section = self._create_help_section(
            "Default Quality and Format",
            "Set preferred video quality and file format.",
            [
                "Quality options: Highest, 1080p, 720p, 480p, 360p, Lowest",
                "Higher quality = larger file size",
                "Format: MP4 (video with audio) or MP3 (audio only)",
                "These are defaults - can be changed per download"
            ]
        )
        layout.addWidget(quality_section)

        # Performance section
        perf_section = self._create_help_section(
            "Performance",
            "Network timeout and connection settings.",
            [
                "Request Timeout: Seconds to wait for server response (10-300)",
                "Increase timeout for slow connections or large files",
                "Decrease for faster failure detection on unstable networks"
            ]
        )
        layout.addWidget(perf_section)

        layout.addStretch()

        scroll = self._create_help_scroll_area(content)
        self.tab_widget.addTab(scroll, "Downloads")

    def _create_authentication_help_tab(self):
        """Create Authentication settings help tab with cookie setup instructions."""
        colors = get_theme_colors()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignTop)

        # Browser Cookie Source section
        browser_section = self._create_help_section(
            "Browser Cookie Source",
            "Extract cookies from your browser to access restricted content.",
            [
                "Select the browser you use to watch videos (Chrome, Firefox, Edge, Safari)",
                "The app extracts cookies to authenticate with video platforms",
                "Cookies allow downloading age-restricted and private videos",
                "Select 'Disabled' to never use browser cookies"
            ]
        )
        layout.addWidget(browser_section)

        # Cookie Setup Instructions section (detailed)
        setup_frame = QFrame()
        setup_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['outer_border']};
                border-radius: 8px;
            }}
        """)
        setup_layout = QVBoxLayout(setup_frame)
        setup_layout.setSpacing(12)
        setup_layout.setContentsMargins(16, 16, 16, 16)

        setup_title = QLabel("Browser Cookie Setup Instructions")
        setup_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
        setup_layout.addWidget(setup_title)

        setup_desc = QLabel(
            "To download age-restricted, private, or members-only videos, "
            "you need to be logged into the video platform in your browser. "
            "The app will use your browser's cookies to authenticate."
        )
        setup_desc.setWordWrap(True)
        setup_desc.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        setup_layout.addWidget(setup_desc)

        # Platform-specific instructions
        platforms = [
            ("YouTube (youtube.com)", [
                "1. Open YouTube in your selected browser",
                "2. Sign in to your Google account",
                "3. Ensure you can watch the video in the browser",
                "4. Select the same browser in app settings",
                "5. For age-restricted videos: You must verify age in browser first"
            ]),
            ("TikTok (tiktok.com)", [
                "1. Open TikTok in your selected browser",
                "2. Sign in to your account",
                "3. Verify you can view the private/restricted content",
                "4. Select the same browser in app settings"
            ]),
            ("Instagram (instagram.com)", [
                "1. Open Instagram in your selected browser",
                "2. Sign in to your account",
                "3. Ensure you can view the private account/reels",
                "4. Select the same browser in app settings"
            ])
        ]

        for platform_name, steps in platforms:
            platform_label = QLabel(platform_name)
            platform_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {colors['text_primary']}; margin-top: 8px;")
            setup_layout.addWidget(platform_label)

            for step in steps:
                step_row = QHBoxLayout()
                step_row.setSpacing(8)

                step_text = QLabel(step)
                step_text.setWordWrap(True)
                step_text.setStyleSheet(f"font-size: 11px; color: {colors['text_secondary']};")
                step_row.addWidget(step_text, 1)
                setup_layout.addLayout(step_row)

        setup_note = QLabel(
            "Note: Cookies are read-only and never transmitted. "
            "The app only extracts them to authenticate download requests."
        )
        setup_note.setWordWrap(True)
        setup_note.setStyleSheet(f"font-size: 11px; color: {colors['accent']}; font-style: italic; margin-top: 8px;")
        setup_layout.addWidget(setup_note)

        layout.addWidget(setup_frame)

        # Per-Site Cookie Usage section
        per_site_section = self._create_help_section(
            "Per-Site Cookie Usage",
            "Control which sites use your browser cookies.",
            [
                "Enable cookies for sites where you need authentication",
                "Disable for sites where you want anonymous downloads",
                "Add custom domains for sites not in the default list",
                "'Unspecified Domains' setting controls behavior for new sites"
            ]
        )
        layout.addWidget(per_site_section)

        layout.addStretch()

        scroll = self._create_help_scroll_area(content)
        self.tab_widget.addTab(scroll, "Authentication")

    def _create_advanced_help_tab(self):
        """Create Advanced settings help tab with environment variables."""
        colors = get_theme_colors()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignTop)

        # FFmpeg Configuration section
        ffmpeg_section = self._create_help_section(
            "FFmpeg Configuration",
            "Path to FFmpeg executable for video processing.",
            [
                "FFmpeg is required for merging audio/video streams",
                "Leave blank for auto-detection (recommended)",
                "Only set manually if FFmpeg is not in system PATH",
                "Required for: thumbnail embedding, format conversion, post-processing"
            ]
        )
        layout.addWidget(ffmpeg_section)

        # Storage Paths section
        storage_section = self._create_help_section(
            "Storage Paths",
            "Customize where application data and logs are stored.",
            [
                "Data Directory: Application configuration and cache files",
                "Log Directory: Download and error logs for troubleshooting",
                "Leave blank to use default system locations",
                "Changing paths requires app restart to take full effect"
            ]
        )
        layout.addWidget(storage_section)

        # Environment Variables section (detailed)
        env_frame = QFrame()
        env_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['outer_border']};
                border-radius: 8px;
            }}
        """)
        env_layout = QVBoxLayout(env_frame)
        env_layout.setSpacing(12)
        env_layout.setContentsMargins(16, 16, 16, 16)

        env_title = QLabel("Environment Variable Overrides")
        env_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {colors['accent']};")
        env_layout.addWidget(env_title)

        env_desc = QLabel(
            "All settings can be overridden using environment variables. "
            "This is useful for containerized deployments or system-wide configuration. "
            "Format: PRO_EXTRACTOR_<CATEGORY>_<SETTING>"
        )
        env_desc.setWordWrap(True)
        env_desc.setStyleSheet(f"font-size: 12px; color: {colors['text_primary']};")
        env_layout.addWidget(env_desc)

        # Environment variables table
        env_vars = [
            ("PRO_EXTRACTOR_GENERAL_DEFAULT_DOWNLOAD_FOLDER", "Download folder path"),
            ("PRO_EXTRACTOR_GENERAL_DEFAULT_FILENAME_PATTERN", "Filename template"),
            ("PRO_EXTRACTOR_GENERAL_THEME", "Theme: auto, light, dark"),
            ("PRO_EXTRACTOR_GENERAL_LANGUAGE", "Language code: en, es, fr, de, zh"),
            ("PRO_EXTRACTOR_DOWNLOADS_MAX_CONCURRENT", "Number (1-8)"),
            ("PRO_EXTRACTOR_DOWNLOADS_RETRIES_ON_FAILURE", "Number of retry attempts"),
            ("PRO_EXTRACTOR_DOWNLOADS_AUTO_RESUME", "true or false"),
            ("PRO_EXTRACTOR_DOWNLOADS_DEFAULT_QUALITY", "highest, 1080p, 720p, etc."),
            ("PRO_EXTRACTOR_DOWNLOADS_DEFAULT_FORMAT", "mp4 or mp3"),
            ("PRO_EXTRACTOR_DOWNLOADS_TIMEOUT", "Seconds (10-300)"),
            ("PRO_EXTRACTOR_AUTH_BROWSER_SOURCE", "chrome, firefox, edge, safari, none"),
            ("PRO_EXTRACTOR_ADVANCED_FFMPEG_PATH", "Path to ffmpeg executable"),
            ("PRO_EXTRACTOR_PATHS_DATA_DIR", "Custom data directory"),
            ("PRO_EXTRACTOR_PATHS_LOG_DIR", "Custom log directory")
        ]

        # Create table-like display
        table_widget = QWidget()
        table_layout = QGridLayout(table_widget)
        table_layout.setSpacing(4)
        table_layout.setContentsMargins(0, 8, 0, 0)
        table_layout.setColumnStretch(0, 2)
        table_layout.setColumnStretch(1, 1)

        # Header row
        var_header = QLabel("Variable Name")
        var_header.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {colors['text_primary']};")
        table_layout.addWidget(var_header, 0, 0)

        val_header = QLabel("Value/Format")
        val_header.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {colors['text_primary']};")
        table_layout.addWidget(val_header, 0, 1)

        for i, (var_name, value_format) in enumerate(env_vars, 1):
            var_label = QLabel(var_name)
            var_label.setStyleSheet(f"font-size: 10px; font-family: 'Consolas', 'Monaco', monospace; color: {colors['text_secondary']};")
            table_layout.addWidget(var_label, i, 0)

            val_label = QLabel(value_format)
            val_label.setStyleSheet(f"font-size: 10px; color: {colors['text_secondary']};")
            table_layout.addWidget(val_label, i, 1)

        env_layout.addWidget(table_widget)

        # Example section
        example_label = QLabel("Example Usage:")
        example_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {colors['text_primary']}; margin-top: 12px;")
        env_layout.addWidget(example_label)

        example_code = QLabel(
            "# Linux/macOS export\n"
            "export PRO_EXTRACTOR_GENERAL_THEME=dark\n"
            "export PRO_EXTRACTOR_DOWNLOADS_MAX_CONCURRENT=2\n\n"
            "# Windows PowerShell\n"
            "$env:PRO_EXTRACTOR_GENERAL_THEME = \"dark\"\n\n"
            "# Docker\n"
            "docker run -e PRO_EXTRACTOR_GENERAL_THEME=dark ..."
        )
        example_code.setStyleSheet(f"""
            font-size: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            color: {colors['text_secondary']};
            background-color: {colors['bg_dark']};
            padding: 12px;
            border-radius: 4px;
        """)
        example_code.setWordWrap(True)
        env_layout.addWidget(example_code)

        layout.addWidget(env_frame)

        layout.addStretch()

        scroll = self._create_help_scroll_area(content)
        self.tab_widget.addTab(scroll, "Advanced")

    def _apply_theme(self):
        colors = get_theme_colors()

        tab_style = f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {colors['bg_dark']};
                color: {colors['text_secondary']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                margin-right: 4px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['accent']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {colors['outer_border']};
                color: {colors['text_primary']};
            }}
        """
        self.setStyleSheet(tab_style)


def show_settings_help(parent=None, initial_tab=0):
    """Show the settings help dialog."""
    dialog = SettingsHelpDialog(parent, initial_tab)
    dialog.exec()
