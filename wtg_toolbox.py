import datetime
import os
import platform
import shutil
import socket
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox


README_CONTENTS = """WTG TOOLBOX

ABOUT

WTG Toolbox is a simple collection of IT scripts and utilities.
Use the categories at the top to browse available tools and run them from the drawer.

USING A TOOL

1. Select a category.
2. Locate the tool you want to use.
3. Click the RUN button.
4. The result will appear in a popup window.

CATEGORIES

Scripts
Contains general-purpose scripts and test tools.

Network
Contains network information, ping, and DNS tools.

System
Contains computer information, disk usage, and environment tools.

Utilities
Contains shortcuts and useful functions.

ADDING A NEW TOOL

Add a new entry to the tool_categories dictionary with a name, description, and command.
Then create the matching method on the ITToolbox class.

NOTES

Some tools behave differently depending on the operating system.
Tools run in a background thread so the toolbox window stays responsive.
"""


class ITToolbox(tk.Tk):
    APP_TITLE = "WTG Toolbox"
    APP_VERSION = "1.1.0"

    def __init__(self):
        super().__init__()

        self.title(f"{self.APP_TITLE} v{self.APP_VERSION}")
        self.geometry("920x680")
        self.minsize(760, 560)
        self.configure(bg="#252525")

        self.tool_categories = self.build_tool_categories()
        self.category_buttons = {}

        self.create_toolbox()
        self.show_category("Scripts")

    def build_tool_categories(self):
        """Build the available tool categories and their actions."""

        return {
            "Scripts": [
                {
                    "name": "Hello Script",
                    "description": "Runs a simple test script.",
                    "command": self.hello_script,
                },
                {
                    "name": "Create Timestamp Log",
                    "description": "Creates a small log file in your temp folder.",
                    "command": self.create_timestamp_log,
                },
                {
                    "name": "List Current Folder",
                    "description": "Lists files in the folder where this program is running.",
                    "command": self.list_current_folder,
                },
            ],
            "Network": [
                {
                    "name": "Network Information",
                    "description": "Displays the computer name and local IP address.",
                    "command": self.network_information,
                },
                {
                    "name": "Ping Localhost",
                    "description": "Tests whether the local TCP/IP stack is responding.",
                    "command": self.ping_localhost,
                },
                {
                    "name": "DNS Lookup",
                    "description": "Looks up the IP address for example.com.",
                    "command": self.dns_lookup,
                },
            ],
            "System": [
                {
                    "name": "System Information",
                    "description": "Displays operating system and Python information.",
                    "command": self.system_information,
                },
                {
                    "name": "Disk Usage",
                    "description": "Displays total, used, and free disk space.",
                    "command": self.disk_usage,
                },
                {
                    "name": "Environment Variables",
                    "description": "Displays the current environment variables.",
                    "command": self.environment_variables,
                },
            ],
            "Utilities": [
                {
                    "name": "Open Current Folder",
                    "description": "Opens the current folder in the system file browser.",
                    "command": self.open_current_folder,
                },
                {
                    "name": "Show Current Time",
                    "description": "Displays the current date and time.",
                    "command": self.show_current_time,
                },
            ],
        }

    def create_toolbox(self):
        """Create the main toolbox layout."""

        handle = tk.Frame(
            self,
            bg="#181818",
            bd=5,
            relief="raised",
            width=300,
            height=58,
        )
        handle.place(relx=0.5, y=15, anchor="n")
        handle.pack_propagate(False)

        handle_inner = tk.Frame(handle, bg="#444444", bd=3, relief="sunken")
        handle_inner.pack(fill="both", expand=True, padx=25, pady=11)

        toolbox = tk.Frame(self, bg="#b71c1c", bd=7, relief="raised")
        toolbox.pack(fill="both", expand=True, padx=32, pady=(58, 28))

        title_plate = tk.Label(
            toolbox,
            text="WTG TOOLBOX",
            bg="#d7d7d7",
            fg="#202020",
            font=("Arial", 17, "bold"),
            bd=4,
            relief="raised",
            padx=25,
            pady=6,
        )
        title_plate.pack(pady=(18, 12))

        category_tray = tk.Frame(toolbox, bg="#303030", bd=5, relief="sunken")
        category_tray.pack(fill="x", padx=20, pady=(0, 12))

        category_title = tk.Label(
            category_tray,
            text="TOOL CATEGORIES",
            bg="#303030",
            fg="#eeeeee",
            font=("Arial", 10, "bold"),
        )
        category_title.pack(anchor="w", padx=10, pady=(7, 3))

        category_button_frame = tk.Frame(category_tray, bg="#303030")
        category_button_frame.pack(fill="x", padx=7, pady=(0, 8))

        for category_name in self.tool_categories:
            button = tk.Button(
                category_button_frame,
                text=category_name,
                command=lambda name=category_name: self.show_category(name),
                bg="#5c5c5c",
                fg="white",
                activebackground="#888888",
                activeforeground="white",
                font=("Arial", 10, "bold"),
                bd=3,
                relief="raised",
                cursor="hand2",
                padx=12,
                pady=8,
            )
            button.pack(side="left", fill="x", expand=True, padx=4)
            self.category_buttons[category_name] = button

        drawer = tk.Frame(toolbox, bg="#850000", bd=5, relief="sunken")
        drawer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.drawer_title = tk.Label(
            drawer,
            text="SCRIPTS",
            bg="#202020",
            fg="#f5f5f5",
            font=("Arial", 12, "bold"),
            pady=8,
        )
        self.drawer_title.pack(fill="x")

        self.script_frame = tk.Frame(drawer, bg="#850000", padx=12, pady=12)
        self.script_frame.pack(fill="both", expand=True)

        bottom_red_space = tk.Frame(toolbox, bg="#b71c1c", height=48)
        bottom_red_space.pack(fill="x", padx=20, pady=(0, 10))
        bottom_red_space.pack_propagate(False)

        button_frame = tk.Frame(bottom_red_space, bg="#b71c1c")
        button_frame.pack(anchor="center", pady=5)

        readme_button = tk.Button(
            button_frame,
            text="README",
            command=self.show_readme,
            bg="#f2c94c",
            fg="#171717",
            activebackground="#ffe487",
            activeforeground="#000000",
            font=("Arial", 10, "bold"),
            bd=4,
            relief="raised",
            cursor="hand2",
            padx=20,
            pady=5,
        )
        readme_button.pack(side="left", padx=6)

        about_button = tk.Button(
            button_frame,
            text="ABOUT",
            command=self.show_about,
            bg="#f2c94c",
            fg="#171717",
            activebackground="#ffe487",
            activeforeground="#000000",
            font=("Arial", 10, "bold"),
            bd=4,
            relief="raised",
            cursor="hand2",
            padx=20,
            pady=5,
        )
        about_button.pack(side="left", padx=6)

    def show_category(self, category_name):
        """Replace the drawer contents with the selected category."""

        self.drawer_title.config(text=f"{category_name.upper()} DRAWER")

        for category, button in self.category_buttons.items():
            if category == category_name:
                button.config(bg="#d7d7d7", fg="#202020", relief="sunken")
            else:
                button.config(bg="#5c5c5c", fg="white", relief="raised")

        for widget in self.script_frame.winfo_children():
            widget.destroy()

        tools = self.tool_categories[category_name]

        for row_number, tool in enumerate(tools):
            self.create_script_row(
                row_number,
                tool["name"],
                tool["description"],
                tool["command"],
            )

    def create_script_row(self, row, name, description, command):
        """Create one script entry in the drawer."""

        script_panel = tk.Frame(self.script_frame, bg="#d0d0d0", bd=4, relief="raised")
        script_panel.grid(row=row, column=0, sticky="ew", padx=4, pady=5)

        self.script_frame.columnconfigure(0, weight=1)

        text_frame = tk.Frame(script_panel, bg="#d0d0d0")
        text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=7)

        name_label = tk.Label(
            text_frame,
            text=name,
            bg="#d0d0d0",
            fg="#202020",
            font=("Arial", 11, "bold"),
            anchor="w",
        )
        name_label.pack(fill="x")

        description_label = tk.Label(
            text_frame,
            text=description,
            bg="#d0d0d0",
            fg="#404040",
            font=("Arial", 9),
            anchor="w",
        )
        description_label.pack(fill="x", pady=(2, 0))

        run_button = tk.Button(
            script_panel,
            text="RUN",
            command=lambda: self.run_script(name, command),
            bg="#3b3b3b",
            fg="white",
            activebackground="#606060",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            bd=3,
            relief="raised",
            cursor="hand2",
            width=10,
            pady=8,
        )
        run_button.pack(side="right", padx=10, pady=8)

    def show_readme(self):
        """Open the WTG Toolbox README window."""

        readme_window = tk.Toplevel(self)
        readme_window.title("WTG Toolbox README")
        readme_window.geometry("620x470")
        readme_window.minsize(500, 350)
        readme_window.configure(bg="#b71c1c")
        readme_window.transient(self)

        title = tk.Label(
            readme_window,
            text="WTG TOOLBOX README",
            bg="#d7d7d7",
            fg="#202020",
            font=("Arial", 16, "bold"),
            bd=4,
            relief="raised",
            padx=20,
            pady=7,
        )
        title.pack(pady=(18, 12))

        text_frame = tk.Frame(readme_window, bg="#202020", bd=5, relief="sunken")
        text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        readme_text = tk.Text(
            text_frame,
            bg="#f0f0f0",
            fg="#202020",
            font=("Arial", 10),
            wrap="word",
            padx=14,
            pady=14,
            bd=0,
            yscrollcommand=scrollbar.set,
        )
        readme_text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=readme_text.yview)
        readme_text.insert("1.0", README_CONTENTS.strip())
        readme_text.config(state="disabled")

        close_button = tk.Button(
            readme_window,
            text="CLOSE",
            command=readme_window.destroy,
            bg="#3b3b3b",
            fg="white",
            activebackground="#606060",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            bd=3,
            relief="raised",
            cursor="hand2",
            width=12,
            pady=5,
        )
        close_button.pack(pady=(0, 15))

    def show_about(self):
        """Open a small about window with version and project information."""

        about_window = tk.Toplevel(self)
        about_window.title("About WTG Toolbox")
        about_window.geometry("480x240")
        about_window.configure(bg="#f3f3f3")
        about_window.transient(self)

        title = tk.Label(
            about_window,
            text="WTG TOOLBOX",
            bg="#d7d7d7",
            fg="#202020",
            font=("Arial", 15, "bold"),
            bd=4,
            relief="raised",
            padx=18,
            pady=6,
        )
        title.pack(pady=(18, 12))

        description = (
            f"Version: {self.APP_VERSION}\n\n"
            "A lightweight desktop toolbox for common IT tasks such as "
            "network checks, system information, and quick file operations."
        )

        info_label = tk.Label(
            about_window,
            text=description,
            bg="#f3f3f3",
            fg="#202020",
            font=("Arial", 10),
            justify="center",
            padx=20,
            pady=8,
        )
        info_label.pack()

        close_button = tk.Button(
            about_window,
            text="CLOSE",
            command=about_window.destroy,
            bg="#3b3b3b",
            fg="white",
            activebackground="#606060",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            bd=3,
            relief="raised",
            cursor="hand2",
            width=12,
            pady=5,
        )
        close_button.pack(pady=(12, 0))

    def run_script(self, script_name, command):
        """Run a script without freezing the GUI."""

        thread = threading.Thread(
            target=self.execute_script,
            args=(script_name, command),
            daemon=True,
        )
        thread.start()

    def execute_script(self, script_name, command):
        """Execute the selected script in a background thread."""

        try:
            result = command()
            self.after(0, lambda result=result: self.script_finished(script_name, result))
        except Exception as error:
            self.after(0, lambda error=str(error): self.script_failed(script_name, error))

    def script_finished(self, script_name, result):
        """Show the script result in a popup."""

        if result:
            messagebox.showinfo(script_name, str(result))
        else:
            messagebox.showinfo(script_name, f"{script_name} completed successfully.")

    def script_failed(self, script_name, error_message):
        """Show a script error in a popup."""

        messagebox.showerror(f"{script_name} Error", error_message)

    # ---------------------------------------------------------
    # Script functions
    # Add your real IT scripts in this section.
    # ---------------------------------------------------------

    def hello_script(self):
        return "Hello from the WTG Toolbox.\n\nThe script system is working."

    def create_timestamp_log(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(tempfile.gettempdir(), f"wtg_toolbox_{timestamp}.log")

        with open(file_path, "w", encoding="utf-8") as log_file:
            log_file.write("WTG Toolbox test log\n")
            log_file.write(f"Created: {datetime.datetime.now()}\n")
            log_file.write(f"Computer: {socket.gethostname()}\n")

        return f"Log created successfully:\n\n{file_path}"

    def list_current_folder(self):
        current_folder = os.getcwd()
        entries = sorted(os.listdir(current_folder))

        if not entries:
            return f"Folder is empty:\n\n{current_folder}"

        formatted_entries = "\n".join(f"  - {entry}" for entry in entries)
        return f"Current folder:\n{current_folder}\n\nContents:\n{formatted_entries}"

    def network_information(self):
        hostname = socket.gethostname()

        try:
            local_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            local_ip = "Unable to determine local IP"

        return f"Computer name: {hostname}\nLocal IP: {local_ip}"

    def ping_localhost(self):
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

    def dns_lookup(self):
        domain = "example.com"
        hostname, aliases, addresses = socket.gethostbyname_ex(domain)

        alias_text = ", ".join(aliases) if aliases else "None"
        address_text = ", ".join(addresses) if addresses else "None"

        return f"Domain: {hostname}\nAliases: {alias_text}\nIP addresses: {address_text}"

    def system_information(self):
        return (
            f"Computer name: {socket.gethostname()}\n"
            f"Operating system: {platform.system()}\n"
            f"OS release: {platform.release()}\n"
            f"OS version: {platform.version()}\n"
            f"Machine type: {platform.machine()}\n"
            f"Processor: {platform.processor() or 'Unknown'}\n"
            f"Python version: {platform.python_version()}"
        )

    def disk_usage(self):
        disk_path = os.path.abspath(os.sep)
        total, used, free = shutil.disk_usage(disk_path)

        return (
            f"Disk path: {disk_path}\n\n"
            f"Total space: {self.format_bytes(total)}\n"
            f"Used space: {self.format_bytes(used)}\n"
            f"Free space: {self.format_bytes(free)}"
        )

    def environment_variables(self):
        variables = sorted(os.environ.items())
        return "\n".join(f"{name}={value}" for name, value in variables)

    def open_current_folder(self):
        folder = os.getcwd()
        operating_system = platform.system()

        if operating_system == "Windows":
            os.startfile(folder)
        elif operating_system == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

        return f"Opened folder:\n\n{folder}"

    def show_current_time(self):
        current_time = datetime.datetime.now()
        return current_time.strftime("Current date and time:\n\n%A, %B %d, %Y at %I:%M:%S %p")

    @staticmethod
    def format_bytes(number_of_bytes):
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(number_of_bytes)

        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}"
            size /= 1024

        return f"{size:.2f} TB"


def main():
    """Launch the WTG Toolbox application."""

    app = ITToolbox()
    app.mainloop()


if __name__ == "__main__":
    main()

