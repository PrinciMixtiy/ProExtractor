"""
Utility functions for the Pro Extractor desktop application.

This module provides helper functions used across the application for
filename sanitization, resource path resolution, and URL parsing.
"""

import re
import sys
import os
from urllib.parse import urlparse

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
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    return os.path.join(base_path, relative_path)


def extract_domain(url: str) -> str:
    """
    Extract normalized domain from a URL.
    
    Normalizes common domain variations like:
    - www.youtube.com -> youtube.com
    - m.youtube.com -> youtube.com
    - youtu.be -> youtube.com (short URL)
    
    Args:
        url: The URL to extract domain from.
        
    Returns:
        Normalized domain string (e.g., "youtube.com"), or empty string if invalid.
    """
    if not url:
        return ""
    
    try:
        # Handle short URLs and edge cases before parsing
        url_lower = url.lower().strip()
        
        # Special handling for youtu.be short URLs
        if 'youtu.be' in url_lower:
            return 'youtube.com'
        
        # Add protocol if missing for proper parsing
        if not url_lower.startswith(('http://', 'https://')):
            url_lower = 'https://' + url_lower
        
        parsed = urlparse(url_lower)
        domain = parsed.netloc
        
        if not domain:
            return ""
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove www., m., etc. prefixes
        domain = re.sub(r'^(www\.|m\.|mobile\.|api\.)', '', domain)
        
        return domain
    except Exception:
        return ""
