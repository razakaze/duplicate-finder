"""Platform-specific utilities."""

import sys
import subprocess
from pathlib import Path


def reveal_in_file_manager(path: Path) -> None:
    """Open the native file manager with the given file selected.

    - Windows: explorer /select, <path>
    - macOS:   open -R <path>
    - Linux:   xdg-open on the parent directory
    """
    path = Path(path).resolve()
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)])
    else:
        # Linux: open the containing folder (no universal "select file" command)
        subprocess.Popen(["xdg-open", str(path.parent)])
