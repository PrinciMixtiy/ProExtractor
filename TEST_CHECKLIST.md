# PRO EXTRACTOR - Test Checklist

Comprehensive testing checklist for the PRO EXTRACTOR desktop application.

---

## 1. Installation & Setup

### 1.1 Dependencies Check
- [ ] Python 3.8+ is installed
- [ ] Virtual environment can be created and activated
- [ ] All requirements install without errors (`pip install -r requirements.txt`)
- [ ] FFmpeg is detected automatically when in PATH
- [ ] App shows warning dialog when FFmpeg is not found
- [ ] App starts successfully after FFmpeg is installed

### 1.2 First Launch
- [ ] App launches without crashes
- [ ] Default directories are created:
  - [ ] `~/.config/pro-extractor/` (config directory)
  - [ ] `~/Desktop/YoutubeThumbnails/` (thumbnail cache)
  - [ ] `desktop/data/` (application data)
- [ ] Default config file is created with correct structure
- [ ] History file is created empty

---

## 2. Core Download Functionality

### 2.1 Single Video Download
- [ ] Valid YouTube URL is accepted
- [ ] Invalid URL shows appropriate error message
- [ ] Video info is fetched correctly (title, author, duration, views, thumbnail)
- [ ] Available formats/qualities are displayed correctly
- [ ] Download starts and completes successfully
- [ ] Downloaded file exists in selected destination
- [ ] File size is reasonable (not 0 bytes)
- [ ] Video plays correctly after download

### 2.2 Playlist Download
- [ ] Playlist URL is recognized
- [ ] All playlist entries are listed correctly
- [ ] Playlist metadata (title, author, video count) is accurate
- [ ] Individual videos can be selected/deselected from playlist
- [ ] Entire playlist downloads successfully
- [ ] Partial playlist downloads (selected items only) work
- [ ] Progress shows correct X/Y count

### 2.3 Quality Selection
- [ ] **Highest quality**: Downloads best available quality
- [ ] **1080p**: Downloads 1080p or best available under 1080p
- [ ] **720p**: Downloads 720p or best available under 720p
- [ ] **480p**: Downloads 480p or best available under 480p
- [ ] **360p**: Downloads 360p or best available under 360p
- [ ] **Lowest quality**: Downloads lowest available quality
- [ ] Quality preference persists across sessions

### 2.4 Audio-Only Downloads
- [ ] MP3 format downloads work correctly
- [ ] M4A format downloads work correctly
- [ ] Audio files play correctly
- [ ] Metadata (title, artist) is embedded in audio files
- [ ] Thumbnail embedding works for audio files (when enabled)

### 2.5 Download States & Lifecycle
- [ ] **Queued**: Task appears in queue before processing
- [ ] **Downloading**: Progress bar updates in real-time
- [ ] **Paused**: Download can be paused and resumed
- [ ] **Completed**: Success state shown, file accessible
- [ ] **Failed**: Error message displayed, retry option available
- [ ] **Cancelled**: Download stops immediately, partial file cleaned up

---

## 3. Concurrent Downloads & Queue Management

### 3.1 Concurrent Limit
- [ ] Default 3 concurrent downloads work correctly
- [ ] Changing limit to 1-10 in settings works
- [ ] Queue respects the limit (no more than max running simultaneously)
- [ ] Additional tasks wait in queue until slot opens

### 3.2 Queue Behavior
- [ ] Tasks process in FIFO order
- [ ] Queue updates correctly when task completes/fails
- [ ] New tasks added during active downloads join queue correctly
- [ ] Queue persists across app restarts (if applicable)

---

## 4. Download History

### 4.1 History Display
- [ ] Completed downloads appear in history
- [ ] Failed downloads appear in history with error status
- [ ] Cancelled downloads appear in history
- [ ] History shows correct metadata (title, URL, date, status)
- [ ] Thumbnails load correctly in history items

### 4.2 History Management
- [ ] Individual items can be deleted from history
- [ ] "Clear completed" removes only completed items
- [ ] "Clear failed" removes only failed items
- [ ] "Clear all" removes all history
- [ ] History persists after app restart
- [ ] Large history (100+ items) loads without performance issues

### 4.3 Pagination (if applicable)
- [ ] Pagination appears when history exceeds page size
- [ ] Navigation between pages works
- [ ] Items per page setting is respected

---

## 5. Settings & Configuration

### 5.1 General Settings
- [ ] **Default download folder**:
  - [ ] Browse button opens file dialog
  - [ ] Selected folder is saved
  - [ ] Default folder is used for new downloads
  - [ ] Invalid folder path handled gracefully
- [ ] **Filename pattern**:
  - [ ] All tags work: `{title}`, `{id}`, `{author}`, `{duration}`
  - [ ] Default pattern is used when custom is empty
  - [ ] Invalid characters are sanitized
  - [ ] Long titles are truncated appropriately
- [ ] **Theme**:
  - [ ] Auto: Follows system theme
  - [ ] Light: Forces light theme
  - [ ] Dark: Forces dark theme
  - [ ] Theme changes apply immediately
- [ ] **Language**:
  - [ ] Language selection persists
  - [ ] UI updates to selected language (if translations exist)

### 5.2 Downloads Settings
- [ ] **Max concurrent downloads**: 1-10 range enforced
- [ ] **Retries on failure**: 1, 3, 5, 10, Unlimited options work
- [ ] **Auto-resume downloads**: Setting persists and applies
- [ ] **Embed thumbnails**: Thumbnails embedded in video files when enabled
- [ ] **Auto-generate subtitles**: Subtitles downloaded when enabled
- [ ] **Default subtitle language**: Selected language used for subtitles
- [ ] **Default quality**: Selected quality is default for new downloads
- [ ] **Default format**: Selected format is default for new downloads
- [ ] **Request timeout**: Timeout value saved and applied

### 5.3 Advanced Settings
- [ ] **FFmpeg path**:
  - [ ] Auto-detect works when field is empty
  - [ ] Custom path can be set via browse button
  - [ ] Invalid FFmpeg path shows appropriate error
  - [ ] Custom path persists across restarts
- [ ] **Data directory**:
  - [ ] Custom data directory can be set
  - [ ] History and config saved to custom location
  - [ ] App handles missing custom directory gracefully

### 5.4 Settings Persistence
- [ ] All settings save when "Apply" is clicked
- [ ] Settings persist after app restart
- [ ] "Reset to Defaults" restores all settings to initial values
- [ ] Config file is valid JSON after changes

---

## 6. UI/UX Testing

### 6.1 Main Window
- [ ] Window opens at default size (1200x800)
- [ ] Minimum size (1100x700) is enforced
- [ ] Window can be maximized
- [ ] Window can be resized
- [ ] Window position persists (if implemented)

### 6.2 Sidebar Navigation
- [ ] Sidebar expands/collapses correctly
- [ ] Navigation buttons work:
  - [ ] Home/New Download
  - [ ] History
  - [ ] Settings
- [ ] Active page is visually highlighted
- [ ] Collapsed sidebar shows icons only
- [ ] Expanded sidebar shows icons + labels

### 6.3 URL Input & Video Info
- [ ] URL input field accepts paste and typing
- [ ] "Get Info" button fetches video information
- [ ] Loading state shown while fetching
- [ ] Video info card displays correctly:
  - [ ] Thumbnail
  - [ ] Title
  - [ ] Author
  - [ ] Duration
  - [ ] Views (if available)
- [ ] Format/quality selector populates correctly
- [ ] Audio-only checkbox works
- [ ] Subtitle options appear when available

### 6.4 Download Progress
- [ ] Progress bar shows 0-100% accurately
- [ ] Download speed is displayed (e.g., "2.5 MB/s")
- [ ] ETA is displayed and updates correctly
- [ ] Status messages update ("Downloading...", "Processing...")
- [ ] Cancel button stops download immediately
- [ ] Retry button appears on failure and works

### 6.5 Visual & Theming
- [ ] No visual glitches or overlapping elements
- [ ] All buttons are clickable and responsive
- [ ] Scrollbars appear when content overflows
- [ ] Dark theme colors are correct and consistent
- [ ] Light theme colors are correct and consistent
- [ ] Accent color (#14b8a6) appears on interactive elements
- [ ] Fonts are readable at all sizes

---

## 7. Error Handling & Edge Cases

### 7.1 Network Errors
- [ ] No internet connection shows appropriate error
- [ ] Timeout after configured timeout period
- [ ] Retry mechanism works on transient failures
- [ ] Exponential backoff between retries
- [ ] User can cancel during retry attempts

### 7.2 URL/Content Errors
- [ ] Private/deleted video shows clear error
- [ ] Age-restricted video handled appropriately
- [ ] Region-blocked video handled appropriately
- [ ] Invalid YouTube URL rejected with clear message
- [ ] Non-YouTube URL rejected (if app is YouTube-only)

### 7.3 File System Errors
- [ ] Permission denied shows clear error
- [ ] Disk full shows clear error
- [ ] Invalid destination path handled gracefully
- [ ] Filename too long is handled (truncation)
- [ ] Special characters in filenames handled
- [ ] Read-only destination handled

### 7.4 Resource Limits
- [ ] App handles 100+ playlist items
- [ ] App handles large file downloads (1GB+)
- [ ] Memory usage stays reasonable during long operations
- [ ] App remains responsive during downloads
- [ ] Multiple rapid UI interactions don't crash app

---

## 8. Integration & Compatibility

### 8.1 FFmpeg Integration
- [ ] Video + audio merging works (high quality downloads)
- [ ] Audio extraction works for audio-only downloads
- [ ] Thumbnail embedding works
- [ ] Invalid FFmpeg path handled gracefully
- [ ] FFmpeg version detection works

### 8.2 yt-dlp Integration
- [ ] Latest yt-dlp version works correctly
- [ ] Video extraction works for standard videos
- [ ] Playlist extraction works
- [ ] Format selection uses yt-dlp correctly
- [ ] Progress hooks update UI correctly

### 8.3 OS Compatibility
- [ ] **Linux**:
  - [ ] App launches correctly
  - [ ] File paths handled correctly
  - [ ] System theme detection works
- [ ] **macOS**:
  - [ ] App launches correctly
  - [ ] File paths handled correctly
  - [ ] System theme detection works
- [ ] **Windows**:
  - [ ] App launches correctly
  - [ ] File paths handled correctly
  - [ ] System theme detection works

---

## 9. Performance & Stress Testing

### 9.1 Startup Performance
- [ ] App launches within 3 seconds
- [ ] History loads without blocking UI
- [ ] No freeze during initialization

### 9.2 Download Performance
- [ ] Download speed is comparable to yt-dlp CLI
- [ ] UI remains responsive during downloads
- [ ] Multiple concurrent downloads don't degrade performance
- [ ] Memory usage is stable during long downloads

### 9.3 Stress Tests
- [ ] Add 50+ items to queue - app remains stable
- [ ] Download 10+ videos concurrently (if allowed)
- [ ] Cancel multiple downloads rapidly
- [ ] Start/stop app during active downloads
- [ ] Switch between pages rapidly during downloads

---

## 10. Regression Testing

After any code changes, verify these core flows still work:

- [ ] Single video download (highest quality, MP4)
- [ ] Audio-only download (MP3)
- [ ] Playlist download (first 5 items)
- [ ] Settings change and persist
- [ ] History records download
- [ ] Theme switching works
- [ ] App restart preserves all data

---

## Test Data Suggestions

### Sample URLs for Testing
```
Standard video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Short URL: https://youtu.be/dQw4w9WgXcQ
Playlist: https://www.youtube.com/playlist?list=PL... (any public playlist)
Live stream: https://www.youtube.com/watch?v=... (if testing live)
4K video: https://www.youtube.com/watch?v=... (for quality testing)
Shorts: https://www.youtube.com/shorts/...
```

### Edge Case URLs
```
Very long title: Find video with 100+ character title
Special characters: Video with emojis/special chars in title
Private video: https://www.youtube.com/watch?v=... (private)
Deleted video: https://www.youtube.com/watch?v=InvalidID123
```

---

## Test Environment Setup

### Required Tools
- Python 3.8+
- FFmpeg (various versions for compatibility testing)
- Git (for version management)
- System monitor (for performance testing)

### Test Scenarios Matrix

| Test Case | Windows | macOS | Linux | Priority |
|-----------|---------|-------|-------|----------|
| Basic download | ✓ | ✓ | ✓ | High |
| Playlist | ✓ | ✓ | ✓ | High |
| Concurrent downloads | ✓ | ✓ | ✓ | High |
| Settings persistence | ✓ | ✓ | ✓ | Medium |
| Theme switching | ✓ | ✓ | ✓ | Low |
| Large playlist (100+) | ✓ | - | ✓ | Medium |
| Long duration download | ✓ | - | - | Low |

---

## Notes

- Mark each checkbox with `[x]` when test passes
- Add comments for any failures or issues found
- Update checklist when new features are added
- Re-run full checklist before major releases
