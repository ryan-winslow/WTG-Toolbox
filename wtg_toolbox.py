import datetime
import importlib
import os
import pkgutil
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
        """Load available tool modules from the tools folder."""

        categories = {}
        base_path = os.path.join(os.path.dirname(__file__), "tools")

        if not os.path.isdir(base_path):
            return categories

        for category_name in sorted(
            entry
            for entry in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, entry))
            and not entry.startswith("__")
        ):
            category_path = os.path.join(base_path, category_name)
            package_name = f"tools.{category_name}"
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

