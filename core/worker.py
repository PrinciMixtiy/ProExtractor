from PySide6.QtCore import QObject, Signal, QThread
from desktop.core.downloader import DesktopDownloader
import traceback
from typing import Optional

class InfoWorker(QObject):
    """Worker for fetching video/playlist information."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url: str = url
        self.downloader: DesktopDownloader = DesktopDownloader()

    def run(self) -> None:
        try:
            info = self.downloader.get_video_info(self.url)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))

class DownloadWorker(QObject):
    """Worker for downloading a single video/playlist."""
    # progress: task_id, percentage, speed (bytes/s), eta (seconds)
    progress = Signal(str, float, float, float)
    # status: task_id, message
    status = Signal(str, str)
    # finished: task_id, output_path
    finished = Signal(str, str)
    # error: task_id, error message
    error = Signal(str, str)

    def __init__(self, task_id: str, url: str, output_path: str, options: dict) -> None:
        super().__init__()
        self.task_id: str = task_id
        self.url: str = url
        self.output_path: str = output_path
        self.options: dict = options
        self.downloader: DesktopDownloader = DesktopDownloader()
        self._is_cancelled: bool = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def _check_cancelled(self) -> bool:
        return self._is_cancelled

    def _progress_callback(self, p: float, speed: float, eta: float) -> None:
        # PySide signals are typed (float). Some yt-dlp callbacks can pass `None`
        # for speed/eta early in a download, which can crash with
        # `_pythonToCppCopy: Cannot copy-convert NoneType to C++`.
        safe_p = float(p) if p is not None else 0.0
        safe_speed = float(speed) if speed is not None else 0.0
        safe_eta = float(eta) if eta is not None else 0.0

        # Emit with task_id so the UI can update the correct row safely.
        self.progress.emit(self.task_id, safe_p, safe_speed, safe_eta)

    def _status_callback(self, msg: str) -> None:
        self.status.emit(self.task_id, msg)

    def run(self) -> None:
        try:
            result = self.downloader.download_with_retry(
                url=self.url,
                output_path=self.output_path,
                quality=self.options.get('quality', 'highest'),
                format=self.options.get('format', 'mp4'),
                audio_only=self.options.get('audio_only', False),
                embed_thumbnails=self.options.get('embed_thumbnails', False),
                auto_generate_subtitles=self.options.get('auto_generate_subtitles', False),
                subtitle_language=self.options.get('subtitle_language', 'en'),
                filename_override=self.options.get('filename_override'),
                force_overwrites=self.options.get('force_overwrites', False),
                progress_callback=self._progress_callback,
                status_callback=self._status_callback,
                cancellation_check=self._check_cancelled
            )
            self.finished.emit(self.task_id, result)
        except Exception as e:
            if "cancelled" in str(e).lower():
                self.error.emit(self.task_id, "Cancelled")
            else:
                self.error.emit(self.task_id, str(e))
                traceback.print_exc()

class WorkerThread(QThread):
    """Helper thread to run workers."""
    def __init__(self, worker: QObject) -> None:
        super().__init__()
        self.worker: QObject = worker
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        
        # Ensure cleanup
        if hasattr(self.worker, 'finished'):
            # Ignore any signal args; QThread.quit() takes no params.
            self.worker.finished.connect(lambda *args: self.quit())
        if hasattr(self.worker, 'error'):
            # Ignore any signal args; QThread.quit() takes no params.
            self.worker.error.connect(lambda *args: self.quit())
        # We don't call self.worker.deleteLater here as the parent manages its lifecycle
