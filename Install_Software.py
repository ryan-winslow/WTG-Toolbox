from __future__ import annotations

import ctypes
import fnmatch
import os
import queue
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import traceback
import winreg
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional
from xml.dom import minidom

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText


# ============================================================
# Configuration
# ============================================================

SOFTWARE_DIR = Path(r"C:\WTG-Tools\Installers")
LOG_DIR = SOFTWARE_DIR / "Install-Logs"
SCRIPT_DIR = Path(__file__).resolve().parent
HEADER_IMAGE_PATH = (
    SCRIPT_DIR
    / "assets"
    / "wtg_security_banner.png"
)

DRY_RUN: bool = False
INSTALL_TIMEOUT_SECONDS: int = 30 * 60
INSTALL_TIMEOUT_MINUTES: int = INSTALL_TIMEOUT_SECONDS // 60
MINIMUM_INSTALLER_SIZE_BYTES: int = 100_000
DETECTION_ATTEMPTS: int = 5
DETECTION_RETRY_DELAY_SECONDS: int = 1
FILE_CLEANUP_ATTEMPTS: int = 15
FILE_CLEANUP_RETRY_DELAY_SECONDS: int = 1
WINSCP_FILE_CLEANUP_ATTEMPTS: int = 3
LOG_TAIL_LINE_COUNT: int = 80

GUI_TITLE: str = "WTG Software Installer"
GUI_GEOMETRY: str = "980x900"
GUI_MINIMUM_SIZE: tuple[int, int] = (980, 780)
GUI_QUEUE_POLL_INTERVAL_MS: int = 100
GUI_HEADER_MAX_WIDTH: int = 860
GUI_BUTTON_GAP: int = 4
GUI_BUTTON_COLUMN_WIDTH: int = 191
GUI_CHECKBOX_SIZE: int = 16
GUI_APPLICATION_COLUMNS: int = 3

THEME_BACKGROUND: str = "#010F26"
THEME_PANEL: str = "#021F3C"
THEME_SURFACE: str = "#052E52"
THEME_BORDER: str = "#0B4771"
THEME_TEXT: str = "#F4F8FB"
THEME_MUTED_TEXT: str = "#9DB9CC"
THEME_ACCENT: str = "#0FA7DF"
THEME_ACCENT_ACTIVE: str = "#29C2F2"
THEME_DANGER: str = "#C44758"
THEME_DANGER_ACTIVE: str = "#E05A6A"
THEME_OUTPUT_BACKGROUND: str = "#000B1C"

MASTER_LOG_FILENAME_FORMAT: str = (
    "WTG-Silent-{operation}-{timestamp}.log"
)
MASTER_LOG_TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"

CREATE_NO_WINDOW: int = 0x08000000
FATAL_ERROR_DIALOG_FLAGS: int = 0x10
MOVEFILE_DELAY_UNTIL_REBOOT: int = 0x00000004

FILEZILLA_NAME: str = "FileZilla Server"
WINSCP_NAME: str = "WinSCP"
PAESSLER_NAME: str = "Paessler SNMP Tester"
MREMOTENG_NAME: str = "mRemoteNG"
PUTTY_NAME: str = "PuTTY"

FILEZILLA_INSTALLER_NAME: str = f"{FILEZILLA_NAME} installer"
WINSCP_INSTALLER_NAME: str = f"{WINSCP_NAME} installer"
PAESSLER_INSTALLER_NAME: str = f"{PAESSLER_NAME} installer"
MREMOTENG_INSTALLER_NAME: str = f"{MREMOTENG_NAME} installer"
PUTTY_EXECUTABLE_NAME: str = f"{PUTTY_NAME} executable"

SUCCESS_EXIT_CODE: int = 0
RESTART_EXIT_CODES: set[int] = {
    1641,
    3010,
}

SUCCESS_EXIT_CODES: set[int] = {
    SUCCESS_EXIT_CODE,
    *RESTART_EXIT_CODES,
}

PROGRAM_FILES = Path(
    os.environ.get(
        "ProgramFiles",
        r"C:\Program Files",
    )
)

PROGRAM_FILES_X86 = Path(
    os.environ.get(
        "ProgramFiles(x86)",
        r"C:\Program Files (x86)",
    )
)

PROGRAM_DATA = Path(
    os.environ.get(
        "ProgramData",
        r"C:\ProgramData",
    )
)

WTG_TOOLS_DIR = SOFTWARE_DIR.parent

WINSCP_INSTALL_DIRS: tuple[Path, ...] = (
    PROGRAM_FILES / WINSCP_NAME,
    PROGRAM_FILES_X86 / WINSCP_NAME,
)
WINSCP_EXECUTABLES: tuple[Path, ...] = tuple(
    directory / "WinSCP.exe"
    for directory in WINSCP_INSTALL_DIRS
)
WINSCP_PROCESS_NAME: str = "WinSCP"
WINSCP_PROCESS_STOP_TIMEOUT_SECONDS: int = 10

PUTTY_DIR = PROGRAM_FILES / PUTTY_NAME
PUTTY_EXE = PUTTY_DIR / "putty.exe"

FILEZILLA_DIR = WTG_TOOLS_DIR / FILEZILLA_NAME
FILEZILLA_SERVER_EXE = FILEZILLA_DIR / "filezilla-server.exe"
FILEZILLA_CRYPT_EXE = FILEZILLA_DIR / "filezilla-server-crypt.exe"
FILEZILLA_SERVICE_NAME: str = "filezilla-server"
FILEZILLA_CONFIG_DIR = PROGRAM_DATA / "filezilla-server"
FILEZILLA_USERS_FILE = FILEZILLA_CONFIG_DIR / "users.xml"
FILEZILLA_SETTINGS_FILE = FILEZILLA_CONFIG_DIR / "settings.xml"
FILEZILLA_ROOT_DIR = WTG_TOOLS_DIR / "FTP-Root"
LEGACY_FILEZILLA_ROOT_DIR = WTG_TOOLS_DIR / "ftproot"
FILEZILLA_USERNAME: str = "ftpuser"
FILEZILLA_PASSWORD: str = "ftpuser"
FILEZILLA_XML_NAMESPACE: str = "https://filezilla-project.org"
XML_NAMESPACE_DECLARATION_URI: str = "http://www.w3.org/2000/xmlns/"
FILEZILLA_ROOT_METADATA_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "product_flavour",
        "product_version",
    }
)
FILEZILLA_PASSWORD_HASH_TIMEOUT_SECONDS: int = 30
FILEZILLA_SERVICE_STOP_TIMEOUT_SECONDS: int = 30
FILEZILLA_CONFIG_INITIALIZATION_TIMEOUT_SECONDS: int = 15
FILEZILLA_ADMIN_PORT: int = 14148
FILEZILLA_PLAIN_AND_EXPLICIT_TLS_MODE: str = "0"
FILEZILLA_ADMIN_PASSWORD_BYTES: int = 24
FILEZILLA_FIREWALL_RULE_NAME: str = FILEZILLA_NAME
FILEZILLA_LEGACY_FIREWALL_RULE_NAMES: tuple[str, ...] = (
    "WTG FileZilla Server",
)
FILEZILLA_GUI_AUTOSTART_VALUE_NAME: str = "FileZilla Server"

PUBLIC_DIR = Path(
    os.environ.get(
        "PUBLIC",
        r"C:\Users\Public",
    )
)

USER_PROFILE_DIR = Path(
    os.environ.get(
        "USERPROFILE",
        str(Path.home()),
    )
)

FILEZILLA_DESKTOP_SHORTCUTS: tuple[Path, ...] = tuple(
    desktop / shortcut
    for desktop in (
        PUBLIC_DIR / "Desktop",
        USER_PROFILE_DIR / "Desktop",
    )
    for shortcut in (
        "Administer FileZilla Server.lnk",
        "Start FileZilla Server.lnk",
        "Stop FileZilla Server.lnk",
    )
)

PUTTY_SHORTCUT = (
    PROGRAM_DATA
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
    / "PuTTY.lnk"
)

FILEZILLA_CLEANUP_DIRS: tuple[Path, ...] = (
    FILEZILLA_DIR,
    PROGRAM_FILES / FILEZILLA_NAME,
    PROGRAM_FILES_X86 / FILEZILLA_NAME,
    FILEZILLA_CONFIG_DIR,
    FILEZILLA_ROOT_DIR,
    LEGACY_FILEZILLA_ROOT_DIR,
)

UNINSTALL_KEY = (
    r"SOFTWARE\Microsoft\Windows"
    r"\CurrentVersion\Uninstall"
)

MASTER_LOG: Optional[Path] = None
LOG_QUEUE: Optional[queue.Queue] = None


# ============================================================
# Startup directory validation
# ============================================================

def ensure_required_directories() -> None:
    """Create and validate directories required by the installer."""

    for path in (
        SOFTWARE_DIR,
        LOG_DIR,
    ):
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not path.is_dir():
            raise RuntimeError(
                f"Required directory is unavailable: {path}"
            )


# ============================================================
# Logging
# ============================================================

def log(message: object = "") -> None:
    """
    Write a message to the master log and GUI output.

    This intentionally does not print to stdout because this
    script is intended to run with pythonw.exe as a .pyw file.
    """

    line = str(message)

    if MASTER_LOG is not None:
        try:
            with MASTER_LOG.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(line + "\n")

        except OSError:
            # Do not interrupt an installation solely because
            # the master log could not be written.
            pass

    if LOG_QUEUE is not None:
        LOG_QUEUE.put(
            (
                "log",
                line,
            )
        )


def command_text(
    command: Iterable[object],
) -> str:
    """Return a readable Windows command line."""

    return subprocess.list2cmdline(
        [
            str(item)
            for item in command
        ]
    )


def split_windows_command_line(
    command_line: str,
) -> list[str]:
    """Split a registered Windows command line into arguments."""

    argument_count = ctypes.c_int()
    command_line_to_argv = (
        ctypes.windll.shell32.CommandLineToArgvW
    )
    command_line_to_argv.argtypes = [
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_int),
    ]
    command_line_to_argv.restype = ctypes.POINTER(
        ctypes.c_wchar_p
    )

    arguments = command_line_to_argv(
        command_line,
        ctypes.byref(argument_count),
    )

    if not arguments:
        raise ctypes.WinError()

    try:
        return [
            arguments[index]
            for index in range(argument_count.value)
        ]

    finally:
        local_free = ctypes.windll.kernel32.LocalFree
        local_free.argtypes = [ctypes.c_void_p]
        local_free.restype = ctypes.c_void_p
        local_free(
            ctypes.cast(
                arguments,
                ctypes.c_void_p,
            )
        )


def show_log_tail(
    path: Optional[Path],
    line_count: int = LOG_TAIL_LINE_COUNT,
) -> None:
    """Copy the end of an installer-specific log into the GUI."""

    if path is None:
        return

    log()
    log(f"Installer-specific log: {path}")

    if not path.is_file():
        log(
            "[DIAGNOSTIC] The installer did not create "
            "its own log file."
        )
        return

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

    except OSError as error:
        log(
            "[DIAGNOSTIC] Could not read installer log: "
            f"{error}"
        )
        return

    if not lines:
        log(
            "[DIAGNOSTIC] Installer-specific log is empty."
        )
        return

    count = min(
        line_count,
        len(lines),
    )

    log(f"--- Last {count} installer-log lines ---")

    for line in lines[-count:]:
        log(line)

    log("--- End installer-log excerpt ---")


# ============================================================
# Administrator elevation without a console window
# ============================================================

def is_admin() -> bool:
    """Return True when running with administrator rights."""

    try:
        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )

    except Exception:
        return False


def pythonw_executable() -> Path:
    """
    Locate pythonw.exe beside the active Python interpreter.

    This is used during UAC elevation so that the elevated copy
    opens only the Tkinter GUI and not a black console window.
    """

    current = Path(sys.executable).resolve()

    if current.name.lower() == "pythonw.exe":
        return current

    candidate = current.with_name("pythonw.exe")

    if candidate.is_file():
        return candidate

    # Virtual environments normally place pythonw.exe beside
    # python.exe. If it is not present, fall back to the current
    # interpreter. Saving and launching this file as .pyw will
    # still normally use pythonw.exe through Windows association.
    return current


def relaunch_as_admin() -> None:
    """Restart this script as administrator using pythonw.exe."""

    script = Path(__file__).resolve()
    interpreter = pythonw_executable()

    parameters = subprocess.list2cmdline(
        [
            str(script),
            *sys.argv[1:],
        ]
    )

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        str(interpreter),
        parameters,
        str(script.parent),
        1,
    )

    if result <= 32:
        raise RuntimeError(
            "Windows could not elevate the installer. "
            f"ShellExecute error: {result}"
        )


# ============================================================
# Installed application detection
# ============================================================

def registry_string(
    key,
    name: str,
) -> str:
    """Read a registry value safely."""

    try:
        value, _value_type = winreg.QueryValueEx(
            key,
            name,
        )

        if value is None:
            return ""

        return str(value).strip()

    except OSError:
        return ""


def installed_apps(
    include_current_user: bool = True,
) -> list[tuple[str, str, str, str, str]]:
    """Read installed applications from Windows registry views."""

    applications: list[
        tuple[str, str, str, str, str]
    ] = []

    seen: set[
        tuple[str, str, str]
    ] = set()

    hives = [
        winreg.HKEY_LOCAL_MACHINE,
    ]

    if include_current_user:
        hives.append(
            winreg.HKEY_CURRENT_USER
        )

    views = (
        winreg.KEY_WOW64_64KEY,
        winreg.KEY_WOW64_32KEY,
    )

    for hive in hives:
        for view in views:
            access = (
                winreg.KEY_READ
                | view
            )

            try:
                root = winreg.OpenKey(
                    hive,
                    UNINSTALL_KEY,
                    0,
                    access,
                )

            except OSError:
                continue

            with root:
                try:
                    count = winreg.QueryInfoKey(
                        root
                    )[0]

                except OSError:
                    continue

                for index in range(count):
                    try:
                        subkey = winreg.EnumKey(
                            root,
                            index,
                        )

                        key = winreg.OpenKey(
                            root,
                            subkey,
                            0,
                            access,
                        )

                    except OSError:
                        continue

                    with key:
                        name = registry_string(
                            key,
                            "DisplayName",
                        )

                        if not name:
                            continue

                        version = registry_string(
                            key,
                            "DisplayVersion",
                        )

                        location = registry_string(
                            key,
                            "InstallLocation",
                        )

                        quiet_uninstall = registry_string(
                            key,
                            "QuietUninstallString",
                        )

                        uninstall = registry_string(
                            key,
                            "UninstallString",
                        )

                        unique = (
                            name.lower(),
                            version.lower(),
                            location.lower(),
                        )

                        if unique in seen:
                            continue

                        seen.add(unique)

                        applications.append(
                            (
                                name,
                                version,
                                location,
                                quiet_uninstall,
                                uninstall,
                            )
                        )

    return applications


def detect_application(
    patterns: Iterable[str],
    fallback_paths: Iterable[Path] = (),
    excluded_patterns: Iterable[str] = (),
    include_current_user: bool = True,
) -> tuple[bool, str]:
    """Detect software using registry names and known paths."""

    for (
        name,
        version,
        location,
        _quiet_uninstall,
        _uninstall,
    ) in installed_apps(
        include_current_user
    ):
        matched = any(
            re.search(
                pattern,
                name,
                re.IGNORECASE,
            )
            for pattern in patterns
        )

        excluded = any(
            re.search(
                pattern,
                name,
                re.IGNORECASE,
            )
            for pattern in excluded_patterns
        )

        if matched and not excluded:
            detail = name

            if version:
                detail += f" {version}"

            if location:
                detail += f" at {location}"

            return (
                True,
                detail,
            )

    for path in fallback_paths:
        if path.exists():
            return (
                True,
                f"file found at {path}",
            )

    return (
        False,
        "",
    )


def find_uninstall_command(
    patterns: Iterable[str],
    excluded_patterns: Iterable[str] = (),
    include_current_user: bool = True,
) -> tuple[Optional[list[str]], str, bool]:
    """Find the registered uninstall command for an application."""

    for (
        name,
        version,
        _location,
        quiet_uninstall,
        uninstall,
    ) in installed_apps(include_current_user):
        matched = any(
            re.search(
                pattern,
                name,
                re.IGNORECASE,
            )
            for pattern in patterns
        )

        excluded = any(
            re.search(
                pattern,
                name,
                re.IGNORECASE,
            )
            for pattern in excluded_patterns
        )

        if not matched or excluded:
            continue

        command_line = quiet_uninstall or uninstall

        if not command_line:
            continue

        detail = name

        if version:
            detail += f" {version}"

        return (
            split_windows_command_line(command_line),
            detail,
            bool(quiet_uninstall),
        )

    return (
        None,
        "",
        False,
    )


def detect_filezilla() -> tuple[bool, str]:
    """Detect FileZilla Server."""

    return detect_application(
        [
            r"^FileZilla Server(?:\s|$)",
        ],
        [
            FILEZILLA_SERVER_EXE,
            (
                PROGRAM_FILES
                / FILEZILLA_NAME
                / "filezilla-server-gui.exe"
            ),
            (
                PROGRAM_FILES_X86
                / FILEZILLA_NAME
                / "filezilla-server.exe"
            ),
        ],
    )


def detect_filezilla_document_install() -> tuple[bool, str]:
    """Detect FileZilla in the location required by the WTG guide."""

    if FILEZILLA_SERVER_EXE.is_file():
        return (
            True,
            f"file exists: {FILEZILLA_SERVER_EXE}",
        )

    return (
        False,
        "not detected in the WTG installation directory",
    )


def detect_winscp() -> tuple[bool, str]:
    """
    Detect a machine-wide WinSCP installation only.

    A current-user installation does not cause an all-users
    installation to be skipped.
    """

    return detect_application(
        [
            r"^WinSCP(?:\s|$)",
        ],
        [
            *WINSCP_EXECUTABLES,
        ],
        [
            r"\.NET Assembly",
            r"Automation",
        ],
        include_current_user=False,
    )


def detect_winscp_registry() -> tuple[bool, str]:
    """Detect only WinSCP's machine-wide uninstall registration."""

    return detect_application(
        [
            r"^WinSCP(?:\s|$)",
        ],
        excluded_patterns=[
            r"\.NET Assembly",
            r"Automation",
        ],
        include_current_user=False,
    )


def detect_paessler() -> tuple[bool, str]:
    """Detect Paessler SNMP Tester."""

    return detect_application(
        [
            r"Paessler.*SNMP.*Tester",
            r"^SNMP Tester(?:\s|$)",
        ],
        [
            (
                PROGRAM_FILES
                / PAESSLER_NAME
                / "snmptest.exe"
            ),
            (
                PROGRAM_FILES_X86
                / PAESSLER_NAME
                / "snmptest.exe"
            ),
            (
                PROGRAM_FILES
                / "Paessler"
                / "SNMP Tester"
                / "snmptest.exe"
            ),
            (
                PROGRAM_FILES_X86
                / "Paessler"
                / "SNMP Tester"
                / "snmptest.exe"
            ),
        ],
    )


def detect_mremoteng() -> tuple[bool, str]:
    """Detect mRemoteNG."""

    return detect_application(
        [
            r"^mRemoteNG(?:\s|$)",
        ],
        [
            (
                PROGRAM_FILES
                / MREMOTENG_NAME
                / "mRemoteNG.exe"
            ),
            (
                PROGRAM_FILES_X86
                / MREMOTENG_NAME
                / "mRemoteNG.exe"
            ),
        ],
    )


def detect_putty() -> tuple[bool, str]:
    """Detect PuTTY."""

    return detect_application(
        [
            r"^PuTTY(?:\s|$)",
        ],
        [
            PUTTY_EXE,
            (
                PROGRAM_FILES_X86
                / PUTTY_NAME
                / "putty.exe"
            ),
        ],
    )


def wait_for_detection(
    detector: Callable[
        [],
        tuple[bool, str],
    ],
) -> tuple[bool, str]:
    """Wait briefly for Windows to register an installation."""

    for attempt in range(DETECTION_ATTEMPTS):
        installed, detail = detector()

        if installed:
            return (
                True,
                detail,
            )

        if attempt < DETECTION_ATTEMPTS - 1:
            time.sleep(DETECTION_RETRY_DELAY_SECONDS)

    return (
        False,
        "",
    )


def wait_for_absence(
    detector: Callable[
        [],
        tuple[bool, str],
    ],
) -> tuple[bool, str]:
    """Wait briefly for Windows to register an uninstallation."""

    for attempt in range(DETECTION_ATTEMPTS):
        installed, detail = detector()

        if not installed:
            return (
                True,
                "",
            )

        if attempt < DETECTION_ATTEMPTS - 1:
            time.sleep(DETECTION_RETRY_DELAY_SECONDS)

    return (
        False,
        detail,
    )


# ============================================================
# File discovery and validation
# ============================================================

def find_file(
    patterns: Iterable[str],
) -> Optional[Path]:
    """Find the newest nonempty file matching the patterns."""

    if not SOFTWARE_DIR.exists():
        return None

    matches: list[Path] = []

    for path in SOFTWARE_DIR.rglob("*"):
        if not path.is_file():
            continue

        try:
            if path.stat().st_size <= 0:
                continue

        except OSError:
            continue

        matched = any(
            fnmatch.fnmatch(
                path.name.lower(),
                pattern.lower(),
            )
            for pattern in patterns
        )

        if matched:
            matches.append(path)

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: item.stat().st_mtime,
    )


def require_file(
    display_name: str,
    patterns: Iterable[str],
) -> Path:
    """Find a required file or raise a descriptive error."""

    pattern_list = list(patterns)
    result = find_file(pattern_list)

    if result is not None:
        return result

    expected = "\n".join(
        f"  - {pattern}"
        for pattern in pattern_list
    )

    raise FileNotFoundError(
        f"{display_name} was not found in:\n"
        f"{SOFTWARE_DIR}\n\n"
        "Expected one of these filename patterns:\n"
        f"{expected}"
    )


def validate_file(
    path: Path,
    display_name: str,
) -> None:
    """Validate an EXE or MSI before running it."""

    if not path.is_file():
        raise RuntimeError(
            f"{display_name} does not exist:\n"
            f"{path}"
        )

    size = path.stat().st_size

    if size < MINIMUM_INSTALLER_SIZE_BYTES:
        raise RuntimeError(
            f"{display_name} is unexpectedly small: "
            f"{size:,} bytes"
        )

    with path.open("rb") as handle:
        header = handle.read(8)

    if (
        path.suffix.lower() == ".exe"
        and not header.startswith(b"MZ")
    ):
        raise RuntimeError(
            f"{display_name} is not a valid "
            f"Windows EXE:\n{path}"
        )

    if path.suffix.lower() == ".msi":
        msi_header = bytes.fromhex(
            "D0CF11E0A1B11AE1"
        )

        if header != msi_header:
            raise RuntimeError(
                f"{display_name} is not a valid MSI:\n"
                f"{path}"
            )


# ============================================================
# Command execution
# ============================================================

def run_command(
    display_name: str,
    command: Iterable[object],
    working_directory: Optional[Path] = None,
    installer_log: Optional[Path] = None,
    success_codes: Optional[set[int]] = None,
    raw_command_line: Optional[str] = None,
) -> int:
    """Run an installer and report its output and exit code."""

    command_list = [
        str(item)
        for item in command
    ]

    valid_codes = (
        success_codes
        if success_codes is not None
        else SUCCESS_EXIT_CODES
    )

    log()
    log(f"Running: {display_name}")
    rendered_command = (
        raw_command_line
        if raw_command_line is not None
        else command_text(command_list)
    )
    log(f"Command: {rendered_command}")

    if installer_log is not None:
        log(f"Installer log: {installer_log}")

        try:
            if installer_log.exists():
                installer_log.unlink()

        except OSError as error:
            log(
                "[WARNING] Could not remove the previous "
                f"installer log: {error}"
            )

    if DRY_RUN:
        log("[DRY RUN] Command was not executed.")
        return 0

    try:
        completed = subprocess.run(
            (
                raw_command_line
                if raw_command_line is not None
                else command_list
            ),
            cwd=(
                str(working_directory)
                if working_directory
                else None
            ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=INSTALL_TIMEOUT_SECONDS,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )

    except subprocess.TimeoutExpired as error:
        show_log_tail(installer_log)

        raise RuntimeError(
            f"{display_name} exceeded the "
            f"{INSTALL_TIMEOUT_MINUTES}-minute timeout."
        ) from error

    if (
        completed.stdout
        and completed.stdout.strip()
    ):
        log("--- Standard output ---")
        log(completed.stdout.strip())

    if (
        completed.stderr
        and completed.stderr.strip()
    ):
        log("--- Error output ---")
        log(completed.stderr.strip())

    log(f"Exit code: {completed.returncode}")

    if completed.returncode not in valid_codes:
        show_log_tail(installer_log)

        raise RuntimeError(
            f"{display_name} failed with exit code "
            f"{completed.returncode}."
        )

    return completed.returncode


def install_and_verify(
    name: str,
    detector: Callable[
        [],
        tuple[bool, str],
    ],
    action: Callable[
        [],
        int,
    ],
) -> str:
    """Install an application and verify it afterward."""

    installed, detail = detector()

    if installed:
        return (
            f"[SKIPPED] {name} is already "
            f"installed ({detail})"
        )

    if DRY_RUN:
        action()

        return (
            f"[DRY RUN] {name} would be installed"
        )

    exit_code = action()

    installed_after, detail_after = (
        wait_for_detection(detector)
    )

    if not installed_after:
        raise RuntimeError(
            f"{name} returned a successful exit code, "
            "but installation could not be verified "
            "through the registry or known paths."
        )

    restart = (
        "; Windows restart required"
        if exit_code in RESTART_EXIT_CODES
        else ""
    )

    return (
        f"[OK] {name} installed successfully "
        f"({detail_after}){restart}"
    )


def prepare_uninstall_command(
    command: list[str],
    quiet_registered: bool,
    silent_arguments: Iterable[str],
) -> list[str]:
    """Make a registered uninstall command silent when necessary."""

    prepared = list(command)

    if not prepared:
        raise RuntimeError(
            "The registered uninstall command is empty."
        )

    executable_name = Path(prepared[0]).name.lower()

    if executable_name in {
        "msiexec",
        "msiexec.exe",
    }:
        for index, argument in enumerate(prepared[1:], start=1):
            if argument.lower().startswith("/i"):
                prepared[index] = "/X" + argument[2:]
                break

        existing = {
            argument.lower()
            for argument in prepared[1:]
        }

        if "/qn" not in existing:
            prepared.append("/qn")

        if "/norestart" not in existing:
            prepared.append("/norestart")

    elif not quiet_registered:
        prepared.extend(
            str(argument)
            for argument in silent_arguments
        )

    return prepared


def uninstall_registered_application(
    display_name: str,
    patterns: Iterable[str],
    silent_arguments: Iterable[str],
    excluded_patterns: Iterable[str] = (),
    include_current_user: bool = True,
) -> int:
    """Run an application's registered uninstall command."""

    command, detail, quiet_registered = find_uninstall_command(
        patterns,
        excluded_patterns,
        include_current_user,
    )

    if command is None:
        raise RuntimeError(
            f"No registered uninstall command was found for "
            f"{display_name}."
        )

    log(f"Registered application: {detail}")

    prepared = prepare_uninstall_command(
        command,
        quiet_registered,
        silent_arguments,
    )

    return run_command(
        f"{display_name} uninstaller",
        prepared,
        working_directory=Path(prepared[0]).parent,
    )


def uninstall_and_verify(
    name: str,
    detector: Callable[
        [],
        tuple[bool, str],
    ],
    action: Callable[
        [],
        int,
    ],
) -> str:
    """Uninstall an application and verify its removal."""

    installed, detail = detector()

    if not installed:
        return f"[SKIPPED] {name} is not installed"

    if DRY_RUN:
        action()
        return f"[DRY RUN] {name} would be uninstalled"

    exit_code = action()
    removed, remaining_detail = wait_for_absence(detector)

    if not removed:
        raise RuntimeError(
            f"{name} returned a successful exit code, but it is "
            f"still detected ({remaining_detail})."
        )

    restart = (
        "; Windows restart required"
        if exit_code in RESTART_EXIT_CODES
        else ""
    )

    return f"[OK] {name} uninstalled successfully{restart}"


# ============================================================
# FileZilla Server
# ============================================================

def install_filezilla_action() -> int:
    """Run FileZilla Server silently."""

    installer = require_file(
        FILEZILLA_INSTALLER_NAME,
        [
            "Filezilla-Server.exe",
            "FileZilla_Server_*_win64-setup.exe",
            "FileZilla_Server_*_setup.exe",
        ],
    )

    validate_file(
        installer,
        FILEZILLA_INSTALLER_NAME,
    )

    arguments = [
        installer,
        "/S",
        f"/D={FILEZILLA_DIR}",
    ]
    raw_command_line = (
        f"{command_text(arguments[:-1])} {arguments[-1]}"
    )

    return run_command(
        FILEZILLA_INSTALLER_NAME,
        arguments,
        working_directory=installer.parent,
        raw_command_line=raw_command_line,
    )


def generate_filezilla_password_data(
    username: str,
    password: str,
) -> tuple[str, str, str, str]:
    """Hash a password with FileZilla's bundled crypt utility."""

    if not FILEZILLA_CRYPT_EXE.is_file():
        raise RuntimeError(
            "FileZilla password utility was not found: "
            f"{FILEZILLA_CRYPT_EXE}"
        )

    try:
        completed = subprocess.run(
            [
                str(FILEZILLA_CRYPT_EXE),
                username,
            ],
            input=password + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=FILEZILLA_PASSWORD_HASH_TIMEOUT_SECONDS,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )

    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "FileZilla password hashing timed out."
        ) from error

    if completed.returncode != 0:
        raise RuntimeError(
            "FileZilla password hashing failed with exit code "
            f"{completed.returncode}."
        )

    match = re.search(
        r"@index=(\d+)\s+"
        r"--.+?\.hash=(\S+)\s+"
        r"--.+?\.salt=(\S+)\s+"
        r"--.+?\.iterations=(\d+)",
        completed.stdout.strip(),
    )

    if match is None:
        raise RuntimeError(
            "FileZilla returned an unexpected password-hash format."
        )

    return (
        match.group(1),
        match.group(2),
        match.group(3),
        match.group(4),
    )


def stop_and_configure_filezilla_service() -> None:
    """Set FileZilla to Manual under SYSTEM and leave it stopped."""

    if not FILEZILLA_SERVER_EXE.is_file():
        raise RuntimeError(
            "FileZilla Server was not found in the WTG installation "
            f"directory: {FILEZILLA_SERVER_EXE}"
        )

    service_command = command_text(
        [
            FILEZILLA_SERVER_EXE,
            "--config-dir",
            FILEZILLA_CONFIG_DIR,
        ]
    )

    run_command(
        "FileZilla service startup configuration",
        [
            "sc.exe",
            "config",
            FILEZILLA_SERVICE_NAME,
            "start=",
            "demand",
            "obj=",
            "LocalSystem",
            "binPath=",
            service_command,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )

    service_name = powershell_quote(
        FILEZILLA_SERVICE_NAME
    )
    stop_script = (
        f"$service=Get-Service -Name '{service_name}' "
        "-ErrorAction Stop;"
        "if ($service.Status -ne 'Stopped') {"
        "$service.Stop();"
        "$service.WaitForStatus("
        "'Stopped',[TimeSpan]::FromSeconds("
        f"{FILEZILLA_SERVICE_STOP_TIMEOUT_SECONDS}));"
        "}"
    )

    run_command(
        "Stop FileZilla service",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            stop_script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def ensure_filezilla_config_access() -> None:
    """Ensure elevated administrators can update FileZilla's config."""

    try:
        list(FILEZILLA_CONFIG_DIR.iterdir())
        return

    except PermissionError:
        log(
            "FileZilla configuration is SYSTEM-protected; granting "
            "the local Administrators group access."
        )

    run_command(
        "Take ownership of FileZilla configuration",
        [
            "takeown.exe",
            "/F",
            FILEZILLA_CONFIG_DIR,
            "/A",
            "/R",
            "/D",
            "Y",
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )
    run_command(
        "Grant FileZilla configuration access",
        [
            "icacls.exe",
            FILEZILLA_CONFIG_DIR,
            "/grant",
            "*S-1-5-18:(OI)(CI)F",
            "*S-1-5-32-544:(OI)(CI)F",
            "/T",
            "/C",
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )

    try:
        list(FILEZILLA_CONFIG_DIR.iterdir())

    except PermissionError as error:
        raise RuntimeError(
            "The FileZilla configuration directory is still "
            f"inaccessible: {FILEZILLA_CONFIG_DIR}"
        ) from error


def cycle_filezilla_service(
    wait_for_settings: bool,
    display_name: str,
) -> None:
    """Start FileZilla briefly, validate it, and leave it stopped."""

    service_name = powershell_quote(FILEZILLA_SERVICE_NAME)
    settings_path = powershell_quote(FILEZILLA_SETTINGS_FILE)
    initialization_timeout = (
        FILEZILLA_CONFIG_INITIALIZATION_TIMEOUT_SECONDS
    )
    stop_timeout = FILEZILLA_SERVICE_STOP_TIMEOUT_SECONDS
    settings_check = ""

    if wait_for_settings:
        settings_check = (
            f"$deadline=(Get-Date).AddSeconds({initialization_timeout});"
            f"while (-not (Test-Path -LiteralPath '{settings_path}') "
            f"-or (Get-Item -LiteralPath '{settings_path}' "
            "-ErrorAction SilentlyContinue).Length -eq 0) {"
            "if ((Get-Date) -ge $deadline) {"
            "throw 'FileZilla did not create settings.xml in time';"
            "}"
            "Start-Sleep -Milliseconds 200;"
            "}"
        )

    script = (
        f"$service=Get-Service -Name '{service_name}' "
        "-ErrorAction Stop;"
        "try {"
        "if ($service.Status -ne 'Running') {"
        "$service.Start();"
        f"$service.WaitForStatus('Running',[TimeSpan]::FromSeconds({stop_timeout}));"
        "}"
        f"{settings_check}"
        "} finally {"
        "$service.Refresh();"
        "if ($service.Status -ne 'Stopped') {"
        "$service.Stop();"
        f"$service.WaitForStatus('Stopped',[TimeSpan]::FromSeconds({stop_timeout}));"
        "}"
        "}"
    )

    run_command(
        display_name,
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def start_filezilla_service() -> None:
    """Start FileZilla, verify it is running, and leave it running."""

    service_name = powershell_quote(FILEZILLA_SERVICE_NAME)
    start_timeout = FILEZILLA_SERVICE_STOP_TIMEOUT_SECONDS
    script = (
        "$ErrorActionPreference='Stop';"
        f"$service=Get-Service -Name '{service_name}';"
        "if ($service.Status -ne 'Running') {"
        "$service.Start();"
        "$service.WaitForStatus("
        "'Running',[TimeSpan]::FromSeconds("
        f"{start_timeout}));"
        "}"
        "$service.Refresh();"
        "if ($service.Status -ne 'Running') {"
        "throw 'FileZilla service did not reach the Running state';"
        "}"
    )

    run_command(
        "Start FileZilla service",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def backup_filezilla_configuration(path: Path) -> None:
    """Create a timestamped backup of a FileZilla XML file."""

    backup_path = path.with_name(
        f"{path.name}.WTG-backup-{datetime.now():%Y%m%d_%H%M%S}"
    )
    shutil.copy2(path, backup_path)
    log(f"FileZilla configuration backup: {backup_path}")


def write_filezilla_xml(
    document: minidom.Document,
    path: Path,
) -> None:
    """Atomically write a FileZilla XML document."""

    temporary_path = path.with_suffix(".xml.tmp")
    xml_data = document.toprettyxml(
        indent="\t",
        encoding="utf-8",
        standalone=True,
    )

    with temporary_path.open("wb") as handle:
        handle.write(xml_data)

    os.replace(temporary_path, path)


def direct_xml_child(
    parent,
    local_name: str,
):
    """Return a directly nested XML element by local name."""

    for child in parent.childNodes:
        if (
            child.nodeType == child.ELEMENT_NODE
            and child.localName == local_name
        ):
            return child

    return None


def set_xml_text(
    document: minidom.Document,
    element,
    value: object,
) -> None:
    """Replace an XML element's text content."""

    for child in list(element.childNodes):
        element.removeChild(child)
        child.unlink()

    element.appendChild(document.createTextNode(str(value)))


def xml_text(element) -> str:
    """Return an XML element's direct text content."""

    return "".join(
        child.data
        for child in element.childNodes
        if child.nodeType == child.TEXT_NODE
    ).strip()


def set_filezilla_password_element(
    document: minidom.Document,
    password_element,
    password_data: tuple[str, str, str, str],
) -> None:
    """Populate a FileZilla password XML element."""

    index, password_hash, salt, iterations = password_data
    password_element.setAttribute("index", index)

    for child in list(password_element.childNodes):
        password_element.removeChild(child)
        child.unlink()

    for name, value in (
        ("hash", password_hash),
        ("salt", salt),
        ("iterations", iterations),
    ):
        child = document.createElementNS(
            FILEZILLA_XML_NAMESPACE,
            name,
        )
        child.appendChild(document.createTextNode(value))
        password_element.appendChild(child)


def copy_filezilla_root_metadata(
    source_root,
    target_root,
) -> None:
    """Copy FileZilla schema metadata from one XML root to another."""

    for index in range(source_root.attributes.length):
        attribute = source_root.attributes.item(index)

        if attribute is None:
            continue

        is_namespace_declaration = (
            attribute.namespaceURI == XML_NAMESPACE_DECLARATION_URI
            or attribute.name == "xmlns"
        )

        if (
            not is_namespace_declaration
            and attribute.localName
            not in FILEZILLA_ROOT_METADATA_ATTRIBUTES
        ):
            continue

        if attribute.namespaceURI is None:
            target_root.setAttribute(
                attribute.name,
                attribute.value,
            )

        else:
            target_root.setAttributeNS(
                attribute.namespaceURI,
                attribute.name,
                attribute.value,
            )


def write_filezilla_user_configuration(
    username: str,
    password_data: tuple[str, str, str, str],
) -> None:
    """Create or replace a FileZilla user in users.xml."""

    if (
        not FILEZILLA_SETTINGS_FILE.is_file()
        or FILEZILLA_SETTINGS_FILE.stat().st_size == 0
    ):
        raise RuntimeError(
            "FileZilla settings are unavailable for determining "
            "the installed configuration version: "
            f"{FILEZILLA_SETTINGS_FILE}"
        )

    try:
        settings_document = minidom.parse(
            str(FILEZILLA_SETTINGS_FILE)
        )

    except Exception as error:
        raise RuntimeError(
            "Could not read FileZilla configuration metadata: "
            f"{error}"
        ) from error

    settings_root = settings_document.documentElement
    namespace = (
        settings_root.namespaceURI
        or FILEZILLA_XML_NAMESPACE
    )

    if (
        FILEZILLA_USERS_FILE.is_file()
        and FILEZILLA_USERS_FILE.stat().st_size > 0
    ):
        try:
            document = minidom.parse(
                str(FILEZILLA_USERS_FILE)
            )

        except Exception as error:
            raise RuntimeError(
                "Could not parse FileZilla user configuration: "
                f"{error}"
            ) from error

        backup_filezilla_configuration(FILEZILLA_USERS_FILE)

    else:
        document = minidom.Document()
        root = document.createElementNS(
            namespace,
            settings_root.tagName,
        )
        copy_filezilla_root_metadata(
            settings_root,
            root,
        )
        document.appendChild(root)

        default_impersonator = document.createElementNS(
            namespace,
            "default_impersonator",
        )
        default_impersonator.setAttribute("index", "0")
        default_impersonator.setAttribute("enabled", "false")
        default_impersonator.appendChild(
            document.createElementNS(namespace, "name")
        )
        default_impersonator.appendChild(
            document.createElementNS(namespace, "password")
        )
        root.appendChild(default_impersonator)

    root = document.documentElement
    copy_filezilla_root_metadata(
        settings_root,
        root,
    )

    for node in list(root.childNodes):
        if (
            node.nodeType == node.ELEMENT_NODE
            and node.localName == "user"
            and node.getAttribute("name") == username
        ):
            root.removeChild(node)
            node.unlink()

    def element(
        name: str,
        attributes: Optional[dict[str, str]] = None,
        text_value: Optional[str] = None,
    ):
        child = document.createElementNS(
            namespace,
            name,
        )

        for key, value in (attributes or {}).items():
            child.setAttribute(key, value)

        if text_value is not None:
            child.appendChild(
                document.createTextNode(text_value)
            )

        return child

    user = element(
        "user",
        {
            "name": username,
            "enabled": "true",
        },
    )
    user.appendChild(
        element(
            "mount_point",
            {
                "tvfs_path": "/",
                "access": "1",
                "native_path": "",
                "new_native_path": str(FILEZILLA_ROOT_DIR),
                "recursive": "2",
                "flags": "1",
            },
        )
    )
    user.appendChild(
        element(
            "rate_limits",
            {
                "inbound": "unlimited",
                "outbound": "unlimited",
                "session_inbound": "unlimited",
                "session_outbound": "unlimited",
            },
        )
    )
    user.appendChild(element("allowed_ips"))
    user.appendChild(element("disallowed_ips"))
    user.appendChild(
        element(
            "session_open_limits",
            {
                "files": "unlimited",
                "directories": "unlimited",
            },
        )
    )
    user.appendChild(
        element(
            "session_count_limit",
            text_value="unlimited",
        )
    )
    user.appendChild(
        element(
            "description",
            text_value="Managed by WTG Software Installer",
        )
    )

    password = element(
        "password",
    )
    set_filezilla_password_element(
        document,
        password,
        password_data,
    )
    user.appendChild(password)
    user.appendChild(
        element("methods", text_value="password")
    )
    root.appendChild(user)

    write_filezilla_xml(
        document,
        FILEZILLA_USERS_FILE,
    )


def configure_filezilla_server_settings() -> Optional[str]:
    """Apply the listener/admin settings required by the WTG guide."""

    if (
        not FILEZILLA_SETTINGS_FILE.is_file()
        or FILEZILLA_SETTINGS_FILE.stat().st_size == 0
    ):
        raise RuntimeError(
            "FileZilla settings were not created: "
            f"{FILEZILLA_SETTINGS_FILE}"
        )

    try:
        document = minidom.parse(str(FILEZILLA_SETTINGS_FILE))

    except Exception as error:
        raise RuntimeError(
            "Could not parse FileZilla server settings: "
            f"{error}"
        ) from error

    namespace = FILEZILLA_XML_NAMESPACE
    changed = False
    listeners = document.getElementsByTagNameNS(
        namespace,
        "listener",
    )

    if not listeners:
        raise RuntimeError(
            "FileZilla settings contain no FTP listeners."
        )

    for listener in listeners:
        tls_mode = direct_xml_child(listener, "tls_mode")

        if tls_mode is None:
            tls_mode = document.createElementNS(
                namespace,
                "tls_mode",
            )
            listener.appendChild(tls_mode)
            changed = True

        if xml_text(tls_mode) != FILEZILLA_PLAIN_AND_EXPLICIT_TLS_MODE:
            set_xml_text(
                document,
                tls_mode,
                FILEZILLA_PLAIN_AND_EXPLICIT_TLS_MODE,
            )
            changed = True

    admin_nodes = document.getElementsByTagNameNS(
        namespace,
        "admin",
    )

    if not admin_nodes:
        raise RuntimeError(
            "FileZilla settings contain no administration section."
        )

    admin = admin_nodes[0]
    local_port = direct_xml_child(admin, "local_port")

    if local_port is None:
        local_port = document.createElementNS(
            namespace,
            "local_port",
        )
        admin.insertBefore(local_port, admin.firstChild)
        changed = True

    if xml_text(local_port) != str(FILEZILLA_ADMIN_PORT):
        set_xml_text(
            document,
            local_port,
            FILEZILLA_ADMIN_PORT,
        )
        changed = True

    admin_password = direct_xml_child(admin, "password")

    if admin_password is None:
        admin_password = document.createElementNS(
            namespace,
            "password",
        )
        admin.insertBefore(
            admin_password,
            direct_xml_child(admin, "tls"),
        )
        changed = True

    password_is_configured = (
        admin_password.getAttribute("index") != "0"
        and direct_xml_child(admin_password, "hash") is not None
    )
    generated_admin_password: Optional[str] = None

    if not password_is_configured:
        generated_admin_password = secrets.token_urlsafe(
            FILEZILLA_ADMIN_PASSWORD_BYTES
        )
        password_data = generate_filezilla_password_data(
            "filezilla-admin",
            generated_admin_password,
        )
        set_filezilla_password_element(
            document,
            admin_password,
            password_data,
        )
        changed = True

    if changed:
        backup_filezilla_configuration(FILEZILLA_SETTINGS_FILE)
        write_filezilla_xml(
            document,
            FILEZILLA_SETTINGS_FILE,
        )

    return generated_admin_password


def configure_filezilla_firewall() -> None:
    """Allow FileZilla inbound on Private Windows networks only."""

    rule_name = powershell_quote(FILEZILLA_FIREWALL_RULE_NAME)
    program = powershell_quote(FILEZILLA_SERVER_EXE)
    legacy_rule_names = ",".join(
        f"'{powershell_quote(name)}'"
        for name in FILEZILLA_LEGACY_FIREWALL_RULE_NAMES
    )
    script = (
        "$ErrorActionPreference='Stop';"
        f"$program='{program}';"
        f"$legacyRuleNames=@({legacy_rule_names});"
        "foreach ($legacyRuleName in $legacyRuleNames) {"
        "$legacyRules=@(Get-NetFirewallRule "
        "-DisplayName $legacyRuleName -ErrorAction SilentlyContinue);"
        "if ($legacyRules.Count -gt 0) {"
        "$legacyRules | Remove-NetFirewallRule -ErrorAction Stop;"
        "}"
        "}"
        f"$rules=@(Get-NetFirewallRule -DisplayName '{rule_name}' "
        "-ErrorAction SilentlyContinue"
        ");"
        "if ($rules.Count -eq 0) {"
        f"New-NetFirewallRule -DisplayName '{rule_name}' "
        "-Direction Inbound -Action Allow -Enabled True "
        "-Profile Private -Program $program "
        "-ErrorAction Stop | Out-Null;"
        "} else {"
        "$rules | Set-NetFirewallRule -Direction Inbound "
        "-Action Allow -Enabled True -Profile Private "
        "-ErrorAction Stop;"
        "$rules | Get-NetFirewallApplicationFilter -ErrorAction Stop | "
        "Set-NetFirewallApplicationFilter -Program $program "
        "-ErrorAction Stop;"
        "}"
        f"$configuredRules=@(Get-NetFirewallRule -DisplayName '{rule_name}' "
        "-ErrorAction Stop | Where-Object { $_.Enabled -eq 'True' });"
        "$matchingFilters=@($configuredRules | "
        "Get-NetFirewallApplicationFilter -ErrorAction Stop | "
        "Where-Object { $_.Program -ieq $program });"
        "if ($matchingFilters.Count -eq 0) {"
        "throw 'FileZilla firewall application rule could not be verified';"
        "}"
    )

    run_command(
        "Configure FileZilla private-network firewall rule",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )
    log(
        "[OK] Windows Firewall allows FileZilla Server "
        "on Private networks."
    )


def remove_filezilla_firewall_rule() -> None:
    """Remove the firewall rule managed by this installer."""

    rule_names = ",".join(
        f"'{powershell_quote(name)}'"
        for name in (
            FILEZILLA_FIREWALL_RULE_NAME,
            *FILEZILLA_LEGACY_FIREWALL_RULE_NAMES,
        )
    )
    script = (
        "$ErrorActionPreference='Stop';"
        f"$ruleNames=@({rule_names});"
        "foreach ($ruleName in $ruleNames) {"
        "$rules=@(Get-NetFirewallRule -DisplayName $ruleName "
        "-ErrorAction SilentlyContinue);"
        "if ($rules.Count -gt 0) {"
        "$rules | Remove-NetFirewallRule -ErrorAction Stop;"
        "}"
        "}"
    )

    run_command(
        "Remove FileZilla firewall rule",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def remove_filezilla_desktop_shortcuts() -> None:
    """Remove FileZilla desktop icons while retaining Start Menu tools."""

    for shortcut in FILEZILLA_DESKTOP_SHORTCUTS:
        if DRY_RUN:
            if shortcut.exists():
                log(
                    f"[DRY RUN] Would remove desktop shortcut {shortcut}"
                )
            continue

        try:
            shortcut.unlink(missing_ok=True)

        except OSError as error:
            raise RuntimeError(
                "Could not remove FileZilla desktop shortcut "
                f"{shortcut}: {error}"
            ) from error


def disable_filezilla_admin_autostart() -> None:
    """Keep the FileZilla Administration interface on manual launch."""

    value_name = powershell_quote(
        FILEZILLA_GUI_AUTOSTART_VALUE_NAME
    )
    script = (
        "$paths=@("
        "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',"
        "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',"
        "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run'"
        ");"
        "foreach ($path in $paths) {"
        "if (Get-ItemProperty -LiteralPath $path "
        f"-Name '{value_name}' -ErrorAction SilentlyContinue) {{"
        "Remove-ItemProperty -LiteralPath $path "
        f"-Name '{value_name}' -Force;"
        "}"
        "}"
    )

    run_command(
        "Disable FileZilla Administration interface autostart",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def queue_filezilla_admin_password(password: str) -> None:
    """Show a generated admin password without writing it to logs."""

    if LOG_QUEUE is None:
        log(
            "[WARNING] A FileZilla administration password was "
            "generated but no GUI queue is available to display it."
        )
        return

    LOG_QUEUE.put(
        (
            "credential",
            "FileZilla administration password",
            password,
        )
    )


def ensure_filezilla_root_directory() -> None:
    """Create the documented FTP root, migrating the former path."""

    if FILEZILLA_ROOT_DIR.is_dir():
        return

    if FILEZILLA_ROOT_DIR.exists():
        raise RuntimeError(
            "The FileZilla root path exists but is not a directory: "
            f"{FILEZILLA_ROOT_DIR}"
        )

    if LEGACY_FILEZILLA_ROOT_DIR.is_dir():
        LEGACY_FILEZILLA_ROOT_DIR.rename(FILEZILLA_ROOT_DIR)
        log(
            "Migrated the former FileZilla root directory to "
            f"{FILEZILLA_ROOT_DIR}."
        )
        return

    FILEZILLA_ROOT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def configure_filezilla() -> None:
    """Configure FileZilla according to the WTG setup guide."""

    log()
    log("Configuring FileZilla Server:")
    log(f"  Root folder: {FILEZILLA_ROOT_DIR}")
    log(f"  User:        {FILEZILLA_USERNAME}")
    log(
        "  Listener:    Explicit FTP over TLS and insecure plain FTP"
    )
    log(
        f"  Admin port:  {FILEZILLA_ADMIN_PORT}"
    )
    log("  Firewall:    Private networks only")
    log("  Service:     LocalSystem, Manual, and running after setup")

    if DRY_RUN:
        log("[DRY RUN] FileZilla configuration was not changed.")
        return

    FILEZILLA_CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stop_and_configure_filezilla_service()
    ensure_filezilla_root_directory()
    ensure_filezilla_config_access()

    if (
        not FILEZILLA_SETTINGS_FILE.is_file()
        or FILEZILLA_SETTINGS_FILE.stat().st_size == 0
    ):
        cycle_filezilla_service(
            wait_for_settings=True,
            display_name="Initialize FileZilla configuration",
        )
        ensure_filezilla_config_access()

    password_data = generate_filezilla_password_data(
        FILEZILLA_USERNAME,
        FILEZILLA_PASSWORD,
    )
    write_filezilla_user_configuration(
        FILEZILLA_USERNAME,
        password_data,
    )
    generated_admin_password = configure_filezilla_server_settings()
    configure_filezilla_firewall()
    remove_filezilla_desktop_shortcuts()
    disable_filezilla_admin_autostart()
    start_filezilla_service()

    if generated_admin_password is not None:
        queue_filezilla_admin_password(generated_admin_password)

    log(
        "[OK] FileZilla root, user, listeners, firewall, and "
        "Manual service startup were configured; the service is running."
    )


def install_filezilla() -> str:
    """Install and configure FileZilla Server."""

    result = install_and_verify(
        FILEZILLA_NAME,
        detect_filezilla_document_install,
        install_filezilla_action,
    )

    configure_filezilla()

    if DRY_RUN:
        return f"{result}; WTG FileZilla configuration would be applied"

    return (
        f"{result}; WTG FileZilla configuration applied"
    )


def filezilla_cleanup_present() -> bool:
    """Return True when a known FileZilla directory remains."""

    return any(
        path.exists()
        for path in FILEZILLA_CLEANUP_DIRS
    )


def cleanup_filezilla_directories() -> None:
    """Remove known FileZilla program, log, and data directories."""

    for path in FILEZILLA_CLEANUP_DIRS:
        if not path.exists():
            continue

        if DRY_RUN:
            log(f"[DRY RUN] Would remove {path}")
            continue

        log(f"Removing FileZilla residual directory: {path}")

        for attempt in range(1, FILE_CLEANUP_ATTEMPTS + 1):
            try:
                shutil.rmtree(path)
                break

            except FileNotFoundError:
                break

            except OSError as error:
                if attempt == FILE_CLEANUP_ATTEMPTS:
                    raise RuntimeError(
                        "Could not remove FileZilla residual "
                        f"directory {path} after "
                        f"{FILE_CLEANUP_ATTEMPTS} attempts: "
                        f"{error}"
                    ) from error

                log(
                    "[WAITING] FileZilla is still releasing "
                    f"files in {path}; retrying cleanup "
                    f"({attempt}/{FILE_CLEANUP_ATTEMPTS})."
                )
                time.sleep(
                    FILE_CLEANUP_RETRY_DELAY_SECONDS
                )


def uninstall_filezilla_action() -> int:
    """Uninstall FileZilla Server and remove its residual files."""

    command, detail, quiet_registered = find_uninstall_command(
        [r"^FileZilla Server(?:\s|$)"],
    )

    exit_code = SUCCESS_EXIT_CODE

    if command is not None:
        log(f"Registered application: {detail}")
        prepared = prepare_uninstall_command(
            command,
            quiet_registered,
            ["/S"],
        )
        exit_code = run_command(
            f"{FILEZILLA_NAME} uninstaller",
            prepared,
            working_directory=Path(prepared[0]).parent,
        )

    else:
        log(
            "No registered FileZilla uninstaller remains; "
            "continuing with residual cleanup."
        )

    cleanup_filezilla_directories()
    remove_filezilla_firewall_rule()
    remove_filezilla_desktop_shortcuts()
    disable_filezilla_admin_autostart()
    return exit_code


def uninstall_filezilla() -> str:
    """Uninstall FileZilla Server and clean known leftovers."""

    installed, _detail = detect_filezilla()

    if not installed and not filezilla_cleanup_present():
        return f"[SKIPPED] {FILEZILLA_NAME} is not installed"

    if DRY_RUN:
        uninstall_filezilla_action()
        return f"[DRY RUN] {FILEZILLA_NAME} would be uninstalled"

    exit_code = uninstall_filezilla_action()
    removed, remaining_detail = wait_for_absence(
        detect_filezilla
    )

    if not removed:
        raise RuntimeError(
            f"{FILEZILLA_NAME} is still detected "
            f"({remaining_detail})."
        )

    remaining_paths = [
        path
        for path in FILEZILLA_CLEANUP_DIRS
        if path.exists()
    ]

    if remaining_paths:
        raise RuntimeError(
            "FileZilla cleanup did not remove: "
            + ", ".join(
                str(path)
                for path in remaining_paths
            )
        )

    restart = (
        "; Windows restart required"
        if exit_code in RESTART_EXIT_CODES
        else ""
    )

    return (
        f"[OK] {FILEZILLA_NAME} uninstalled and cleaned up "
        f"successfully{restart}"
    )


# ============================================================
# WinSCP — always all users
# ============================================================

def install_winscp_action() -> int:
    """Install WinSCP silently for all users."""

    installer = require_file(
        WINSCP_INSTALLER_NAME,
        [
            "winscp.exe",
            "WinSCP_*.msi",
            "WinSCP-*-Setup.exe",
            "WinSCP*Setup*.exe",
            "WinSCP_*_User_*_inno_*.exe",
            "WinSCP*.exe",
        ],
    )

    validate_file(
        installer,
        WINSCP_INSTALLER_NAME,
    )

    installer_log = (
        LOG_DIR
        / "WinSCP-Setup.log"
    )

    if installer.suffix.lower() == ".msi":
        command = [
            "msiexec.exe",
            "/i",
            installer,
            "/qn",
            "/norestart",
            "ALLUSERS=1",
            "REBOOT=ReallySuppress",
            "/L*v",
            installer_log,
        ]

    else:
        command = [
            installer,
            "/SP-",
            "/VERYSILENT",
            "/ALLUSERS",
            "/NORESTART",
            f"/LOG={installer_log}",
        ]

    log("WinSCP installation mode: all users")

    return run_command(
        WINSCP_INSTALLER_NAME,
        command,
        working_directory=installer.parent,
        installer_log=installer_log,
    )


def install_winscp() -> str:
    """Install WinSCP for all users."""

    return install_and_verify(
        WINSCP_NAME,
        detect_winscp,
        install_winscp_action,
    )


def stop_winscp_processes() -> None:
    """Stop WinSCP before uninstalling files that it may have locked."""

    if DRY_RUN:
        log(
            f"[DRY RUN] Would stop running {WINSCP_NAME} processes"
        )
        return

    process_name = powershell_quote(WINSCP_PROCESS_NAME)
    stop_timeout = WINSCP_PROCESS_STOP_TIMEOUT_SECONDS
    script = (
        "$ErrorActionPreference='Stop';"
        f"$processes=@(Get-Process -Name '{process_name}' "
        "-ErrorAction SilentlyContinue);"
        "if ($processes.Count -gt 0) {"
        "$processIds=@($processes.Id);"
        "$processes | Stop-Process -Force -ErrorAction SilentlyContinue;"
        f"$deadline=(Get-Date).AddSeconds({stop_timeout});"
        "while (@(Get-Process -Id $processIds "
        "-ErrorAction SilentlyContinue).Count -gt 0) {"
        "if ((Get-Date) -ge $deadline) {"
        "throw 'WinSCP is still running and could not be closed';"
        "}"
        "Start-Sleep -Milliseconds 200;"
        "}"
        "}"
    )

    run_command(
        "Close WinSCP before uninstall",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        success_codes={SUCCESS_EXIT_CODE},
    )


def schedule_delete_on_restart(path: Path) -> None:
    """Ask Windows to delete a locked file or directory on restart."""

    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    move_file_ex = kernel32.MoveFileExW
    move_file_ex.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_uint32,
    ]
    move_file_ex.restype = ctypes.c_int

    if not move_file_ex(
        str(path),
        None,
        MOVEFILE_DELAY_UNTIL_REBOOT,
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    log(f"[RESTART REQUIRED] Scheduled removal of {path}")


def schedule_winscp_directory_cleanup(path: Path) -> None:
    """Delete unlocked WinSCP remnants and schedule locked ones."""

    try:
        entries = sorted(
            path.rglob("*"),
            key=lambda entry: len(entry.parts),
            reverse=True,
        )

    except OSError as error:
        raise RuntimeError(
            f"Could not enumerate WinSCP residual directory {path}: "
            f"{error}"
        ) from error

    for entry in entries:
        try:
            if entry.is_dir() and not entry.is_symlink():
                entry.rmdir()

            else:
                entry.unlink(missing_ok=True)

        except FileNotFoundError:
            continue

        except OSError:
            schedule_delete_on_restart(entry)

    try:
        path.rmdir()

    except FileNotFoundError:
        return

    except OSError:
        schedule_delete_on_restart(path)


def cleanup_winscp_directories() -> bool:
    """Remove WinSCP directories, scheduling locked shell files."""

    restart_required = False

    for path in WINSCP_INSTALL_DIRS:
        if not path.exists():
            continue

        if DRY_RUN:
            log(f"[DRY RUN] Would remove {path}")
            continue

        log(f"Removing WinSCP residual directory: {path}")

        for attempt in range(1, WINSCP_FILE_CLEANUP_ATTEMPTS + 1):
            try:
                shutil.rmtree(path)
                break

            except FileNotFoundError:
                break

            except OSError as error:
                if attempt == WINSCP_FILE_CLEANUP_ATTEMPTS:
                    log(
                        "[WAITING FOR RESTART] Windows is using part "
                        f"of {path}; scheduling the locked remnants "
                        "for removal on restart."
                    )
                    schedule_winscp_directory_cleanup(path)
                    restart_required = True
                    break

                log(
                    "[WAITING] WinSCP is still releasing files in "
                    f"{path}; retrying cleanup "
                    f"({attempt}/{WINSCP_FILE_CLEANUP_ATTEMPTS})."
                )
                time.sleep(FILE_CLEANUP_RETRY_DELAY_SECONDS)

    return restart_required


def uninstall_winscp_action() -> tuple[int, bool]:
    """Uninstall WinSCP and remove files left by a running client."""

    stop_winscp_processes()

    command, detail, quiet_registered = find_uninstall_command(
        [r"^WinSCP(?:\s|$)"],
        [
            r"\.NET Assembly",
            r"Automation",
        ],
        include_current_user=False,
    )
    exit_code = SUCCESS_EXIT_CODE

    if command is not None:
        log(f"Registered application: {detail}")
        prepared = prepare_uninstall_command(
            command,
            quiet_registered,
            [
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
            ],
        )
        exit_code = run_command(
            f"{WINSCP_NAME} uninstaller",
            prepared,
            working_directory=Path(prepared[0]).parent,
        )

    else:
        log(
            "No registered WinSCP uninstaller remains; "
            "continuing with residual cleanup."
        )

    restart_required = cleanup_winscp_directories()
    return (
        exit_code,
        restart_required,
    )


def uninstall_winscp() -> str:
    """Uninstall machine-wide WinSCP and clean known leftovers."""

    installed, _detail = detect_winscp()

    if not installed and not any(
        path.exists()
        for path in WINSCP_INSTALL_DIRS
    ):
        return f"[SKIPPED] {WINSCP_NAME} is not installed"

    if DRY_RUN:
        uninstall_winscp_action()
        return f"[DRY RUN] {WINSCP_NAME} would be uninstalled"

    exit_code, cleanup_restart_required = uninstall_winscp_action()
    removed, remaining_detail = wait_for_absence(detect_winscp)

    if not removed:
        registered, registered_detail = detect_winscp_registry()

        if registered or not cleanup_restart_required:
            detail = registered_detail or remaining_detail
            raise RuntimeError(
                f"{WINSCP_NAME} is still detected ({detail})."
            )

    remaining_paths = [
        path
        for path in WINSCP_INSTALL_DIRS
        if path.exists()
    ]

    if remaining_paths and not cleanup_restart_required:
        raise RuntimeError(
            "WinSCP cleanup did not remove: "
            + ", ".join(
                str(path)
                for path in remaining_paths
            )
        )

    restart = (
        "; Windows restart required"
        if (
            exit_code in RESTART_EXIT_CODES
            or cleanup_restart_required
        )
        else ""
    )

    return (
        f"[OK] {WINSCP_NAME} uninstalled and cleaned up "
        f"successfully{restart}"
    )


# ============================================================
# Paessler SNMP Tester
# ============================================================

def install_paessler_action() -> int:
    """Install Paessler SNMP Tester silently."""

    installer = require_file(
        PAESSLER_INSTALLER_NAME,
        [
            "Passler-snmp.exe",
            "Paessler SNMP Tester Setup.exe",
            "*SNMP*Tester*Setup*.exe",
        ],
    )

    validate_file(
        installer,
        PAESSLER_INSTALLER_NAME,
    )

    installer_log = (
        LOG_DIR
        / "Paessler-SNMP-Tester-Setup.log"
    )

    command = [
        installer,
        "/SP-",
        "/VERYSILENT",
        "/NORESTART",
        f"/LOG={installer_log}",
    ]

    return run_command(
        PAESSLER_INSTALLER_NAME,
        command,
        working_directory=installer.parent,
        installer_log=installer_log,
    )


def install_paessler() -> str:
    """Install Paessler SNMP Tester."""

    return install_and_verify(
        PAESSLER_NAME,
        detect_paessler,
        install_paessler_action,
    )


def uninstall_paessler() -> str:
    """Uninstall Paessler SNMP Tester."""

    return uninstall_and_verify(
        PAESSLER_NAME,
        detect_paessler,
        lambda: uninstall_registered_application(
            PAESSLER_NAME,
            [
                r"Paessler.*SNMP.*Tester",
                r"^SNMP Tester(?:\s|$)",
            ],
            [
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
            ],
        ),
    )


# ============================================================
# mRemoteNG — all users MSI
# ============================================================

def install_mremoteng_action() -> int:
    """Install mRemoteNG silently for all users."""

    installer = require_file(
        MREMOTENG_INSTALLER_NAME,
        [
            "Remoteng.msi",
            "mRemoteNG*.msi",
        ],
    )

    validate_file(
        installer,
        MREMOTENG_INSTALLER_NAME,
    )

    installer_log = (
        LOG_DIR
        / "mRemoteNG-Setup.log"
    )

    command = [
        "msiexec.exe",
        "/i",
        installer,
        "/qn",
        "/norestart",
        "ALLUSERS=1",
        "REBOOT=ReallySuppress",
        "/L*v",
        installer_log,
    ]

    log("mRemoteNG installation mode: all users")

    return run_command(
        MREMOTENG_INSTALLER_NAME,
        command,
        working_directory=installer.parent,
        installer_log=installer_log,
    )


def install_mremoteng() -> str:
    """Install mRemoteNG for all users."""

    return install_and_verify(
        MREMOTENG_NAME,
        detect_mremoteng,
        install_mremoteng_action,
    )


def uninstall_mremoteng() -> str:
    """Uninstall mRemoteNG."""

    return uninstall_and_verify(
        MREMOTENG_NAME,
        detect_mremoteng,
        lambda: uninstall_registered_application(
            MREMOTENG_NAME,
            [r"^mRemoteNG(?:\s|$)"],
            [],
        ),
    )


# ============================================================
# PuTTY portable deployment
# ============================================================

def powershell_quote(
    value: object,
) -> str:
    """Escape a PowerShell single-quoted string."""

    return str(value).replace(
        "'",
        "''",
    )


def install_putty_action() -> int:
    """Copy PuTTY and create a Start Menu shortcut."""

    source = require_file(
        PUTTY_EXECUTABLE_NAME,
        [
            "putty-portable.exe",
            "putty.exe",
        ],
    )

    validate_file(
        source,
        PUTTY_EXECUTABLE_NAME,
    )

    log(
        f"Copying PuTTY from {source} to {PUTTY_EXE}"
    )

    if DRY_RUN:
        return 0

    PUTTY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        PUTTY_EXE,
    )

    PUTTY_SHORTCUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    powershell_script = (
        "$shell=New-Object -ComObject WScript.Shell;"
        "$shortcut=$shell.CreateShortcut("
        f"'{powershell_quote(PUTTY_SHORTCUT)}'"
        ");"
        "$shortcut.TargetPath="
        f"'{powershell_quote(PUTTY_EXE)}';"
        "$shortcut.WorkingDirectory="
        f"'{powershell_quote(PUTTY_DIR)}';"
        "$shortcut.Description="
        "'PuTTY SSH and Telnet client';"
        "$shortcut.Save();"
    )

    run_command(
        "PuTTY Start Menu shortcut",
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            powershell_script,
        ],
        success_codes={
            0,
        },
    )

    if not PUTTY_EXE.is_file():
        raise RuntimeError(
            f"PuTTY was not copied to {PUTTY_EXE}"
        )

    return 0


def install_putty() -> str:
    """Deploy PuTTY."""

    return install_and_verify(
        PUTTY_NAME,
        detect_putty,
        install_putty_action,
    )


def uninstall_putty_action() -> int:
    """Remove registered and portable PuTTY installations."""

    command, detail, quiet_registered = find_uninstall_command(
        [r"^PuTTY(?:\s|$)"],
    )

    exit_code = SUCCESS_EXIT_CODE

    if command is not None:
        log(f"Registered application: {detail}")
        prepared = prepare_uninstall_command(
            command,
            quiet_registered,
            ["/S"],
        )
        exit_code = run_command(
            f"{PUTTY_NAME} uninstaller",
            prepared,
            working_directory=Path(prepared[0]).parent,
        )

    if DRY_RUN:
        log(f"[DRY RUN] Would remove {PUTTY_EXE}")
        log(f"[DRY RUN] Would remove {PUTTY_SHORTCUT}")
        return exit_code

    for path in (
        PUTTY_SHORTCUT,
        PUTTY_EXE,
    ):
        try:
            path.unlink(missing_ok=True)

        except OSError as error:
            raise RuntimeError(
                f"Could not remove {path}: {error}"
            ) from error

    try:
        PUTTY_DIR.rmdir()

    except FileNotFoundError:
        pass

    except OSError:
        # Preserve the directory if it contains unrelated files.
        pass

    return exit_code


def uninstall_putty() -> str:
    """Uninstall PuTTY."""

    return uninstall_and_verify(
        PUTTY_NAME,
        detect_putty,
        uninstall_putty_action,
    )


# ============================================================
# GUI
# ============================================================

APPLICATIONS: list[
    tuple[
        str,
        Callable[[], str],
        Callable[[], str],
        bool,
    ]
] = [
    (
        FILEZILLA_NAME,
        install_filezilla,
        uninstall_filezilla,
        False,
    ),
    (
        WINSCP_NAME,
        install_winscp,
        uninstall_winscp,
        False,
    ),
    (
        PAESSLER_NAME,
        install_paessler,
        uninstall_paessler,
        False,
    ),
    (
        MREMOTENG_NAME,
        install_mremoteng,
        uninstall_mremoteng,
        False,
    ),
    (
        PUTTY_NAME,
        install_putty,
        uninstall_putty,
        False,
    ),
]


class InstallerGUI:
    """Checkbox-based GUI for the software installer."""

    def __init__(
        self,
        root: tk.Tk,
    ) -> None:
        global LOG_QUEUE

        self.root = root

        self.root.title(
            GUI_TITLE
        )

        self.root.geometry(
            GUI_GEOMETRY
        )

        self.root.minsize(
            *GUI_MINIMUM_SIZE,
        )

        self.root.configure(
            background=THEME_BACKGROUND
        )

        self.configure_theme()
        self.header_image = self.load_header_image()

        self.queue: queue.Queue = queue.Queue()
        LOG_QUEUE = self.queue

        self.running = False

        self.app_vars: dict[
            str,
            tk.BooleanVar,
        ] = {}

        self.app_checks: list[
            ttk.Checkbutton
        ] = []

        self.uninstall_var = tk.BooleanVar(
            value=False
        )

        self.action_button_text = tk.StringVar(
            value="Install Selected"
        )

        self.status_var = tk.StringVar(
            value=(
                "Select applications, then "
                "click Install Selected."
            )
        )

        self.build_ui()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

        self.root.after(
            GUI_QUEUE_POLL_INTERVAL_MS,
            self.process_queue,
        )

        self.append_output(
            f"{GUI_TITLE} ready."
        )

        self.append_output(
            f"Source folder: {SOFTWARE_DIR}"
        )

        self.append_output(
            "WinSCP and mRemoteNG operations apply to all-users "
            "installations."
        )

    def configure_theme(self) -> None:
        """Configure the Winslow-inspired dark ttk theme."""

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        self.style.configure(
            ".",
            background=THEME_BACKGROUND,
            foreground=THEME_TEXT,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "TFrame",
            background=THEME_BACKGROUND,
        )
        self.style.configure(
            "Header.TFrame",
            background=THEME_BACKGROUND,
        )
        self.style.configure(
            "TLabel",
            background=THEME_BACKGROUND,
            foreground=THEME_TEXT,
        )
        self.style.configure(
            "Muted.TLabel",
            background=THEME_BACKGROUND,
            foreground=THEME_MUTED_TEXT,
        )
        self.style.configure(
            "HeaderTitle.TLabel",
            background=THEME_BACKGROUND,
            foreground=THEME_TEXT,
            font=("Segoe UI", 20, "bold"),
        )
        self.style.configure(
            "Card.TFrame",
            background=THEME_PANEL,
        )
        self.style.configure(
            "SectionTitle.TLabel",
            background=THEME_BACKGROUND,
            foreground=THEME_ACCENT,
            font=("Segoe UI", 10, "bold"),
        )

        self.create_checkbox_images()
        self.style.element_create(
            "Winslow.Checkbutton.indicator",
            "image",
            self.checkbox_unchecked_image,
            (
                "disabled",
                "selected",
                self.checkbox_checked_disabled_image,
            ),
            (
                "selected",
                self.checkbox_checked_image,
            ),
            (
                "disabled",
                self.checkbox_disabled_image,
            ),
            border=0,
            sticky="",
        )
        self.style.layout(
            "Winslow.TCheckbutton",
            [
                (
                    "Checkbutton.padding",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "Winslow.Checkbutton.indicator",
                                {
                                    "side": "left",
                                    "sticky": "",
                                },
                            ),
                            (
                                "Checkbutton.focus",
                                {
                                    "side": "left",
                                    "sticky": "w",
                                    "children": [
                                        (
                                            "Checkbutton.label",
                                            {
                                                "sticky": "nswe",
                                            },
                                        ),
                                    ],
                                },
                            ),
                        ],
                    },
                ),
            ],
        )
        self.style.configure(
            "Winslow.TCheckbutton",
            background=THEME_PANEL,
            foreground=THEME_TEXT,
            padding=4,
        )
        self.style.map(
            "Winslow.TCheckbutton",
            background=[
                ("active", THEME_PANEL),
            ],
            foreground=[
                ("disabled", THEME_MUTED_TEXT),
                ("active", THEME_TEXT),
            ],
        )
        self.style.configure(
            "TButton",
            background=THEME_SURFACE,
            foreground=THEME_TEXT,
            bordercolor=THEME_BORDER,
            focuscolor=THEME_BORDER,
            padding=(12, 7),
        )
        self.style.map(
            "TButton",
            background=[
                ("active", THEME_BORDER),
                ("disabled", THEME_PANEL),
            ],
            foreground=[
                ("disabled", THEME_MUTED_TEXT),
            ],
        )
        self.style.configure(
            "Accent.TButton",
            background=THEME_ACCENT,
            foreground=THEME_BACKGROUND,
            bordercolor=THEME_ACCENT,
            focuscolor=THEME_ACCENT,
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "Accent.TButton",
            background=[
                ("active", THEME_ACCENT_ACTIVE),
                ("disabled", THEME_PANEL),
            ],
            foreground=[
                ("disabled", THEME_MUTED_TEXT),
            ],
        )
        self.style.configure(
            "Danger.TButton",
            background=THEME_DANGER,
            foreground=THEME_TEXT,
            bordercolor=THEME_DANGER,
            focuscolor=THEME_DANGER,
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "Danger.TButton",
            background=[
                ("active", THEME_DANGER_ACTIVE),
                ("disabled", THEME_PANEL),
            ],
            foreground=[
                ("disabled", THEME_MUTED_TEXT),
            ],
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            background=THEME_ACCENT,
            troughcolor=THEME_SURFACE,
            bordercolor=THEME_BORDER,
            lightcolor=THEME_ACCENT,
            darkcolor=THEME_ACCENT,
        )

    def create_checkbox_images(self) -> None:
        """Create checkbox indicators that use checkmarks, not Xs."""

        def indicator(
            selected: bool,
            disabled: bool = False,
        ) -> tk.PhotoImage:
            image = tk.PhotoImage(
                master=self.root,
                width=GUI_CHECKBOX_SIZE,
                height=GUI_CHECKBOX_SIZE,
            )
            border_color = (
                THEME_MUTED_TEXT
                if disabled
                else THEME_ACCENT
            )
            fill_color = (
                THEME_BORDER
                if disabled
                else (
                    THEME_ACCENT
                    if selected
                    else THEME_SURFACE
                )
            )
            image.put(
                border_color,
                to=(
                    0,
                    0,
                    GUI_CHECKBOX_SIZE,
                    GUI_CHECKBOX_SIZE,
                ),
            )
            image.put(
                fill_color,
                to=(
                    1,
                    1,
                    GUI_CHECKBOX_SIZE - 1,
                    GUI_CHECKBOX_SIZE - 1,
                ),
            )

            if selected:
                check_color = (
                    THEME_MUTED_TEXT
                    if disabled
                    else THEME_TEXT
                )
                check_points = [
                    (3, 8),
                    (4, 9),
                    (5, 10),
                    (6, 11),
                    (7, 12),
                    (8, 11),
                    (9, 10),
                    (10, 9),
                    (11, 8),
                    (12, 7),
                    (13, 6),
                ]

                for x, y in check_points:
                    image.put(
                        check_color,
                        to=(x, y, x + 2, y + 2),
                    )

            return image

        self.checkbox_unchecked_image = indicator(False)
        self.checkbox_checked_image = indicator(True)
        self.checkbox_disabled_image = indicator(
            False,
            disabled=True,
        )
        self.checkbox_checked_disabled_image = indicator(
            True,
            disabled=True,
        )

    def load_header_image(self) -> Optional[tk.PhotoImage]:
        """Load and scale the branded security header image."""

        if not HEADER_IMAGE_PATH.is_file():
            return None

        try:
            source = tk.PhotoImage(
                master=self.root,
                file=str(HEADER_IMAGE_PATH),
            )
            divisor = max(
                1,
                (
                    source.width()
                    + GUI_HEADER_MAX_WIDTH
                    - 1
                )
                // GUI_HEADER_MAX_WIDTH,
            )
            return source.subsample(
                divisor,
                divisor,
            )

        except tk.TclError:
            return None

    def build_ui(self) -> None:
        """Create the installer window."""

        outer = ttk.Frame(
            self.root,
            padding=12,
        )

        outer.pack(
            fill="both",
            expand=True,
        )

        header = ttk.Frame(
            outer,
            style="Header.TFrame",
        )
        header.pack(
            fill="x",
            pady=(0, 12),
        )

        if self.header_image is not None:
            tk.Label(
                header,
                image=self.header_image,
                background=THEME_BACKGROUND,
                borderwidth=0,
                highlightthickness=0,
            ).pack(
                anchor="center"
            )

        else:
            ttk.Label(
                header,
                text=GUI_TITLE,
                style="HeaderTitle.TLabel",
            ).pack(
                anchor="w",
                padx=8,
                pady=12,
            )

        ttk.Label(
            outer,
            text=(
                "Choose the applications to install, or enable "
                "uninstall mode to remove the selected applications."
            ),
            style="Muted.TLabel",
            wraplength=820,
        ).pack(
            anchor="w",
            pady=(
                2,
                12,
            ),
        )

        ttk.Label(
            outer,
            text="Applications",
            style="SectionTitle.TLabel",
        ).pack(
            anchor="w",
        )

        app_frame = tk.Frame(
            outer,
            background=THEME_PANEL,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=THEME_BORDER,
            highlightcolor=THEME_BORDER,
            padx=10,
            pady=10,
        )

        app_frame.pack(
            fill="x",
            pady=(3, 0),
        )

        for column in range(GUI_APPLICATION_COLUMNS):
            app_frame.columnconfigure(
                column,
                weight=1,
                uniform="applications",
            )

        for (
            index,
            (
                name,
                _install_function,
                _uninstall_function,
                selected,
            ),
        ) in enumerate(
            APPLICATIONS
        ):
            variable = tk.BooleanVar(
                value=selected
            )

            self.app_vars[name] = variable

            check = ttk.Checkbutton(
                app_frame,
                text=name,
                variable=variable,
                style="Winslow.TCheckbutton",
            )

            check.grid(
                row=index // GUI_APPLICATION_COLUMNS,
                column=index % GUI_APPLICATION_COLUMNS,
                sticky="w",
                padx=(
                    0,
                    24,
                ),
                pady=3,
            )

            self.app_checks.append(check)

        ttk.Label(
            outer,
            text="Options",
            style="SectionTitle.TLabel",
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        option_frame = tk.Frame(
            outer,
            background=THEME_PANEL,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=THEME_BORDER,
            highlightcolor=THEME_BORDER,
            padx=10,
            pady=10,
        )

        option_frame.pack(
            fill="x",
            pady=(3, 0),
        )

        self.uninstall_check = ttk.Checkbutton(
            option_frame,
            text=(
                "Uninstall selected applications instead of "
                "installing them"
            ),
            variable=self.uninstall_var,
            command=self.update_operation_ui,
            style="Winslow.TCheckbutton",
        )

        self.uninstall_check.pack(
            anchor="w"
        )

        buttons = ttk.Frame(
            outer
        )

        buttons.pack(
            fill="x",
            pady=10,
        )

        for column in range(5):
            buttons.columnconfigure(
                column,
                weight=0,
                minsize=GUI_BUTTON_COLUMN_WIDTH,
            )

        buttons.grid_anchor("center")

        self.all_button = ttk.Button(
            buttons,
            text="Select All",
            command=self.select_all,
        )

        self.all_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=GUI_BUTTON_GAP,
        )

        self.clear_button = ttk.Button(
            buttons,
            text="Unselect All",
            command=self.clear_all,
        )

        self.clear_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=GUI_BUTTON_GAP,
        )

        self.install_button = ttk.Button(
            buttons,
            textvariable=self.action_button_text,
            command=self.start_installation,
            style="Accent.TButton",
        )

        self.install_button.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=GUI_BUTTON_GAP,
        )

        self.logs_button = ttk.Button(
            buttons,
            text="Open Logs Folder",
            command=self.open_logs,
        )

        self.logs_button.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=GUI_BUTTON_GAP,
        )

        self.close_button = ttk.Button(
            buttons,
            text="Close",
            command=self.close,
        )

        self.close_button.grid(
            row=0,
            column=4,
            sticky="ew",
            padx=GUI_BUTTON_GAP,
        )

        self.progress = ttk.Progressbar(
            outer,
            mode="determinate",
            maximum=1,
            value=0,
        )

        self.progress.pack(
            fill="x"
        )

        ttk.Label(
            outer,
            textvariable=self.status_var,
        ).pack(
            anchor="w",
            pady=(
                4,
                8,
            ),
        )

        ttk.Label(
            outer,
            text="Installation output",
            style="SectionTitle.TLabel",
        ).pack(
            anchor="w",
        )

        output_frame = tk.Frame(
            outer,
            background=THEME_PANEL,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=THEME_BORDER,
            highlightcolor=THEME_BORDER,
            padx=6,
            pady=6,
        )

        output_frame.pack(
            fill="both",
            expand=True,
            pady=(3, 0),
        )

        self.output = ScrolledText(
            output_frame,
            wrap="word",
            font=(
                "Consolas",
                10,
            ),
            background=THEME_OUTPUT_BACKGROUND,
            foreground=THEME_TEXT,
            insertbackground=THEME_ACCENT,
            selectbackground=THEME_ACCENT,
            selectforeground=THEME_BACKGROUND,
            borderwidth=0,
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME_BORDER,
            highlightcolor=THEME_ACCENT,
            state="disabled",
        )

        self.output.pack(
            fill="both",
            expand=True,
        )

    def append_output(
        self,
        line: str,
    ) -> None:
        """Add a line to the GUI output pane."""

        self.output.configure(
            state="normal"
        )

        self.output.insert(
            "end",
            line + "\n",
        )

        self.output.see("end")

        self.output.configure(
            state="disabled"
        )

    def select_all(self) -> None:
        """Select every application."""

        for variable in self.app_vars.values():
            variable.set(True)

    def clear_all(self) -> None:
        """Unselect every application."""

        for variable in self.app_vars.values():
            variable.set(False)

    def update_operation_ui(self) -> None:
        """Update labels when install or uninstall mode changes."""

        uninstalling = self.uninstall_var.get()
        operation = (
            "Uninstall"
            if uninstalling
            else "Install"
        )

        self.action_button_text.set(
            f"{operation} Selected"
        )

        self.install_button.configure(
            style=(
                "Danger.TButton"
                if uninstalling
                else "Accent.TButton"
            )
        )

        self.status_var.set(
            "Select applications, then click "
            f"{operation} Selected."
        )

    def selected_jobs(
        self,
        uninstalling: bool,
    ) -> list[
        tuple[
            str,
            Callable[[], str],
        ]
    ]:
        """Return only the checked applications."""

        return [
            (
                name,
                (
                    uninstall_function
                    if uninstalling
                    else install_function
                ),
            )
            for (
                name,
                install_function,
                uninstall_function,
                _default,
            ) in APPLICATIONS
            if self.app_vars[name].get()
        ]

    def enable_controls(
        self,
        enabled: bool,
    ) -> None:
        """Enable or disable installer controls."""

        state = (
            "normal"
            if enabled
            else "disabled"
        )

        for widget in self.app_checks:
            widget.configure(
                state=state
            )

        for widget in (
            self.uninstall_check,
            self.all_button,
            self.clear_button,
            self.install_button,
        ):
            widget.configure(
                state=state
            )

    def start_installation(self) -> None:
        """Start selected operations in a worker thread."""

        if self.running:
            return

        uninstalling = self.uninstall_var.get()
        selected = self.selected_jobs(uninstalling)

        if not selected:
            messagebox.showwarning(
                "Nothing selected",
                "Select at least one application.",
                parent=self.root,
            )
            return

        if uninstalling:
            selected_names = "\n".join(
                f"  - {name}"
                for name, _function in selected
            )
            filezilla_data_warning = ""

            if any(
                name == FILEZILLA_NAME
                for name, _function in selected
            ):
                filezilla_data_warning = (
                    "\n\nWARNING: Uninstalling FileZilla Server will "
                    "permanently delete its FTP root folder and all "
                    f"contents:\n{FILEZILLA_ROOT_DIR}"
                )

            confirmed = messagebox.askyesno(
                "Confirm uninstall",
                (
                    "Uninstall these applications?\n\n"
                    f"{selected_names}"
                    f"{filezilla_data_warning}"
                ),
                icon="warning",
                parent=self.root,
            )

            if not confirmed:
                return

        self.running = True
        self.enable_controls(False)

        self.progress.configure(
            maximum=len(selected),
            value=0,
        )

        self.status_var.set(
            "Starting selected "
            f"{'uninstallations' if uninstalling else 'installations'}..."
        )

        threading.Thread(
            target=self.operation_worker,
            args=(
                selected,
                uninstalling,
            ),
            daemon=True,
        ).start()

    def operation_worker(
        self,
        selected: list[
            tuple[
                str,
                Callable[[], str],
            ]
        ],
        uninstalling: bool,
    ) -> None:
        """Install or uninstall the selected applications."""

        global MASTER_LOG

        LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        MASTER_LOG = (
            LOG_DIR
            / MASTER_LOG_FILENAME_FORMAT.format(
                operation=(
                    "Uninstall"
                    if uninstalling
                    else "Install"
                ),
                timestamp=datetime.now().strftime(
                    MASTER_LOG_TIMESTAMP_FORMAT
                )
            )
        )

        results: list[str] = []
        failures: list[str] = []

        log()
        log("=" * 76)
        operation_name = (
            "UNINSTALLER"
            if uninstalling
            else "INSTALLER"
        )

        log(f"WTG SAFE SILENT SOFTWARE {operation_name}")
        log("=" * 76)
        log(f"Source folder:         {SOFTWARE_DIR}")
        log(f"Master log:            {MASTER_LOG}")
        log(
            "Operation:             "
            f"{'Uninstall' if uninstalling else 'Install'}"
        )
        log("Selected applications:")

        for (
            name,
            _function,
        ) in selected:
            log(f"  - {name}")

        for (
            index,
            (
                name,
                function,
            ),
        ) in enumerate(
            selected,
            start=1,
        ):
            self.queue.put(
                (
                    "progress",
                    index - 1,
                    name,
                )
            )

            try:
                log()
                log("-" * 76)
                log(f"[STARTING] {name}")

                started = time.monotonic()
                result = function()
                elapsed = (
                    time.monotonic()
                    - started
                )

                result = (
                    f"{result} "
                    f"[elapsed: {elapsed:.1f}s]"
                )

                results.append(result)
                log(result)

            except Exception as error:
                failure = (
                    f"[FAILED] {name}: {error}"
                )

                failures.append(failure)
                log(failure)
                log(traceback.format_exc())

            self.queue.put(
                (
                    "progress",
                    index,
                    name,
                )
            )

        log()
        log("=" * 76)
        log("INSTALLATION SUMMARY")
        log("=" * 76)
        log(
            "Completed or skipped: "
            f"{len(results)}"
        )
        log(
            f"Failed:               {len(failures)}"
        )
        log()

        for result in results:
            log(result)

        for failure in failures:
            log(failure)

        log()
        log(f"Detailed log: {MASTER_LOG}")

        if failures:
            log(
                "One or more operations failed. "
                "Successful operations were not rolled back."
            )

        else:
            log(
                "Finished without operation failures."
            )

        self.queue.put(
            (
                "done",
                1 if failures else 0,
                len(results),
                len(failures),
                str(MASTER_LOG),
                uninstalling,
            )
        )

    def process_queue(self) -> None:
        """Process messages from the installation worker."""

        try:
            while True:
                item = self.queue.get_nowait()
                event = item[0]

                if event == "log":
                    self.append_output(
                        item[1]
                    )

                elif event == "credential":
                    password = item[2]
                    self.root.clipboard_clear()
                    self.root.clipboard_append(password)
                    self.root.update_idletasks()

                    messagebox.showwarning(
                        item[1],
                        (
                            "A new FileZilla administration password "
                            "was generated:\n\n"
                            f"{password}\n\n"
                            "It has been copied to the clipboard. Save "
                            "it in the approved password system before "
                            "closing this message. The password is not "
                            "written to the installer log."
                        ),
                        parent=self.root,
                    )

                elif event == "progress":
                    self.progress.configure(
                        value=item[1]
                    )

                    self.status_var.set(
                        f"Processing: {item[2]}"
                    )

                elif event == "done":
                    (
                        exit_code,
                        completed,
                        failed,
                        log_path,
                        uninstalling,
                    ) = item[1:]

                    self.running = False
                    self.enable_controls(True)

                    if exit_code == 0:
                        self.status_var.set(
                            "Finished successfully. "
                            f"{completed} completed or skipped."
                        )

                        messagebox.showinfo(
                            (
                                "Uninstallation complete"
                                if uninstalling
                                else "Installation complete"
                            ),
                            (
                                "Selected operations "
                                "finished successfully.\n\n"
                                f"Log:\n{log_path}"
                            ),
                            parent=self.root,
                        )

                    else:
                        self.status_var.set(
                            "Finished with "
                            f"{failed} failure(s)."
                        )

                        messagebox.showerror(
                            "Operation finished with errors",
                            (
                                f"{failed} operation(s) failed.\n\n"
                                f"Log:\n{log_path}"
                            ),
                            parent=self.root,
                        )

        except queue.Empty:
            pass

        self.root.after(
            GUI_QUEUE_POLL_INTERVAL_MS,
            self.process_queue,
        )

    def open_logs(self) -> None:
        """Open the installer log directory."""

        try:
            LOG_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            os.startfile(
                LOG_DIR
            )

        except Exception as error:
            messagebox.showerror(
                "Could not open logs",
                str(error),
                parent=self.root,
            )

    def close(self) -> None:
        """Close the GUI when no installation is running."""

        if self.running:
            messagebox.showwarning(
                "Installation in progress",
                (
                    "Wait for the selected operations "
                    "to finish before closing."
                ),
                parent=self.root,
            )
            return

        self.root.destroy()


# ============================================================
# Startup and fatal-error handling
# ============================================================

def show_fatal_error(
    error: BaseException,
) -> None:
    """Display startup failures without requiring a console."""

    details = traceback.format_exc()

    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            (
                f"{type(error).__name__}: {error}"
                f"\n\n{details}"
            ),
            "WTG Installer - Fatal Error",
            FATAL_ERROR_DIALOG_FLAGS,
        )

    except Exception:
        pass


def main() -> int:
    """Elevate and open the graphical installer."""

    if os.name != "nt":
        raise RuntimeError(
            "This installer is intended to run on Windows."
        )

    if not is_admin():
        relaunch_as_admin()
        return 0

    ensure_required_directories()

    root = tk.Tk()

    InstallerGUI(root)

    root.mainloop()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except SystemExit:
        raise

    except BaseException as fatal_error:
        show_fatal_error(
            fatal_error
        )

        raise SystemExit(1)
