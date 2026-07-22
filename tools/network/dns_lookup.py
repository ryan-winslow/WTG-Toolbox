import socket

TOOL_NAME = "DNS Lookup"
TOOL_DESCRIPTION = "Looks up the IP address for example.com."

def run():
    domain = "example.com"
    hostname, aliases, addresses = socket.gethostbyname_ex(domain)

    alias_text = ", ".join(aliases) if aliases else "None"
    address_text = ", ".join(addresses) if addresses else "None"
    return f"Domain: {hostname}\nAliases: {alias_text}\nIP addresses: {address_text}"
