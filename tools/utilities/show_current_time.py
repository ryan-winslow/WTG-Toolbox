import datetime

TOOL_NAME = "Show Current Time"
TOOL_DESCRIPTION = "Displays the current date and time."

def run():
    current_time = datetime.datetime.now()
    return current_time.strftime("Current date and time:\n\n%A, %B %d, %Y at %I:%M:%S %p")
