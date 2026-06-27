"""
Main application window for the Pro Extractor desktop application.

This module provides the primary UI window containing the sidebar navigation,
search functionality, task list with pagination, and download management.
It coordinates between the UI components, download workers, and history storage.
"""

import os
import logging
from core.worker import WorkerThread, InfoWorker, DownloadWorker
from core.storage import HistoryManager
from core.config import config
from core.downloader import DesktopDownloader
from core.constants import (DEFAULT_PAGE_SIZE,
                                    QUEUE_WAITING_COLOR, QUEUE_ACTIVE_COLOR,
                                    QUEUE_STATUS_STYLE, THEME_CHECK_INTERVAL,
                                    THUMBNAIL_DOWNLOAD_TIMEOUT, MIN_WINDOW_WIDTH,
                                    MIN_WINDOW_HEIGHT, THUMBNAIL_EXTENSION, DownloadStatus,
                                    MAX_FILENAME_ATTEMPTS, MAX_AUTO_RESUME_ATTEMPTS)
from ui.sidebar import Sidebar
from ui.settings import SettingsPage
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QScrollArea,
                               QMessageBox, QFrame, QStackedWidget, QMenu,
                               QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer, Slot, QSize, QThread
from typing import Dict, List, Set, Tuple, Any, Optional
from PySide6.QtGui import QTransform
from styles import get_stylesheet, get_theme_colors
from ui.icons import get_icon
from ui.widgets import (VideoInfoCard, StreamOptionsCard, TaskItem,
                                PlaylistItemWidget, VirtualPlaylistWidget, PaginationWidget)
from ui.help_dialog import show_troubleshooting, show_log_viewer, TroubleshootingDialog, show_legal
import uuid
import requests
import re


class TaskItemWidgetPool:
    """Widget pool for reusing TaskItem instances (memory optimization).

    Instead of destroying and creating widgets on every page navigation,
    this pool reuses existing widgets, significantly reducing:
    - Memory allocation overhead
- Garbage collection pressure
    - UI flickering during pagination
    """

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self._available: list = []  # Widgets ready for reuse
        self._in_use: dict = {}  # task_id -> widget mapping

    def acquire(self, task_id: str, title: str, source: str = "", thumb_path: str = ""):
        """Get a widget from pool or create new if empty."""
        from ui.widgets import TaskItem

        # Return existing if already in use for this task
        if task_id in self._in_use:
            return self._in_use[task_id]

        # Try to reuse from pool
        if self._available:
            widget = self._available.pop()
            widget.reset(task_id, title, source, thumb_path)
        else:
            # Create new widget
            widget = TaskItem(task_id, title, source, thumb_path)

        self._in_use[task_id] = widget
        return widget

    def release(self, task_id: str):
        """Return widget to pool for reuse."""
        if task_id in self._in_use:
            widget = self._in_use.pop(task_id)
            # Keep widget in pool if under max size
            if len(self._available) < self.max_size:
                self._available.append(widget)
                return widget  # Return for caller to hide/remove from layout
            return None  # Widget should be deleted
        return None

    def release_all(self):
        """Release all in-use widgets back to pool."""
        widgets_to_return = list(self._in_use.values())
        self._in_use.clear()

        for widget in widgets_to_return:
            # Check if C++ object is still valid before operating on it
            try:
                # Attempt a harmless operation to test if object is valid
                _ = widget.isVisible()
            except RuntimeError:
                # C++ object already deleted, skip this widget
                continue

            if len(self._available) < self.max_size:
                self._available.append(widget)
            else:
                widget.deleteLater()

        return widgets_to_return

    def clear(self):
        """Clear pool and delete all widgets."""
        for widget in self._available:
            widget.deleteLater()
        for widget in self._in_use.values():
            widget.deleteLater()
        self._available.clear()
        self._in_use.clear()


class ThumbnailWorker(QThread):
    finished_one = Signal(str, str)

    def __init__(self, tasks, thumb_dir):
        super().__init__()
        self.tasks = tasks
        self.thumb_dir = thumb_dir

    def run(self):
        for t in self.tasks:
            task_id = t.get('task_id')
            if not task_id:
                continue

            thumb_path = os.path.join(self.thumb_dir, f"{task_id}{THUMBNAIL_EXTENSION}")
            if os.path.exists(thumb_path):
                self.finished_one.emit(task_id, thumb_path)
                continue

            thumb_url = t.get('thumb_url')
            if not thumb_url:
                url = t.get('url', '')
                m = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url)
                if m:
                    thumb_url = f"https://img.youtube.com/vi/{m.group(1)}/mqdefault.jpg"

            if thumb_url:
                try:
                    resp = requests.get(thumb_url, timeout=THUMBNAIL_DOWNLOAD_TIMEOUT)
                    if resp.status_code == 200:
                        with open(thumb_path, 'wb') as f:
                            f.write(resp.content)
                        self.finished_one.emit(task_id, thumb_path)
                except Exception as e:
                    logging.getLogger(__name__).debug(
                        f"Thumbnail fetch failed for {task_id}: {e}")


class MainWindow(QMainWindow):
    # Theme change signal
    theme_changed = Signal()

    def __init__(self, tasks=None, thumb_dir=None):
        super().__init__()
        self.setWindowTitle("PRO EXTRACTOR")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Set defaults if not provided
        if tasks is None:
            tasks = []
        if thumb_dir is None:
            thumb_dir = os.path.expanduser("~/Desktop/YoutubeThumbnails")

        self.history_manager = HistoryManager()
        self._downloader = DesktopDownloader()
        self._reconcile_history_on_startup()
        self.active_workers: Dict[str, Tuple[QThread, Any]] = {}  # task_id -> (thread, worker)
        # Task queues store only task metadata to keep memory usage low.
        # UI widgets are created only for the currently visible history page.
        # List of (task_id, url, dest, options) - will be processed (active/pending)
        self.pending_tasks: List[Tuple[str, str, str, dict]] = []
        # List of (task_id, url, dest, options) - waiting behind capacity
        self.queued_tasks: List[Tuple[str, str, str, dict]] = []
        self.visible_widgets: Dict[str, Any] = {}  # task_id -> TaskItem for currently displayed page only

        # Memory optimization: widget pool for reusing TaskItem instances
        # This reduces allocation overhead and GC pressure during pagination
        self._task_widget_pool = TaskItemWidgetPool(max_size=20)

        # Prevent duplicate thumbnail downloads and reduce peak memory.
        self._thumbnail_requested_task_ids: Set[str] = set()

        # Throttle refreshes during bursty status changes (starting/promoting many tasks).
        self._refresh_scheduled: bool = False
        # Allow exactly one history page rebuild even while downloads are active.
        # This is needed so the first page contents appear right after clicking
        # "Start Download" (destination folder selection).
        self._allow_history_rebuild_once: bool = False
        # Duplicate-file dialog: None = ask each time; "copy" | "replace" | "skip" when remembered for this batch.
        self._duplicate_policy: Optional[str] = None

        # Performance optimization: O(1) lookup sets
        self.active_task_ids: Set[str] = set()  # Track active task IDs
        self.pending_task_ids: Set[str] = set()  # Track pending task IDs
        self.queued_task_ids: Set[str] = set()   # Track queued task IDs

        # Track active filenames to prevent concurrent download conflicts
        # Maps destination_dir -> set of filenames currently being downloaded
        self._active_filenames: Dict[str, Set[str]] = {}
        # Maps task_id -> (dest, filename) for active downloads to enable cleanup
        self._task_filenames: Dict[str, Tuple[str, str]] = {}

        self.max_concurrent: int = config.get('downloads.max_concurrent', 4)
        self.current_info: Optional[dict] = None
        self.running_info_workers: List[Tuple[QThread, Any]] = []  # Track active info workers to prevent crash

        # Pagination for history
        self.pagination_widget = PaginationWidget(page_size=DEFAULT_PAGE_SIZE)
        self.pagination_widget.page_changed.connect(self._load_history_page)

        # Log pagination setup
        self.logger.debug(
            f"Pagination widget initialized with page_size={DEFAULT_PAGE_SIZE}")

        # Queue status indicator
        self.queue_status_label = QLabel("Queue: 0 waiting")
        self.queue_status_label.setStyleSheet(
            f"{QUEUE_STATUS_STYLE} color: #64748b;")

        # Store history title elements for theme updates
        self.hist_title = None
        self.history_section = None

        self._setup_ui()
        self._apply_theme()

        # Auto theme switch check
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self._check_theme)
        self.theme_timer.start(THEME_CHECK_INTERVAL)

    def _reconcile_history_on_startup(self):
        """
        If the app was closed while downloads were in progress, history items can be left
        in processing/pending/queued. On startup, mark them as paused (interrupted) so
        the UI doesn't mislead users.
        """
        try:
            interrupted_statuses = {DownloadStatus.PROCESSING.value, DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value}
            updated_any = False
            for h in list(self.history_manager.get_all()):
                task_id = h.get("task_id")
                if not task_id:
                    continue
                status = h.get("status", "")
                if status not in interrupted_statuses:
                    continue

                # If we have a file_path and it exists, treat as completed.
                file_path = h.get("file_path", "")
                if file_path and os.path.exists(file_path):
                    self.history_manager.update_task(
                        task_id, {"status": DownloadStatus.COMPLETED.value})
                    updated_any = True
                    continue

                # Otherwise mark as paused/interrupted.
                self.history_manager.update_task(
                    task_id, {"status": DownloadStatus.PAUSED.value, "error": "Interrupted (app closed)"})
                updated_any = True

            if updated_any and hasattr(self.history_manager, "flush"):
                self.history_manager.flush()
        except Exception:
            # Never block startup on reconciliation.
            pass

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Base Horizontal Layout: [Sidebar] | [Main Content]
        self.base_layout = QHBoxLayout(central_widget)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)

        # --- 1. Sidebar ---
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.base_layout.addWidget(self.sidebar)

        # --- 2. Main Content Area ---
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # --- 2a. Header (Search Style) ---
        self.header = QFrame()
        self.header.setFixedHeight(54)
        self.header.setObjectName("Header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(32, 0, 32, 0)
        header_layout.setSpacing(20)

        # Add vertical centering
        header_vbox = QVBoxLayout()
        header_vbox.setContentsMargins(0, 0, 0, 0)
        header_vbox.setSpacing(0)
        header_vbox.addStretch()

        # Main horizontal content
        header_hbox = QHBoxLayout()
        header_hbox.setContentsMargins(0, 0, 0, 0)
        header_hbox.setSpacing(20)

        # Center the search container
        header_hbox.addStretch(1)

        # Search Container with Internal Icons
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_container.setMinimumWidth(400)
        search_container.setMaximumWidth(560)

        # Main input container that simulates an input field with icons
        input_wrapper = QWidget()
        input_wrapper.setObjectName("InputWrapper")
        input_wrapper.setStyleSheet("""
            #InputWrapper {
                background-color: %s;
                border: 2px solid %s;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                height: 38px;
            }
            #InputWrapper:focus {
                border: 2px solid %s;
                background-color: %s;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                height: 38px;
            }
        """ % (get_theme_colors()['input_bg'], get_theme_colors()['outer_border'],
               get_theme_colors()['accent'], get_theme_colors()['bg_card']))

        input_wrapper_layout = QHBoxLayout(input_wrapper)
        input_wrapper_layout.setContentsMargins(4, 0, 4, 0)
        input_wrapper_layout.setSpacing(12)

        # Link icon inside input (no background)
        search_icon_label = QLabel()
        search_icon_label.setPixmap(get_icon("link.png", get_theme_colors()[
                                    'text_secondary']).pixmap(QSize(18, 18)))
        search_icon_label.setFixedSize(18, 18)
        search_icon_label.setStyleSheet(
            "background-color: transparent; border: none;")
        input_wrapper_layout.addWidget(search_icon_label)

        # Actual input field without border
        self.url_input = QLineEdit()
        self.url_input.setObjectName("InnerSearchInput")
        self.url_input.setPlaceholderText("Paste video URL here...")
        self.url_input.setFixedHeight(38)
        self.url_input.setStyleSheet("""
            QLineEdit#InnerSearchInput {
                background-color: transparent;
                border: none;
                padding: 0;
                color: %s;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit#InnerSearchInput:focus {
                border: none;
                outline: none;
            }
        """ % get_theme_colors()['text_primary'])
        self.url_input.returnPressed.connect(self._on_analyze)
        input_wrapper_layout.addWidget(self.url_input, 1)

        # Clear button inside input
        self.clear_btn = QPushButton()
        colors = get_theme_colors()
        # Keep red for clear action
        self.clear_btn.setIcon(get_icon("close.png", "#f43f5e"))
        self.clear_btn.setIconSize(QSize(18, 18))
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: transparent; 
                border-radius: 4px; 
                border: none;
            }} 
            QPushButton:hover {{ 
                background-color: rgba(244, 63, 94, 0.1); 
            }}
        """)
        self.clear_btn.hide()
        input_wrapper_layout.addWidget(self.clear_btn)

        # Analyze button inside input wrapper
        self.analyze_btn = QPushButton("ANALYZE")
        self.analyze_btn.setObjectName("AnalyzeButton")
        self.analyze_btn.setFixedSize(80, 29)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        colors = get_theme_colors()
        self.analyze_btn.setStyleSheet(f"""
            QPushButton#AnalyzeButton {{
                background-color: {colors['accent']};
                color: {colors['button_text']};
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: 700;
                font-size: 10px;
                border: none;
                margin-left: 8px;
            }}
            QPushButton#AnalyzeButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            QPushButton#AnalyzeButton:pressed {{
                background-color: {colors['accent']};
            }}
            QPushButton#AnalyzeButton:disabled {{
                background-color: {colors['accent']};
                color: {colors['button_text']};
            }}
        """)
        self.analyze_btn.clicked.connect(self._on_analyze)
        input_wrapper_layout.addWidget(self.analyze_btn)

        # Store references for theme updates
        self.input_wrapper = input_wrapper
        self.search_icon_label = search_icon_label

        def on_text_changed(text):
            self.clear_btn.setVisible(bool(text))

        def on_clear():
            self.url_input.clear()
            self.url_input.setFocus()

        self.url_input.textChanged.connect(on_text_changed)
        self.clear_btn.clicked.connect(on_clear)

        # Update focus handlers to use current theme
        def on_input_focus_in():
            colors = get_theme_colors()
            self.input_wrapper.setStyleSheet(f"""
                #InputWrapper {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {colors['accent']};
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                    height: 38px;
                }}
            """)

        def on_input_focus_out():
            colors = get_theme_colors()
            self.input_wrapper.setStyleSheet(f"""
                #InputWrapper {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {colors['outer_border']};
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                    height: 38px;
                }}
            """)

        # Connect to focus signals using event filtering
        def on_focus_changed(old_widget, new_widget):
            if new_widget == self.url_input:
                on_input_focus_in()
            elif old_widget == self.url_input:
                on_input_focus_out()

        # Connect to application-level focus change signal
        from PySide6.QtWidgets import QApplication
        QApplication.instance().focusChanged.connect(on_focus_changed)

        search_layout.addWidget(input_wrapper, 1)

        header_hbox.addWidget(search_container, 2)

        header_hbox.addStretch(1)

        header_vbox.addLayout(header_hbox)
        header_vbox.addStretch()
        header_layout.addLayout(header_vbox)

        self.content_layout.addWidget(self.header)

        # --- 2b. Stacked Widget (Pages) ---
        self.pages = QStackedWidget()

        # Home Page (Integrated UI)
        self.home_page = QScrollArea()
        self.home_page.setWidgetResizable(True)
        self.home_page.setFrameShape(QFrame.NoFrame)

        self.home_content = QWidget()
        self.home_page.setWidget(self.home_content)

        self._setup_home_page()
        self.pages.addWidget(self.home_page)

        # Settings Page
        self.settings_page = SettingsPage()
        self.settings_page.settings_changed.connect(self._on_settings_changed)
        self.theme_changed.connect(self.settings_page.update_theme)
        self.pages.addWidget(self.settings_page)

        self.content_layout.addWidget(self.pages)
        self.base_layout.addWidget(self.content_area)

    def _setup_home_page(self):
        self.home_layout = QVBoxLayout(self.home_content)
        self.home_layout.setContentsMargins(24, 16, 24, 16)
        self.home_layout.setSpacing(20)

        # --- TOP SECTION: Extraction Dashboard ---
        top_section = QHBoxLayout()
        top_section.setSpacing(16)

        # Left: Preview
        preview_container = QVBoxLayout()
        preview_title = QLabel("VIDEO PREVIEW")
        preview_title.setObjectName("OptionHeader")
        preview_container.addWidget(preview_title)

        self.video_card = VideoInfoCard()
        preview_container.addWidget(self.video_card)
        top_section.addLayout(preview_container, 2)

        # Right: Options
        options_container = QVBoxLayout()
        options_title = QLabel("EXTRACTION PROFILE")
        options_title.setObjectName("OptionHeader")
        options_container.addWidget(options_title)

        self.options_card = StreamOptionsCard()
        self.options_card.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.options_card.download_clicked.connect(self._on_download)
        # Connect to theme change signal
        self.theme_changed.connect(self.options_card.update_theme)
        self.theme_changed.connect(self.video_card.update_theme)
        options_container.addWidget(self.options_card)
        top_section.addLayout(options_container, 3)

        self.home_layout.addLayout(top_section)

        # Playlist items area (Overlay/Expandable logic could go here)
        playlist_header = QHBoxLayout()
        self.playlist_label = QLabel("Playlist Items")
        self.playlist_label.setObjectName("OptionHeader")
        playlist_header.addWidget(self.playlist_label)

        playlist_header.addStretch()

        self.select_all_btn = QPushButton("All")
        self.select_all_btn.setFixedWidth(50)
        self.select_all_btn.setObjectName("SecondaryButton")
        self.select_all_btn.clicked.connect(
            lambda: self._set_all_selected(True))

        self.select_none_btn = QPushButton("None")
        self.select_none_btn.setFixedWidth(50)
        self.select_none_btn.setObjectName("SecondaryButton")
        self.select_none_btn.clicked.connect(
            lambda: self._set_all_selected(False))

        playlist_header.addWidget(self.select_all_btn)
        playlist_header.addWidget(self.select_none_btn)

        self.playlist_header_container = QWidget()
        self.playlist_header_container.setLayout(playlist_header)
        self.playlist_header_container.hide()
        self.home_layout.addWidget(self.playlist_header_container)

        self.playlist_scroll = QScrollArea()
        self.playlist_scroll.setWidgetResizable(True)
        self.playlist_scroll.setMinimumHeight(200)
        self.playlist_scroll.hide()
        self.playlist_widget = QWidget()
        self.playlist_layout = QVBoxLayout(self.playlist_widget)
        self.playlist_layout.setAlignment(Qt.AlignTop)
        self.playlist_scroll.setWidget(self.playlist_widget)
        self.home_layout.addWidget(self.playlist_scroll)

        # --- BOTTOM SECTION: History Archive ---
        history_section = QVBoxLayout()
        history_section.setSpacing(12)

        # History Header: Title + Filters + Clear
        history_header = QHBoxLayout()

        title_vbox = QVBoxLayout()
        hist_title = QLabel("DOWNLOAD HISTORY")
        colors = get_theme_colors()
        hist_title.setStyleSheet(
            "font-weight: 900; font-size: 17px; color: {};".format(colors['text_primary']))

        # Store as instance variables for theme updates
        self.hist_title = hist_title

        title_vbox.addWidget(hist_title)
        history_header.addLayout(title_vbox)

        history_header.addStretch()

        # Retry All Failed Button
        self.retry_all_btn = QPushButton(" RETRY FAILED")
        colors = get_theme_colors()
        self.retry_all_btn.setIcon(get_icon("retry.png", colors['accent']))
        self.retry_all_btn.setIconSize(QSize(13, 13))
        self.retry_all_btn.setFixedHeight(29)
        self.retry_all_btn.clicked.connect(self._retry_all_failed)
        history_header.addWidget(self.retry_all_btn)

        # Resume Unfinished Button (paused + failed + cancelled)
        self.resume_unfinished_btn = QPushButton(" RESUME UNFINISHED")
        self.resume_unfinished_btn.setIcon(
            get_icon("play.png", colors['accent']))
        self.resume_unfinished_btn.setIconSize(QSize(13, 13))
        self.resume_unfinished_btn.setFixedHeight(29)
        self.resume_unfinished_btn.clicked.connect(self._resume_all_unfinished)
        history_header.addWidget(self.resume_unfinished_btn)

        # Clear History Button (Dropdown)
        self.clear_history_btn = QPushButton(" CLEAR HISTORY")
        self.clear_history_btn.setIcon(
            get_icon("trash.png", "#f43f5e"))  # Keep red for clear action
        self.clear_history_btn.setIconSize(QSize(13, 13))
        self.clear_history_btn.setFixedHeight(29)
        history_header.addWidget(self.clear_history_btn)

        # Queue Status Indicator
        history_header.addWidget(self.queue_status_label)

        # History List with proper alignment and column headers
        history_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(history_list_widget)
        self.task_list_layout.setAlignment(Qt.AlignTop)  # Keep top alignment
        self.task_list_layout.setSpacing(8)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)

        # Add column header for better alignment
        column_header_layout = QHBoxLayout()
        column_header_layout.setContentsMargins(
            16, 8, 16, 8)  # Match history header margins

        column_header_layout.addStretch()

        # Add column header to history layout
        history_section.insertLayout(0, column_header_layout)

        history_section.addWidget(history_list_widget, 1)

        # Store history section for theme updates
        self.history_section = history_section

        self.clear_menu = QMenu(self.clear_history_btn)
        self._update_clear_menu_theme()

        act_all = self.clear_menu.addAction("Clear All")
        act_all.triggered.connect(lambda: self._clear_tasks("all"))

        act_comp = self.clear_menu.addAction("Clear Completed")
        act_comp.triggered.connect(lambda: self._clear_tasks("completed"))

        act_fail = self.clear_menu.addAction("Clear Failed")
        act_fail.triggered.connect(lambda: self._clear_tasks("failed"))

        self.clear_history_btn.setMenu(self.clear_menu)

        history_section.addLayout(history_header)

        # Labels for list
        labels_layout = QHBoxLayout()
        labels_layout.setContentsMargins(16, 0, 16, 0)
        for text, stretch in [("MEDIA ASSET", 6), ("SIZE / SPEED", 2), ("STATUS", 2), ("ACTIONS", 2)]:
            lbl = QLabel(text)
            lbl.setObjectName("OptionHeader")
            labels_layout.addWidget(lbl, stretch)
        history_section.addLayout(labels_layout)

        # List
        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        self.task_list_layout.setSpacing(8)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)
        history_section.addWidget(self.task_list_widget, 1)

        # Add pagination widget
        history_section.addWidget(self.pagination_widget)

        self.home_layout.addLayout(history_section, 1)

        # Ensure thumbnail directory exists (use absolute path based on file location)
        _ui_dir = os.path.dirname(os.path.abspath(__file__))
        _desktop_root = os.path.dirname(_ui_dir)  # ui/ -> desktop/
        self.thumb_dir = os.path.join(_desktop_root, 'data', 'thumbnails')
        os.makedirs(self.thumb_dir, exist_ok=True)

        self._load_history()

    def _cleanup_unused_thumbnails(self):
        """
        Remove thumbnail files that are no longer referenced by any history item.

        This keeps `self.thumb_dir` from growing unbounded after deletes/clears.
        """
        try:
            thumb_dir_abs = os.path.abspath(self.thumb_dir)
            if not os.path.isdir(thumb_dir_abs):
                return

            # Collect referenced thumbnail filenames (UUID.jpg).
            # Compare by basename to avoid cwd/path differences.
            referenced_names = set()
            for h in self.history_manager.get_all():
                p = h.get("thumbnail")
                if not p:
                    continue
                try:
                    referenced_names.add(os.path.basename(p))
                except Exception:
                    continue

            # Delete thumbnail files not referenced by history.
            for name in os.listdir(thumb_dir_abs):
                # Only delete files created by the app (uuid.jpg).
                if not name.lower().endswith(f"{THUMBNAIL_EXTENSION}"):
                    continue
                full = os.path.join(thumb_dir_abs, name)
                if not os.path.isfile(full):
                    continue
                if name not in referenced_names:
                    try:
                        os.remove(full)
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        self.logger.warning(
                            f"Thumbnail cleanup failed for {full}: {e}")
        except Exception as e:
            # Never break UI if cleanup fails.
            self.logger.warning(f"Thumbnail cleanup error: {e}")

    def _on_page_changed(self, page_name: str):
        if page_name == "home":
            self.pages.setCurrentIndex(0)
        elif page_name == "settings":
            self.pages.setCurrentIndex(1)
        elif page_name == "help":
            # Show log viewer dialog instead of a page
            show_log_viewer(self)
            # Uncheck the help button and restore previous selection
            self.sidebar.btn_help.setChecked(False)
            # Re-check the current page's button
            current_page = self.pages.currentIndex()
            if current_page == 0:
                self.sidebar.btn_home.setChecked(True)
            elif current_page == 1:
                self.sidebar.btn_settings.setChecked(True)
        elif page_name == "legal":
            # Show legal/compliance dialog
            show_legal(self)
            # Uncheck the legal button and restore previous selection
            self.sidebar.btn_legal.setChecked(False)
            # Re-check the current page's button
            current_page = self.pages.currentIndex()
            if current_page == 0:
                self.sidebar.btn_home.setChecked(True)
            elif current_page == 1:
                self.sidebar.btn_settings.setChecked(True)

    def _on_settings_changed(self):
        """Handle settings changes."""
        # Update max concurrent downloads
        self.max_concurrent = config.get('downloads.max_concurrent', 4)

        # Refresh extraction options from new config
        self.options_card.refresh_settings()

        # Update theme colors for DOWNLOAD HISTORY title
        colors = get_theme_colors()
        self.hist_title.setStyleSheet(
            "font-weight: 900; font-size: 17px; color: {};".format(colors['text_primary']))

        # Emit theme change signal for all TaskItems
        self.theme_changed.emit()

        # Re-apply theme if changed
        self._apply_theme()

        # Update theme check interval
        self.theme_timer.setInterval(THEME_CHECK_INTERVAL)

    def _apply_theme(self):
        self.setStyleSheet(get_stylesheet())
        # Update input wrapper styling
        self._update_input_theme()
        # Update clear history menu theme
        self._update_clear_menu_theme()

    def _update_input_theme(self):
        """Update input elements to match current theme."""
        colors = get_theme_colors()

        # Update input wrapper styling
        if hasattr(self, 'input_wrapper'):
            self.input_wrapper.setStyleSheet(f"""
                #InputWrapper {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {colors['outer_border']};
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                    height: 46px;
                }}
            """)

        # Update input field text color
        if hasattr(self, 'url_input'):
            self.url_input.setStyleSheet(f"""
                QLineEdit#InnerSearchInput {{
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    color: {colors['text_primary']};
                    font-size: 12px;
                    font-weight: 500;
                }}
                QLineEdit#InnerSearchInput:focus {{
                    border: none;
                    outline: none;
                }}
            """)

        # Update search icon color
        if hasattr(self, 'search_icon_label'):
            self.search_icon_label.setPixmap(
                get_icon("link.png", colors['text_secondary']).pixmap(QSize(18, 18)))

    def _update_clear_menu_theme(self):
        """Update clear history menu to match current theme."""
        if hasattr(self, 'clear_menu'):
            colors = get_theme_colors()
            menu_bg = colors['bg_card']
            menu_text = colors['text_primary']
            menu_border = colors['outer_border']
            menu_hover = colors['accent']
            menu_hover_text = colors['button_text']
            self.clear_menu.setStyleSheet(
                f"QMenu {{ background-color: {menu_bg}; color: {menu_text}; border: 1px solid {menu_border}; border-radius: 4px; padding: 4px; }}"
                f"QMenu::item {{ padding: 8px 16px; border-radius: 4px; }}"
                f"QMenu::item:selected {{ background-color: {menu_hover}; color: {menu_hover_text}; }}")

    def _check_theme(self):
        # We could compare current stylesheet with new one if we really wanted to be efficient
        # but for now we just reapply if it doesn't match a stored state
        self._apply_theme()

    @Slot()
    def _on_analyze(self):
        url = self.url_input.text().strip()
        if not url:
            return

        self.analyze_btn.setEnabled(False)
        # Store original text and show spinning retry icon
        self._analyze_btn_original_text = "ANALYZE"
        self.analyze_btn.setText("")
        self._setup_analyze_spinner()

        worker = InfoWorker(url)
        thread = WorkerThread(worker)

        self.running_info_workers.append((thread, worker))

        worker.finished.connect(self._on_info_finished)
        worker.error.connect(self._on_info_error)
        thread.finished.connect(
            lambda t=thread, w=worker: self._cleanup_info_worker(t, w))
        thread.start()

    def _cleanup_info_worker(self, thread, worker):
        if (thread, worker) in self.running_info_workers:
            self.running_info_workers.remove((thread, worker))
            thread.deleteLater()
            # Object ownership in Qt handles worker if it has a parent,
            # otherwise we let it be collected by GC or we call deleteLater once.
            try:
                worker.deleteLater()
            except RuntimeError:
                pass

    @Slot(dict)
    def _on_info_finished(self, info):
        self._stop_analyze_spinner()
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText(self._analyze_btn_original_text)
        self.current_info = info

        # Check if user might want single video instead of playlist
        if info.get("is_playlist") and info.get("playlist_entries"):
            url = self.url_input.text().strip()
            import urllib.parse
            parsed = urllib.parse.urlparse(url)

            # Check if URL looks like a single video (has path or query suggesting single item)
            # but backend detected it as a playlist
            looks_like_single = (
                "watch" in parsed.path or
                "youtu.be" in parsed.netloc or
                "shorts" in parsed.path or
                ("v=" in parsed.query)
            )

            # For URLs that look like single items but are playlists, offer choice
            if looks_like_single and len(info.get("playlist_entries", [])) > 1:
                msg = QMessageBox(self)
                msg.setWindowTitle("Playlist Detected")
                msg.setText(f"This URL contains a playlist with {len(info['playlist_entries'])} items.")
                msg.setInformativeText("What would you like to extract?")

                msg.addButton("Full Playlist", QMessageBox.ActionRole)
                btn_video = msg.addButton("First Video Only", QMessageBox.ActionRole)
                msg.setStandardButtons(QMessageBox.Cancel)

                msg.exec()

                if msg.clickedButton() == msg.button(QMessageBox.Cancel):
                    return
                elif msg.clickedButton() == btn_video:
                    # Convert to single video by keeping only first entry
                    first_entry = info["playlist_entries"][0]
                    info["is_playlist"] = False
                    info["playlist_entries"] = []
                    info["title"] = first_entry.get("title", info.get("title"))
                    self.url_input.setText(first_entry.get("url", url))

        self.video_card.update_info(info)
        self.options_card.update_streams(info.get("available_streams", {}))

        # Handling playlist entries
        # Clear old items
        while self.playlist_layout.count():
            item = self.playlist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = info.get("playlist_entries", [])
        if entries:
            self.playlist_header_container.show()
            self.playlist_scroll.show()

            # Use virtual playlist widget for efficient handling
            if not hasattr(self, 'virtual_playlist'):
                # Replace the old layout with virtual playlist
                self.virtual_playlist = VirtualPlaylistWidget()
                self.virtual_playlist.selection_changed.connect(
                    self._on_playlist_selection_changed)

                # Clear the old layout and add virtual playlist
                while self.playlist_layout.count():
                    item = self.playlist_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                self.playlist_layout.addWidget(self.virtual_playlist)

            # Load entries efficiently (only creates visible widgets)
            self.virtual_playlist.load_playlist(entries)
        else:
            self.playlist_header_container.hide()
            self.playlist_scroll.hide()

    def _on_playlist_selection_changed(self):
        """Handle playlist selection changes."""
        if not hasattr(self, 'virtual_playlist'):
            return

        selected_items = self.virtual_playlist.get_selected_items()

    def _set_all_selected(self, selected: bool):
        if hasattr(self, 'virtual_playlist'):
            self.virtual_playlist.set_all_selected(selected)
        else:
            # Fallback to old method
            for i in range(self.playlist_layout.count()):
                widget = self.playlist_layout.itemAt(i).widget()
                if isinstance(widget, PlaylistItemWidget):
                    widget.set_selected(selected)

    def _create_playlist_titles_file(self, output_path: str, playlist_title: str, titles: list) -> str:
        """Create a text file containing playlist video titles in order.

        Args:
            output_path: Directory where the file should be saved
            playlist_title: Title of the playlist (used for filename)
            titles: List of video titles in order

        Returns:
            Path to the created file
        """
        from core.utils import sanitize_filename

        safe_playlist_title = sanitize_filename(playlist_title or "Playlist")
        filename = f"{safe_playlist_title} - Titles.txt"
        filepath = os.path.join(output_path, filename)

        # Handle duplicate filenames
        counter = 1
        base_filepath = filepath
        while os.path.exists(filepath):
            filename = f"{safe_playlist_title} - Titles ({counter}).txt"
            filepath = os.path.join(output_path, filename)
            counter += 1

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Playlist: {playlist_title}\n")
            f.write(f"Total videos: {len(titles)}\n")
            f.write("=" * 50 + "\n\n")
            for i, title in enumerate(titles, 1):
                f.write(f"{i}. {title}\n")

        return filepath

    @Slot(str)
    def _on_info_error(self, err):
        self._stop_analyze_spinner()
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText(self._analyze_btn_original_text)
        
        # Show troubleshooting dialog with the raw backend error so pattern
        # matching in ErrorAnalyzer works correctly (no decorating prefix).
        show_troubleshooting(self, err, context="Video Info Fetch Failed:")

    @Slot(dict)
    def _on_download(self, options):
        if not self.current_info:
            return

        # Use the folder already chosen in the extraction profile card.
        dest = self.options_card.target_folder
        if not dest or not os.path.isdir(dest):
            # If for some reason the folder is missing, provide a warning instead of a popup
            # this shouldn't happen as it defaults to ~/Downloads
            QMessageBox.warning(
                self, "Invalid Folder", f"The destination folder does not exist:\n{dest}\n\nPlease select a valid folder in the Extraction Profile.")
            return

        # New batch: reset duplicate-file policy for this run.

        # New batch: reset duplicate-file policy for this run.
        self._duplicate_policy = None

        # 2. Collect Items
        tasks_to_add = []
        if self.current_info.get("is_playlist"):
            # Use virtual playlist for efficient selection
            if hasattr(self, 'virtual_playlist'):
                selected_items = self.virtual_playlist.get_selected_items()
                for item in selected_items:
                    url = item.get('url')
                    title = item.get('title')
                    thumb_url = item.get('thumb_url', '')
                    if url and isinstance(url, str):
                        tasks_to_add.append((url, title, thumb_url))
            else:
                # Fallback to old method
                for i in range(self.playlist_layout.count()):
                    widget = self.playlist_layout.itemAt(i).widget()
                    if isinstance(widget, PlaylistItemWidget) and widget.is_selected():
                        data = widget.get_data()
                        url = data.get('url')
                        title = data.get('title')
                        thumb_url = data.get('thumb_url', '')
                        if url and isinstance(url, str):
                            tasks_to_add.append((url, title, thumb_url))
        else:
            thumb_url = self.current_info.get("thumbnail", "")
            if not thumb_url:
                m = re.search(
                    r'(?:v=|/)([0-9A-Za-z_-]{11})', self.url_input.text().strip())
                if m:
                    thumb_url = f"https://img.youtube.com/vi/{m.group(1)}/mqdefault.jpg"
            tasks_to_add.append((self.url_input.text().strip(), self.current_info.get(
                "title", "Unknown Video"), thumb_url))

        # Create playlist titles file for playlist downloads
        if self.current_info.get("is_playlist") and tasks_to_add:
            playlist_title = self.current_info.get("title", "Playlist")
            titles = [title for _, title, _ in tasks_to_add]
            try:
                titles_file_path = self._create_playlist_titles_file(dest, playlist_title, titles)
                self.logger.info(f"Created playlist titles file: {titles_file_path}")
            except Exception as e:
                self.logger.error(f"Failed to create playlist titles file: {e}")

        if not tasks_to_add:
            QMessageBox.warning(self, "No Selection",
                                "Please select at least one video to download.")
            return

        # Allow the coalesced "smart refresh" to rebuild the history page once,
        # even though active workers may start immediately after task creation.
        self._allow_history_rebuild_once = True

        thumb_tasks = []
        for url, title, thumb_url in tasks_to_add:
            task_id = str(uuid.uuid4())
            self._create_task_entry(
                task_id, url, title, dest, options, "")  # Setup blank first
            thumb_tasks.append(
                {'task_id': task_id, 'url': url, 'thumb_url': thumb_url})

        # Start async worker for thumbnails
        if thumb_tasks:
            self._start_thumbnail_worker(thumb_tasks)

        self._process_queue()

    def _start_thumbnail_worker(self, tasks):
        """Start thumbnail worker with batch processing and concurrency limit."""
        if not hasattr(self, 'thumb_workers'):
            self.thumb_workers = []
            self.thumbnail_queue = []  # Queue for pending thumbnails

        # Add tasks to queue, but avoid scheduling duplicates for the same task_id.
        # Also skip if the thumbnail file already exists.
        filtered = []
        for t in tasks:
            task_id = t.get("task_id")
            if not task_id:
                continue
            if task_id in self._thumbnail_requested_task_ids:
                continue
            thumb_path = os.path.join(self.thumb_dir, f"{task_id}{THUMBNAIL_EXTENSION}")
            if os.path.exists(thumb_path):
                self._thumbnail_requested_task_ids.add(task_id)
                continue
            self._thumbnail_requested_task_ids.add(task_id)
            filtered.append(t)

        # Add tasks to queue instead of creating new worker immediately
        self.thumbnail_queue.extend(filtered)

        # Process queue with limited concurrency
        self._process_thumbnail_queue()

    def _process_thumbnail_queue(self):
        """Process thumbnail queue with limited concurrency."""
        MAX_CONCURRENT_THUMBNAILS = 5  # Limit concurrent thumbnail downloads

        # Start new workers if we have capacity
        while (len(self.thumb_workers) < MAX_CONCURRENT_THUMBNAILS and
               self.thumbnail_queue):

            # Take batch of up to 10 thumbnails
            batch = self.thumbnail_queue[:10]
            self.thumbnail_queue = self.thumbnail_queue[10:]

            worker = ThumbnailWorker(batch, self.thumb_dir)
            worker.finished_one.connect(self._on_thumbnail_fetched)
            worker.finished.connect(
                lambda w=worker: self._on_thumbnail_worker_finished(w))
            self.thumb_workers.append(worker)
            worker.start()

    def _on_thumbnail_worker_finished(self, worker):
        """Handle thumbnail worker completion and process queue."""
        if worker in self.thumb_workers:
            self.thumb_workers.remove(worker)

        # Process more items from queue if available
        self._process_thumbnail_queue()

    @Slot(str, str)
    def _on_thumbnail_fetched(self, task_id, path):
        self.history_manager.update_task(task_id, {"thumbnail": path})

        # Update only if the task is currently visible in the history list.
        widget = self.visible_widgets.get(task_id)
        if widget:
            widget.set_thumbnail(path)

    def _cache_thumbnail(self, task_id, url):
        if not url:
            return ""
        try:
            path = os.path.join(self.thumb_dir, f"{task_id}{THUMBNAIL_EXTENSION}")
            response = requests.get(url, timeout=THUMBNAIL_DOWNLOAD_TIMEOUT)
            with open(path, "wb") as f:
                f.write(response.content)
            return path
        except:
            return ""

    def _create_task_entry(self, task_id, url, title, dest, options, thumb_path=""):
        # Smart queue logic:
        # - "pending"  => ready to start (limited by max_concurrent)
        # - "queued"   => waiting behind capacity (not started yet)
        # When adding many tasks in one batch (e.g. playlist), downloads are
        # not started until after creation finishes. Account for both active
        # workers and already-enqueued "pending" tasks.
        if len(self.active_workers) + len(self.pending_tasks) < self.max_concurrent:
            # Add to pending but don't show in UI yet (let pagination handle it)
            self.pending_tasks.append((task_id, url, dest, options))
            self.pending_task_ids.add(task_id)
            self.logger.debug(f"Task {task_id} added to pending queue")
            history_status = DownloadStatus.DOWNLOADING.value
        else:
            # Hide in queue, don't show in UI yet
            self.queued_tasks.append((task_id, url, dest, options))
            self.queued_task_ids.add(task_id)
            self.logger.debug(
                f"Task {task_id} added to hidden queue (position {len(self.queued_tasks)})")
            history_status = DownloadStatus.QUEUED.value

        # Don't add to UI layout directly - let pagination handle display
        # self.task_list_layout.insertWidget(0, task_widget)  # REMOVED

        self.history_manager.add_task(task_id, {
            "task_id": task_id,
            "title": title,
            "url": url,
            "status": history_status,
            "options": options,
            "dest": dest,
            "thumbnail": thumb_path
        })

        # Update queue status
        self._update_queue_status()

        # Smart refresh: show new downloads immediately without memory spikes
        self._smart_refresh_for_new_tasks()

    def _smart_refresh_for_new_tasks(self):
        """Smart refresh that shows new downloads without memory spikes."""
        try:
            # Memory optimization: use get_count() for just the count
            current_count = self.history_manager.get_count()

            # Update pagination widget with new count (cheap).
            self.pagination_widget.update_pagination(current_count)

            # IMPORTANT:
            # During batch starts (playlist with 85 items), calling `_load_history_page`
            # for every single new history item causes UI freezes. Coalesce the actual
            # widget rebuild via `_request_refresh_current_page()`.
            self._request_refresh_current_page()

        except Exception as e:
            try:
                self.logger.error(f"Error in smart refresh: {e}")
            except AttributeError:
                logging.getLogger(__name__).error(f"Error in smart refresh: {e}")
            # Fallback to safe refresh if needed
            pass

    def _process_queue(self):
        # Process active pending tasks first.
        # Memory efficiency: worker progress updates only the widget if that
        # widget is currently visible; otherwise UI won't update (by design, option B).
        while len(self.active_workers) < self.max_concurrent and self.pending_tasks:
            task_id, url, dest, options = self.pending_tasks.pop(0)

            self.logger.debug(f"Starting download: {task_id}")

            # Duplicate file handling: prompt user when target already exists.
            # Uses yt-dlp metadata (same as the worker) so resume-from-history matches on-disk names.
            # Memory optimization: use get_by_id for single lookup
            history_item = self.history_manager.get_by_id(task_id)
            title = (history_item or {}).get("title", "Unknown")
            opts = dict((history_item or {}).get("options") or {})
            opts.update(dict(options or {}))
            options = opts
            try:
                existing_path, skip_dup_prompt = self._duplicate_existing_path(
                    dest, url, title, opts, history_item
                )
                if not skip_dup_prompt and existing_path and os.path.isfile(existing_path):
                    decision = self._duplicate_policy or self._prompt_duplicate_decision(
                        existing_path)
                    if decision == "skip":
                        self.pending_task_ids.discard(task_id)
                        self.history_manager.update_task(
                            task_id, {"status": "skipped", "error": "Skipped (file already exists)"})
                        self._update_queue_status()
                        self._refresh_task_in_current_page(task_id)
                        # Promote queued tasks and continue processing (same as _cleanup_worker)
                        if len(self.active_workers) < self.max_concurrent and self.queued_tasks:
                            next_task = self.queued_tasks.pop(0)
                            self.pending_tasks.append(next_task)
                            self.pending_task_ids.add(next_task[0])
                            self.queued_task_ids.discard(next_task[0])
                        continue
                    if decision == "replace":
                        options = dict(opts)
                        options["force_overwrites"] = True
                    elif decision == "copy":
                        options = dict(opts)
                        base = os.path.splitext(
                            os.path.basename(existing_path))[0]
                        ext = os.path.splitext(existing_path)[1]
                        # Use reservation system to prevent concurrent conflicts
                        new_base = self._reserve_unique_filename(
                            dest, base, ext, task_id)
                        options["filename_override"] = new_base
                        # Track the reservation for cleanup
                        self._task_filenames[task_id] = (dest, f"{new_base}{ext}")
            except Exception as e:
                self.logger.debug(
                    "Duplicate-file check failed: %s", e, exc_info=True)

            # For non-duplicate cases, still reserve a unique filename to prevent
            # concurrent download conflicts (multiple videos with same title)
            if not options.get("filename_override") and not options.get("force_overwrites"):
                try:
                    # Predict the base filename that yt-dlp would use
                    predicted_path = self._predict_output_path(dest, url, title, options)
                    if predicted_path:
                        base = os.path.splitext(os.path.basename(predicted_path))[0]
                        ext = os.path.splitext(predicted_path)[1]
                        unique_base = self._reserve_unique_filename(dest, base, ext, task_id)
                        if unique_base != base:
                            options["filename_override"] = unique_base
                        # Track the reservation for cleanup (even if same as base)
                        self._task_filenames[task_id] = (dest, f"{unique_base}{ext}")
                except Exception as e:
                    self.logger.debug("Filename reservation failed: %s", e, exc_info=True)

            worker = DownloadWorker(task_id, url, dest, options)

            # Connect signals - DownloadWorker uses process isolation with monitor thread
            worker.progress.connect(
                self._on_worker_progress, Qt.QueuedConnection)
            worker.status.connect(self._on_worker_status, Qt.QueuedConnection)
            worker.finished.connect(
                self._on_download_finished, Qt.QueuedConnection)
            worker.error.connect(self._on_download_error, Qt.QueuedConnection)
            worker.cancelled.connect(
                self._on_download_cancelled, Qt.QueuedConnection)

            # Use finished/error/cancelled signals to safely cleanup
            worker.finished.connect(
                lambda tid=task_id: self._cleanup_worker(tid))
            worker.error.connect(
                lambda tid=task_id: self._cleanup_worker(tid))
            worker.cancelled.connect(
                lambda tid=task_id: self._cleanup_worker(tid))

            self.active_workers[task_id] = worker
            self.active_task_ids.add(task_id)  # Add to performance tracking
            # Remove from pending tracking
            self.pending_task_ids.discard(task_id)
            worker.start()

            self.history_manager.update_task(task_id, {"status": "processing"})

            widget = self.visible_widgets.get(task_id)
            if widget:
                widget.set_status("Starting...")

            # Re-ordering: keep active items on page 1.
            if self.pagination_widget.current_page == 0:
                # Avoid full page rebuild during active downloads; rebuilds
                # can destroy widgets while worker emits final signals.
                self._refresh_task_in_current_page(task_id)
            else:
                # Targeted refresh: update this task if currently displayed
                self._refresh_task_in_current_page(task_id)

        # NOTE: We don't process queued_tasks here to prevent exceeding max_concurrent
        # Queued tasks are only promoted when active workers finish in _cleanup_worker

    def _duplicate_existing_path(self, dest: str, url: str, title: str, opts: dict, history_item) -> tuple:
        """
        Returns (existing_file_path_or_none, skip_duplicate_prompt).
        skip_duplicate_prompt is True when a paused download is resuming with yt-dlp partial files (.part).
        """
        candidates = []
        # Fast local-only path prediction using history metadata (avoids blocking network call)
        try:
            fast = self._predict_output_path(dest, url, title, opts)
            if fast:
                n = os.path.normpath(fast)
                if n not in candidates:
                    candidates.append(n)
        except Exception as e:
            self.logger.debug("Fast duplicate path prediction failed: %s", e)

        fp = (history_item or {}).get("file_path") or ""
        if fp and os.path.isfile(fp):
            dest_n = os.path.normpath(dest)
            if os.path.normpath(os.path.dirname(fp)) == dest_n:
                n = os.path.normpath(fp)
                if n not in candidates:
                    candidates.append(n)

        for c in candidates:
            if os.path.isfile(c):
                if self._should_skip_duplicate_prompt_for_resume(c, history_item):
                    return (None, True)
                return (c, False)
        return (None, False)

    def _should_skip_duplicate_prompt_for_resume(self, output_path: str, history_item) -> bool:
        """Do not nag when a task is resuming and yt-dlp left partial fragment files."""
        if not output_path:
            return False

        # If .part or .ytdl files exist, we are accurately resuming a partial download.
        # We check this first to allow resumption even if history status was recently changed.
        if os.path.exists(output_path + ".part") or os.path.exists(output_path + ".ytdl"):
            return True

        # Fallback to history check (e.g. for completed but now resuming? rarely happens)
        if history_item and history_item.get("status") == "paused":
            return True

        return False

    def _predict_output_path(self, dest: str, url: str, title: str, options: dict) -> str:
        """
        Predict the final output path for duplicate checks using the unified downloader logic.
        This ensures the check matches exactly what yt-dlp will produce.
        """
        return self._downloader.predict_download_filepath(
            url=url,
            output_path=dest,
            opts=options,
            title_hint=title
        ) or ""

    def _next_available_copy_name(self, dest: str, base: str, ext: str) -> str:
        """Return a new base name (without extension) that doesn't exist yet."""
        n = 1
        while True:
            candidate_base = f"{base} ({n})"
            if not os.path.exists(os.path.join(dest, f"{candidate_base}{ext}")):
                return candidate_base
            n += 1

    def _reserve_unique_filename(self, dest: str, base: str, ext: str, task_id: str) -> str:
        """
        Reserve a unique filename for a concurrent download.

        This prevents multiple concurrent downloads from racing to use the same
        filename (e.g., 'Module Intro (1).mp4'), which causes fragment file conflicts.

        Returns the unique base name (without extension) that was reserved.
        """
        # Initialize tracking for this destination directory
        if dest not in self._active_filenames:
            self._active_filenames[dest] = set()

        active_in_dest = self._active_filenames[dest]

        # Start with the base name
        candidate_base = base
        n = 1

        while n <= MAX_FILENAME_ATTEMPTS:
            candidate_filename = f"{candidate_base}{ext}"
            # Check both active downloads and existing files on disk
            if candidate_filename not in active_in_dest and not os.path.exists(os.path.join(dest, candidate_filename)):
                # Found a unique name, reserve it
                active_in_dest.add(candidate_filename)
                return candidate_base
            # Try next number
            candidate_base = f"{base} ({n})"
            n += 1

        # Fallback: use a UUID suffix if we somehow exhausted all attempts
        import uuid as _uuid
        fallback = f"{base}_{_uuid.uuid4().hex[:8]}"
        active_in_dest.add(f"{fallback}{ext}")
        self.logger.warning(f"Could not find unique filename for '{base}{ext}' after {MAX_FILENAME_ATTEMPTS} attempts, using '{fallback}{ext}'")
        return fallback

    def _release_filename(self, dest: str, filename: str):
        """Release a filename reservation when download completes."""
        if dest in self._active_filenames:
            self._active_filenames[dest].discard(filename)
            # Clean up empty sets
            if not self._active_filenames[dest]:
                del self._active_filenames[dest]

    def _prompt_duplicate_decision(self, existing_path: str) -> str:
        """Prompt user: copy duplicate, replace, or skip; optionally remember for this batch."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("File already exists")
        box.setText(
            "A file with the same name already exists in the target folder.")
        box.setInformativeText(existing_path)
        copy_btn = box.addButton("Copy duplicate", QMessageBox.AcceptRole)
        replace_btn = box.addButton("Replace", QMessageBox.DestructiveRole)
        skip_btn = box.addButton("Skip", QMessageBox.RejectRole)
        remember = QCheckBox(
            "Remember my choice for the rest of this download batch")
        box.setCheckBox(remember)
        box.setDefaultButton(copy_btn)
        box.exec()

        clicked = box.clickedButton()
        if clicked == replace_btn:
            decision = "replace"
        elif clicked == skip_btn:
            decision = "skip"
        else:
            decision = "copy"
        if remember.isChecked():
            self._duplicate_policy = decision
        return decision

    def _on_worker_progress(self, task_id: str, p: float, speed: float, eta: float):
        """Update progress only if the task widget is currently visible."""
        widget = self.visible_widgets.get(task_id)
        if widget:
            widget.update_progress(p, speed, eta)

    def _on_worker_status(self, task_id: str, msg: str):
        """Update status only if the task widget is currently visible."""
        widget = self.visible_widgets.get(task_id)
        if widget:
            widget.set_status(msg)

    def _cleanup_worker(self, task_id):
        if task_id in self.active_workers:
            worker = self.active_workers.pop(task_id)

            # Schedule Qt object cleanup; don't join the process here — doing so
            # on the main thread blocks the event loop for up to 2 s per task.
            # The process will exit on its own once it processes the cancel event.
            try:
                if worker:
                    worker.deleteLater()
            except Exception as e:
                self.logger.warning(f"Error cleaning up worker {task_id}: {e}")

            # Remove from performance tracking sets
            self.active_task_ids.discard(task_id)

        # Release filename reservation if any
        if task_id in self._task_filenames:
            dest, filename = self._task_filenames.pop(task_id)
            self._release_filename(dest, filename)

        # Promote one queued task to pending if we have capacity
        if len(self.active_workers) < self.max_concurrent and self.queued_tasks:
            task_id, url, dest, options = self.queued_tasks.pop(0)

            # Add to pending tasks
            self.pending_tasks.append((task_id, url, dest, options))
            self.pending_task_ids.add(task_id)
            self.queued_task_ids.discard(task_id)
            self.history_manager.update_task(task_id, {"status": DownloadStatus.DOWNLOADING.value})
            widget = self.visible_widgets.get(task_id)
            if widget:
                widget.set_status("Queued...")

            # If the user is on page 1, ordering might have changed
            if self.pagination_widget.current_page == 0:
                # Avoid full rebuild; just update the promoted row.
                self._refresh_task_in_current_page(task_id)

        self._process_queue()
        self._update_queue_status()

    def _is_task_active(self, task_id):
        """Check if task is active using O(1) lookup."""
        return task_id in self.active_task_ids or task_id in self.pending_task_ids

    def _update_widget_state(self, widget, item):
        """Update widget state based on item status."""
        status = item.get("status", "pending")

        # Debug: Log widget state update
        try:
            self.logger.debug(
                f"Updating widget {widget.task_id} to status: {status}")
        except AttributeError:
            logging.getLogger(__name__).debug(
                f"Updating widget {widget.task_id} to status: {status}")

        state_handlers = {
            DownloadStatus.COMPLETED.value: lambda: widget.set_finished(item.get("file_path", "")),
            DownloadStatus.FAILED.value: lambda: widget.set_error(item.get("error", "Failed")),
            DownloadStatus.CANCELLED.value: lambda: widget.set_error(item.get("error", "Failed")),
            'skipped': lambda: widget.set_status("Skipped"),
            DownloadStatus.PAUSED.value: lambda: widget.set_status("Paused"),
            DownloadStatus.PROCESSING.value: lambda: widget.set_status("Downloading..."),
            DownloadStatus.DOWNLOADING.value: lambda: widget.set_status("Queued..."),
            DownloadStatus.QUEUED.value: lambda: widget.set_status("Waiting in queue...")
        }

        handler = state_handlers.get(
            status, lambda: widget.set_status("Queued..."))
        handler()

        # Debug: Log widget state update completion
        try:
            self.logger.debug(f"Widget {widget.task_id} updated to {status}")
        except AttributeError:
            logging.getLogger(__name__).debug(f"Widget {widget.task_id} updated to {status}")

    def _safe_delete_widget(self, widget):
        """Safely delete widget with proper error handling."""
        try:
            if widget:
                widget.deleteLater()
        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Failed to delete widget: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting widget: {e}")

    def _update_queue_status(self):
        """Update the queue status indicator with detailed information."""
        queued_count = len(self.queued_tasks)  # Waiting in queue
        pending_count = len(self.pending_tasks)  # Ready to download next
        active_count = len(self.active_workers)  # Currently downloading

        if queued_count > 0 or pending_count > 0:
            # Show detailed status when there are items in queue
            parts = []
            if active_count > 0:
                parts.append(f"{active_count} active")
            if pending_count > 0:
                parts.append(f"{pending_count} pending")
            if queued_count > 0:
                parts.append(f"{queued_count} waiting")

            text = "Queue: " + " | ".join(parts)
            color = QUEUE_WAITING_COLOR
        else:
            # Only show active downloads when queue is empty
            text = f"{active_count} active downloads" if active_count > 0 else "No active downloads"
            color = QUEUE_ACTIVE_COLOR

        self.queue_status_label.setText(text)
        self.queue_status_label.setStyleSheet(
            f"{QUEUE_STATUS_STYLE} color: {color};")

    def _on_download_finished(self, task_id, path):
        widget = self.visible_widgets.get(task_id)
        if widget:
            widget.set_finished(path)
        self.history_manager.update_task(task_id, {
            "status": DownloadStatus.COMPLETED.value,
            "file_path": path,
            "finished_at": str(os.path.basename(path))
        })

        # Log download completion
        self.logger.info(f"Download finished: {task_id} -> {path}")

        # Re-ordering: keep active items on page 1.
        if self.pagination_widget.current_page == 0:
            # Avoid full rebuild during signal bursts; update only this row.
            self._refresh_task_in_current_page(task_id)
        else:
            # Targeted refresh: only update this specific task in current page
            self._refresh_task_in_current_page(task_id)
        # Note: Worker cleanup happens in _cleanup_worker triggered by thread.finished

    def _on_download_error(self, task_id, err):
        widget = self.visible_widgets.get(task_id)
        if err == "Cancelled":
            if widget:
                widget.set_status("Paused")
            self.history_manager.update_task(task_id, {"status": DownloadStatus.PAUSED.value})
        else:
            if widget:
                widget.set_error(err)
            self.history_manager.update_task(
                task_id, {"status": DownloadStatus.FAILED.value, "error": err})

        # Log download error
        self.logger.error(f"Download error: {task_id} -> {err}")

        self._refresh_task_in_current_page(task_id)

        # Check if auto-resume is enabled
        auto_resume = config.get('downloads.auto_resume', True)
        if auto_resume and err != "Cancelled":
            item = self.history_manager.get_by_id(task_id)
            auto_resume_count = item.get("auto_resume_count", 0) if item else 0
            if auto_resume_count < MAX_AUTO_RESUME_ATTEMPTS:
                self.history_manager.update_task(task_id, {"auto_resume_count": auto_resume_count + 1})
                # Schedule auto-resume after a delay
                QTimer.singleShot(5000, lambda: self._auto_resume_task(task_id))
            else:
                self.logger.warning(f"Task {task_id} failed after {MAX_AUTO_RESUME_ATTEMPTS} auto-resumes. Giving up.")

    def _on_download_cancelled(self, task_id):
        """Handle download cancellation from worker process."""
        widget = self.visible_widgets.get(task_id)
        if widget:
            widget.set_status("Paused")
        self.history_manager.update_task(task_id, {"status": DownloadStatus.PAUSED.value})
        self._refresh_task_in_current_page(task_id)

    def _auto_resume_task(self, task_id):
        """Automatically resume a failed download if auto-resume is enabled."""
        # Check if the task is still failed and auto-resume is still enabled
        # Memory optimization: use get_by_id for single lookup
        item = self.history_manager.get_by_id(task_id)
        if not item or item.get("status") != DownloadStatus.FAILED.value:
            return

        auto_resume = config.get('downloads.auto_resume', True)
        if not auto_resume:
            return

        # Don't auto-retry unrecoverable errors (DRM, geo-blocked, etc.)
        error_msg = item.get("error", "").lower()
        unrecoverable_patterns = [
            "drm", "drm protected", "geo-blocked", "geo restricted",
            "not available", "removed", "private", "login", "password",
            "members only", "subscription", "premium"
        ]
        if any(pattern in error_msg for pattern in unrecoverable_patterns):
            self.logger.info(f"Skipping auto-resume for {task_id}: unrecoverable error")
            return

        # Resume the task
        self._on_resume_task(task_id)

    def _on_filter_changed(self, filter_name: str):
        # Update button states
        for btn in self.filter_btns:
            btn.setChecked(btn.text() == filter_name)

        # Refilter list using widget registry for O(1) lookups
        for widget in self.visible_widgets.values():
            # Get status from history item linked to widget
            # Memory optimization: use get_by_id for single lookup
            item = self.history_manager.get_by_id(widget.task_id)
            if not item:
                widget.setVisible(False)
                continue

            status = item.get("status", "")
            is_visible = False
            if filter_name == "ALL":
                is_visible = True
            elif filter_name == "COMPLETED":
                is_visible = (status == DownloadStatus.COMPLETED.value)
            elif filter_name == "ACTIVE":
                is_visible = (
                    status in [DownloadStatus.PROCESSING.value, DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value, DownloadStatus.PAUSED.value])

            widget.setVisible(is_visible)

    def _on_pause_task(self, task_id):
        if task_id in self.active_workers:
            worker = self.active_workers[task_id]
            worker.cancel()  # Signal graceful cancellation to process
            self.history_manager.update_task(task_id, {"status": DownloadStatus.PAUSED.value})
            # Update widget UI immediately so user sees the paused state
            widget = self.visible_widgets.get(task_id)
            if widget:
                widget.set_status("Paused")
            # Immediately remove from active_workers to free up a concurrent slot
            # _cleanup_worker will handle the rest of the cleanup and trigger queue processing
            self._cleanup_worker(task_id)

    def _on_open_task(self, task_id):
        # Memory optimization: use get_by_id for single lookup
        item = self.history_manager.get_by_id(task_id)
        if not item:
            return
        file_path = item.get("file_path", "")
        dest = item.get("dest", "")
        # Try to open the exact file, or fallback to the destination folder
        target = file_path if os.path.exists(file_path) else dest
        if not target or not os.path.exists(target):
            return

        import subprocess
        import platform
        try:
            if platform.system() == "Windows":
                os.startfile(target)
            elif platform.system() == "Darwin":
                # macOS: use -R only for files, not directories
                if os.path.isfile(target):
                    subprocess.run(["open", "-R", target])
                else:
                    subprocess.run(["open", target])
            else:  # Linux
                # We open the directory containing the file if it's a file
                parent_dir = os.path.dirname(
                    target) if os.path.isfile(target) else target
                subprocess.run(["xdg-open", parent_dir])
        except Exception as e:
            self.logger.error(f"Error opening location: {e}")

    def _on_resume_task(self, task_id):
        # 1. Find in history
        # Memory optimization: use get_by_id for single lookup
        item = self.history_manager.get_by_id(task_id)
        if not item:
            return

        opts = dict(item.get("options") or {})

        # 2. Get widget if currently visible (option B allows non-visible tasks to not update UI)
        widget = self.visible_widgets.get(task_id)

        if len(self.active_workers) + len(self.pending_tasks) < self.max_concurrent:
            self.pending_tasks.append(
                (task_id, item["url"], item["dest"], opts))
            self.pending_task_ids.add(task_id)
            self.queued_task_ids.discard(task_id)
            self.history_manager.update_task(task_id, {"status": DownloadStatus.DOWNLOADING.value})
            if widget:
                widget.set_status("Queued...")
        else:
            self.queued_tasks.append(
                (task_id, item["url"], item["dest"], opts))
            self.queued_task_ids.add(task_id)
            self.pending_task_ids.discard(task_id)
            self.history_manager.update_task(task_id, {"status": DownloadStatus.QUEUED.value})
            if widget:
                widget.set_status("Waiting in queue...")

        self._process_queue()

        # If user is on page 1, ordering might have changed
        if self.pagination_widget.current_page == 0:
            self._request_refresh_current_page()
        else:
            self._refresh_task_in_current_page(task_id)

    def _on_retry_task(self, task_id):
        self._on_resume_task(task_id)

    def _on_help_task(self, task_id: str, error_message: str):
        """Show troubleshooting dialog for a failed task."""
        # Show troubleshooting dialog and check if user wants to retry
        should_retry = show_troubleshooting(self, error_message, context="Download Failed:")
        if should_retry:
            self._on_retry_task(task_id)

    def _retry_all_failed(self):
        """Retry all failed downloads in the history list."""
        # Get all failed items from history (O(n) but only once)
        failed_items = [h for h in self.history_manager.get_all()
                        if h.get('status') in (DownloadStatus.FAILED.value, DownloadStatus.CANCELLED.value)]

        # Retry each failed item using O(1) lookup
        for item in failed_items:
            self._on_resume_task(item['task_id'])

    def _resume_all_unfinished(self):
        """Resume all unfinished downloads (paused, failed, cancelled)."""
        # Get all unfinished items from history
        unfinished_items = [h for h in self.history_manager.get_all()
                            if h.get('status') in (DownloadStatus.PAUSED.value, DownloadStatus.FAILED.value, DownloadStatus.CANCELLED.value)]

        # Resume each unfinished item
        for item in unfinished_items:
            self._on_resume_task(item['task_id'])

    def _on_delete_task(self, task_id):
        # 1. Stop if running and cleanup to free the slot
        if task_id in self.active_workers:
            worker = self.active_workers[task_id]
            worker.cancel()
            # Immediately cleanup to free up concurrent slot
            self._cleanup_worker(task_id)

        # 2. Remove from pending and queued
        self.pending_tasks = [t for t in self.pending_tasks if t[0] != task_id]
        self.queued_tasks = [t for t in self.queued_tasks if t[0] != task_id]

        # Remove from performance tracking sets
        self.pending_task_ids.discard(task_id)
        self.queued_task_ids.discard(task_id)
        self.active_task_ids.discard(task_id)

        # 3. Remove from UI (only if currently displayed on the current page)
        widget = self.visible_widgets.get(task_id)
        if widget:
            for i in reversed(range(self.task_list_layout.count())):
                w = self.task_list_layout.itemAt(i).widget()
                if w == widget:
                    self.task_list_layout.takeAt(i)
                    self._safe_delete_widget(w)
                    break
        self.visible_widgets.pop(task_id, None)

        # 4. Remove from history
        self.history_manager.delete_task(task_id)

        # 6. Refresh pagination to show updated item count
        self._refresh_current_page()

        # Cleanup thumbnails no longer referenced in history.
        self._cleanup_unused_thumbnails()

    def _refresh_task_in_current_page(self, task_id):
        """Refresh a specific task if it's on the current page with thread safety."""
        try:
            # Get widget from current page cache
            widget = self.visible_widgets.get(task_id)
            if not widget:
                return

            # Check if widget is currently visible in layout
            if self.task_list_layout.indexOf(widget) < 0:
                return

            # Get current history item with thread safety
            try:
                # Memory optimization: use get_by_id for single lookup
                item = self.history_manager.get_by_id(task_id)
                if not item:
                    return

                # Update widget state safely
                self._update_widget_state(widget, item)

            except Exception as e:
                self.logger.warning(f"Error updating task {task_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error refreshing task {task_id}: {e}")

    def _load_history(self):
        """Load history with smart pagination."""
        # Memory optimization: use get_count() instead of loading all items
        history_count = self.history_manager.get_count()

        # Log history loading
        self.logger.debug(f"Loading history: {history_count} items found")

        # Update pagination widget
        self.pagination_widget.update_pagination(history_count)

        # Log pagination update
        self.logger.debug(
            f"Pagination updated: total_items={history_count}, total_pages={self.pagination_widget.total_pages}")

        # Load current page (preserves current page if possible)
        self._load_history_page(self.pagination_widget.current_page)

    def _refresh_current_page(self):
        """Refresh the current page to show updated items and update pagination."""
        # Memory optimization: use get_count() for pagination update
        history_count = self.history_manager.get_count()
        self.pagination_widget.update_pagination(history_count)

        # Validate current page is still valid
        current_page = self.pagination_widget.current_page
        total_pages = self.pagination_widget.total_pages

        if current_page >= total_pages and total_pages > 0:
            # Current page is invalid, go to last valid page
            self.pagination_widget.current_page = total_pages - 1
            current_page = self.pagination_widget.current_page

        # Reload current page
        self._load_history_page(current_page)

    def _request_refresh_current_page(self):
        """Coalesce multiple rapid refresh calls into one."""
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        QTimer.singleShot(200, self._do_refresh_current_page)

    def _do_refresh_current_page(self):
        self._refresh_scheduled = False
        # Safety: avoid rebuilding/destroying widgets while downloads are active.
        # Rebuilds can race with final progress/status emissions and cause crashes.
        if self.active_workers and not self._allow_history_rebuild_once:
            self._refresh_scheduled = True
            QTimer.singleShot(300, self._do_refresh_current_page)
            return
        # Consume the one-time allowance.
        self._allow_history_rebuild_once = False
        self._refresh_current_page()

    def _load_history_page(self, page_number):
        """Load a specific page of history items."""
        try:
            # Memory optimization: release widgets to pool instead of destroying
            # This reduces allocation overhead and GC pressure during pagination
            self.visible_widgets.clear()
            self._task_widget_pool.release_all()
            for i in reversed(range(self.task_list_layout.count())):
                item = self.task_list_layout.takeAt(i)
                w = item.widget() if item else None
                if w:
                    w.setParent(None)

            # Memory optimization: use get_page() to load only visible items
            # Note: Sorting by status is now handled in memory after loading page
            # This trades CPU for RAM savings on large histories (1000+ items)
            page_size = self.pagination_widget.page_size
            history_items = self.history_manager.get_page(page_number, page_size)

            if not history_items:
                return

            for item in history_items:
                task_id = item.get("task_id")
                if not task_id:
                    continue

                thumb_path = item.get("thumbnail", "")
                # Memory optimization: use widget pool to reuse TaskItem instances
                task_widget = self._task_widget_pool.acquire(
                    task_id,
                    item.get("title", "Unknown"),
                    source=item.get("url", ""),
                    thumb_path=thumb_path,
                )
                # Only connect signals once (new widgets need connections)
                if not task_widget.signals_connected:
                    task_widget.paused.connect(self._on_pause_task)
                    task_widget.resumed.connect(self._on_resume_task)
                    task_widget.retried.connect(self._on_retry_task)
                    task_widget.deleted.connect(self._on_delete_task)
                    task_widget.opened.connect(self._on_open_task)
                    task_widget.help_requested.connect(self._on_help_task)
                    self.theme_changed.connect(task_widget.update_theme)
                    task_widget.signals_connected = True

                self._update_widget_state(task_widget, item)

                self.task_list_layout.addWidget(task_widget)
                self.visible_widgets[task_id] = task_widget

                # Handle missing thumbnails (limit concurrent requests)
                if not thumb_path or not os.path.exists(thumb_path):
                    missing_thumbs = [{
                        "task_id": task_id,
                        "url": item.get("url", ""),
                        "thumb_url": "",
                    }]
                    self._start_thumbnail_worker(missing_thumbs)

        except Exception as e:
            try:
                self.logger.error(
                    f"Error loading history page {page_number}: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            except AttributeError:
                logging.getLogger(__name__).error(
                    f"Error loading history page {page_number}: {e}")
                import traceback
                traceback.print_exc()
            # Ensure UI doesn't break completely
            pass

    def _clear_tasks(self, mode: str):
        """
        Clear history across *all* pages (not just the currently visible ones).

        Previously this only removed items that had widgets on the current page,
        which meant other pages' history remained in `history.json` and came back
        after restarting the app.
        """
        # mode: all, completed, failed
        mode = (mode or "").lower()

        # Show confirmation dialog before clearing
        from PySide6.QtWidgets import QMessageBox

        if mode == "all":
            reply = QMessageBox.question(
                self, "Clear History",
                "Are you sure you want to clear ALL download history?\n\nThis will cancel any active downloads and cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        elif mode == "completed":
            reply = QMessageBox.question(
                self, "Clear History",
                "Are you sure you want to clear all COMPLETED downloads from history?\n\nThis cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        elif mode == "failed":
            reply = QMessageBox.question(
                self, "Clear History",
                "Are you sure you want to clear all FAILED downloads from history?\n\nThis cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        else:
            return

        if reply != QMessageBox.Yes:
            return

        # Snapshot visible widget task_ids + statuses before mutating history
        visible_task_ids = set(self.visible_widgets.keys())
        history_before = self.history_manager.get_all()
        status_map = {h.get("task_id"): h.get("status", "")
                      for h in history_before if h.get("task_id")}

        if mode == "all":
            # Cancel and cleanup active downloads immediately to free slots.
            active_task_ids = list(self.active_workers.keys())
            for task_id in active_task_ids:
                try:
                    worker = self.active_workers[task_id]
                    worker.cancel()
                    self._cleanup_worker(task_id)
                except Exception:
                    pass

            # Clear in-memory queues.
            self.pending_tasks.clear()
            self.queued_tasks.clear()
            self.pending_task_ids.clear()
            self.queued_task_ids.clear()
            self.active_task_ids.clear()

            # Clear history on disk (flushes immediately due to HistoryManager logic).
            self.history_manager.clear()

            # Clear visible UI widgets.
            for i in reversed(range(self.task_list_layout.count())):
                w = self.task_list_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()
            self.task_list_layout.update()
            self.visible_widgets.clear()

            self.pagination_widget.update_pagination(0)
            self.pagination_widget.current_page = 0
            self._update_queue_status()
            self._cleanup_unused_thumbnails()
            return

        if mode == "completed":
            statuses_to_delete = {"completed"}
            self.history_manager.delete_by_status("completed")
        elif mode == "failed":
            statuses_to_delete = {"failed", "cancelled"}
            self.history_manager.delete_by_status("failed")
            self.history_manager.delete_by_status("cancelled")
        else:
            return

        # Remove visible widgets whose task_id was cleared from history.
        to_remove = [tid for tid in visible_task_ids if status_map.get(
            tid, "") in statuses_to_delete]
        for tid in to_remove:
            widget = self.visible_widgets.pop(tid, None)
            if not widget:
                continue
            # Remove from layout
            for i in reversed(range(self.task_list_layout.count())):
                w = self.task_list_layout.itemAt(i).widget()
                if w == widget:
                    self.task_list_layout.takeAt(i)
                    break
            widget.deleteLater()

        # Update pagination counts; avoid rebuilding immediately if active downloads are running.
        self._update_queue_status()
        # Memory optimization: use get_count() instead of len(get_all())
        self.pagination_widget.update_pagination(self.history_manager.get_count())
        self._request_refresh_current_page()
        self._cleanup_unused_thumbnails()

    def _setup_analyze_spinner(self):
        """Setup spinning retry icon on analyze button."""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtGui import QPixmap

        # Create label for spinner
        self._spinner_label = QLabel(self.analyze_btn)
        self._spinner_label.setFixedSize(20, 20)
        self._spinner_label.setAlignment(Qt.AlignCenter)
        self._spinner_label.setStyleSheet(
            "background-color: transparent; border: none;")

        # Center the spinner in the button
        btn_geo = self.analyze_btn.geometry()
        self._spinner_label.move(
            (btn_geo.width() - 20) // 2, (btn_geo.height() - 20) // 2)

        # Load and colorize the retry icon
        colors = get_theme_colors()
        spinner_icon = get_icon("retry.png", colors['button_text'])
        self._spinner_pixmap = spinner_icon.pixmap(QSize(20, 20))
        self._spinner_label.setPixmap(self._spinner_pixmap)

        # Setup rotation animation with timer
        self._spinner_angle = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._rotate_spinner)
        self._spinner_timer.start(50)  # Rotate every 50ms
        self._spinner_label.show()

    def _rotate_spinner(self):
        """Rotate the spinner icon."""
        if not hasattr(self, '_spinner_label') or not self._spinner_label:
            return

        self._spinner_angle = (self._spinner_angle + 30) % 360

        transform = QTransform()
        transform.rotate(self._spinner_angle)
        rotated = self._spinner_pixmap.transformed(
            transform, Qt.SmoothTransformation)

        # Keep centered
        self._spinner_label.setPixmap(rotated)

    def _stop_analyze_spinner(self):
        """Stop the spinning animation and clean up."""
        if hasattr(self, '_spinner_timer') and self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

        if hasattr(self, '_spinner_label') and self._spinner_label:
            self._spinner_label.hide()
            self._spinner_label.deleteLater()
            self._spinner_label = None

    def closeEvent(self, event):
        """Ensure debounced history writes are flushed on app exit."""
        try:
            if hasattr(self, "history_manager") and hasattr(self.history_manager, "flush"):
                self.history_manager.flush()
        except Exception:
            pass

        # Stop all thumbnail workers
        if hasattr(self, 'thumb_workers'):
            for worker in list(self.thumb_workers):
                try:
                    worker.quit()
                    worker.wait(1000)
                    if worker.isRunning():
                        worker.terminate()
                except Exception:
                    pass
            self.thumb_workers.clear()

        # Stop all info workers
        if hasattr(self, 'running_info_workers'):
            for thread, worker in list(self.running_info_workers):
                try:
                    thread.quit()
                    thread.wait(1000)
                    if thread.isRunning():
                        thread.terminate()
                except Exception:
                    pass
            self.running_info_workers.clear()

        # Stop all download workers
        if hasattr(self, 'active_workers'):
            for task_id, worker in list(self.active_workers.items()):
                try:
                    worker.cancel()
                    worker.terminate()
                    worker.join(1.0)
                except Exception:
                    pass
            self.active_workers.clear()

        super().closeEvent(event)
