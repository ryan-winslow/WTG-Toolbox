import socket

TOOL_NAME = "Network Information"
TOOL_DESCRIPTION = "Displays the computer name and local IP address."

def run():
    hostname = socket.gethostname()

    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "Unable to determine local IP"

    return f"Computer name: {hostname}\nLocal IP: {local_ip}"
