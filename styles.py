"""
Styles and theme management for the Pro Extractor desktop application.

This module provides theme color palettes and stylesheet generation
for light and dark modes, with automatic system theme detection.
"""

import darkdetect
from core.config import config
from core.constants import Theme


def get_theme_colors():
    """Return color palette based on system theme."""
    # Check for configured theme preference
    theme_preference = config.get('general.theme', Theme.AUTO.value)

    if theme_preference == Theme.DARK.value:
        is_dark = True
    elif theme_preference == Theme.LIGHT.value:
        is_dark = False
    else:  # auto
        is_dark = darkdetect.isDark()

    if is_dark:
        return {
            "bg_dark": "#0a0a0a",      # deep neutral-950
            "bg_main": "#0a0a0a",      # unified content area
            "bg_card": "#121212",      # slightly lighter for cards
            "text_primary": "#ffffff",
            "text_secondary": "#94a3b8",
            "accent": "#14b8a6",       # teal-500
            "accent_hover": "#0d9488",  # teal-600
            "border": "#1a1a1a",
            "outer_border": "#262626",  # subtle line
            "header_bg": "#0a0a0a",
            "sidebar_bg": "#0a0a0a",   # same as header for consistency
            "button_bg": "#14b8a6",
            "button_text": "#ffffff",
            "input_bg": "#171717",
        }
    else:
        return {
            "bg_dark": "#f8fafc",      # slate-50
            "bg_main": "#f8fafc",      # unified content area
            "bg_card": "#f1f5f9",      # slightly darker for cards
            "text_primary": "#0f172a",  # slate-950
            "text_secondary": "#64748b",  # slate-500
            "accent": "#0d9488",       # teal-600
            "accent_hover": "#0f766e",  # teal-700
            "border": "#f1f5f9",
            "outer_border": "#e2e8f0",  # slate-200
            "header_bg": "#f8fafc",    # same as main
            "sidebar_bg": "#f8fafc",   # same as header for consistency
            "button_bg": "#0d9488",
            "button_text": "#ffffff",
            "input_bg": "#ffffff",
        }


def get_stylesheet():
    """Generate QSS stylesheet based on current theme."""
    colors = get_theme_colors()

    return f"""
    QMainWindow {{
        background-color: {colors['bg_dark']};
    }}
    
    QWidget {{
        color: {colors['text_primary']};
        font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        font-size: 13px;
    }}
    
    /* Header */
    #Header {{
        background-color: {colors['header_bg']};
        border: none;
        border-bottom: 1px solid {colors['outer_border']};
    }}
    
    #AppTitle {{
        font-weight: 800;
        font-size: 16px;
        color: {colors['accent']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Inputs */
    QLineEdit {{
        background-color: {colors['input_bg']};
        border: 1px solid {colors['outer_border']};
        padding: 10px 16px;
        border-radius: 4px;
        color: {colors['text_primary']};
        font-size: 11px;
    }}
    
    QLineEdit:focus {{
        border: 1px solid {colors['outer_border']};
    }}
    
    QLineEdit#SearchInput {{
        background-color: {colors['input_bg']};
        border: 1px solid {colors['outer_border']};
        padding: 14px 24px;
        border-radius: 4px;   /* Pill shape */
        color: {colors['text_primary']};
        font-size: 12px;
        selection-background-color: {colors['accent']};
        font-weight: 500;
    }}
    
    QLineEdit#SearchInput:focus {{
        border: 1px solid {colors['outer_border']};
        background-color: {colors['bg_card']};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {colors['button_bg']};
        color: {colors['button_text']};
        border: none;
        padding: 10px 20px;
        font-weight: 700;
        border-radius: 4px;
        font-size: 10px;
    }}
    
    QPushButton:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['accent']};
    }}
    
    QPushButton#PrimaryButton {{
        background-color: {colors['accent']};
        color: {colors['button_text']};
        border-radius: 4px;
        padding: 12px 32px 12px 32px;
        font-weight: 800;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 1px;
        border: none;
    }}
    
    QPushButton#PrimaryButton:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    QPushButton#PrimaryButton:pressed {{
        background-color: {colors['accent']};
    }}
    
    QPushButton#SecondaryButton {{
        background-color: transparent;
        border: 1px solid {colors['outer_border']};
        color: {colors['text_primary']};
        padding: 6px 12px;
        font-size: 9px;
    }}
    
    QPushButton#SecondaryButton:hover {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        color: {colors['accent']};
    }}
    
    /* Scroll Bar */
    QScrollBar:vertical {{
        border: none;
        background: {colors['bg_dark']};
        width: 8px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {colors['bg_card']};
        min-height: 20px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {colors['accent']};
    }}
    
    /* Progress Bars */
    QProgressBar {{
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        text-align: center;
        background-color: {colors['bg_main']};
        height: 8px;
        font-size: 8px;
        font-weight: bold;
        color: {colors['text_primary']};
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: 4px;
    }}
    
    /* Progress bars in history cards */
    #HistoryCard QProgressBar {{
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        background-color: {colors['bg_main']};
        height: 6px;
    }}
    
    #HistoryCard QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: 4px;
    }}
    
    /* Radio Buttons */
    QRadioButton {{
        color: {colors['text_primary']};
        spacing: 8px;
        font-size: 13px;
    }}
    
    QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 2px solid {colors['outer_border']};
        background-color: {colors['bg_main']};
    }}
    
    QRadioButton::indicator:hover {{
        border: 2px solid {colors['accent']};
    }}
    
    QRadioButton::indicator:checked {{
        background-color: {colors['accent']};
        border: 2px solid {colors['accent']};
    }}
    
    QRadioButton::indicator:checked:hover {{
        background-color: {colors['accent_hover']};
        border: 2px solid {colors['accent_hover']};
    }}
    
    /* Combo Boxes */
    QComboBox {{
        background-color: {colors['input_bg']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 6px 12px;
        color: {colors['text_primary']};
        font-size: 11px;
        min-height: 20px;
    }}
    
    QComboBox:focus {{
        border: 1px solid {colors['outer_border']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid {colors['text_secondary']};
        margin-right: 4px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors['bg_main']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        selection-background-color: {colors['bg_card']};
        selection-color: {colors['text_primary']};
        color: {colors['text_primary']};
        outline: none;
        padding: 4px;
    }}
    
    QComboBox QAbstractItemView::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}
    
    QComboBox QAbstractItemView::item:selected {{
        background-color: {colors['accent']};
        color: {colors['button_text']};
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {colors['bg_card']};
    }}
    
    /* Checkboxes */
    QCheckBox {{
        color: {colors['text_primary']};
        spacing: 8px;
        font-size: 13px;
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {colors['outer_border']};
        border-radius: 4px;
        background-color: {colors['input_bg']};
    }}
    
    QCheckBox::indicator:hover {{
        border: 2px solid {colors['accent']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors['accent']};
        border: 2px solid {colors['accent']};
        image: none;
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: {colors['accent_hover']};
        border: 2px solid {colors['accent_hover']};
    }}
    
    /* Spin Boxes */
    QSpinBox {{
        background-color: {colors['input_bg']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 6px 12px;
        color: {colors['text_primary']};
        font-size: 11px;
        min-height: 20px;
    }}
    
    QSpinBox:focus {{
        border: 1px solid {colors['accent']};
    }}
    
    QSpinBox::up-button, QSpinBox::down-button {{
        border: none;
        width: 16px;
    }}
    
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {colors['bg_card']};
    }}
    
    QSpinBox::up-arrow {{
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-bottom: 3px solid {colors['text_secondary']};
        margin: 2px;
    }}
    
    QSpinBox::down-arrow {{
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 3px solid {colors['text_secondary']};
        margin: 2px;
    }}
    
    /* Group Boxes */
    QGroupBox {{
        color: {colors['text_primary']};
        font-weight: 600;
        font-size: 14px;
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 8px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px 0 8px;
        color: {colors['text_primary']};
    }}
    
    /* Message Box (Popups) */
    QMessageBox {{
        background-color: {colors['bg_main']};
        color: {colors['text_primary']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
    }}
    
    QMessageBox QLabel {{
        color: {colors['text_primary']};
        font-size: 14px;
    }}
    
    QMessageBox QPushButton {{
        background-color: {colors['button_bg']};
        color: {colors['button_text']};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
        min-width: 80px;
    }}
    
    QMessageBox QPushButton:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    QMessageBox QPushButton:pressed {{
        background-color: {colors['accent']};
    }}
    
    QMessageBox QMessageBoxIcon {{
        background-color: transparent;
        border: none;
    }}
    
    /* Main Window Content */
    QWidget {{
        background-color: {colors['bg_main']};
        color: {colors['text_primary']};
    }}
    
    /* Content Cards */
    #Card {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 16px;
    }}
    
    #PaginationCard {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 4px 12px;
    }}
    
    #Card QLabel {{
        background-color: transparent;
        border: none;
    }}
    
    #Card QCheckBox {{
        background-color: transparent;
        border: none;
    }}
    
    #InfoCard {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 16px;
    }}
    
    #InfoCard QLabel {{
        background-color: transparent;
        border: none;
    }}
    
    #ListItem {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        margin-bottom: 6px;
    }}
    
    #ListItem:hover {{
        border: 1px solid {colors['outer_border']};
        background-color: {colors['bg_main']};
    }}
    
    /* Task Items */
    #HistoryCard {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        margin-bottom: 4px;
    }}
    
    /* Task Item Labels */
    #ItemTitle {{
        color: {colors['text_primary']};
        font-size: 14px;
        font-weight: 700;
        background-color: transparent;
        border: none;
    }}
    
    #ItemSubtitle {{
        color: {colors['text_secondary']};
        font-size: 9px;
        background-color: transparent;
        border: none;
    }}
    
    /* All labels in history cards */
    #HistoryCard QLabel {{
        background-color: transparent;
        border: none;
    }}
    
    #HistoryCard QLabel#ItemTitle {{
        color: {colors['text_primary']};
        font-size: 14px;
        font-weight: 700;
        background-color: transparent;
        border: none;
    }}
    
    #HistoryCard QLabel#ItemSubtitle {{
        color: {colors['text_secondary']};
        font-size: 9px;
        background-color: transparent;
        border: none;
    }}
    
    /* Task Item Buttons */
    #HistoryCard QPushButton {{
        background-color: {colors['bg_main']};
        border: 1px solid {colors['outer_border']};
        color: {colors['text_primary']};
        border-radius: 4px;
        font-size: 14px;
    }}
    
    #HistoryCard QPushButton:hover {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
    }}
    
    #HistoryCard QPushButton#open_btn {{
        background-color: {colors['accent']};
        color: {colors['button_text']};
        border: none;
    }}
    
    #HistoryCard QPushButton#open_btn:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    /* Icon colors for action buttons */
    #HistoryCard QPushButton:hover {{
        border: 1px solid {colors['outer_border']};
    }}
    
    /* Ensure icons are visible */
    #HistoryCard QPushButton {{
        padding: 4px;
    }}
    
    #HistoryCard QPushButton#pause_btn, 
    #HistoryCard QPushButton#resume_btn, 
    #HistoryCard QPushButton#delete_btn {{
        background-color: {colors['bg_main']};
        border: 1px solid {colors['outer_border']};
    }}
    
    #HistoryCard QPushButton#pause_btn:hover, 
    #HistoryCard QPushButton#resume_btn:hover, 
    #HistoryCard QPushButton#delete_btn:hover {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
    }}
    
    /* Status Badge */
    #HistoryCard QLabel[style*="status_badge"] {{
        color: {colors['accent']};
        background-color: transparent;
        font-size: 8px;
        font-weight: 900;
        letter-spacing: 1px;
        border: none;
    }}
    
    /* Size and Speed Labels */
    #HistoryCard QLabel {{
        background-color: transparent;
        border: none;
    }}
    
    /* Force transparent backgrounds for all text in history */
    #HistoryCard * {{
        background-color: transparent;
    }}
    
    /* Additional override for any stubborn text elements */
    #HistoryCard QLabel, #HistoryCard QLabel#ItemTitle, #HistoryCard QLabel#ItemSubtitle {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }}
    
    /* Scroll Areas */
    QScrollArea {{
        background-color: {colors['bg_main']};
        border: none;
    }}
    
    QScrollArea > QWidget > QWidget {{
        background-color: {colors['bg_main']};
    }}
    
    /* Labels and Headers */
    QLabel#OptionHeader {{
        font-weight: 800;
        font-size: 9px;
        color: {colors['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
    }}
    
    QLabel#InfoKey {{
        color: {colors['text_secondary']};
        font-size: 9px;
        font-weight: 600;
        text-transform: uppercase;
    }}

    QLabel#InfoValue {{
        color: {colors['text_primary']};
        font-size: 10px;
        font-weight: 700;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
    }}

    QLabel#InfoValueAccent {{
        color: {colors['accent']};
        font-size: 13px;
        font-weight: 700;
    }}
    
    /* Modern Input System (Redesigned Profile) */
    #ModernInput {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 500;
        color: {colors['text_primary']};
    }}
    
    #ModernInput:focus {{
        border: 1px solid {colors['outer_border']};
    }}

    /* Modern Selectors (ComboBox specific) */
    QComboBox#ModernInput {{
        padding-right: 30px;
    }}

    QComboBox#ModernInput::down-arrow {{
        border-top: 5px solid {colors['text_secondary']};
        margin-right: 12px;
    }}

    /* Settings specific */
    QLabel#settingsTitle {{
        color: {colors['text_primary']};
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 16px;
    }}
    
    /* Sidebar */
    #Sidebar {{
        background-color: {colors['sidebar_bg']};
        border: none;
        border-right: 1px solid {colors['outer_border']};
    }}
    
    #Sidebar QWidget {{
        background-color: transparent;
    }}
    
    QPushButton#SidebarButton {{
        background-color: transparent;
        color: {colors['text_secondary']};
        border-radius: 0px;
        text-align: left;
        padding-left: 12px;
        font-weight: 700;
        font-size: 12px;
        border: none;
        margin: 2px 4px;
    }}
    
    QPushButton#SidebarButton:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {colors['text_primary']};
    }}
    
    QPushButton#SidebarButton:checked {{
        background-color: rgba(20, 184, 166, 0.15);
        color: {colors['accent']};
        border-left: 4px solid {colors['accent']};
        padding-left: 8px;
    }}
    
    #ListItem {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['outer_border']};
        border-radius: 4px;
        margin-bottom: 6px;
    }}
    
    #ListItem:hover {{
        border: 1px solid {colors['outer_border']};
        background-color: {colors['bg_main']};
    }}
    """
