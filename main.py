"""
Main entry point for the Pro Extractor desktop application.

This module initializes the PySide6 application, sets up logging,
checks dependencies, and launches the main application window.
"""

import sys
import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
# Add the project root to sys.path to allow absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
from core.config import config
from core.constants import APP_NAME, ORG_NAME, LOGS_DIR_NAME
from core.utils import get_resource_path


class DailyRotatingFileHandler(logging.FileHandler):
    """Custom log handler that rotates daily with date-based filenames."""
    
    def __init__(self, log_dir: Path, backup_days: int = 7, encoding: str = 'utf-8'):
        self.log_dir = Path(log_dir)
        self.backup_days = backup_days
        self.current_date = datetime.now().date()
        self.current_log_file = self._get_log_file_path()
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up old logs on initialization
        self._cleanup_old_logs()
        
        super().__init__(self.current_log_file, mode='a', encoding=encoding)
    
    def _get_log_file_path(self) -> Path:
        """Generate log file path with current date."""
        date_str = self.current_date.strftime('%Y-%m-%d')
        return self.log_dir / f"app-{date_str}.log"
    
    def _cleanup_old_logs(self):
        """Remove log files older than backup_days."""
        cutoff_date = datetime.now().date() - timedelta(days=self.backup_days)
        
        try:
            for log_file in self.log_dir.glob('app-*.log'):
                # Extract date from filename (app-YYYY-MM-DD.log)
                try:
                    date_str = log_file.stem.replace('app-', '')
                    file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logging.info(f"Cleaned up old log file: {log_file.name}")
                except (ValueError, OSError):
                    # Skip files that don't match the expected format
                    pass
        except OSError:
            # Don't crash if cleanup fails
            pass
    
    def emit(self, record):
        """Emit a log record, rotating if date has changed."""
        now = datetime.now().date()
        
        # Check if we need to rotate
        if now != self.current_date:
            self.current_date = now
            self.current_log_file = self._get_log_file_path()
            
            # Close old stream and open new one
            if self.stream:
                self.stream.close()
            
            self.baseFilename = str(self.current_log_file)
            self.stream = self._open()
            
            # Clean up old logs on rotation
            self._cleanup_old_logs()
        
        super().emit(record)


def check_dependencies():
    """Check for required external dependencies."""
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
    # Check config for custom log directory
    config_log_dir = config.get('paths.log_dir')
    if config_log_dir:
        log_dir = Path(config_log_dir)
    else:
        # Determine log directory (platform specific)
        if sys.platform == 'win32':
            log_dir = Path(os.environ.get('APPDATA', '.')) / APP_NAME / LOGS_DIR_NAME
        elif sys.platform == 'darwin':
            log_dir = Path.home() / "Library" / "Logs" / APP_NAME
        else:
            log_dir = Path.home() / ".config" / APP_NAME / LOGS_DIR_NAME
        
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging with daily rotation and 7-day retention
    handler = DailyRotatingFileHandler(log_dir, backup_days=7, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler, console_handler]
    )
    
    logging.info(f"--- Application Starting ({APP_NAME}) ---")
    logging.info(f"Logs directory: {log_dir} (7-day retention)")


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
