"""
Build script for creating a standalone executable using PyInstaller.

This module provides automated build generation for distributing the
Pro Extractor application as a standalone executable.
"""

import sys
import subprocess
from pathlib import Path

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

    # 2. Define paths
    project_root = Path(__file__).parent
    main_script = project_root / "main.py"
    icon_path = project_root / "assets" / "icons" / "logo.png"
    
    # OS-specific separator for --add-data
    sep = ";" if sys.platform == "win32" else ":"
    
    # 3. Build command
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
        f"--add-data=styles.py{sep}.",
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
