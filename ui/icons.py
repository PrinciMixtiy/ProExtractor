import os
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
from core.utils import get_resource_path


def get_icon(name: str, color_hex: str = "#E2E8F0") -> QIcon:
    """
    Loads a PNG or SVG icon from assets/icons and colorizes it.
    For PNG icons: Since icons are black with a transparent background, this function
    replaces the black with the given color (suitable for dark mode).
    For SVG icons: Returns the SVG as-is (for colored logos).
    """
    icon_path = get_resource_path(os.path.join('assets', 'icons', name))

    if not os.path.exists(icon_path):
        return QIcon()

    # Handle SVG files differently (no colorization for colored logos)
    if name.lower().endswith('.svg'):
        return QIcon(icon_path)

    # Handle PNG files with colorization
    pixmap = QPixmap(icon_path)
    if pixmap.isNull():
        return QIcon()

    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.transparent)

    painter = QPainter(colored_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), QColor(color_hex))
    painter.end()

    return QIcon(colored_pixmap)
