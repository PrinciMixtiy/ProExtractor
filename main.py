import sys
import os
import subprocess
import logging
from pathlib import Path
from PySide6.QtGui import QIcon

# Add the project root to sys.path to allow absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from desktop.ui.main_window import MainWindow
from desktop.core.config import config
from desktop.core.constants import APP_NAME, ORG_NAME
from desktop.core.utils import get_resource_path


def check_dependencies():
    """Check for mandatory and optional native dependencies."""
    results = {
        'ffmpeg': False
    }
    
    ffmpeg_path = config.get('advanced.ffmpeg_path') or "ffmpeg"
    try:
        subprocess.run([ffmpeg_path, "-version"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        results['ffmpeg'] = True
    except FileNotFoundError:
        pass

    return results


def setup_logging():
    """Configure application-wide logging."""
    from desktop.core.constants import APP_NAME
    
    # Determine log directory (platform specific)
    if sys.platform == 'win32':
        log_dir = Path(os.environ.get('APPDATA', '.')) / APP_NAME / "logs"
    elif sys.platform == 'darwin':
        log_dir = Path.home() / "Library" / "Logs" / APP_NAME
    else:
        log_dir = Path.home() / ".config" / APP_NAME / "logs"
        
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"--- Application Starting ({APP_NAME}) ---")
    logging.info(f"Logs saved to: {log_file}")


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    
    # Set application icon
    icon_path = get_resource_path(os.path.join("assets", "icons", "logo.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        logging.warning(f"Application icon not found at: {icon_path}")
    
    # Check for native dependencies
    deps = check_dependencies()
    
    if not deps['ffmpeg']:
        logging.error("Mandatory dependency 'FFmpeg' not found. Shutting down.")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Missing Dependency")
        msg.setText("FFmpeg not found!")
        msg.setInformativeText(
            "FFmpeg is required for video merging and audio extraction.\n\n"
            "Please install it to use this application.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        sys.exit(1)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
