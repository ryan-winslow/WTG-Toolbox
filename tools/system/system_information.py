import platform
import socket

TOOL_NAME = "System Information"
TOOL_DESCRIPTION = "Displays operating system and Python information."

def run():
    return (
        f"Computer name: {socket.gethostname()}\n"
        f"Operating system: {platform.system()}\n"
        f"OS release: {platform.release()}\n"
        f"OS version: {platform.version()}\n"
        f"Machine type: {platform.machine()}\n"
        f"Processor: {platform.processor() or 'Unknown'}\n"
        f"Python version: {platform.python_version()}"
    )
