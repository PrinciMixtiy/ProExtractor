"""
Worker classes for background operations in the desktop application.

This module uses multiprocessing for downloads to isolate yt-dlp,
which is not thread-safe. InfoWorker can still use threads as it
doesn't have the same thread-safety constraints.
"""

from PySide6.QtCore import QObject, Signal, QThread
from multiprocessing import Process, Queue, Event
import logging
import threading
import queue as queue_module
import traceback
from typing import Optional

logger = logging.getLogger(__name__)

from core.downloader import DesktopDownloader
from core.worker_process import download_worker_process


class InfoWorker(QObject):
    """Worker for fetching video/playlist information (thread-safe)."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url: str = url
        self.downloader: DesktopDownloader = DesktopDownloader()

    def run(self) -> None:
        logger.info(f"Fetching video info for URL: {self.url}")
        try:
            info = self.downloader.get_video_info(self.url)
            logger.info(f"Video info fetched successfully: {info.get('title', 'Unknown')}")
            self.finished.emit(info)
        except Exception as e:
            logger.error(f"Failed to fetch video info for {self.url}: {e}")
            self.error.emit(str(e))


class DownloadWorker(QObject):
    """
    Worker for downloading a single video/playlist using process isolation.
    
    Spawns a separate process for yt-dlp to avoid thread-safety issues.
    Uses a monitor thread to relay progress from the process via Queue.
    """
    # progress: task_id, percentage, speed (bytes/s), eta (seconds)
    progress = Signal(str, float, float, float)
    # status: task_id, message
    status = Signal(str, str)
    # finished: task_id, output_path
    finished = Signal(str, str)
    # error: task_id, error message
    error = Signal(str, str)
    # cancelled: task_id
    cancelled = Signal(str)

    def __init__(self, task_id: str, url: str, output_path: str, options: dict) -> None:
        super().__init__()
        self.task_id: str = task_id
        self.url: str = url
        self.output_path: str = output_path
        self.options: dict = options
        
        # Multiprocessing components
        self._process: Optional[Process] = None
        self._result_queue: Optional[Queue] = None
        self._cancel_event: Optional[Event] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._is_finished: bool = False

    def start(self) -> None:
        """Start the download process and monitor thread."""
        logger.info(f"Starting download worker for task {self.task_id}: {self.url}")
        # Create multiprocessing primitives
        self._result_queue = Queue()
        self._cancel_event = Event()
        self._is_finished = False
        
        # Get the log file path from the root logger's file handlers
        log_file_path = None
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                log_file_path = handler.baseFilename
                break
        
        # Spawn the worker process with log file path for proper logging
        self._process = Process(
            target=download_worker_process,
            args=(
                self.url,
                self.output_path,
                self.options,
                self._result_queue,
                self._cancel_event,
                log_file_path
            )
        )
        self._process.start()
        
        # Start monitor thread to relay queue messages to Qt signals
        self._monitor_thread = threading.Thread(target=self._monitor_queue, daemon=True)
        self._monitor_thread.start()

    def cancel(self) -> None:
        """Signal graceful cancellation to the worker process."""
        logger.info(f"Cancelling download worker for task {self.task_id}")
        if self._cancel_event is not None:
            self._cancel_event.set()

    def _monitor_queue(self) -> None:
        """Monitor result queue and emit Qt signals."""
        while not self._is_finished:
            try:
                # Use timeout to allow checking for process death
                msg = self._result_queue.get(timeout=0.1)
                msg_type = msg[0]
                
                if msg_type == 'progress':
                    _, p, speed, eta = msg
                    self.progress.emit(self.task_id, p, speed, eta)
                elif msg_type == 'status':
                    _, status_msg = msg
                    logger.debug(f"Task {self.task_id} status: {status_msg}")
                    self.status.emit(self.task_id, status_msg)
                elif msg_type == 'finished':
                    _, path = msg
                    self._is_finished = True
                    logger.info(f"Task {self.task_id} finished successfully: {path}")
                    self.finished.emit(self.task_id, path)
                    break
                elif msg_type == 'error':
                    _, error_msg = msg
                    self._is_finished = True
                    if "cancelled" in error_msg.lower():
                        logger.info(f"Task {self.task_id} was cancelled")
                        self.cancelled.emit(self.task_id)
                    else:
                        logger.error(f"Task {self.task_id} failed: {error_msg}")
                        self.error.emit(self.task_id, error_msg)
                    break
                elif msg_type == 'cancelled':
                    self._is_finished = True
                    logger.info(f"Task {self.task_id} was cancelled")
                    self.cancelled.emit(self.task_id)
                    break
                    
            except queue_module.Empty:
                # Check if process died unexpectedly
                if self._process is not None and not self._process.is_alive():
                    if not self._is_finished:
                        self._is_finished = True
                        logger.error(f"Task {self.task_id} process terminated unexpectedly")
                        self.error.emit(self.task_id, "Process terminated unexpectedly")
                    break

    def is_running(self) -> bool:
        """Check if the worker process is still running."""
        return self._process is not None and self._process.is_alive()

    def join(self, timeout: Optional[float] = None) -> None:
        """Wait for the process to finish."""
        if self._process is not None:
            self._process.join(timeout)
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout)

    def terminate(self) -> None:
        """Force terminate the worker process. Use cancel() for graceful shutdown."""
        logger.warning(f"Force terminating task {self.task_id}")
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join(1.0)


class WorkerThread(QThread):
    """Helper thread to run InfoWorker (not needed for DownloadWorker which uses Process)."""
    def __init__(self, worker: QObject) -> None:
        super().__init__()
        self.worker: QObject = worker
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        
        # Ensure cleanup
        if hasattr(self.worker, 'finished'):
            self.worker.finished.connect(lambda *args: self.quit())
        if hasattr(self.worker, 'error'):
            self.worker.error.connect(lambda *args: self.quit())
