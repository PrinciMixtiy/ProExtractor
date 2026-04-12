from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame, QLineEdit,
                             QSizePolicy, QComboBox, QCheckBox, QWidget, QScrollArea, QFileDialog)
from PySide6.QtCore import Qt, Signal, QSize, Property, QEasingCurve, QPropertyAnimation, QRect
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from desktop.ui.icons import get_icon
from desktop.core.config import config
from desktop.core.constants import DEFAULT_PAGE_SIZE, PAGE_LABEL_STYLE, QUEUE_WAITING_COLOR
from desktop.styles import get_theme_colors
import requests
import os

class ModernToggle(QFrame):
    """Modern iOS-style switch toggle with smooth animation."""
    toggled = Signal(bool)

    def __init__(self, parent=None, active_color="#14b8a6"):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._set_colors(active_color)
        self._active = False
        self._circle_pos = 2
        
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def _set_colors(self, active_color):
        colors = get_theme_colors()
        self._bg_off = colors['outer_border']
        self._bg_on = active_color
        self._circle_color = "#ffffff"

    @Property(int)
    def circle_pos(self):
        return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    def isChecked(self):
        return self._active

    def setChecked(self, checked):
        if self._active == checked:
            return
        self._active = checked
        self.animation.stop()
        self.animation.setEndValue(22 if checked else 2)
        self.animation.start()
        self.toggled.emit(checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._active)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setPen(Qt.NoPen)
        bg_color = QColor(self._bg_on if self._active else self._bg_off)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw circle
        painter.setBrush(QColor(self._circle_color))
        painter.drawEllipse(self._circle_pos, 2, 20, 20)
        painter.end()

class ModernActionRow(QFrame):
    """A row with icon, title, and a toggle switch."""
    def __init__(self, title, icon_name, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setObjectName("ActionRow")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_name = icon_name
        layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(self.title_label, 1)
        
        # Toggle
        self.toggle = ModernToggle()
        layout.addWidget(self.toggle)
        
        self.update_theme()

    def update_theme(self):
        colors = get_theme_colors()
        self.setStyleSheet(f"""
            #ActionRow {{
                background-color: {colors['bg_main']};
                border-radius: 8px;
            }}
        """)
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: 600; background: transparent; color: {colors['text_primary']};")
        self.icon_label.setPixmap(get_icon(self.icon_name, colors['accent']).pixmap(20, 20))
        self.toggle._set_colors(colors['accent'])
        self.toggle.update()

class PaginationWidget(QFrame):
    """Smart pagination widget for history management."""
    page_changed = Signal(int)  # page_number
    
    def __init__(self, page_size=DEFAULT_PAGE_SIZE):
        super().__init__()
        self.page_size = page_size
        self.current_page = 0
        self.total_items = 0
        self.total_pages = 0
        self.setObjectName("Card")
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Previous button
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self._go_previous)
        layout.addWidget(self.prev_btn)
        
        layout.addStretch()
        
        # Page info
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setStyleSheet(PAGE_LABEL_STYLE)
        layout.addWidget(self.page_label)
        
        layout.addStretch()
        
        # Next button
        self.next_btn = QPushButton("Next →")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._go_next)
        layout.addWidget(self.next_btn)
        
    def update_pagination(self, total_items):
        """Update pagination info and buttons."""
        self.total_items = total_items
        self.total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        
        # Ensure current page is valid
        self.current_page = min(self.current_page, self.total_pages - 1)
        
        self._update_ui()
        
    def _update_ui(self):
        """Update UI elements."""
        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
        
    def _go_previous(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_ui()
            self.page_changed.emit(self.current_page)
            
    def _go_next(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_ui()
            self.page_changed.emit(self.current_page)
            
    def get_page_range(self):
        """Get start and end indices for current page."""
        start = self.current_page * self.page_size
        end = min(start + self.page_size, self.total_items)
        return start, end
        
    def reset_to_first_page(self):
        """Reset to first page."""
        self.current_page = 0
        self._update_ui()

class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class ThumbnailLabel(QLabel):
    """A label that fetches and displays a thumbnail that fills its container."""
    def __init__(self):
        super().__init__()
        # Allow width to be the master for height calculation
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setAlignment(Qt.AlignCenter)
        colors = get_theme_colors()
        self.setStyleSheet(f"background-color: {colors['bg_dark']}; border-radius: 8px;")
        self._pixmap = None
        self.setText("Waiting for URL...")

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width: int) -> int:
        """Maintain a 16:9 aspect ratio based on width."""
        return int(width * 9 / 16)

    def paintEvent(self, event):
        if not self._pixmap or self._pixmap.isNull():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.Antialiasing)

            # Implementation of "Object-Fit: Cover"
            size = self.size()
            pixmap_size = self._pixmap.size()
            pixmap_size.scale(size, Qt.KeepAspectRatioByExpanding)
            
            # Calculate cropping area
            x = (size.width() - pixmap_size.width()) // 2
            y = (size.height() - pixmap_size.height()) // 2
            
            target_rect = QRect(x, y, pixmap_size.width(), pixmap_size.height())
            
            # Draw the pixmap centered and filling the widget
            painter.drawPixmap(target_rect, self._pixmap)
        finally:
            painter.end()

    def load_from_url(self, url: str):
        if not url:
            return
        try:
            response = requests.get(url, timeout=5)
            image = QImage()
            image.loadFromData(response.content)
            self._pixmap = QPixmap.fromImage(image)
            self.setText("") # Clear "Loading..." text
            self.update() # Trigger repaint
        except Exception as e:
            self._pixmap = None
            self.setText(f"Error: {str(e)}")
            self.update()

    def update_theme(self):
        colors = get_theme_colors()
        self.setStyleSheet(f"background-color: {colors['bg_dark']}; color: {colors['text_secondary']}; border-radius: 8px;")

class VideoInfoCard(QFrame):
    """Square container for video preview info."""
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        # Let the content (Thumbnail) drive the height
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # Tighten margins for aspect ratio
        self.layout.setSpacing(0)
        
        self.thumbnail = ThumbnailLabel()
        # No fixed height - let the card height control this
        self.layout.addWidget(self.thumbnail, 1) # Priority to thumbnail
        
        self.info_container = QVBoxLayout()
        self.info_container.setContentsMargins(16, 12, 16, 12)
        self.info_container.setSpacing(6)
        
        self.title = QLabel("Video Title")
        self.title.setObjectName("ItemTitle")
        self.title.setWordWrap(True)
        self.title.setStyleSheet("font-size: 18px; font-weight: 700;")  # Increased from default
        self.info_container.addWidget(self.title)
        
        self.author = QLabel("Author Name")
        self.author.setObjectName("ItemSubtitle")
        self.author.setStyleSheet("font-size: 14px; font-weight: 500;")  # Increased from default
        self.info_container.addWidget(self.author)
        
        self.stats = QLabel("0 Views • 0:00")
        self.stats.setObjectName("ItemSubtitle")
        self.stats.setStyleSheet("font-size: 13px; font-weight: 500;")  # Increased from default
        self.info_container.addWidget(self.stats)
        
        self.layout.addLayout(self.info_container)

    def update_info(self, info: dict):
        self.title.setText(info.get("title", "Unknown Title"))
        self.author.setText(info.get("author", "Unknown Author"))
        
        duration = info.get("length")
        if duration:
            h, m = divmod(int(duration), 3600)
            m, s = divmod(m, 60)
            duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        else:
            duration_str = "Playlist"
            
        views = info.get("views", 0) or 0
        self.stats.setText(f"{int(views):,} Views • {duration_str}")
        self.thumbnail.load_from_url(info.get("thumbnail"))

    def update_theme(self):
        colors = get_theme_colors()
        self.thumbnail.update_theme()
        self.title.setStyleSheet(f"color: {colors['text_primary']}; font-size: 18px; font-weight: 700;")
        self.author.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 14px; font-weight: 500;")
        self.stats.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 13px; font-weight: 500;")

    def reset(self):
        """Reset preview UI when starting a new download batch."""
        self.title.setText("Video Title")
        self.author.setText("Author Name")
        self.stats.setText("0 Views • 0:00")
        # Clear thumbnail pixmap and show loading placeholder text.
        self.thumbnail._pixmap = None
        self.thumbnail.setText("Waiting for URL...")
        self.thumbnail.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Content dynamic resizing logic if needed
        pass

class FileInfoCard(QFrame):
    """Sub-widget showing summary of the selected extraction profile."""
    def __init__(self):
        super().__init__()
        self.setObjectName("InfoCard")
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("FILE INFORMATION")
        header.setObjectName("OptionHeader")
        self.layout.addWidget(header)
        
        # Grid for info
        grid = QVBoxLayout()
        grid.setSpacing(12)
        
        self.size_row = self._create_row("Estimated Size", "0.00 MB", is_accent=True)
        self.format_row = self._create_row("Format", "MP4 / H.264")
        self.folder_row = self._create_row("Target Folder", "/Downloads/...")
        
        grid.addLayout(self.size_row[0])
        grid.addLayout(self.format_row[0])
        grid.addLayout(self.folder_row[0])
        
        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _create_row(self, key, value, is_accent=False):
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 4, 0, 4)
        k_lbl = QLabel(key)
        k_lbl.setObjectName("InfoKey")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("InfoValueAccent" if is_accent else "InfoValue")
        v_lbl.setAlignment(Qt.AlignRight)
        layout.addWidget(k_lbl)
        layout.addStretch()
        layout.addWidget(v_lbl)
        return layout, v_lbl

    def update_info(self, size_str, format_str, path_str):
        self.size_row[1].setText(size_str)
        self.format_row[1].setText(format_str)
        
        # Smart path eliding: show the end of the path
        if len(path_str) > 25:
            # Try to show parent folder + folder
            parts = path_str.split(os.sep)
            if len(parts) > 1:
                path_str = f".../{parts[-2]}/{parts[-1]}"
            else:
                path_str = "..." + path_str[-22:]
        self.folder_row[1].setText(path_str)

class StreamOptionsCard(QFrame):
    """Redesigned extraction profile matching the high-fidelity mockup."""
    download_clicked = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(24)
        
        # --- TOP ROW: Format & Resolution ---
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        # Format Selector
        format_col = QVBoxLayout()
        f_header = QLabel("FORMAT")
        f_header.setObjectName("OptionHeader")
        format_col.addWidget(f_header)
        self.format_combo = QComboBox()
        self.format_combo.setFixedHeight(54)
        self.format_combo.setObjectName("ModernInput")
        format_col.addWidget(self.format_combo)
        top_row.addLayout(format_col, 1)
        
        # Resolution Selector
        res_col = QVBoxLayout()
        r_header = QLabel("RESOLUTION")
        r_header.setObjectName("OptionHeader")
        res_col.addWidget(r_header)
        self.quality_combo = QComboBox()
        self.quality_combo.setFixedHeight(54)
        self.quality_combo.setObjectName("ModernInput")
        self.quality_combo.currentIndexChanged.connect(self._on_selection_changed)
        res_col.addWidget(self.quality_combo)
        top_row.addLayout(res_col, 1)
        
        self.main_layout.addLayout(top_row)
        
        # Connect format to quality updates and save
        self.format_combo.currentIndexChanged.connect(self._update_quality_list)
        self.format_combo.currentIndexChanged.connect(self._save_settings)
        
        # --- TOGGLE ROWS ---
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(12)
        
        self.thumb_toggle = ModernActionRow("Extract Thumbnails", "thumbnail.png")
        self.thumb_toggle.toggle.setChecked(config.get('downloads.embed_thumbnails', True))
        toggle_row.addWidget(self.thumb_toggle, 1)
        
        self.sub_toggle = ModernActionRow("Auto-Subtitle (SRT)", "subtitles.png")
        self.sub_toggle.toggle.setChecked(config.get('downloads.auto_generate_subtitles', False))
        toggle_row.addWidget(self.sub_toggle, 1)
        
        self.main_layout.addLayout(toggle_row)
        
        # Connect toggles to save
        self.thumb_toggle.toggle.toggled.connect(self._save_settings)
        self.sub_toggle.toggle.toggled.connect(self._save_settings)
        
        # --- DESTINATION FOLDER ---
        dest_col = QVBoxLayout()
        dest_header = QLabel("DESTINATION FOLDER")
        dest_header.setObjectName("OptionHeader")
        dest_col.addWidget(dest_header)
        
        dest_row = QHBoxLayout()
        dest_row.setSpacing(12)
        
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        self.path_display.setFixedHeight(54)
        self.path_display.setObjectName("ModernInput")
        dest_row.addWidget(self.path_display, 1)
        
        self.folder_btn = QPushButton()
        self.folder_btn.setFixedSize(54, 54)
        self.folder_btn.setObjectName("SecondaryButton")
        self.folder_btn.setIcon(get_icon("folder.png", get_theme_colors()['text_primary']))
        dest_row.addWidget(self.folder_btn)
        
        dest_col.addLayout(dest_row)
        self.main_layout.addLayout(dest_col)
        
        # Push the download button to the absolute bottom
        self.main_layout.addStretch()
        
        # --- START BUTTON ---
        self.download_btn = QPushButton("  START DOWNLOAD")
        self.download_btn.setObjectName("PrimaryButton")
        self.download_btn.setFixedHeight(54)
        self.download_btn.setFont(QFont("Inter", 13, QFont.Bold))
        self.download_btn.setIcon(get_icon("download.png", "#ffffff"))
        self.download_btn.setIconSize(QSize(22, 22))
        self.download_btn.setStyleSheet("padding-left: 15px; padding-right: 15px;")
        self.download_btn.clicked.connect(self._on_download)
        self.main_layout.addWidget(self.download_btn)
        
        # Connect folder click
        self.folder_btn.clicked.connect(self._on_select_folder)
        
        self.current_streams = []
        # Support both legacy and new config keys
        default_folder = config.get('downloads.path') or config.get('general.default_download_folder')
        self.target_folder = default_folder or os.path.join(os.path.expanduser("~"), "Downloads")
        self.path_display.setText(self.target_folder)

        # Hidden labels for logic back-compat (if needed by main_window)
        self.size_label = QLabel()
        self.format_label = QLabel()
        self.folder_label = QLabel()

    def _on_select_folder(self):
        """Open system folder dialog and update target."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Destination Folder",
            self.target_folder
        )
        if folder:
            self.set_target_folder(folder)
            # Persist to config immediately
            config.set('downloads.path', folder)
            config.set('general.default_download_folder', folder)

    def set_target_folder(self, path: str):
        self.target_folder = path
        self.path_display.setText(path)
        self._on_selection_changed()

    def update_streams(self, streams: dict):
        """Update available formats and resolutions from video info."""
        self.current_streams = streams.get("formats", [])
        if not self.current_streams:
            return

        # 1. Identify unique available extensions (formats)
        available_exts = set()
        for f in self.current_streams:
            ext = f.get('ext')
            if ext: available_exts.add(ext)
        
        # Simplified Format Selection: Unified MP4 for video, plus Audio Only.
        self.format_combo.blockSignals(True)
        self.format_combo.clear()
        self.format_combo.addItem("MP4 Video", "mp4")
        self.format_combo.addItem("Audio Only (MP3)", "audio_only")
        
        # Try to match the configured default format
        default_format = config.get('downloads.default_format', 'mp4')
        if config.get('downloads.audio_only'): default_format = "audio_only"
        
        for i in range(self.format_combo.count()):
            if self.format_combo.itemData(i) == default_format:
                self.format_combo.setCurrentIndex(i)
                break
        self.format_combo.blockSignals(False)

        # 2. Trigger quality list update for the selected format
        self._update_quality_list()
        
        # Set default toggle states
        self.thumb_toggle.toggle.setChecked(config.get('downloads.embed_thumbnails', True))
        self.sub_toggle.toggle.setChecked(config.get('downloads.auto_generate_subtitles', False))
        
        self._on_selection_changed()

    def _update_quality_list(self):
        """Populate resolutions or bitrates. Resolution list now shows ALL qualities."""
        selected_format = self.format_combo.currentData()
        if not selected_format:
            return

        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        
        # Add virtual "Highest" option
        self.quality_combo.addItem("Highest Quality", "highest")

        if selected_format == "audio_only":
            # --- AUDIO ONLY MODE ---
            # Filter for audio streams
            audio_streams = [f for f in self.current_streams if f.get('vcodec') == 'none']
            # Sort by bitrate (abr) descending
            audio_streams.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
            
            for f in audio_streams:
                abr = f.get('abr')
                if abr:
                    label = f"{int(abr)} kbps"
                    if f.get('ext'): label += f" ({f['ext'].upper()})"
                    self.quality_combo.addItem(label, f)
        else:
            # --- VIDEO MODE ---
            # Unified Strategy: Show ALL resolutions available, regardless of extension.
            # Downloader will handle merging high-res (WebM) into MP4.
            
            # Extract unique resolutions (heights) to avoid duplicates
            seen_heights = set()
            filtered = []
            
            # Sort all streams by height descending
            sorted_streams = sorted(self.current_streams, key=lambda x: x.get('height', 0) or 0, reverse=True)
            
            for f in sorted_streams:
                height = f.get('height')
                if height and height not in seen_heights:
                    seen_heights.add(height)
                    filtered.append(f)

            # Add filtered streams
            for f in filtered:
                height = f.get('height')
                if height:
                    label = f"{height}p"
            # Sort by resolution (height) descending
            filtered.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)

            # Add filtered streams
            for f in filtered:
                height = f.get('height')
                if height:
                    label = f"{height}p"
                    note = f.get('note', '')
                    # Avoid redundant labels like "1080p - 1080p"
                    if note and note.lower() != f"{height}p":
                        label += f" - {note}"
                    self.quality_combo.addItem(label, f)

        # Try to match preferred resolution from settings
        default_quality = config.get('downloads.default_quality', 'highest')
        match_index = 0
        if default_quality != 'highest':
            for i in range(self.quality_combo.count()):
                data = self.quality_combo.itemData(i)
                if isinstance(data, dict):
                    # Check both height for video and abr for audio fallback
                    h = f"{data.get('height')}p"
                    if h == default_quality:
                        match_index = i
                        break
        
        self.quality_combo.setCurrentIndex(match_index)
        self.quality_combo.blockSignals(False)
        
        # Update labels (size, etc.)
        self._on_selection_changed()

    def reset_to_defaults(self):
        """Reset extraction profile selectors to configured defaults."""
        self.thumb_toggle.toggle.setChecked(config.get('downloads.embed_thumbnails', True))
        self.sub_toggle.toggle.setChecked(config.get('downloads.auto_generate_subtitles', False))

        default_quality = config.get('downloads.default_quality', 'highest')
        default_format = config.get('downloads.default_format', 'mp4')
        
        for i in range(self.format_combo.count()):
            if self.format_combo.itemData(i) == default_format:
                self.format_combo.setCurrentIndex(i)
                break

        default_index = 0
        for i in range(self.quality_combo.count()):
            data = self.quality_combo.itemData(i)
            if default_quality == "highest" and data == "highest":
                default_index = i
                break
            if default_quality in ["1080p", "720p", "480p", "360p"] and isinstance(data, dict):
                if data.get('height') == int(default_quality.replace('p', '')):
                    if default_format == data.get('ext'):
                        default_index = i
                        break

        if self.quality_combo.count() > 0:
            self.quality_combo.setCurrentIndex(default_index)
        self._on_selection_changed()

        # Refresh derived labels (estimated size/format).
        self._on_selection_changed()

    def _on_selection_changed(self):
        data = self.quality_combo.currentData()
        size_str = "Unknown Size"
        fmt_str = "Auto / MP4"
        
        if isinstance(data, dict):
            # Estimate size
            size = data.get("filesize") or data.get("filesize_approx")
            if size:
                size_mb = size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
            
            if data.get('vcodec') == 'none':
                fmt_str = f"Audio ({data.get('ext', 'MP3').upper()}) / {int(data.get('abr', 0))}kbps"
            else:
                fmt_str = f"{data.get('ext', 'MP4').upper()} / {data.get('vcodec', 'H.264').split('.')[0]}"
        elif data == "audio_only" or self.format_combo.currentData() == "audio_only":
            fmt_str = "MP3 / Audio Only"
            
        # Update the new layout labels
        self.size_label.setText(f"Estimated Size: {size_str}")
        self.format_label.setText(f"Format: {fmt_str}")
        
        # Smart path eliding for folder
        path_str = self.target_folder
        if len(path_str) > 25:
            # Try to show parent folder + folder
            parts = path_str.split(os.sep)
            if len(parts) > 1:
                path_str = f".../{parts[-2]}/{parts[-1]}"
            else:
                path_str = "..." + path_str[-22:]
        self.folder_label.setText(f"Target: {path_str}")
        
        # Save current state to settings
        self._save_settings()

    def refresh_settings(self):
        """Reload settings from config and update UI switches."""
        self.thumb_toggle.toggle.setChecked(config.get('downloads.embed_thumbnails', True))
        self.sub_toggle.toggle.setChecked(config.get('downloads.auto_generate_subtitles', False))
        
        # Update target folder from config as well
        default_folder = config.get('downloads.path') or config.get('general.default_download_folder')
        if default_folder:
            self.set_target_folder(default_folder)

    def _save_settings(self):
        """Persist current UI selections to config."""
        fmt = self.format_combo.currentData()
        if fmt:
            audio_only = (fmt == "audio_only")
            config.set('downloads.audio_only', audio_only)
            if not audio_only:
                config.set('downloads.default_format', fmt)
            
        qual_data = self.quality_combo.currentData()
        if qual_data:
            if isinstance(qual_data, dict):
                h = qual_data.get('height')
                if h:
                    config.set('downloads.default_quality', f"{h}p")
            else:
                config.set('downloads.default_quality', str(qual_data))
                
        config.set('downloads.embed_thumbnails', self.thumb_toggle.toggle.isChecked())
        config.set('downloads.auto_generate_subtitles', self.sub_toggle.toggle.isChecked())

    def _on_download(self):
        data = self.quality_combo.currentData()
        current_format = self.format_combo.currentData()
        
        options = {
            "quality": data if not isinstance(data, dict) else str(data.get('height', data.get('abr', ''))),
            "format": current_format or "mp4",
            "audio_only": current_format == "audio_only",
            "embed_thumbnails": self.thumb_toggle.toggle.isChecked(),
            "auto_generate_subtitles": self.sub_toggle.toggle.isChecked(),
            "subtitle_language": config.get('downloads.subtitle_language', 'en'),
        }
        self.download_clicked.emit(options)

    def update_theme(self):
        """Update checkbox and label colors when theme changes."""
        colors = get_theme_colors()
        
        # Update toggles
        self.thumb_toggle.update_theme()
        self.sub_toggle.update_theme()
        
        # Update folder button icon
        self.folder_btn.setIcon(get_icon("folder.png", colors['text_primary']))
        
        # Update file information labels
        self.size_label.setStyleSheet(f"color: {colors['text_primary']}; font-size: 12px; font-weight: 500; margin: 1px 0; background-color: transparent;")
        self.format_label.setStyleSheet(f"color: {colors['text_primary']}; font-size: 12px; font-weight: 500; margin: 1px 0; background-color: transparent;")
        self.folder_label.setStyleSheet(f"color: {colors['text_primary']}; font-size: 12px; font-weight: 500; margin: 1px 0; background-color: transparent;")

class TaskItem(QFrame):
    """High-fidelity horizontal card for the integrated history archive."""
    cancelled = Signal(str)
    paused = Signal(str)
    resumed = Signal(str)
    retried = Signal(str)
    deleted = Signal(str)
    opened = Signal(str)

    def __init__(self, task_id: str, title: str, source: str = "", thumb_path: str = ""):
        super().__init__()
        self.task_id = task_id
        self.current_status = "pending"
        self.current_msg = "DOWNLOADING"
        self.setObjectName("HistoryCard")
        self.setFixedHeight(100)
        # Remove hard-coded color - will use stylesheet
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(20)
        
        # --- 1. Thumbnail (Left) ---
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 68)
        colors = get_theme_colors()
        self.thumb_label.setStyleSheet(f"background-color: {colors['bg_dark']}; border-radius: 4px;")  # Theme-aware dark background for thumbnail contrast
        self.thumb_label.setScaledContents(True)
        # We manually scale pixmaps to the label size to reduce peak memory usage.
        # Leaving setScaledContents(True) can keep the original pixmap around internally.
        self.thumb_label.setScaledContents(False)
        if thumb_path and os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            self.thumb_label.setPixmap(
                pix.scaled(
                    self.thumb_label.width(),
                    self.thumb_label.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )
        else:
            self.thumb_label.setText("🎞️")
            self.thumb_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.thumb_label)
        
        # --- 2. Metadata (Middle-Left) ---
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ItemTitle")
        # Remove hard-coded color - will use stylesheet
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.title_label.setFixedWidth(250)
        # Elide title
        metrics = self.title_label.fontMetrics()
        elided = metrics.elidedText(title, Qt.ElideRight, 250)
        self.title_label.setText(elided)
        meta_layout.addWidget(self.title_label)
        
        self.source_label = QLabel(source if source else "Source unknown")
        self.source_label.setObjectName("ItemSubtitle")
        # Remove hard-coded color - will use stylesheet
        self.source_label.setStyleSheet("font-size: 11px;")
        meta_layout.addWidget(self.source_label)
        
        self.main_layout.addLayout(meta_layout, 4)
        
        # --- 3. Size / Speed (Middle) ---
        metric_layout = QVBoxLayout()
        metric_layout.setSpacing(4)
        metric_layout.setAlignment(Qt.AlignCenter)
        
        self.size_label = QLabel("0.0 MB / 0.0 MB")
        # Remove hard-coded color - will use stylesheet
        self.size_label.setStyleSheet("font-size: 12px; font-weight: 700;")
        metric_layout.addWidget(self.size_label)
        
        self.speed_label = QLabel("Waiting...")
        # Remove hard-coded color - will use stylesheet
        self.speed_label.setStyleSheet("font-size: 11px; font-weight: 800;")
        metric_layout.addWidget(self.speed_label)
        
        self.main_layout.addLayout(metric_layout, 2)
        
        # --- 4. Status (Middle-Right) ---
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        status_layout.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { border-radius: 4px; }")
        status_layout.addWidget(self.progress_bar)
        
        self.status_badge = QLabel("PENDING")
        self.status_badge.setAlignment(Qt.AlignCenter)
        # Remove hard-coded color - will use stylesheet
        self.status_badge.setStyleSheet("font-size: 10px; font-weight: 900; letter-spacing: 1px;")
        status_layout.addWidget(self.status_badge)
        
        self.main_layout.addLayout(status_layout, 2)
        
        # --- 5. Actions (Right) ---
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(8)
        
        # Remove hard-coded button styles - will use stylesheet
        
        # Get theme-aware icon colors
        colors = get_theme_colors()
        # Use a more visible color for icons in light mode
        icon_color = colors['text_secondary'] if colors['text_primary'] == '#0f172a' else colors['text_primary']
        
        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(get_icon("pause.png", icon_color))
        
        self.resume_btn = QPushButton()
        self.resume_btn.setIcon(get_icon("play.png", icon_color))
        
        self.open_btn = QPushButton(" OPEN")
        self.open_btn.setIcon(get_icon("folder.png", "#0ea5e9"))  # Blue folder icon
        
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(get_icon("close.png", icon_color))
        
        # Store icon color reference for theme updates
        self._icon_color = icon_color
        self._button_text_color = colors['button_text']
        
        self.pause_btn.setIconSize(QSize(18, 18))
        self.resume_btn.setIconSize(QSize(18, 18))
        self.open_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setIconSize(QSize(18, 18))
        
        self.pause_btn.setFixedSize(36, 36)
        self.resume_btn.setFixedSize(36, 36)
        self.delete_btn.setFixedSize(36, 36)
        
        self.open_btn.setFixedHeight(36)
        # Remove hard-coded style - will use stylesheet
        self.open_btn.setStyleSheet("QPushButton { border-radius: 4px; font-size: 13px; font-weight: 800; padding: 0 16px; }")
        
        for btn in [self.pause_btn, self.resume_btn, self.delete_btn]:
            # Remove hard-coded style - will use stylesheet
            btn.setStyleSheet("QPushButton { border-radius: 4px; font-size: 14px; }")
            
        for btn in [self.pause_btn, self.resume_btn, self.open_btn, self.delete_btn]:
            self.actions_layout.addWidget(btn)
            
        self.pause_btn.clicked.connect(lambda: self.paused.emit(self.task_id))
        self.resume_btn.clicked.connect(lambda: self.resumed.emit(self.task_id))
        self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.task_id))
        self.open_btn.clicked.connect(lambda: self.opened.emit(self.task_id))
        
        self.main_layout.addLayout(self.actions_layout, 2)
        self._update_ui_state()

    def update_theme(self):
        """Update icon colors when theme changes."""
        colors = get_theme_colors()
        # Use a more visible color for icons in light mode
        icon_color = colors['text_secondary'] if colors['text_primary'] == '#0f172a' else colors['text_primary']
        self._icon_color = icon_color
        self._button_text_color = colors['button_text']
        
        # Update all icons with new theme colors
        self.pause_btn.setIcon(get_icon("pause.png", icon_color))
        self.resume_btn.setIcon(get_icon("play.png", icon_color))
        self.delete_btn.setIcon(get_icon("close.png", icon_color))
        self.open_btn.setIcon(get_icon("folder.png", "#0ea5e9"))  # Keep folder icon blue
        
        # Update current state icons
        self._update_ui_state()

    def set_thumbnail(self, thumb_path: str):
        if thumb_path and os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            self.thumb_label.setPixmap(
                pix.scaled(
                    self.thumb_label.width(),
                    self.thumb_label.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )

    def _update_ui_state(self):
        # Hide all by default
        self.pause_btn.hide()
        self.resume_btn.hide()
        self.open_btn.hide()
        self.progress_bar.hide()
        
        if self.current_status == "processing":
            self.pause_btn.show()
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            # Show the descriptive stage directly from yt-dlp
            self.status_badge.setText(self.current_msg.upper())
            # Only move the progress bar during active downloads.
            self.progress_bar.setRange(0, 100)
            self.progress_bar.show()
        elif self.current_status == "paused":
            self.resume_btn.show()
            self.resume_btn.setIcon(get_icon("play.png", self._icon_color))
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            self.status_badge.setText("PAUSED")
            self.speed_label.setText("Paused")
            self.progress_bar.setValue(0)
        elif self.current_status == "pending":
            # Ready to start, but max_concurrent may still be saturated.
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            self.delete_btn.show()
            self.status_badge.setText("● QUEUED")
            colors = get_theme_colors()
            self.status_badge.setStyleSheet(
                f"font-size: 10px; font-weight: 900; color: {colors['accent']}; background-color: rgba(20, 184, 166, 0.1); padding: 4px 8px; border-radius: 4px;"
            )
            self.speed_label.setText("Queued...")
            self.speed_label.show()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        elif self.current_status == "queued":
            # Waiting behind capacity.
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            self.delete_btn.show()
            self.status_badge.setText("WAITING")
            self.status_badge.setStyleSheet(
                f"color: {QUEUE_WAITING_COLOR}; font-size: 10px; font-weight: 900;"
            )
            self.speed_label.setText("Waiting in queue...")
            self.speed_label.show()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        elif self.current_status == "completed":
            self.open_btn.show()
            self.delete_btn.setIcon(get_icon("trash.png", self._icon_color))
            self.progress_bar.hide()
            self.status_badge.setText("● COMPLETE")
            colors = get_theme_colors()
            self.status_badge.setStyleSheet(f"font-size: 10px; font-weight: 900; color: {colors['accent']}; background-color: rgba(20, 184, 166, 0.1); padding: 4px 8px; border-radius: 4px;")
            self.speed_label.hide()
        elif self.current_status == "skipped":
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            self.delete_btn.show()
            self.progress_bar.hide()
            self.status_badge.setText("SKIPPED")
            self.status_badge.setStyleSheet("color: #f59e0b; font-size: 10px; font-weight: 900;")
            self.speed_label.setText("Skipped (already exists)")
            self.speed_label.show()
        elif self.current_status == "failed":
            self.resume_btn.show()
            self.resume_btn.setIcon(get_icon("retry.png", self._icon_color))
            self.delete_btn.setIcon(get_icon("close.png", self._icon_color))
            self.status_badge.setText("FAILED")
            self.status_badge.setStyleSheet("color: #f43f5e;")

    def update_progress(self, p: float, speed: float, eta: float):
        self.current_status = "processing"
        self._update_ui_state()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(p))
        
        speed_kb = speed / 1024
        speed_str = f"{speed_kb:.1f} KB/s" if speed_kb < 1024 else f"{speed_kb/1024:.1f} MB/s"
        self.speed_label.setText(speed_str)
        
        # We don't have total size in this call easily without yt-dlp hook change, 
        # but we can show % in the size area
        self.size_label.setText(f"{int(p)}% Complete")

    def set_status(self, text: str):
        if "Paused" in text: self.current_status = "paused"
        elif "Starting" in text or "Downloading" in text or "Converting" in text or "Embedding" in text or "Processing" in text: 
            self.current_status = "processing"
            # Store cleaned status message for the badge
            self.current_msg = text.strip().rstrip('.')
        elif "Waiting" in text: self.current_status = "queued"
        elif "Skipped" in text: self.current_status = "skipped"
        elif "Queued" in text: self.current_status = "pending"
        self._update_ui_state()

    def set_finished(self, path: str):
        self.current_status = "completed"
        self.progress_bar.setValue(100)
        self._update_ui_state()
        size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
        size_mb = size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
        self.size_label.setText(size_str)

    def set_error(self, error: str):
        self.current_status = "failed"
        self.status_badge.setText("ERROR")
        self.speed_label.setText(error)
        self.speed_label.setStyleSheet("color: #f43f5e; font-size: 9px;")
        self._update_ui_state()

class VirtualPlaylistModel:
    """Virtual model for efficient playlist handling."""
    
    def __init__(self):
        self.items = []  # Store all playlist data
        self.visible_start = 0  # Start index of visible items
        self.visible_count = 50  # Number of items to show at once
        
    def load_playlist(self, entries):
        """Load playlist entries into virtual model."""
        self.items = entries
        # Explicitly initialize the selection state to True for all items
        # so the model's reality matches the UI's default checked state.
        for item in self.items:
            if 'selected' not in item:
                item['selected'] = True
        self.visible_start = 0
        
    def get_visible_items(self):
        """Get items currently visible in UI."""
        end = min(self.visible_start + self.visible_count, len(self.items))
        return self.items[self.visible_start:end]
        
    def scroll_to(self, start_index):
        """Update visible window for scrolling."""
        self.visible_start = max(0, min(start_index, len(self.items) - self.visible_count))
        
    def get_all_selected(self):
        """Get all selected items from entire playlist."""
        selected = []
        for item in self.items:
            if item.get('selected', False):
                selected.append(item)
        return selected
        
    def set_all_selected(self, selected):
        """Set selection state for all items."""
        for i, item in enumerate(self.items):
            item['selected'] = i in selected
            
    def search(self, query):
        """Search through all items."""
        if not query:
            return self.items
        query_lower = query.lower()
        return [item for item in self.items 
                if query_lower in item.get('title', '').lower()]

class VirtualPlaylistWidget(QFrame):
    """Efficient playlist widget using virtual model for large playlists."""
    
    selection_changed = Signal()  # Emitted when selection changes
    
    def __init__(self):
        super().__init__()
        self.model = VirtualPlaylistModel()
        self.widgets = {}  # Cache of created widgets
        self.setObjectName("PlaylistContainer")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the playlist UI layout."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scroll area for playlist items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for playlist items
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(4)
        self.container_layout.addStretch()
        
        self.scroll_area.setWidget(self.container)
        self.layout.addWidget(self.scroll_area)
        
    def load_playlist(self, entries):
        """Load playlist entries efficiently."""
        # Load data into model
        self.model.load_playlist(entries)
        
        # Clear existing widgets
        self._clear_widgets()
        
        # Create widgets for visible items only
        visible_items = self.model.get_visible_items()
        for item in visible_items:
            widget = self._create_widget(item)
            self.widgets[item.get('url')] = widget
            self.container_layout.insertWidget(self.container_layout.count() - 1, widget)  # Insert before stretch
        
    def _create_widget(self, item):
        """Create a playlist widget for an item."""
        widget = PlaylistItemWidget(
            item.get('index', 0),
            item.get('title', ''),
            item.get('duration', 0),
            item.get('url', ''),
            item.get('thumb_url', '')
        )
        
        # Set initial selection state
        widget.set_selected(item.get('selected', True))
        
        # Connect selection change to model update
        widget.selection_changed.connect(self._on_item_selection_changed)
        
        return widget
    
    def _on_item_selection_changed(self, index: int, is_selected: bool):
        """Update model when individual item selection changes."""
        # Update selection by index (handles duplicate URLs safely)
        if 0 <= index < len(self.model.items):
            self.model.items[index]['selected'] = is_selected
        self.selection_changed.emit()
        
    def _clear_widgets(self):
        """Clear all existing widgets."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.widgets.clear()
        
    def scroll_to_item(self, index):
        """Scroll to show specific item."""
        self.model.scroll_to(index)
        self._refresh_visible_widgets()
        
    def _refresh_visible_widgets(self):
        """Refresh widgets to match model's visible items."""
        visible_items = self.model.get_visible_items()
        
        # Remove widgets that are no longer visible
        urls_to_remove = []
        for url, widget in self.widgets.items():
            if not any(item.get('url') == url for item in visible_items):
                urls_to_remove.append(url)
                
        for url in urls_to_remove:
            if url in self.widgets:
                widget = self.widgets.pop(url)
                widget.setParent(None)
                widget.deleteLater()
                
        # Add widgets for newly visible items
        for item in visible_items:
            url = item.get('url')
            if url not in self.widgets:
                widget = self._create_widget(item)
                self.widgets[url] = widget
                self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
                
    def get_selected_items(self):
        """Get all selected items from model."""
        return self.model.get_all_selected()
        
    def set_all_selected(self, selected):
        """Set selection state for all items and update widgets."""
        if isinstance(selected, bool):
            # Handle boolean: select all or select none
            if selected:
                # Select all items
                all_indices = list(range(len(self.model.items)))
                self.model.set_all_selected(all_indices)
                for widget in self.widgets.values():
                    widget.set_selected(True)
            else:
                # Select none
                self.model.set_all_selected([])
                for widget in self.widgets.values():
                    widget.set_selected(False)
        else:
            # Handle list of indices
            self.model.set_all_selected(selected)
            for widget in self.widgets.values():
                widget.set_selected(widget.url in selected)
        
        self.selection_changed.emit()

class PlaylistItemWidget(QFrame):
    """Small item for playlist listing with selection."""
    selection_changed = Signal(int, bool)  # index, is_selected
    
    def __init__(self, index: int, title: str, duration: int, url: str, thumb_url: str = ""):
        super().__init__()
        self.index = index
        self.url = url
        self.title = title
        self.thumb_url = thumb_url
        self.setObjectName("ListItem")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.layout.addWidget(self.checkbox)
        
        self.index_label = QLabel(str(index))
        self.index_label.setFixedWidth(24)
        self.layout.addWidget(self.index_label)
        
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label, 1)
        
        # Format duration
        duration = duration or 0
        h, m = divmod(int(duration), 3600)
        m, s = divmod(m, 60)
        duration_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        self.duration_label = QLabel(duration_str)
        self.duration_label.setObjectName("ItemSubtitle")
        self.layout.addWidget(self.duration_label)

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    def set_selected(self, selected: bool):
        self.checkbox.setChecked(selected)

    def _on_checkbox_changed(self, state):
        """Emit signal when checkbox state changes."""
        self.selection_changed.emit(self.index, state == Qt.Checked)

    def get_data(self) -> dict:
        return {'url': self.url, 'title': self.title, 'thumb_url': self.thumb_url}
