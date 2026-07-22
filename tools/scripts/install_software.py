from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOL_NAME = "Install Software"
TOOL_DESCRIPTION = "Launch the WTG software installer GUI."


def run() -> None:
    """Launch the standalone software installer script."""
    installer_path = Path(__file__).resolve().parents[1] / "Install_Software.py"
    if not installer_path.exists():
        raise FileNotFoundError(f"Installer script not found: {installer_path}")

    subprocess.Popen(
        [sys.executable, str(installer_path)],
        cwd=str(installer_path.parent),
    )
