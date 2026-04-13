"""
Standalone download worker process entry point.

This module contains NO PySide6 imports and is designed to run in a
separate process via multiprocessing. It communicates back to the main
process via multiprocessing.Queue.
"""

import sys
import os

# Add project root to path for imports in subprocess
if __name__ == "__main__":
    # When running as __main__, __file__ is the entry point
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from core.downloader import DesktopDownloader, DownloadCancelledException


def download_worker_process(url, output_path, options, result_queue, cancel_event):
    """
    Entry point for download worker process.
    
    Runs yt-dlp in complete process isolation. Communicates progress
    and results back to main process via result_queue.
    
    Args:
        url: Video URL to download
        output_path: Destination directory
        options: Dict with download options (quality, format, etc.)
        result_queue: multiprocessing.Queue for sending progress updates
        cancel_event: multiprocessing.Event for cancellation signal
    """
    
    def progress_callback(p, speed, eta):
        """Send progress update to main process."""
        if not cancel_event.is_set():
            # Ensure values are not None
            safe_p = float(p) if p is not None else 0.0
            safe_speed = float(speed) if speed is not None else 0.0
            safe_eta = float(eta) if eta is not None else 0.0
            try:
                result_queue.put(('progress', safe_p, safe_speed, safe_eta))
            except:
                pass
    
    def status_callback(msg):
        """Send status update to main process."""
        try:
            result_queue.put(('status', str(msg)))
        except:
            pass
    
    def cancellation_check():
        """Check if cancellation was requested."""
        return cancel_event.is_set()
    
    try:
        downloader = DesktopDownloader()
        
        result = downloader.download_with_retry(
            url=url,
            output_path=output_path,
            quality=options.get('quality', 'highest'),
            format=options.get('format', 'mp4'),
            audio_only=options.get('audio_only', False),
            embed_thumbnails=options.get('embed_thumbnails', False),
            auto_generate_subtitles=options.get('auto_generate_subtitles', False),
            subtitle_language=options.get('subtitle_language', 'en'),
            filename_override=options.get('filename_override'),
            force_overwrites=options.get('force_overwrites', False),
            progress_callback=progress_callback,
            status_callback=status_callback,
            cancellation_check=cancellation_check
        )
        
        try:
            result_queue.put(('finished', result))
        except:
            pass
            
    except DownloadCancelledException:
        try:
            result_queue.put(('cancelled',))
        except:
            pass
    except Exception as e:
        try:
            result_queue.put(('error', str(e)))
        except:
            pass


if __name__ == "__main__":
    # When spawned as a process, __name__ == "__main__"
    # Arguments are passed via multiprocessing
    pass
