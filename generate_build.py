"""
Build script for creating a standalone executable using PyInstaller.

This module provides automated build generation for distributing the
Pro Extractor application as a standalone executable.
"""

import sys
import subprocess
import platform
import zipfile
import urllib.request
from pathlib import Path

def get_ffmpeg_download_url() -> str:
    """Get FFmpeg download URL for current platform."""
    system = platform.system()
    machine = platform.machine().lower()
    
    # Using BtbN FFmpeg builds (reliable, static builds)
    base_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"
    
    if system == "Windows":
        if "64" in machine:
            return f"{base_url}/ffmpeg-master-latest-win64-gpl.zip"
        else:
            return f"{base_url}/ffmpeg-master-latest-win32-gpl.zip"
    elif system == "Darwin":  # macOS
        return f"{base_url}/ffmpeg-master-latest-macos64-gpl.zip"
    else:  # Linux
        return f"{base_url}/ffmpeg-master-latest-linux64-gpl.tar.xz"


def download_ffmpeg(resources_dir: Path) -> bool:
    """Download and extract FFmpeg to resources directory."""
    import shutil
    
    ffmpeg_dir = resources_dir / "ffmpeg"
    
    if ffmpeg_dir.exists() and any(ffmpeg_dir.iterdir()):
        print("FFmpeg already present in resources/ffmpeg")
        return True
    
    print("Downloading FFmpeg...")
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        url = get_ffmpeg_download_url()
        system = platform.system()
        
        # Determine archive extension
        if system == "Linux":
            archive_name = "ffmpeg_download.tar.xz"
        else:
            archive_name = "ffmpeg_download.zip"
        
        archive_path = resources_dir / archive_name
        
        # Download
        urllib.request.urlretrieve(url, archive_path)
        
        # Extract based on format
        if system == "Linux":
            import tarfile
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                tar_ref.extractall(ffmpeg_dir)
        else:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
        
        # Clean up archive
        archive_path.unlink()
        
        # Find and flatten nested structure (BtbN builds have nested directories)
        for item in ffmpeg_dir.rglob("ffmpeg*"):
            if item.is_file() and item.stat().st_mode & 0o111:  # Check if executable
                # Move all binaries to root of ffmpeg_dir
                for binary in item.parent.glob("*"):
                    if binary.is_file():
                        dest = ffmpeg_dir / binary.name
                        if not dest.exists():
                            shutil.move(str(binary), str(dest))
                # Clean up empty subdirectories
                for subdir in ffmpeg_dir.rglob("*/"):
                    try:
                        subdir.rmdir()
                    except OSError:
                        pass  # Directory not empty
                break
        
        # Make binaries executable on Unix
        if system != "Windows":
            for binary in ffmpeg_dir.glob("ffmpeg*"):
                binary.chmod(binary.stat().st_mode | 0o111)
        
        print(f"FFmpeg downloaded to {ffmpeg_dir}")
        return True
        
    except Exception as e:
        print(f"Warning: Could not download FFmpeg: {e}")
        print("Build will continue, but FFmpeg features may not work.")
        return False


def generate_build():
    """
    Automated script to build a standalone executable using PyInstaller.
    """
    print("--- Pro Extractor Build Generator ---")
    
    # 1. Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 2. Setup FFmpeg
    project_root = Path(__file__).parent
    resources_dir = project_root / "resources"
    resources_dir.mkdir(exist_ok=True)
    download_ffmpeg(resources_dir)

    # 3. Define paths
    main_script = project_root / "main.py"
    icon_path = project_root / "assets" / "icons" / "logo.png"
    
    # OS-specific separator for --add-data
    sep = ";" if sys.platform == "win32" else ":"
    
    # 4. Build command
    # --noconsole: Hide terminal window on launch (GUI mode)
    # --onefile: Bundle into a single executable
    # --add-data: Include assets and resources
    # --icon: Set application icon
    # --hidden-import: Ensure dynamic imports are captured
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--name=ProExtractor",
        f"--add-data=assets{sep}assets",
        f"--add-data=core{sep}core",
        f"--add-data=ui{sep}ui",
        f"--add-data=resources{sep}resources",
        f"--add-data=styles.py{sep}.",
        "--hidden-import=core.ffmpeg_manager",
    ]
    
    if icon_path.exists():
        if sys.platform == "win32":
            # For Windows, you need a .ico file. 
            # PyInstaller can sometimes convert png, but .ico is safer.
            cmd.append(f"--icon={icon_path}")
        else:
            cmd.append(f"--icon={icon_path}")
            
    cmd.append(str(main_script))
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n--- Build Successful! ---")
        print(f"Executable found in: {project_root / 'dist'}")
    except subprocess.CalledProcessError as e:
        print(f"\n--- Build Failed! ---\n{e}")

if __name__ == "__main__":
    generate_build()
