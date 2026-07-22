import datetime
import os
import socket
import tempfile

TOOL_NAME = "Create Timestamp Log"
TOOL_DESCRIPTION = "Creates a small log file in your temp folder."

def run():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(tempfile.gettempdir(), f"wtg_toolbox_{timestamp}.log")

    with open(file_path, "w", encoding="utf-8") as log_file:
        log_file.write("WTG Toolbox test log\n")
        log_file.write(f"Created: {datetime.datetime.now()}\n")
        log_file.write(f"Computer: {socket.gethostname()}\n")

    return f"Log created successfully:\n\n{file_path}"
