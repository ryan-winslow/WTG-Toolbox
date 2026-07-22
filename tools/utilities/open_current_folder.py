import os
import platform
import subprocess

TOOL_NAME = "Open Current Folder"
TOOL_DESCRIPTION = "Opens the current folder in the system file browser."

def run():
    folder = os.getcwd()
    operating_system = platform.system()

    if operating_system == "Windows":
        os.startfile(folder)
    elif operating_system == "Darwin":
        subprocess.Popen(["open", folder])
    else:
        subprocess.Popen(["xdg-open", folder])

    return f"Opened folder:\n\n{folder}"
