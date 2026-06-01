"""
Extended computer-use MCP tools — system, filesystem, window, process, keyboard.
All tools use coordinate-based or named-parameter APIs matching the CUA standard.
"""
from __future__ import annotations

from app.mcp.gateway import mcp
from app.mcp.dispatch import run_action


# ---------------------------------------------------------------------------
# Keyboard — key hold/release (modifier support)
# ---------------------------------------------------------------------------

@mcp.tool()
def key_down(device_id: str, key: str) -> dict:
    """
    Hold a key down without releasing. Use with key_up for modifier combos.
    Examples: 'shift', 'ctrl', 'alt', 'cmd', 'meta'.
    """
    return run_action(device_id, "key_down", {"key": key})


@mcp.tool()
def key_up(device_id: str, key: str) -> dict:
    """Release a held key. Must be paired with a prior key_down call."""
    return run_action(device_id, "key_up", {"key": key})


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

@mcp.tool()
def run_shell(device_id: str, command: str, timeout_ms: int = 30000) -> dict:
    """
    Execute a shell command on the device. Returns stdout, stderr, and exit_code.
    On Windows devices, executes via PowerShell.
    On Android, executes via adb shell.
    On browser devices, not supported.
    """
    return run_action(device_id, "run_shell", {"command": command, "timeout_ms": timeout_ms})


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------

@mcp.tool()
def get_clipboard(device_id: str) -> dict:
    """Read the current clipboard contents. Returns text field with clipboard value."""
    return run_action(device_id, "get_clipboard", {})


@mcp.tool()
def set_clipboard(device_id: str, text: str) -> dict:
    """Write text to the clipboard. Useful for pasting large content reliably."""
    return run_action(device_id, "set_clipboard", {"text": text})


# ---------------------------------------------------------------------------
# Application launch
# ---------------------------------------------------------------------------

@mcp.tool()
def launch_app(device_id: str, app: str) -> dict:
    """
    Launch an application.
    - Linux/macOS: app name or path (e.g. 'firefox', '/usr/bin/gedit')
    - Windows: executable name or full path (e.g. 'notepad.exe')
    - Android: package/activity (e.g. 'com.android.chrome/.Main')
    - iOS Simulator: bundle ID (e.g. 'com.apple.mobilesafari')
    - Browser: treated as navigate(url)
    """
    return run_action(device_id, "launch_app", {"app": app})


# ---------------------------------------------------------------------------
# Wait for condition
# ---------------------------------------------------------------------------

@mcp.tool()
def wait_for(device_id: str, condition: str, timeout_ms: int = 10000) -> dict:
    """
    Wait until a text string or CSS selector appears on screen.
    For browser devices uses Playwright's native wait_for_selector.
    For other devices polls the accessibility tree every 500 ms.
    Returns found=True and elapsed_ms when matched.
    """
    return run_action(device_id, "wait_for", {"condition": condition, "timeout_ms": timeout_ms})


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------

@mcp.tool()
def read_file(device_id: str, path: str) -> dict:
    """Read a file from the device filesystem. Returns content as a string."""
    return run_action(device_id, "read_file", {"path": path})


@mcp.tool()
def write_file(device_id: str, path: str, content: str) -> dict:
    """Write a string to a file on the device filesystem. Creates the file if missing."""
    return run_action(device_id, "write_file", {"path": path, "content": content})


@mcp.tool()
def list_directory(device_id: str, path: str) -> dict:
    """List files and directories at path. Returns entries with name, type, size."""
    return run_action(device_id, "list_directory", {"path": path})


# ---------------------------------------------------------------------------
# Window management
# ---------------------------------------------------------------------------

@mcp.tool()
def list_windows(device_id: str) -> dict:
    """List all open windows with their titles and positions."""
    return run_action(device_id, "list_windows", {})


@mcp.tool()
def focus_window(device_id: str, title: str) -> dict:
    """Bring the window whose title contains `title` to the foreground."""
    return run_action(device_id, "focus_window", {"title": title})


@mcp.tool()
def resize_window(device_id: str, title: str, width: int, height: int) -> dict:
    """Resize a window by title match to width × height pixels."""
    return run_action(device_id, "resize_window", {"title": title, "width": width, "height": height})


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------

@mcp.tool()
def list_processes(device_id: str) -> dict:
    """List running processes with PID, name, and CPU/memory usage."""
    return run_action(device_id, "list_processes", {})


@mcp.tool()
def kill_process(device_id: str, pid_or_name: str) -> dict:
    """Terminate a process by PID (numeric string) or exact name."""
    return run_action(device_id, "kill_process", {"pid_or_name": pid_or_name})


# ---------------------------------------------------------------------------
# Screen info
# ---------------------------------------------------------------------------

@mcp.tool()
def get_screen_size(device_id: str) -> dict:
    """Return the screen resolution as {width, height} in pixels."""
    return run_action(device_id, "get_screen_size", {})
