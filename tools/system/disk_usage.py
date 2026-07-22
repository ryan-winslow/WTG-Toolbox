import os
import shutil

TOOL_NAME = "Disk Usage"
TOOL_DESCRIPTION = "Displays total, used, and free disk space."


def _format_bytes(number_of_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(number_of_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} TB"


def run():
    disk_path = os.path.abspath(os.sep)
    total, used, free = shutil.disk_usage(disk_path)
    return (
        f"Disk path: {disk_path}\n\n"
        f"Total space: {_format_bytes(total)}\n"
        f"Used space: {_format_bytes(used)}\n"
        f"Free space: {_format_bytes(free)}"
    )
