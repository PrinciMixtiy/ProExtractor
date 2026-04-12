"""
Settings UI components for Video Downloader Desktop.

This module provides the settings interface with General and Downloads sections,
allowing users to configure application behavior.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QFileDialog,
    QGroupBox, QFormLayout, QStackedWidget, QButtonGroup,
    QRadioButton, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from core.config import config
from core.constants import (
    CONTENT_MARGIN, CARD_SPACING, BUTTON_HEIGHT,
    INPUT_HEIGHT, FILENAME_TAGS
)


class SettingsPage(QWidget):
    """Main settings page with tabbed sections."""
    
    settings_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_settings()
        self._connect_signals()
        
        # Apply button should always be active
        self.apply_btn.setEnabled(True)
    
    def _setup_ui(self):
        """Setup the settings page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_MARGIN, CONTENT_MARGIN, CONTENT_MARGIN, CONTENT_MARGIN)
        layout.setSpacing(CARD_SPACING)
        
        # Title
        title = QLabel("Settings")
        title.setObjectName("settingsTitle")
        layout.addWidget(title)
        
        # Tab buttons
        tab_buttons_layout = QHBoxLayout()
        self.tab_buttons = QButtonGroup()
        
        self.general_btn = QPushButton("General")
        self.general_btn.setCheckable(True)
        self.general_btn.setChecked(True)
        self.tab_buttons.addButton(self.general_btn, 0)
        tab_buttons_layout.addWidget(self.general_btn)
        
        self.downloads_btn = QPushButton("Downloads")
        self.downloads_btn.setCheckable(True)
        self.tab_buttons.addButton(self.downloads_btn, 1)
        tab_buttons_layout.addWidget(self.downloads_btn)
        
        self.auth_btn = QPushButton("Authentication")
        self.auth_btn.setCheckable(True)
        self.tab_buttons.addButton(self.auth_btn, 2)
        tab_buttons_layout.addWidget(self.auth_btn)
        
        self.advanced_btn = QPushButton("Advanced")
        self.advanced_btn.setCheckable(True)
        self.tab_buttons.addButton(self.advanced_btn, 3)
        tab_buttons_layout.addWidget(self.advanced_btn)
        
        tab_buttons_layout.addStretch()
        layout.addLayout(tab_buttons_layout)
        
        # Stacked widget for content
        self.stacked_widget = QStackedWidget()
        
        # Create settings sections
        self.general_section = GeneralSettings()
        self.downloads_section = DownloadsSettings()
        self.auth_section = AuthenticationSettings()
        self.advanced_section = AdvancedSettings()
        
        self.stacked_widget.addWidget(self.general_section)
        self.stacked_widget.addWidget(self.downloads_section)
        self.stacked_widget.addWidget(self.auth_section)
        self.stacked_widget.addWidget(self.advanced_section)
        
        layout.addWidget(self.stacked_widget)
        
        # Apply button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.tab_buttons.buttonClicked.connect(self._on_tab_changed)
        
        # Connect settings changes
        self.general_section.setting_changed.connect(self._on_setting_changed)
        self.downloads_section.setting_changed.connect(self._on_setting_changed)
        self.auth_section.setting_changed.connect(self._on_setting_changed)
        self.advanced_section.setting_changed.connect(self._on_setting_changed)
    
    def _on_tab_changed(self, button):
        """Handle tab button clicks."""
        index = self.tab_buttons.id(button)
        self.stacked_widget.setCurrentIndex(index)
    
    def _on_setting_changed(self):
        """Handle setting changes."""
        self.apply_btn.setEnabled(True)
    
    def _load_settings(self):
        """Load settings from configuration."""
        self.general_section.load_settings()
        self.downloads_section.load_settings()
        self.auth_section.load_settings()
        self.advanced_section.load_settings()
        # Apply button remains enabled
    
    def _apply_settings(self):
        """Apply all settings."""
        self.general_section.save_settings()
        self.downloads_section.save_settings()
        self.auth_section.save_settings()
        self.advanced_section.save_settings()
        
        config.save()
        self.settings_changed.emit()
        # Apply button remains enabled for user convenience
        
        QMessageBox.information(self, "Settings", "Settings applied successfully!")
    
    def _reset_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            config.reset()
            self._load_settings()


class GeneralSettings(QWidget):
    """General settings section."""
    
    setting_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup general settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(CARD_SPACING)
        
        # Download Folder
        folder_group = QGroupBox("Default Download Folder")
        folder_layout = QVBoxLayout(folder_group)
        
        folder_path_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setFixedHeight(INPUT_HEIGHT)
        folder_path_layout.addWidget(self.folder_path)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedHeight(BUTTON_HEIGHT)
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse_folder)
        folder_path_layout.addWidget(self.browse_btn)
        
        folder_layout.addLayout(folder_path_layout)
        layout.addWidget(folder_group)
        
        # Filename Pattern
        pattern_group = QGroupBox("Default Filename Pattern")
        pattern_layout = QVBoxLayout(pattern_group)
        
        self.filename_pattern = QLineEdit()
        self.filename_pattern.setFixedHeight(INPUT_HEIGHT)
        pattern_layout.addWidget(self.filename_pattern)
        
        # Pattern tags
        tags_label = QLabel("Available tags:")
        tags_label.setObjectName("tagsLabel")
        pattern_layout.addWidget(tags_label)
        
        tags_layout = QVBoxLayout()
        for tag, description in FILENAME_TAGS.items():
            tag_label = QLabel(f"{{{tag}}} - {description}")
            tag_label.setObjectName("tagLabel")
            tags_layout.addWidget(tag_label)
        
        pattern_layout.addLayout(tags_layout)
        layout.addWidget(pattern_group)
        
        # Theme
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)
        
        theme_buttons_layout = QHBoxLayout()
        self.theme_buttons = QButtonGroup()
        
        self.theme_auto = QRadioButton("Auto")
        self.theme_auto.setChecked(True)
        self.theme_buttons.addButton(self.theme_auto, 0)
        theme_buttons_layout.addWidget(self.theme_auto)
        
        self.theme_light = QRadioButton("Light")
        self.theme_buttons.addButton(self.theme_light, 1)
        theme_buttons_layout.addWidget(self.theme_light)
        
        self.theme_dark = QRadioButton("Dark")
        self.theme_buttons.addButton(self.theme_dark, 2)
        theme_buttons_layout.addWidget(self.theme_dark)
        
        theme_layout.addLayout(theme_buttons_layout)
        layout.addWidget(theme_group)
        
        # Language
        language_group = QGroupBox("Language")
        language_layout = QFormLayout(language_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Chinese"])
        self.language_combo.setFixedHeight(INPUT_HEIGHT)
        language_layout.addRow("Interface Language:", self.language_combo)
        
        layout.addWidget(language_group)
        
        layout.addStretch()
    
    def _browse_folder(self):
        """Browse for download folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", 
            self.folder_path.text() or str(Path.home())
        )
        if folder:
            self.folder_path.setText(folder)
            self.setting_changed.emit()
    
    def load_settings(self):
        """Load general settings."""
        self.folder_path.setText(config.get('general.default_download_folder', ''))
        self.filename_pattern.setText(config.get('general.default_filename_pattern', ''))
        
        theme = config.get('general.theme', 'auto')
        if theme == 'light':
            self.theme_light.setChecked(True)
        elif theme == 'dark':
            self.theme_dark.setChecked(True)
        else:
            self.theme_auto.setChecked(True)
        
        language = config.get('general.language', 'en')
        language_map = {'en': 0, 'es': 1, 'fr': 2, 'de': 3, 'zh': 4}
        self.language_combo.setCurrentIndex(language_map.get(language, 0))
    
    def save_settings(self):
        """Save general settings."""
        config.set('general.default_download_folder', self.folder_path.text())
        config.set('general.default_filename_pattern', self.filename_pattern.text())
        
        theme_map = {0: 'auto', 1: 'light', 2: 'dark'}
        theme_index = self.theme_buttons.checkedId()
        config.set('general.theme', theme_map.get(theme_index, 'auto'))
        
        language_map = {0: 'en', 1: 'es', 2: 'fr', 3: 'de', 4: 'zh'}
        config.set('general.language', language_map.get(self.language_combo.currentIndex(), 'en'))


class DownloadsSettings(QWidget):
    """Downloads settings section."""
    
    setting_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup downloads settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(CARD_SPACING)
        
        # Concurrent Downloads
        concurrent_group = QGroupBox("Download Limits")
        concurrent_layout = QFormLayout(concurrent_group)
        
        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 10)
        self.max_concurrent.setValue(3)
        self.max_concurrent.setFixedHeight(INPUT_HEIGHT)
        concurrent_layout.addRow("Max Concurrent Downloads:", self.max_concurrent)
        
        self.retries = QComboBox()
        self.retries.addItems(["1 Attempt", "3 Attempts", "5 Attempts", "10 Attempts", "Unlimited"])
        self.retries.setCurrentIndex(2)
        self.retries.setFixedHeight(INPUT_HEIGHT)
        concurrent_layout.addRow("Retries on Failure:", self.retries)
        
        layout.addWidget(concurrent_group)
        
        # Download Options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_resume = QCheckBox("Auto-resume downloads")
        self.auto_resume.setChecked(True)
        options_layout.addWidget(self.auto_resume)
        
        self.embed_thumbnails = QCheckBox("Embed thumbnails in video files")
        options_layout.addWidget(self.embed_thumbnails)
        
        self.auto_subtitles = QCheckBox("Auto-generate subtitles")
        options_layout.addWidget(self.auto_subtitles)
        
        # Subtitle Language
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(QLabel("Default Subtitle Language:"))
        
        self.subtitle_language = QComboBox()
        self.subtitle_language.addItems(["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"])
        self.subtitle_language.setCurrentText("en")
        self.subtitle_language.setFixedHeight(INPUT_HEIGHT)
        subtitle_layout.addWidget(self.subtitle_language)
        subtitle_layout.addStretch()
        
        options_layout.addLayout(subtitle_layout)
        layout.addWidget(options_group)
        
        # Quality and Format
        quality_group = QGroupBox("Default Quality and Format")
        quality_layout = QFormLayout(quality_group)
        
        self.default_quality = QComboBox()
        quality_options = ["Highest", "1080p", "720p", "480p", "360p", "Lowest"]
        self.default_quality.addItems(quality_options)
        self.default_quality.setCurrentIndex(0)
        self.default_quality.setFixedHeight(INPUT_HEIGHT)
        quality_layout.addRow("Default Quality:", self.default_quality)
        
        self.default_format = QComboBox()
        format_options = ["MP4", "WebM", "MKV", "Audio Only (MP3)", "Audio Only (M4A)"]
        self.default_format.addItems(format_options)
        self.default_format.setCurrentIndex(0)
        self.default_format.setFixedHeight(INPUT_HEIGHT)
        quality_layout.addRow("Default Format:", self.default_format)
        
        layout.addWidget(quality_group)
        
        # Performance
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.timeout = QSpinBox()
        self.timeout.setRange(10, 300)
        self.timeout.setValue(30)
        self.timeout.setSuffix(" seconds")
        self.timeout.setFixedHeight(INPUT_HEIGHT)
        performance_layout.addRow("Request Timeout:", self.timeout)
        
        layout.addWidget(performance_group)
        
        layout.addStretch()
    
    def load_settings(self):
        """Load download settings."""
        self.max_concurrent.setValue(config.get('downloads.max_concurrent', 3))
        
        retries = config.get('downloads.retries_on_failure', 5)
        retries_map = {1: 0, 3: 1, 5: 2, 10: 3, 999: 4}
        self.retries.setCurrentIndex(retries_map.get(retries, 2))
        
        self.auto_resume.setChecked(config.get('downloads.auto_resume', True))
        self.embed_thumbnails.setChecked(config.get('downloads.embed_thumbnails', False))
        self.auto_subtitles.setChecked(config.get('downloads.auto_generate_subtitles', False))
        self.subtitle_language.setCurrentText(config.get('downloads.subtitle_language', 'en'))
        
        quality = config.get('downloads.default_quality', 'highest')
        quality_map = {'highest': 0, '1080p': 1, '720p': 2, '480p': 3, '360p': 4, 'lowest': 5}
        self.default_quality.setCurrentIndex(quality_map.get(quality, 0))
        
        format_val = config.get('downloads.default_format', 'mp4')
        format_map = {'mp4': 0, 'webm': 1, 'mkv': 2, 'mp3': 3, 'm4a': 4}
        self.default_format.setCurrentIndex(format_map.get(format_val, 0))
        
        self.timeout.setValue(config.get('downloads.timeout', 30))
        # Removed: chunk_size setting
    
    def save_settings(self):
        """Save download settings."""
        config.set('downloads.max_concurrent', self.max_concurrent.value())
        
        retries_map = {0: 1, 1: 3, 2: 5, 3: 10, 4: 999}
        retries = retries_map.get(self.retries.currentIndex(), 5)
        config.set('downloads.retries_on_failure', retries)
        
        config.set('downloads.auto_resume', self.auto_resume.isChecked())
        config.set('downloads.embed_thumbnails', self.embed_thumbnails.isChecked())
        config.set('downloads.auto_generate_subtitles', self.auto_subtitles.isChecked())
        config.set('downloads.subtitle_language', self.subtitle_language.currentText())
        
        quality_map = {0: 'highest', 1: '1080p', 2: '720p', 3: '480p', 4: '360p', 5: 'lowest'}
        quality = quality_map.get(self.default_quality.currentIndex(), 'highest')
        config.set('downloads.default_quality', quality)
        
        format_map = {0: 'mp4', 1: 'webm', 2: 'mkv', 3: 'mp3', 4: 'm4a'}
        format_val = format_map.get(self.default_format.currentIndex(), 'mp4')
        config.set('downloads.default_format', format_val)
        
        config.set('downloads.timeout', self.timeout.value())
        # Removed: chunk_size setting


class AdvancedSettings(QWidget):
    """Advanced settings section."""
    
    setting_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(CARD_SPACING)
        
        # FFmpeg Path
        ffmpeg_group = QGroupBox("FFmpeg Configuration")
        ffmpeg_layout = QFormLayout(ffmpeg_group)
        
        ffmpeg_path_layout = QHBoxLayout()
        self.ffmpeg_path = QLineEdit()
        self.ffmpeg_path.setFixedHeight(INPUT_HEIGHT)
        self.ffmpeg_path.setPlaceholderText("Auto-detect (recommended)")
        ffmpeg_path_layout.addWidget(self.ffmpeg_path)
        
        self.ffmpeg_browse = QPushButton("Browse")
        self.ffmpeg_browse.setFixedHeight(BUTTON_HEIGHT)
        self.ffmpeg_browse.setFixedWidth(80)
        self.ffmpeg_browse.clicked.connect(self._browse_ffmpeg)
        ffmpeg_path_layout.addWidget(self.ffmpeg_browse)
        
        ffmpeg_layout.addRow("FFmpeg Path:", ffmpeg_path_layout)
        layout.addWidget(ffmpeg_group)
        
        # Storage
        storage_group = QGroupBox("Storage Paths")
        storage_layout = QFormLayout(storage_group)
        
        self.data_dir = QLineEdit()
        self.data_dir.setFixedHeight(INPUT_HEIGHT)
        self.data_dir.setPlaceholderText("Default data directory")
        storage_layout.addRow("Data Directory:", self.data_dir)
        
        layout.addWidget(storage_group)
        
        layout.addStretch()
    
    def _browse_ffmpeg(self):
        """Browse for FFmpeg executable."""
        if os.name == 'nt':  # Windows
            file_filter = "Executable Files (*.exe)"
        else:
            file_filter = "All Files (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select FFmpeg Executable", "", file_filter
        )
        if file_path:
            self.ffmpeg_path.setText(file_path)
            self.setting_changed.emit()
    
    def load_settings(self):
        """Load advanced settings."""
        self.ffmpeg_path.setText(config.get('advanced.ffmpeg_path', ''))
        
        # Removed: proxy, user_agent, debug_mode, log_level settings
        
        self.data_dir.setText(config.get('paths.data_dir', ''))
    
    def save_settings(self):
        """Save advanced settings."""
        config.set('advanced.ffmpeg_path', self.ffmpeg_path.text())
        
        # Removed: proxy, user_agent, debug_mode, log_level settings
        
        config.set('paths.data_dir', self.data_dir.text())


class AuthenticationSettings(QWidget):
    """Authentication settings section for browser cookies."""
    
    setting_changed = Signal()
    
    # Default domains with their display names
    DEFAULT_DOMAINS = {
        "youtube.com": "YouTube",
        "tiktok.com": "TikTok",
        "instagram.com": "Instagram",
        "facebook.com": "Facebook",
        "twitter.com": "Twitter / X",
        "x.com": "X (Twitter)",
        "twitch.tv": "Twitch",
        "reddit.com": "Reddit"
    }
    
    def __init__(self):
        super().__init__()
        self.domain_checkboxes = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup authentication settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(CARD_SPACING)
        
        # Browser Source Section
        browser_group = QGroupBox("Browser Cookie Source")
        browser_layout = QVBoxLayout(browser_group)
        
        browser_label = QLabel("Select which browser to extract cookies from:")
        browser_layout.addWidget(browser_label)
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge", "Safari", "Disabled"])
        self.browser_combo.setFixedHeight(INPUT_HEIGHT)
        self.browser_combo.currentIndexChanged.connect(self._on_browser_changed)
        browser_layout.addWidget(self.browser_combo)
        
        info_label = QLabel("Cookies help download age-restricted or private content. "
                           "Select 'Disabled' to never use browser cookies.")
        info_label.setWordWrap(True)
        info_label.setObjectName("infoLabel")
        browser_layout.addWidget(info_label)
        
        layout.addWidget(browser_group)
        
        # Default for Unspecified Domains
        defaults_group = QGroupBox("Unspecified Domains")
        defaults_layout = QVBoxLayout(defaults_group)
        
        self.default_cookies_checkbox = QCheckBox("Use cookies for domains not in the list below")
        self.default_cookies_checkbox.setChecked(True)
        self.default_cookies_checkbox.setToolTip("When enabled, browser cookies will be used for any site not explicitly configured above.")
        self.default_cookies_checkbox.stateChanged.connect(self._on_setting_changed)
        defaults_layout.addWidget(self.default_cookies_checkbox)
        
        layout.addWidget(defaults_group)
        
        # Domain Toggles Section
        domains_group = QGroupBox("Per-Site Cookie Usage")
        domains_layout = QVBoxLayout(domains_group)
        
        domains_label = QLabel("Enable/disable cookies for specific sites:")
        domains_layout.addWidget(domains_label)
        
        # Create scroll area for many domains
        from PySide6.QtWidgets import QScrollArea, QWidget as QScrollWidget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QScrollWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        # Create checkbox for each default domain
        for domain, display_name in self.DEFAULT_DOMAINS.items():
            checkbox = QCheckBox(f"{display_name} ({domain})")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_setting_changed)
            self.domain_checkboxes[domain] = checkbox
            scroll_layout.addWidget(checkbox)
        
        # Custom domains container
        self.custom_domains_layout = QVBoxLayout()
        self.custom_domains_layout.setSpacing(8)
        scroll_layout.addLayout(self.custom_domains_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        domains_layout.addWidget(scroll)
        
        # Add custom domain button
        add_layout = QHBoxLayout()
        self.custom_domain_input = QLineEdit()
        self.custom_domain_input.setPlaceholderText("example.com")
        self.custom_domain_input.setFixedHeight(INPUT_HEIGHT)
        add_layout.addWidget(self.custom_domain_input)
        
        add_btn = QPushButton("Add Domain")
        add_btn.setFixedHeight(BUTTON_HEIGHT)
        add_btn.clicked.connect(self._add_custom_domain)
        add_layout.addWidget(add_btn)
        
        domains_layout.addLayout(add_layout)
        layout.addWidget(domains_group)
        
        layout.addStretch()
    
    def _on_browser_changed(self, index):
        """Handle browser selection change."""
        # Enable/disable checkboxes based on browser selection
        is_disabled = (index == 4)  # "Disabled" is index 4
        self.default_cookies_checkbox.setEnabled(not is_disabled)
        for checkbox in self.domain_checkboxes.values():
            checkbox.setEnabled(not is_disabled)
        # Also disable custom domain checkboxes
        for i in range(self.custom_domains_layout.count()):
            widget = self.custom_domains_layout.itemAt(i).widget()
            if widget and isinstance(widget, QCheckBox):
                widget.setEnabled(not is_disabled)
        self._on_setting_changed()
    
    def _add_custom_domain(self):
        """Add a custom domain to the list."""
        domain = self.custom_domain_input.text().strip().lower()
        if not domain:
            return
        
        # Validate domain format (basic check)
        if '.' not in domain or domain.startswith('.') or domain.endswith('.'):
            QMessageBox.warning(self, "Invalid Domain", "Please enter a valid domain (e.g., example.com)")
            return
        
        # Check if already exists
        if domain in self.domain_checkboxes:
            QMessageBox.information(self, "Domain Exists", f"{domain} is already in the list.")
            return
        
        # Add checkbox for custom domain
        checkbox = QCheckBox(f"{domain} (custom)")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self._on_setting_changed)
        
        # Check if browser is disabled
        is_disabled = (self.browser_combo.currentIndex() == 4)
        checkbox.setEnabled(not is_disabled)
        
        self.domain_checkboxes[domain] = checkbox
        self.custom_domains_layout.addWidget(checkbox)
        self.custom_domain_input.clear()
        self._on_setting_changed()
    
    def _on_setting_changed(self):
        """Emit signal when any setting changes."""
        self.setting_changed.emit()
    
    def load_settings(self):
        """Load authentication settings."""
        browser_source = config.get('auth.browser_source', 'chrome')
        browser_map = {
            'chrome': 0,
            'firefox': 1,
            'edge': 2,
            'safari': 3,
            'none': 4,
            '': 4
        }
        self.browser_combo.setCurrentIndex(browser_map.get(browser_source.lower(), 0))
        
        # Load default cookies setting
        self.default_cookies_checkbox.setChecked(config.get('auth.default_cookies', True))
        
        # Load domain overrides
        domain_overrides = config.get('auth.domain_overrides', {})
        
        # Update default domain checkboxes
        for domain, checkbox in self.domain_checkboxes.items():
            if domain in domain_overrides:
                checkbox.setChecked(domain_overrides[domain])
        
        # Load any custom domains that aren't in defaults
        default_keys = set(self.DEFAULT_DOMAINS.keys())
        for domain, enabled in domain_overrides.items():
            if domain not in default_keys and domain not in self.domain_checkboxes:
                # Add custom domain checkbox
                checkbox = QCheckBox(f"{domain} (custom)")
                checkbox.setChecked(enabled)
                checkbox.stateChanged.connect(self._on_setting_changed)
                self.domain_checkboxes[domain] = checkbox
                self.custom_domains_layout.addWidget(checkbox)
        
        # Trigger browser changed to set enabled state
        self._on_browser_changed(self.browser_combo.currentIndex())
    
    def save_settings(self):
        """Save authentication settings."""
        # Save browser source
        browser_map = {0: 'chrome', 1: 'firefox', 2: 'edge', 3: 'safari', 4: None}
        browser_source = browser_map.get(self.browser_combo.currentIndex(), 'chrome')
        config.set('auth.browser_source', browser_source)
        
        # Save default cookies setting
        config.set('auth.default_cookies', self.default_cookies_checkbox.isChecked())
        
        # Save domain overrides
        domain_overrides = {}
        for domain, checkbox in self.domain_checkboxes.items():
            domain_overrides[domain] = checkbox.isChecked()
        
        config.set('auth.domain_overrides', domain_overrides)
