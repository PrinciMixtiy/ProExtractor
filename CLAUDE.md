# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate venv first
source venv/bin/activate

# Run the application
python main.py

# Build standalone executable (downloads FFmpeg ~100MB on first run)
python generate_build.py

# Run tests (no test runner — execute directly)
python test_extract.py
python test_cookies.py
python test_cookie_save.py
```

There is no lint step configured. The project follows PEP 8 with type hints on new code.

## Architecture

**Stack**: PySide6 (Qt6) + yt-dlp + FFmpeg. Python 3.8+.

### Module layout

| Module | Responsibility |
|---|---|
| `main.py` | App entry, logging setup, FFmpeg dependency check |
| `core/constants.py` | All magic numbers, enums (`DownloadStatus`, `Theme`), accent colors |
| `core/config.py` | JSON config with env var overrides (`YOUTUBE_DOWNLOADER_*`) |
| `core/downloader.py` | yt-dlp wrapper — `get_video_info()`, `download()`, `download_with_retry()` |
| `core/worker.py` | Qt worker classes: `InfoWorker` (QThread), `DownloadWorker` (Process) |
| `core/worker_process.py` | The function that runs inside the spawned download subprocess |
| `core/storage.py` | Debounced history persistence to `data/history.json` |
| `core/ffmpeg_manager.py` | Resolves FFmpeg path (bundled in `resources/ffmpeg/` or system PATH) |
| `core/utils.py` | `sanitize_filename()`, `extract_domain()`, `get_resource_path()` |
| `styles.py` | Dynamic dark/light theme — returns Qt stylesheet strings |
| `ui/main_window.py` | Root window, download queue orchestration |
| `ui/widgets.py` | `VideoInfoCard`, `TaskItem`, `PaginationWidget` |
| `ui/settings.py` | Settings dialog (General / Downloads / Authentication / Advanced tabs) |
| `ui/sidebar.py` | Collapsible navigation sidebar |

### Critical design decisions

**Multiprocessing for downloads, not threads.** `DownloadWorker` spawns a `multiprocessing.Process` because yt-dlp is not thread-safe. A monitor thread inside the Qt process reads from a `Queue` and re-emits Qt signals. `InfoWorker` is fine on a `QThread` since it only calls `get_video_info()`.

**Debounced history saves.** `storage.py` batches writes to avoid UI freezes during large playlist operations. Don't replace this with immediate writes.

**Virtualized history list.** `PaginationWidget` renders only the current page of history items (`DEFAULT_PAGE_SIZE = 30`). Adding widgets for all history entries at once causes memory issues with large playlists.

**yt-dlp native output templates.** `_pattern_to_ydl_template()` converts `{title}` tags to `%(title).100B` yt-dlp syntax so there is no separate `extract_info` pre-fetch before downloading. Don't revert to manual filename formatting.

**Unified MP4 strategy.** All video downloads produce `.mp4` regardless of source container. Audio-only resolves to the requested codec. `format_sort` is set to `['res', 'ext:mp4:m4a', 'vcodec:h264', 'codec:a:m4a']`.

**Browser cookie auth is per-domain.** `_apply_browser_cookies()` reads `auth.domain_overrides` (dict) and `auth.default_cookies` (bool) from config. The global `auth.browser_source` must be set and non-`"none"` for any cookies to be sent.

### Config keys (dot-notation via `config.get()`)

`general.default_download_folder`, `general.default_filename_pattern`, `general.theme`  
`downloads.max_concurrent`, `downloads.retries_on_failure`, `downloads.retry_delay` (ms), `downloads.timeout`  
`auth.browser_source`, `auth.domain_overrides`, `auth.default_cookies`  
`paths.data_dir`, `paths.log_dir`  
`advanced.ffmpeg_path`

Config file location: `~/.config/pro-extractor/config.json` (Linux/macOS), `%APPDATA%/pro-extractor/config.json` (Windows).

### Logging

Daily-rotating file handler in `main.py` (`DailyRotatingFileHandler`). Log files: `~/.config/PRO EXTRACTOR/logs/app-YYYY-MM-DD.log`. 7-day retention. The subprocess logger path is passed as an argument to `download_worker_process` so download logs go to the same file.
