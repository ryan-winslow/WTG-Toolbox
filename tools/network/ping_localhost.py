import platform
import subprocess

TOOL_NAME = "Ping Localhost"
TOOL_DESCRIPTION = "Tests whether the local TCP/IP stack is responding."

def run():
    count_option = "-n" if platform.system() == "Windows" else "-c"
    completed_process = subprocess.run(
        ["ping", count_option, "4", "127.0.0.1"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    output = completed_process.stdout or completed_process.stderr or "No ping output was returned."
    return output.strip()
