import os

TOOL_NAME = "List Current Folder"
TOOL_DESCRIPTION = "Lists files in the folder where this program is running."

def run():
    current_folder = os.getcwd()
    entries = sorted(os.listdir(current_folder))

    if not entries:
        return f"Folder is empty:\n\n{current_folder}"

    formatted_entries = "\n".join(f"  - {entry}" for entry in entries)
    return f"Current folder:\n{current_folder}\n\nContents:\n{formatted_entries}"
