"""Core modules for the Pro Extractor desktop application."""

from core.ffmpeg_manager import ffmpeg_manager, get_ffmpeg_path, is_ffmpeg_available

__all__ = ['ffmpeg_manager', 'get_ffmpeg_path', 'is_ffmpeg_available']
