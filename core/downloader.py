"""
Desktop Video Downloader Module.

This module provides the core download functionality for a desktop YouTube
downloader application using yt-dlp as the backend. It handles video and
audio downloads from YouTube and other supported platforms with support for
various quality options, formats, and post-processing features.

Classes:
    DownloadCancelledException: Exception raised when download is cancelled by user.
    DownloadFailedException: Exception raised when download fails after retries.
    InvalidURLException: Exception raised when the provided URL is invalid.
    DesktopDownloader: Main class containing all download logic and utilities.

Features:
    - Single video and playlist downloads
    - Multiple quality options (highest, lowest, or specific resolution)
    - Audio-only extraction (MP3, M4A, WAV, FLAC, OGG)
    - Automatic retry mechanism with exponential backoff
    - Progress and status callbacks for UI integration
    - Subtitle downloading (manual and automatic)
    - Thumbnail embedding
    - Custom filename patterns with template variables
    - FFmpeg encoder availability checking
"""

import os
import re
import time
import logging
from typing import Any, Dict, Optional, Callable
from yt_dlp import YoutubeDL
from core.config import config
from core.constants import FRAGMENT_RETRIES, SOCKET_TIMEOUT
from core.utils import sanitize_filename, extract_domain
from core.ffmpeg_manager import ffmpeg_manager


class DownloadCancelledException(Exception):
    """Raised when download is cancelled by user."""
    pass


class SimpleDownloadLogger:
    """Custom logger that only shows download progress, not extractor details."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".yt_dlp")
        self.last_error: str = ''
    
    def debug(self, msg: str) -> None:
        # Filter verbose extractor messages, only show download progress
        if '[download]' in msg and ('Downloading item' in msg or 'Downloading playlist' in msg):
            self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        self.logger.warning(msg)
    
    def error(self, msg: str) -> None:
        self.logger.error(msg)
        self.last_error = msg


class DownloadFailedException(Exception):
    """Raised when download fails."""
    pass


class InvalidURLException(Exception):
    """Raised when URL is invalid."""
    pass


class DesktopDownloader:
    """Core logic for downloading videos adapted for desktop usage."""
    _encoder_cache = {}

    def __init__(self):
        # We don't need a default output path as it's provided per download
        pass

    def _apply_browser_cookies(self, ydl_opts: Dict[str, Any], url: str) -> None:
        """Apply browser cookies based on per-domain auth settings.
        
        Args:
            ydl_opts: yt-dlp options dictionary to modify
            url: The URL being downloaded
        """
        domain = extract_domain(url)
        if not domain:
            return
        
        # Get auth configuration
        browser_source = config.get('auth.browser_source', None)
        domain_overrides = config.get('auth.domain_overrides', {})
        default_cookies = config.get('auth.default_cookies', False)
        
        # If browser source is not set or "none", don't use cookies
        if not browser_source or browser_source.lower() == 'none':
            return
        
        # Check if domain has an override
        use_cookies = None
        for configured_domain, enabled in domain_overrides.items():
            if domain == configured_domain or domain.endswith('.' + configured_domain):
                use_cookies = enabled
                break
        
        # If no override found, use the default setting
        if use_cookies is None:
            use_cookies = default_cookies
        
        if use_cookies:
            ydl_opts['cookiesfrombrowser'] = (browser_source,)

    def _has_ffmpeg_encoder(self, encoder_name: str) -> bool:
        """Check if FFmpeg has a specific encoder available."""
        if encoder_name in self._encoder_cache:
            return self._encoder_cache[encoder_name]
            
        ffmpeg_path = ffmpeg_manager.get_ffmpeg_path()
        if not ffmpeg_path:
            return False
            
        import subprocess
        try:
            # Check for the encoder in the list of available encoders
            result = subprocess.run([ffmpeg_path, '-encoders'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            # Standard output of ffmpeg -encoders has lines like " S..... mov_text ..."
            has_it = any(
                f" {encoder_name} " in line for line in result.stdout.splitlines())
            self._encoder_cache[encoder_name] = has_it
            return has_it
        except Exception:
            # Fallback to False if ffmpeg check fails
            return False

    def _format_filename_pattern(self, pattern: str, info: Dict, original_url: str = '') -> str:
        """Format filename pattern with video information.

        Args:
            pattern: Filename pattern with tags like {title}, {id}, etc.
            info: Video information dictionary
            original_url: Original video URL for ID extraction

        Returns:
            Formatted filename string
        """
        if not pattern:
            pattern = config.get('general.default_filename_pattern', '{title}')

        # Create mapping of available tags (only working tags)
        tag_mapping = {
            'title': sanitize_filename(info.get('title', 'Unknown')),
            'id': sanitize_filename(info.get('id', info.get('display_id', self._extract_id_from_url(original_url)))),
            'author': sanitize_filename(info.get('author', info.get('uploader', 'Unknown'))),
            'duration': str(int(info.get('duration', info.get('length', 0)))) if info.get('duration') or info.get('length') else 'unknown'
        }

        # Replace tags in pattern
        formatted = pattern
        for tag, value in tag_mapping.items():
            formatted = formatted.replace(f'{{{tag}}}', value)

        # Ensure we don't have empty filename
        if not formatted or formatted.isspace():
            formatted = sanitize_filename(info.get('title', 'video'))

        return formatted.strip()

    def _extract_unique_formats(self, formats_list: list) -> list:
        """Extract unique video formats by resolution from yt-dlp format list.
        
        Args:
            formats_list: Raw formats list from yt-dlp extract_info
            
        Returns:
            Sorted list of unique formats (highest resolution first)
        """
        seen_heights = set()
        unique_formats = []
        
        for f in formats_list:
            if f.get("vcodec") == "none":
                continue
            height = f.get("height")
            if height and height not in seen_heights:
                seen_heights.add(height)
                unique_formats.append({
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "height": height,
                    "filesize": f.get("filesize"),
                    "note": f.get("format_note")
                })
        
        unique_formats.sort(key=lambda x: x["height"] or 0, reverse=True)
        return unique_formats

    def _extract_id_from_url(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        if not url:
            return 'unknown'

        # Try to extract video ID from URL
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})',  # Standard YouTube URL
            r'youtu\.be/([0-9A-Za-z_-]{11})',  # Short URL
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return 'unknown'

    def _pattern_to_ydl_template(self, pattern: str) -> str:
        """Convert our {tag} filename pattern to a native yt-dlp outtmpl template.

        Using yt-dlp's own template system means:
        - No separate extract_info pre-fetch is needed before downloading.
        - yt-dlp applies per-OS filename sanitization automatically.
        - %(title).100B caps the title at 100 bytes without mid-word cuts.
        """
        tag_map = {
            '{title}':    '%(title).100B',
            '{id}':       '%(id)s',
            '{author}':   '%(uploader)s',
            '{duration}': '%(duration)s',
        }
        template = pattern
        for tag, field in tag_map.items():
            template = template.replace(tag, field)
        return template

    def get_video_info(self, url: str) -> Dict:
        """Get video information including available streams from an URL."""
        try:
            # Use configured timeout and retry values
            timeout = config.get('downloads.timeout', 30)
            retries = config.get('downloads.retries_on_failure', 5)

            ytdlp_logger = SimpleDownloadLogger()
            ydl_opts = {
                'retries': retries,
                'fragment_retries': FRAGMENT_RETRIES,
                'timeout': timeout,
                'socket_timeout': SOCKET_TIMEOUT,
                'nocheckcertificate': False,
                'ignoreerrors': True,
                'noplaylist': False,
                'yes_playlist': True,
                'logger': ytdlp_logger,
                'quiet': True,
                # Speed up playlist info extraction - don't fetch full video details for each entry
                'extract_flat': True,
                # Use web_embedded first: it often bypasses strict DASH hiding/throttling
                # that the standard web client suffers from. Fallback to android/ios.
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web_embedded', 'android', 'ios', 'web'],
                        'remote_components': ['ejs:github']
                    }
                },
            }

            # Apply browser cookies based on per-domain auth settings
            self._apply_browser_cookies(ydl_opts, url)

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    # Surface a specific error if yt-dlp rejected the URL due to DRM
                    last_err = ytdlp_logger.last_error
                    if 'DRM' in last_err or 'drm' in last_err.lower():
                        raise InvalidURLException(
                            "This site uses DRM protection and cannot be downloaded.\n"
                            "Crunchyroll and similar streaming services encrypt their content "
                            "with Widevine DRM, which is not supported by yt-dlp."
                        )
                    raise InvalidURLException(
                        "Failed to extract video info. "
                        + (last_err.strip() or "The video might be unavailable or the URL is invalid.")
                    )

                if 'list=' in url and info.get('_type') != 'playlist' and 'entries' not in info:
                    try:
                        list_id = url.split('list=')[1].split('&')[0]
                        playlist_url = f"https://www.youtube.com/playlist?list={list_id}"
                        info = ydl.extract_info(playlist_url, download=False)
                    except Exception:
                        pass

                is_playlist = info.get(
                    '_type') == 'playlist' or 'entries' in info

                formats = self._extract_unique_formats(info.get("formats", []))

                if is_playlist and not formats and info.get("entries"):
                    try:
                        first_entry = info["entries"][0]
                        if not first_entry.get("formats"):
                            first_video_url = first_entry['url'].split('&list=')[
                                0]
                            with YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl_entry:
                                first_entry = ydl_entry.extract_info(
                                    first_video_url, download=False)
                                info["entries"][0] = first_entry

                        formats = self._extract_unique_formats(first_entry.get("formats", []))
                    except Exception as e:
                        logging.debug(
                            f"Failed to extract formats from playlist entry: {e}")

                if is_playlist and not formats:
                    formats.append({
                        "format_id": "playlist_highest",
                        "ext": "mp4/m4a",
                        "height": 1080,
                        "filesize": None,
                        "note": "Playlist (Automatic)"
                    })

                thumbnail = info.get("thumbnail")
                if is_playlist and info.get("entries"):
                    first_entry_thumb = info["entries"][0].get("thumbnail")
                    if first_entry_thumb:
                        thumbnail = first_entry_thumb

                playlist_entries = []
                if is_playlist and info.get("entries"):
                    for i, entry in enumerate(info.get("entries", [])):
                        entry_url = entry.get('url', '').strip() if entry else ''
                        if entry and entry_url:
                            playlist_entries.append({
                                "id": entry.get('id'),
                                "title": entry.get('title'),
                                "url": entry_url,
                                "duration": entry.get('duration'),
                                "thumbnail": entry.get('thumbnail'),
                                "index": i + 1
                            })

                available_subtitles = set()

                def extract_langs(info_dict):
                    if info_dict.get('subtitles'):
                        available_subtitles.update(
                            info_dict['subtitles'].keys())
                    if info_dict.get('automatic_captions'):
                        for lang, formats in info_dict['automatic_captions'].items():
                            if formats:
                                url = formats[0].get('url', '')
                                if 'tlang=' not in url:
                                    available_subtitles.add(lang)

                # Skip subtitle extraction for playlists (too slow for large lists)
                if not is_playlist:
                    extract_langs(info)
                    available_subtitles = sorted(list(available_subtitles))
                else:
                    available_subtitles = []

                return {
                    "title": info.get("title"),
                    "author": info.get("uploader") or info.get("playlist_uploader") or "Various",
                    "length": info.get("duration"),
                    "views": info.get("view_count") or info.get("playlist_count"),
                    "description": info.get("description"),
                    "thumbnail": thumbnail,
                    "is_playlist": is_playlist,
                    "playlist_entries": playlist_entries,
                    "available_subtitles": available_subtitles,
                    "available_streams": {
                        "formats": formats
                    }
                }
        except Exception as e:
            raise InvalidURLException(f"Error fetching video info: {str(e)}")

    def download_with_retry(self, url: str,
                            output_path: str,
                            quality: str = "highest",
                            format: str = "mp4",
                            audio_only: bool = False,
                            embed_thumbnails: bool = False,
                            auto_generate_subtitles: bool = False,
                            subtitle_language: str = "en",
                            filename_override: Optional[str] = None,
                            force_overwrites: bool = False,
                            progress_callback: Optional[Callable] = None,
                            status_callback: Optional[Callable] = None,
                            cancellation_check: Optional[Callable] = None) -> str:
        """Download with automatic retry mechanism."""
        max_retries = config.get('downloads.retries_on_failure', 5)
        retry_delay = config.get('downloads.retry_delay', 1000)

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    if status_callback:
                        status_callback(
                            f"Retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    # retry_delay is stored in milliseconds; convert to seconds for time.sleep()
                    time.sleep((retry_delay / 1000.0) * attempt)  # Exponential backoff

                return self.download(
                    url, output_path, quality, format, audio_only, embed_thumbnails,
                    auto_generate_subtitles, subtitle_language,
                    filename_override, force_overwrites,
                    progress_callback, status_callback, cancellation_check
                )

            except DownloadCancelledException:
                raise  # Don't retry if user cancelled
            except Exception as e:
                if attempt == max_retries:
                    raise DownloadFailedException(
                        f"Download failed after {max_retries + 1} attempts: {str(e)}")

                if status_callback:
                    status_callback(f"Attempt {attempt + 1} failed: {str(e)}")

                # Check if we should continue retrying
                if cancellation_check and cancellation_check():
                    raise DownloadCancelledException(
                        "Download cancelled during retry")

        # Should never reach here (loop always raises or returns), but be explicit.
        raise DownloadFailedException("Download failed: exhausted all retries")

    def download(self, url: str,
                 output_path: str,
                 quality: str = "highest",
                 format: str = "mp4",
                 audio_only: bool = False,
                 embed_thumbnails: bool = False,
                 auto_generate_subtitles: bool = False,
                 subtitle_language: str = "en",
                 filename_override: Optional[str] = None,
                 force_overwrites: bool = False,
                 progress_callback: Optional[Callable] = None,
                 status_callback: Optional[Callable] = None,
                 cancellation_check: Optional[Callable] = None) -> str:
        """Download video/playlist in specified quality directly to output_path."""
        if not url or not isinstance(url, str):
            raise InvalidURLException("Invalid or missing URL")
        try:
            def ydl_progress_hook(d):
                if cancellation_check and cancellation_check():
                    raise DownloadCancelledException(
                        "Download cancelled by user")

                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get(
                        'total_bytes_estimate')
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)

                    if total:
                        progress = round(downloaded / total * 100, 1)
                        if progress_callback:
                            progress_callback(progress, speed, eta)
                    else:
                        p_str = d.get('_percent_str', '0%').replace(
                            '%', '').strip()
                        try:
                            p_val = float(p_str)
                            if progress_callback:
                                progress_callback(p_val, speed, eta)
                        except ValueError:
                            pass
                elif d['status'] == 'finished':
                    if progress_callback:
                        progress_callback(100.0, 0, 0)
                    if status_callback:
                        status_callback("Processing...")

            def ydl_postprocessor_hook(d):
                """Separate hook for FFmpeg postprocessing stages."""
                if cancellation_check and cancellation_check():
                    raise DownloadCancelledException(
                        "Download cancelled by user")
                if d.get('status') == 'started':
                    pp = d.get('postprocessor', '')
                    if 'Audio' in pp or 'Extract' in pp:
                        if status_callback:
                            status_callback("Converting audio...")
                    elif 'Embed' in pp or 'Thumbnail' in pp:
                        if status_callback:
                            status_callback("Embedding thumbnail...")
                    elif 'Subtitle' in pp:
                        if status_callback:
                            status_callback("Embedding subtitles...")
                    else:
                        if status_callback:
                            status_callback("Processing...")
                    if progress_callback:
                        progress_callback(100.0, 0, 0)

            # Build output template — use yt-dlp's native template to avoid
            # a separate extract_info pre-fetch before the actual download.
            if filename_override:
                outtmpl = os.path.join(
                    output_path, f'{filename_override}.%(ext)s')
            else:
                pattern = config.get('general.default_filename_pattern', '{title}')
                template = self._pattern_to_ydl_template(pattern)
                outtmpl = os.path.join(output_path, f'{template}.%(ext)s')

            # Unified MP4 Strategy: Always use MP4 for video downloads for maximum compatibility.
            # Audio-only downloads resolve to their specific codec (MP3/M4A/etc).
            effective_merge_format = 'mp4' if not audio_only else format

            options: Dict[str, Any] = {
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [ydl_progress_hook],
                'postprocessor_hooks': [ydl_postprocessor_hook],
                'retries': config.get('downloads.retries_on_failure', 5),
                'fragment_retries': FRAGMENT_RETRIES,
                'timeout': config.get('downloads.timeout', 30),
                'socket_timeout': SOCKET_TIMEOUT,
                'logger': SimpleDownloadLogger(),
                # Prioritize web_embedded and android for downloads. 
                # android client: no PO Token required for some formats, but web_embedded
                # is more reliable for seeing all resolutions.
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web_embedded', 'android', 'web'],
                        'remote_components': ['ejs:github']
                    }
                },
                # NEW STRATEGY: Prioritize Resolution first, then TV compatibility (H.264/AAC).
                'format_sort': ['res', 'ext:mp4:m4a', 'vcodec:h264', 'codec:a:m4a'],
            }

            # Only set merge_output_format for video downloads; omitting the key
            # entirely for audio-only avoids yt-dlp mishandling a None value.
            if not audio_only:
                options['merge_output_format'] = effective_merge_format

            # Apply FFmpeg location if available
            ffmpeg_opts = ffmpeg_manager.get_ytdlp_options()
            if ffmpeg_opts:
                options.update(ffmpeg_opts)

            # Apply browser cookies based on per-domain auth settings
            self._apply_browser_cookies(options, url)

            if force_overwrites:
                # Ensure yt-dlp overwrites existing target files.
                options['overwrites'] = True

            postprocessors = []
            if audio_only:
                options['format'] = 'bestaudio/best'
                # Resolve to a real codec — never pass "audio_only" as codec name
                audio_format = format if format in (
                    'mp3', 'm4a', 'wav', 'flac', 'ogg') else 'mp3'
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                })
            else:
                # Extension-Agnostic Input: Allow high-res (4K/8K) WebM sources but merge to MP4.
                if quality == "highest":
                    # With format_sort, 'bestvideo+bestaudio' will pick the highest resolution,
                    # favoring H.264 if multiple codecs exist at that resolution.
                    options['format'] = 'bestvideo+bestaudio/best'
                elif quality == "lowest":
                    options['format'] = 'worstvideo+worstaudio/worst'
                else:
                    raw = str(quality).rstrip('p')
                    if raw.isdigit():
                        h = raw
                        # Prioritize requested resolution, favoring H.264/AAC via format_sort.
                        options['format'] = (
                            f'bestvideo[height<={h}]+bestaudio'
                            f'/best[height<={h}]'
                            f'/best'
                        )
                    else:
                        options['format'] = 'bestvideo+bestaudio/best'

            if embed_thumbnails:
                options['writethumbnail'] = True
                postprocessors.append(
                    {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
                postprocessors.append({'key': 'FFmpegMetadata'})
                postprocessors.append({
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                })

            if auto_generate_subtitles:
                options['writesubtitles'] = True
                options['subtitleslangs'] = [subtitle_language]
                options['subtitlesformat'] = 'srt'
                options['writeautomaticsub'] = True
                # Throttle requests to avoid 429 rate limit errors on subtitle/caption endpoints
                options['sleep_interval_requests'] = 1
                # Per user request: Always download separate subtitles, never embed them.

            if postprocessors:
                options['postprocessors'] = postprocessors

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url)
                actual_filepath = info.get('requested_downloads', [{}])[0].get(
                    'filepath') or ydl.prepare_filename(info)
                actual_filepath = os.path.abspath(actual_filepath)
                # Verify file was actually downloaded (handles cases like DRM errors)
                if not os.path.exists(actual_filepath):
                    raise DownloadFailedException(
                        "Download failed: File was not created. "
                        "The video may be DRM protected or unavailable."
                    )
                return actual_filepath

        except DownloadCancelledException:
            raise
        except Exception as e:
            raise DownloadFailedException(f"Error downloading: {str(e)}")

    def predict_download_filepath(self, url: str, output_path: str, opts: Optional[Dict[str, Any]] = None,
                                  title_hint: str = '') -> Optional[str]:
        """Predict the final output path locally without any network call."""
        opts = dict(opts or {})
        if not url:
            return None

        pattern = config.get('general.default_filename_pattern', '{title}')

        if opts.get('filename_override'):
            base = opts['filename_override']
        else:
            title = title_hint or 'video'
            vid_id = self._extract_id_from_url(url)
            info = {
                'title': sanitize_filename(title),
                'id': vid_id,
                'uploader': '',
                'duration': ''
            }
            base = self._format_filename_pattern(pattern, info, url)

        audio_only = bool(opts.get('audio_only', False))
        fmt = opts.get('format', 'mp4')

        # Unified Strategy Prediction:
        # Video is ALWAYS .mp4. Audio extractions resolve to codec (default .mp3).
        if not audio_only:
            ext = 'mp4'
        else:
            ext = fmt if fmt in ('mp3', 'm4a', 'wav', 'flac', 'ogg') else 'mp3'

        return os.path.normpath(os.path.join(output_path, f'{base}.{ext}'))
