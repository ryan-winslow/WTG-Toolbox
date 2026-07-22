import os

TOOL_NAME = "Environment Variables"
TOOL_DESCRIPTION = "Displays the current environment variables."

def run():
    variables = sorted(os.environ.items())
    return "\n".join(f"{name}={value}" for name, value in variables)
