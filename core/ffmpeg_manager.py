"""
FFmpeg management for bundled executables.

Handles locating FFmpeg binaries in both development and PyInstaller-packaged environments.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional
from core.config import config


class FFmpegManager:
    """Manages FFmpeg binary location for the application."""
    
    _instance = None
    _ffmpeg_path: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_ffmpeg_path(self) -> Optional[str]:
        """Get the path to FFmpeg binary, checking multiple sources."""
        # Always re-check config first so Settings changes take effect immediately
        config_path = config.get('advanced.ffmpeg_path', '')
        if config_path and Path(config_path).exists():
            return config_path

        # Cache bundled/system paths — they don't change at runtime
        if self._ffmpeg_path:
            return self._ffmpeg_path

        # 2. Check bundled FFmpeg (PyInstaller)
        bundled = self._get_bundled_ffmpeg()
        if bundled:
            self._ffmpeg_path = bundled
            return bundled

        # 3. Check system PATH
        system_ffmpeg = self._find_in_path()
        if system_ffmpeg:
            self._ffmpeg_path = system_ffmpeg
            return system_ffmpeg

        return None
    
    def _get_bundled_ffmpeg(self) -> Optional[str]:
        """Get FFmpeg from bundled resources (PyInstaller)."""
        # PyInstaller extracts to _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS) / 'resources'
        else:
            # Development mode - check resources/ffmpeg directory
            base_path = Path(__file__).parent.parent / 'resources'
        
        ffmpeg_dir = base_path / 'ffmpeg'
        
        if platform.system() == 'Windows':
            ffmpeg_exe = ffmpeg_dir / 'ffmpeg.exe'
        else:
            ffmpeg_exe = ffmpeg_dir / 'ffmpeg'
        
        if ffmpeg_exe.exists():
            return str(ffmpeg_exe)
        
        return None
    
    def _find_in_path(self) -> Optional[str]:
        """Find FFmpeg in system PATH."""
        import shutil
        return shutil.which('ffmpeg')
    
    def is_available(self) -> bool:
        """Check if FFmpeg is available for use."""
        return self.get_ffmpeg_path() is not None
    
    def get_ytdlp_options(self) -> dict:
        """Get yt-dlp options dict with FFmpeg path configured."""
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path:
            return {'ffmpeg_location': str(Path(ffmpeg_path).parent)}
        return {}


# Global instance
ffmpeg_manager = FFmpegManager()


def get_ffmpeg_path() -> Optional[str]:
    """Convenience function to get FFmpeg path."""
    return ffmpeg_manager.get_ffmpeg_path()


def is_ffmpeg_available() -> bool:
    """Convenience function to check FFmpeg availability."""
    return ffmpeg_manager.is_available()
