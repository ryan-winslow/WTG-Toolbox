import ctypes
import datetime
import importlib
import os
import pkgutil
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import tkinter.simpledialog as simpledialog
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

TOOL_PACKAGE_FOLDER = "tools"
DEFAULT_CATEGORY = "Scripts"
WINDOW_WIDTH = 920
WINDOW_HEIGHT = 680
WINDOW_MIN_WIDTH = 760
WINDOW_MIN_HEIGHT = 560
APP_BG = "#252525"
HANDLE_BG = "#181818"
HANDLE_INNER_BG = "#444444"
TOOLBOX_BG = "#b71c1c"
TRAY_BG = "#303030"
TRAY_TEXT_FG = "#eeeeee"
TRAY_BUTTON_BG = "#5c5c5c"
TRAY_BUTTON_FG = "white"
TRAY_BUTTON_ACTIVE_BG = "#888888"
CATEGORY_BUTTON_BG = "#5c5c5c"
CATEGORY_BUTTON_FG = "white"
CATEGORY_BUTTON_ACTIVE_BG = TITLE_BG = "#d7d7d7"
CATEGORY_BUTTON_ACTIVE_FG = TITLE_FG = "#202020"
DRAWER_BG = "#850000"
DRAWER_TITLE_BG = "#202020"
DRAWER_TITLE_FG = "#f5f5f5"
CARD_BG = "#d0d0d0"
CARD_TEXT_FG = "#202020"
CARD_DESC_FG = "#404040"
RUN_BUTTON_BG = "#3b3b3b"
RUN_BUTTON_ACTIVE_BG = "#606060"
CLOSE_BUTTON_BG = "#3b3b3b"
CLOSE_BUTTON_FG = "white"
CLOSE_BUTTON_ACTIVE_BG = "#606060"
CLOSE_BUTTON_ACTIVE_FG = "white"
README_BUTTON_BG = "#f2c94c"
README_BUTTON_FG = "#171717"
README_BUTTON_ACTIVE_BG = "#ffe487"
README_BUTTON_ACTIVE_FG = "#000000"
ABOUT_BG = "#f3f3f3"
TITLE_BG = "#d7d7d7"
TITLE_FG = "#202020"
TITLE_FONT = ("Arial", 17, "bold")
SECTION_FONT = ("Arial", 10, "bold")
SCRIPT_FONT = ("Arial", 11, "bold")
DESC_FONT = ("Arial", 9)
BUTTON_FONT = ("Arial", 10, "bold")
README_FONT = ("Arial", 10)
ABOUT_FONT = ("Arial", 10)
DEFAULT_FONT = ("Arial", 12, "bold")
README_TITLE_FONT = ("Arial", 16, "bold")
ABOUT_TITLE_FONT = ("Arial", 15, "bold")
PASSWORD = "1234"


def is_admin():
    """Return True when running with administrative privileges."""
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def restart_as_admin():
    """Attempt to relaunch the script with elevated permissions."""
    if os.name != "nt":
        return False

    parameters = subprocess.list2cmdline([sys.argv[0], *sys.argv[1:]])
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            parameters,
            None,
            1,
        )
        return result > 32
    except Exception:
        return False


def check_prerequisites():
    """Verify Python version and required modules before launching."""
    if sys.version_info < (3, 10):
        messagebox.showerror(
            "Prerequisite Error",
            "Python 3.10 or newer is required to run WTG Toolbox.",
        )
        return False

    try:
        import tkinter
    except ImportError:
        messagebox.showerror(
            "Prerequisite Error",
            "Tkinter is required and not available in this Python installation.",
        )
        return False

    return True


def authenticate():
    """Request the password before launching the toolbox."""
    root = tk.Tk()
    root.withdraw()
    user_password = simpledialog.askstring(
        "WTG Toolbox Authentication",
        "Enter password:",
        show="*",
        parent=root,
    )
    root.destroy()

    return user_password == PASSWORD


def show_startup_status(message):
    """Show a brief status dialog during startup checks."""
    status_window = tk.Tk()
    status_window.title("WTG Toolbox Startup")
    status_window.geometry("360x120")
    status_window.resizable(False, False)
    status_window.configure(bg=APP_BG)
    status_window.eval("tk::PlaceWindow . center")

    label = tk.Label(
        status_window,
        text=message,
        bg=APP_BG,
        fg=TRAY_TEXT_FG,
        font=DEFAULT_FONT,
        wraplength=320,
        justify="center",
        padx=12,
        pady=18,
    )
    label.pack(expand=True)

    status_window.after(1200, status_window.destroy)
    status_window.mainloop()


class ITToolbox(tk.Tk):
    APP_TITLE = "WTG Toolbox"
    APP_VERSION = "1.1.0"

    def __init__(self):
        super().__init__()

        self.title(f"{self.APP_TITLE} v{self.APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(bg=APP_BG)

        self.tool_categories = self.build_tool_categories()
        self.category_buttons = {}

        self.create_toolbox()
        self.show_category(DEFAULT_CATEGORY)

    def build_tool_categories(self):
        """Load available tool modules from the tools folder."""

        categories = {}
        base_path = os.path.join(os.path.dirname(__file__), TOOL_PACKAGE_FOLDER)

        if not os.path.isdir(base_path):
            return categories

        for category_name in sorted(
            entry
            for entry in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, entry))
            and not entry.startswith("__")
        ):
            category_path = os.path.join(base_path, category_name)
            package_name = f"{TOOL_PACKAGE_FOLDER}.{category_name}"
            tools = []

            for finder, module_name, ispkg in pkgutil.iter_modules([category_path]):
                if ispkg:
                    continue

                module_path = f"{package_name}.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                except Exception as error:
                    print(f"Failed to load {module_path}: {error}")
                    continue

                tool_name = getattr(module, "TOOL_NAME", module_name)
                tool_description = getattr(module, "TOOL_DESCRIPTION", "")
                tool_command = getattr(module, "run", None)

                if callable(tool_command):
                    tools.append(
                        {
                            "name": tool_name,
                            "description": tool_description,
                            "command": tool_command,
                        }
                    )

            categories[category_name.capitalize()] = sorted(
                tools, key=lambda item: item["name"]
            )

        return categories

    def create_toolbox(self):
        """Create the main toolbox layout."""

        handle = tk.Frame(
            self,
            bg=HANDLE_BG,
            bd=5,
            relief="raised",
            width=300,
            height=58,
        )
        handle.place(relx=0.5, y=15, anchor="n")
        handle.pack_propagate(False)

        handle_inner = tk.Frame(handle, bg=HANDLE_INNER_BG, bd=3, relief="sunken")
        handle_inner.pack(fill="both", expand=True, padx=25, pady=11)

        toolbox = tk.Frame(self, bg=TOOLBOX_BG, bd=7, relief="raised")
        toolbox.pack(fill="both", expand=True, padx=32, pady=(58, 28))

        title_plate = tk.Label(
            toolbox,
            text="WTG TOOLBOX",
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=TITLE_FONT,
            bd=4,
            relief="raised",
            padx=25,
            pady=6,
        )
        title_plate.pack(pady=(18, 12))

        category_tray = tk.Frame(toolbox, bg=TRAY_BG, bd=5, relief="sunken")
        category_tray.pack(fill="x", padx=20, pady=(0, 12))

        category_title = tk.Label(
            category_tray,
            text="TOOL CATEGORIES",
            bg=TRAY_BG,
            fg=TRAY_TEXT_FG,
            font=SECTION_FONT,
        )
        category_title.pack(anchor="w", padx=10, pady=(7, 3))

        category_button_frame = tk.Frame(category_tray, bg=TRAY_BG)
        category_button_frame.pack(fill="x", padx=7, pady=(0, 8))

        for category_name in self.tool_categories:
            button = tk.Button(
                category_button_frame,
                text=category_name,
                command=lambda name=category_name: self.show_category(name),
                bg=CATEGORY_BUTTON_BG,
                fg=CATEGORY_BUTTON_FG,
                activebackground=TRAY_BUTTON_ACTIVE_BG,
                activeforeground=CATEGORY_BUTTON_FG,
                font=BUTTON_FONT,
                bd=3,
                relief="raised",
                cursor="hand2",
                padx=12,
                pady=8,
            )
            button.pack(side="left", fill="x", expand=True, padx=4)
            self.category_buttons[category_name] = button

        drawer = tk.Frame(toolbox, bg=DRAWER_BG, bd=5, relief="sunken")
        drawer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.drawer_title = tk.Label(
            drawer,
            text="SCRIPTS",
            bg=DRAWER_TITLE_BG,
            fg=DRAWER_TITLE_FG,
            font=DEFAULT_FONT,
            pady=8,
        )
        self.drawer_title.pack(fill="x")

        self.script_frame = tk.Frame(drawer, bg=DRAWER_BG, padx=12, pady=12)
        self.script_frame.pack(fill="both", expand=True)

        bottom_red_space = tk.Frame(toolbox, bg=TOOLBOX_BG, height=48)
        bottom_red_space.pack(fill="x", padx=20, pady=(0, 10))
        bottom_red_space.pack_propagate(False)

        button_frame = tk.Frame(bottom_red_space, bg=TOOLBOX_BG)
        button_frame.pack(anchor="center", pady=5)

        readme_button = tk.Button(
            button_frame,
            text="README",
            command=self.show_readme,
            bg=README_BUTTON_BG,
            fg=README_BUTTON_FG,
            activebackground=README_BUTTON_ACTIVE_BG,
            activeforeground=README_BUTTON_ACTIVE_FG,
            font=BUTTON_FONT,
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
            bg=README_BUTTON_BG,
            fg=README_BUTTON_FG,
            activebackground=README_BUTTON_ACTIVE_BG,
            activeforeground=README_BUTTON_ACTIVE_FG,
            font=BUTTON_FONT,
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
                button.config(bg=CATEGORY_BUTTON_ACTIVE_BG, fg=CATEGORY_BUTTON_ACTIVE_FG, relief="sunken")
            else:
                button.config(bg=CATEGORY_BUTTON_BG, fg=CATEGORY_BUTTON_FG, relief="raised")

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

        script_panel = tk.Frame(self.script_frame, bg=CARD_BG, bd=4, relief="raised")
        script_panel.grid(row=row, column=0, sticky="ew", padx=4, pady=5)

        self.script_frame.columnconfigure(0, weight=1)

        text_frame = tk.Frame(script_panel, bg=CARD_BG)
        text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=7)

        name_label = tk.Label(
            text_frame,
            text=name,
            bg=CARD_BG,
            fg=CARD_TEXT_FG,
            font=SCRIPT_FONT,
            anchor="w",
        )
        name_label.pack(fill="x")

        description_label = tk.Label(
            text_frame,
            text=description,
            bg=CARD_BG,
            fg=CARD_DESC_FG,
            font=DESC_FONT,
            anchor="w",
        )
        description_label.pack(fill="x", pady=(2, 0))

        run_button = tk.Button(
            script_panel,
            text="RUN",
            command=lambda: self.run_script(name, command),
            bg=RUN_BUTTON_BG,
            fg=TRAY_BUTTON_FG,
            activebackground=RUN_BUTTON_ACTIVE_BG,
            activeforeground=TRAY_BUTTON_FG,
            font=BUTTON_FONT,
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
        readme_window.configure(bg=TOOLBOX_BG)
        readme_window.transient(self)

        title = tk.Label(
            readme_window,
            text="WTG TOOLBOX README",
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=README_TITLE_FONT,
            bd=4,
            relief="raised",
            padx=20,
            pady=7,
        )
        title.pack(pady=(18, 12))

        text_frame = tk.Frame(readme_window, bg=TRAY_BG, bd=5, relief="sunken")
        text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        readme_text = tk.Text(
            text_frame,
            bg="#f0f0f0",
            fg=TITLE_FG,
            font=README_FONT,
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
            bg=RUN_BUTTON_BG,
            fg=TRAY_BUTTON_FG,
            activebackground=RUN_BUTTON_ACTIVE_BG,
            activeforeground=TRAY_BUTTON_FG,
            font=BUTTON_FONT,
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
        about_window.configure(bg=ABOUT_BG)
        about_window.transient(self)

        title = tk.Label(
            about_window,
            text="WTG TOOLBOX",
            bg=TITLE_BG,
            fg=TITLE_FG,
            font=ABOUT_TITLE_FONT,
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
            bg=ABOUT_BG,
            fg=TITLE_FG,
            font=ABOUT_FONT,
            justify="center",
            padx=20,
            pady=8,
        )
        info_label.pack()

        close_button = tk.Button(
            about_window,
            text="CLOSE",
            command=about_window.destroy,
            bg=RUN_BUTTON_BG,
            fg=TRAY_BUTTON_FG,
            activebackground=RUN_BUTTON_ACTIVE_BG,
            activeforeground=TRAY_BUTTON_FG,
            font=BUTTON_FONT,
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

    show_startup_status("Checking administrator privileges...")
    if not is_admin():
        if not restart_as_admin():
            messagebox.showerror(
                "Administrator Required",
                "WTG Toolbox requires administrator privileges. Please restart as admin.",
            )
            return
        return

    show_startup_status("Verifying Python prerequisites...")
    if not check_prerequisites():
        return

    show_startup_status("Authenticating user access...")
    if not authenticate():
        messagebox.showerror("Authentication Failed", "Invalid password. Exiting.")
        return

    app = ITToolbox()
    app.mainloop()


if __name__ == "__main__":
    main()

