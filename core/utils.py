"""
Utility functions for the YouTube Downloader application.
This module provides helper functions used across the application for
filename sanitization and resource path resolution.
Functions:
    sanitize_filename: Sanitizes video titles for use as valid filenames.
    get_resource_path: Resolves absolute paths for bundled resources.
"""

import re

def sanitize_filename(text: str, length: int = 100) -> str:
    """
    Centrally managed sanitization for filenames.
    Ensures consistency between the UI path prediction and actual downloader writing.
    
    Args:
        text: The string to sanitize (e.g. video title).
        length: Maximum character length. Truncates at word boundary.
        
    Returns:
        Sanitized filename string.
    """
    if not text:
        return ""
        
    # Remove invalid filename characters for cross-platform safety
    # (Windows is the most restrictive)
    text = re.sub(r'[<>:"/\\|?*]', '', str(text))
    
    # Replace multiple whitespaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Word-boundary aware truncation
    if len(text) > length:
        # Look for the last space within the first 'length' characters
        chopped = text[:length]
        if ' ' in chopped:
            text = chopped.rsplit(' ', 1)[0].rstrip(' -_')
        else:
            text = chopped
            
    return text

def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for dev and for PyInstaller.
    
    Args:
        relative_path: The path relative to the project root (e.g. 'assets/icons/logo.png').
        
    Returns:
        Absolute path to the resource.
    """
    import sys
    import os
    
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    return os.path.join(base_path, relative_path)
