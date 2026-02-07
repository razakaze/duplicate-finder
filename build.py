#!/usr/bin/env python3
"""Build script for Duplicate File Finder.

Run on each target platform:
    python build.py

Produces:
    dist/DuplicateFileFinder/           <- the runnable application folder
    dist/DuplicateFileFinder/source/    <- copy of the Python source code
"""

import subprocess
import sys
import shutil
from pathlib import Path

APP_NAME = "DuplicateFileFinder"
ENTRY_POINT = "main.py"

# Directories and patterns to exclude from the source copy
SOURCE_EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    ".idea",
    ".vscode",
}

PROJECT_ROOT = Path(__file__).resolve().parent


def ensure_pyinstaller():
    """Make sure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("  PyInstaller not found. Installing...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            stdout=subprocess.DEVNULL,
        )
        print("  PyInstaller installed.")


def run_pyinstaller():
    """Run PyInstaller to build the application."""
    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--collect-all", "customtkinter",
        "--noconfirm",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        str(PROJECT_ROOT / ENTRY_POINT),
    ]

    print(f"  Command: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def copy_source():
    """Copy source code into the dist folder alongside the built app."""
    source_dst = PROJECT_ROOT / "dist" / APP_NAME / "source"

    # Clean previous source copy
    if source_dst.exists():
        shutil.rmtree(source_dst)
    source_dst.mkdir(parents=True)

    def should_exclude(rel_path: Path) -> bool:
        """Check if a path should be excluded from copy."""
        for part in rel_path.parts:
            if part in SOURCE_EXCLUDE_DIRS:
                return True
        return False

    # Copy all .py files preserving directory structure
    copied = 0
    for py_file in PROJECT_ROOT.rglob("*.py"):
        rel = py_file.relative_to(PROJECT_ROOT)
        if should_exclude(rel):
            continue
        dst = source_dst / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py_file, dst)
        copied += 1

    # Also copy requirements.txt and any docs
    for extra in ["requirements.txt", "README.md", "LICENSE"]:
        src = PROJECT_ROOT / extra
        if src.exists():
            shutil.copy2(src, source_dst / extra)
            copied += 1

    print(f"  {copied} files copied to: {source_dst}")


def main():
    print("=" * 60)
    print(f"  Building {APP_NAME}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")
    print("=" * 60)
    print()

    print("[1/3] Checking PyInstaller...")
    ensure_pyinstaller()
    print()

    print("[2/3] Running PyInstaller...")
    run_pyinstaller()
    print()

    print("[3/3] Copying source code...")
    copy_source()
    print()

    app_dir = PROJECT_ROOT / "dist" / APP_NAME
    exe_name = APP_NAME + (".exe" if sys.platform == "win32" else "")

    print("=" * 60)
    print("  BUILD SUCCESSFUL")
    print(f"  Output folder: {app_dir}")
    print(f"  Run the app:   {app_dir / exe_name}")
    print(f"  Source code:    {app_dir / 'source'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
