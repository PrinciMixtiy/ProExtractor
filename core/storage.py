"""
Persistent history storage manager for the Pro Extractor desktop application.

This module provides the HistoryManager class, which handles loading, saving,
and managing download task history in a JSON file. It implements debounced
background saving to prevent UI freezes during rapid updates, such as when
processing large playlists.
"""

import json
import os
import sys
import threading
from datetime import datetime
from typing import List, Dict, Any
from core.config import config

from .constants import DATA_DIR_NAME

if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle - use executable directory
    _PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    # Running in normal Python environment
    _MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(_MODULE_DIR)  # core -> project root

_DEFAULT_DATA_DIR = os.path.join(_PROJECT_ROOT, DATA_DIR_NAME)

class HistoryManager:
    """Manages persistent history for the desktop application."""
    
    def __init__(self, storage_path: str = None):
        # Use configured data directory or default absolute path
        data_dir = config.get('paths.data_dir') or _DEFAULT_DATA_DIR
        if storage_path is None:
            storage_path = os.path.join(data_dir, 'history.json')
        
        self.storage_path = storage_path
        # Ensure directory exists
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        self.history: List[Dict[str, Any]] = self._load()
        
        # Debounced background saving to avoid UI freezes.
        self._lock = threading.RLock()
        self._dirty = False
        self._save_timer = None
        self._save_delay_s = 0.5

    def _write_to_disk(self):
        with self._lock:
            if not self._dirty:
                # Allow future scheduling.
                self._save_timer = None
                return
            self._dirty = False
            try:
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=4, default=str)
            except IOError as e:
                # Don't crash the app if persistence fails.
                print(f"Error saving history: {e}")
            finally:
                # The timer is one-shot; clear it so future updates can schedule a new save.
                self._save_timer = None

    def _schedule_save(self, immediate: bool = False):
        with self._lock:
            self._dirty = True
            
            if immediate:
                if self._save_timer is not None:
                    try:
                        self._save_timer.cancel()
                    except Exception:
                        pass
                    self._save_timer = None
                # Write immediately (still under lock).
                self._write_to_disk()
                return

            # Debounce strategy:
            # - Create the timer only once.
            # - Subsequent updates just mark dirty.
            # This avoids timer churn (important during large playlist starts).
            if self._save_timer is None:
                self._save_timer = threading.Timer(self._save_delay_s, self._write_to_disk)
                self._save_timer.daemon = True
                self._save_timer.start()

    def flush(self):
        """Force an immediate write of any pending history changes."""
        self._schedule_save(immediate=True)

    def _load(self) -> List[Dict[str, Any]]:
        """Load history from JSON file."""
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save(self):
        """Save history to JSON file (synchronous)."""
        self.flush()

    def add_task(self, task_id: str, data: Dict[str, Any]):
        """Add a new task to history."""
        with self._lock:
            # Check if already exists
            for item in self.history:
                if item.get("task_id") == task_id:
                    item.update(data)
                    self._schedule_save()
                    return
            
            # Add timestamp if not present
            if "created_at" not in data:
                data["created_at"] = datetime.now().isoformat()
            
            self.history.insert(0, data)  # Newest first
            self._schedule_save()

    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """Update an existing task."""
        with self._lock:
            for item in self.history:
                if item.get("task_id") == task_id:
                    item.update(updates)
                    self._schedule_save()
                    return

    def delete_task(self, task_id: str):
        """Remove a task from history."""
        with self._lock:
            self.history = [h for h in self.history if h.get("task_id") != task_id]
            self._schedule_save()

    def delete_by_status(self, status: str):
        """Remove all tasks with a specific status."""
        with self._lock:
            self.history = [h for h in self.history if h.get("status") != status]
            # Destructive action: flush immediately.
            self._schedule_save(immediate=True)

    def clear(self):
        """Clear all history."""
        with self._lock:
            self.history = []
            # Destructive action: flush immediately.
            self._schedule_save(immediate=True)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all history items."""
        return self.history
