"""
Sidebar navigation component for the Pro Extractor desktop application.

This module provides the collapsible sidebar widget with navigation buttons,
animated transitions, and version display for the application interface.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize

from core.constants import APP_VERSION
from ui.icons import get_icon
from styles import get_theme_colors

class SidebarButton(QPushButton):
    """Specific styling for navigation sidebar buttons."""
    def __init__(self, icon_name: str, label_text: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.label_text = label_text
        self.is_collapsed = False
        
        self.setObjectName("SidebarButton")
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        # We'll dynamically update the icon color on hover and toggle
        self.toggled.connect(self._update_icon)
        self._update_icon()
        
        self._update_text()

    def _update_icon(self):
        colors = get_theme_colors()
        color = colors['accent'] if self.isChecked() else colors['text_secondary']
        self.setIcon(get_icon(self.icon_name, color))
        self.setIconSize(QSize(18, 18))

    def enterEvent(self, event):
        colors = get_theme_colors()
        if not self.isChecked():
            # In light mode, use black for hover; in dark mode, use white
            hover_color = colors['text_primary'] if colors['text_primary'] == '#0f172a' else '#ffffff'
            self.setIcon(get_icon(self.icon_name, hover_color))
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        colors = get_theme_colors()
        if not self.isChecked():
            self.setIcon(get_icon(self.icon_name, colors['text_secondary']))
        super().leaveEvent(event)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        self._update_text()

    def _update_text(self):
        if self.is_collapsed:
            self.setText("")
            self.setToolTip(self.label_text)
        else:
            self.setText("  " + self.label_text)
            self.setToolTip("")

class Sidebar(QFrame):
    """Collapsible navigation sidebar for multi-page switching."""
    page_changed = Signal(str) # Emits page name: "home", "downloads", "settings"

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.is_collapsed = True
        self.expanded_width = 160
        self.collapsed_width = 65
        
        self.setFixedWidth(self.collapsed_width)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 20)
        self.layout.setSpacing(0)
        
        # --- Top Section: Brand & Toggle ---
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(16, 20, 16, 20)
        
        self.brand_label = QLabel("PRO <span style='color:#14b8a6'>EXTRACTOR</span>")
        self.brand_label.setStyleSheet("font-weight: 900; font-size: 13px; letter-spacing: 1px; border: none;")
        self.brand_label.setTextFormat(Qt.RichText)
        header_layout.addWidget(self.brand_label)
        
        self.toggle_btn = QPushButton() # Hamburger
        colors = get_theme_colors()
        self.toggle_btn.setIcon(get_icon("menu.png", colors['text_secondary']))  # Theme-aware icon
        self.toggle_btn.setIconSize(QSize(19, 19))
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        # Theme-aware hover background
        hover_bg = colors['bg_card'] if colors['text_primary'] == '#0f172a' else '#262626'
        self.toggle_btn.setStyleSheet(f"QPushButton {{ border: none; background-color: transparent; border-radius: 20px; }} QPushButton:hover {{ background-color: {hover_bg}; }}")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.toggle_btn)
        
        self.layout.addWidget(header_container)
        
        # --- Navigation Buttons ---
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(8, 0, 8, 0)
        self.nav_layout.setSpacing(4)
        
        self.btn_home = SidebarButton("home.png", "HOME")
        self.btn_home.setChecked(True)
        self.btn_home.clicked.connect(lambda: self._on_nav_clicked("home"))
        
        self.btn_settings = SidebarButton("settings.png", "SETTINGS")
        self.btn_settings.clicked.connect(lambda: self._on_nav_clicked("settings"))
        
        self.btn_help = SidebarButton("user-question.png", "HELP")
        self.btn_help.clicked.connect(lambda: self._on_nav_clicked("help"))
        
        self.btn_legal = SidebarButton("info.png", "LEGAL")
        self.btn_legal.clicked.connect(lambda: self._on_nav_clicked("legal"))
        
        # Group for exclusive selection
        self.buttons = [self.btn_home, self.btn_settings, self.btn_help, self.btn_legal]
        for btn in self.buttons:
            btn.set_collapsed(True)
            self.nav_layout.addWidget(btn)
            
        self.layout.addWidget(self.nav_container)
        self.layout.addStretch()
        
        # --- Footer Section ---
        self.version_label = QLabel(f"v{APP_VERSION} PRECISION")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; background-color: transparent; border: none;")
        self.layout.addWidget(self.version_label)

        # Set initial visibility for collapsed state
        self.brand_label.setVisible(False)
        self.version_label.setVisible(False)

    def toggle_sidebar(self):
        self.is_collapsed = not self.is_collapsed
        
        # Target width
        target_width = self.collapsed_width if self.is_collapsed else self.expanded_width
        
        # Create animations
        self.animation1 = QPropertyAnimation(self, b"minimumWidth")
        self.animation1.setDuration(200)
        self.animation1.setStartValue(self.width())
        self.animation1.setEndValue(target_width)
        self.animation1.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.animation2 = QPropertyAnimation(self, b"maximumWidth")
        self.animation2.setDuration(200)
        self.animation2.setStartValue(self.width())
        self.animation2.setEndValue(target_width)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.animation1.start()
        self.animation2.start()
        
        # Update buttons
        for btn in self.buttons:
            btn.set_collapsed(self.is_collapsed)
            
        # Update brand label visibility
        self.brand_label.setVisible(not self.is_collapsed)
        self.version_label.setVisible(not self.is_collapsed)

    def _on_nav_clicked(self, page_name: str):
        # Exclusive selection logic (except for help which opens a dialog)
        if page_name != "help":
            for btn in self.buttons:
                btn.setChecked(False)
                
        if page_name == "home": self.btn_home.setChecked(True)
        elif page_name == "settings": self.btn_settings.setChecked(True)
        # Help button doesn't stay checked - it opens a dialog
        
        self.page_changed.emit(page_name)
