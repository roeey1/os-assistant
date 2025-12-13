import subprocess
import platform
import os
import webbrowser
from pathlib import Path


class SystemOps:
    """
    Active system operations.
    Interacts with the OS to manage Apps, Windows, and Power States.
    """

    def _is_mac(self):
        return platform.system() == "Darwin"

    def _is_windows(self):
        return platform.system() == "Windows"

    # ==========================================
    # 1. GENERIC APP MANAGEMENT
    # ==========================================

    def open_app(self, app_name: str) -> str:
        """Opens any application by name."""
        try:
            if self._is_mac():
                subprocess.run(["open", "-a", app_name], check=True)
            elif self._is_windows():
                subprocess.run(f"start {app_name}", shell=True, check=True)
            return f"Success: Launched '{app_name}'"
        except Exception as e:
            return f"Error opening '{app_name}': {str(e)}"

    def close_app(self, app_name: str) -> str:
        """Closes an application."""
        try:
            if self._is_mac():
                script = f'quit app "{app_name}"'
                subprocess.run(["osascript", "-e", script], check=True)
            elif self._is_windows():
                proc_name = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
                subprocess.run(f"taskkill /IM \"{proc_name}\" /F", shell=True, check=True)
            return f"Success: Closed '{app_name}'"
        except Exception as e:
            return f"Error closing '{app_name}': {str(e)}"

    # ==========================================
    # 2. SPECIFIC TOOLS (Terminal, Browser, Finder)
    # ==========================================

    def open_terminal(self) -> str:
        """Opens the default Command Line Interface."""
        try:
            if self._is_mac():
                subprocess.run(["open", "-a", "Terminal"], check=True)
            elif self._is_windows():
                subprocess.run("start cmd", shell=True, check=True)
            return "Success: Opened Terminal."
        except Exception as e:
            return f"Error: {str(e)}"

    def close_terminal(self) -> str:
        """Closes the Terminal application."""
        if self._is_mac():
            return self.close_app("Terminal")
        elif self._is_windows():
            # Closing cmd.exe or powershell.exe
            try:
                subprocess.run("taskkill /IM cmd.exe /F", shell=True)
                subprocess.run("taskkill /IM powershell.exe /F", shell=True)
                return "Success: Closed Terminal windows."
            except Exception as e:
                return f"Error: {str(e)}"

    def open_browser(self, url: str = "https://google.com") -> str:
        """Opens the default web browser."""
        try:
            webbrowser.open(url)
            return f"Success: Opened browser to {url}"
        except Exception as e:
            return f"Error: {str(e)}"

    def close_browser(self) -> str:
        """Attempts to close common browsers."""
        browsers = ["Google Chrome", "Safari", "Firefox", "Microsoft Edge"]
        results = []
        if self._is_mac():
            for b in browsers:
                try:
                    self.close_app(b)
                    results.append(b)
                except:
                    pass
        elif self._is_windows():
            exes = ["chrome.exe", "firefox.exe", "msedge.exe"]
            for exe in exes:
                try:
                    subprocess.run(f"taskkill /IM {exe} /F", shell=True, stderr=subprocess.DEVNULL)
                    results.append(exe)
                except:
                    pass

        return f"Success: Attempted to close browsers ({', '.join(results)})"


    def open_task_manager(self) -> str:
        """Opens Activity Monitor or Task Manager."""
        try:
            if self._is_mac():
                subprocess.run(["open", "-a", "Activity Monitor"], check=True)
            elif self._is_windows():
                subprocess.run("start taskmgr", shell=True, check=True)
            return "Success: Opened Task Manager."
        except Exception as e:
            return f"Error: {str(e)}"

    # ==========================================
    # 3. WINDOW & SYSTEM STATE
    # ==========================================

    def minimize_all_windows(self) -> str:
        """Hides all windows to show Desktop."""
        try:
            if self._is_mac():
                # Command+Option+H+M is hard to script reliably, using Finder approach
                script = '''
                tell application "Finder"
                    set visible of every process to false
                    set visible of process "Finder" to true
                end tell
                '''
                subprocess.run(["osascript", "-e", script], check=True)
            elif self._is_windows():
                # PowerShell generic method
                cmd = "powershell -command \"(New-Object -ComObject Shell.Application).MinimizeAll()\""
                subprocess.run(cmd, shell=True, check=True)
            return "Success: All windows minimized."
        except Exception as e:
            return f"Error: {str(e)}"

    def lock_screen(self) -> str:
        """Locks the computer."""
        try:
            if self._is_mac():
                script = 'tell application "System Events" to keystroke "q" using {control down, command down}'
                subprocess.run(["osascript", "-e", script], check=True)
            elif self._is_windows():
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True, check=True)
            return "Success: Screen locked."
        except Exception as e:
            return f"Error: {str(e)}"

    # ==========================================
    # 4. SETTINGS & PROPERTIES (UPDATED)
    # ==========================================

    def open_settings(self, page: str = None) -> str:
        """
        Opens System Settings, optionally to a specific page.
        """
        # Map common terms to OS-specific URIs
        # Windows: ms-settings:<URI>
        # macOS: x-apple.systempreferences:com.apple.preference.<ID>

        page = page.lower() if page else ""

        windows_map = {
            "battery": "batterysaver",
            "display": "display",
            "sound": "sound",
            "wifi": "network-wifi",
            "bluetooth": "bluetooth",
            "update": "windowsupdate",
            "apps": "appsfeatures",
            "storage": "storagesense",
            "network": "network",
            "privacy": "privacy",
            "notifications": "notifications"
        }

        mac_map = {
            "battery": "com.apple.preference.battery",  # Might vary on Ventura+
            "display": "com.apple.preference.displays",
            "sound": "com.apple.preference.sound",
            "wifi": "com.apple.preference.network",
            "network": "com.apple.preference.network",
            "bluetooth": "com.apple.preferences.Bluetooth",
            "update": "com.apple.preferences.softwareupdate",
            "users": "com.apple.preferences.users",
            "security": "com.apple.preference.security",
            "privacy": "com.apple.preference.security"
        }

        try:
            if self._is_mac():
                uri = "x-apple.systempreferences:"
                if page and page in mac_map:
                    uri += mac_map[page]
                # Fallback: Just open the main app settings pane if specific mapping fails/not found
                elif page:
                    # Try heuristic: most prefs start with com.apple.preference.[name]
                    uri += f"com.apple.preference.{page}"
                else:
                    # Open main window
                    subprocess.run(["open", "-b", "com.apple.systempreferences"], check=True)
                    return "Success: Opened System Settings."

                subprocess.run(["open", uri], check=True)

            elif self._is_windows():
                uri = "ms-settings:"
                if page and page in windows_map:
                    uri += windows_map[page]
                elif page:
                    uri += page  # Try passing raw match

                subprocess.run(f"start {uri}", shell=True, check=True)

            return f"Success: Opened Settings ({page or 'Main'})."
        except Exception as e:
            return f"Error opening settings for '{page}': {str(e)}"

    def close_settings(self) -> str:
        if self._is_mac():
            return self.close_app("System Settings")
        elif self._is_windows():
            return self.close_app("SystemSettings")
        return "Info: Not supported."

    def show_file_properties(self, path: str) -> str:
        target = Path(path).resolve()
        if not target.exists(): return "Error: File not found."
        try:
            if self._is_mac():
                script = f'set t to (POSIX file "{str(target)}") as alias\ntell application "Finder"\nactivate\nopen information window of t\nend tell'
                subprocess.run(["osascript", "-e", script], check=True)
            elif self._is_windows():
                subprocess.run(f'explorer /select,"{str(target)}"', shell=True)
            return f"Success: Info opened for '{target.name}'"
        except Exception as e:
            return str(e)

    def close_file_properties(self) -> str:
        if self._is_mac():
            try:
                subprocess.run(["osascript", "-e", 'tell application "Finder" to close every information window'],
                               check=True)
                return "Success: Closed Info windows."
            except Exception as e:
                return str(e)
        return "Info: Not supported on Windows."

    def get_trash_items(self) -> str:
        try:
            if self._is_mac():
                t = Path.home() / ".Trash"
                items = [f.name for f in t.iterdir() if f.name != ".DS_Store"] if t.exists() else []
            elif self._is_windows():
                cmd = "powershell -command \"(New-Object -ComObject Shell.Application).NameSpace(0xa).Items() | Select-Object -ExpandProperty Name\""
                res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                items = [i.strip() for i in res.stdout.split('\n') if i.strip()]

            return f"Trash contains {len(items)} items." if items else "Trash is empty."
        except Exception as e:
            return f"Error: {str(e)}"

    def empty_trash(self) -> str:
        try:
            if self._is_mac():
                subprocess.run(["osascript", "-e", 'tell application "Finder" to empty trash'], check=True)
            elif self._is_windows():
                subprocess.run("powershell -command \"Clear-RecycleBin -Force\"", shell=True, check=True)
            return "Success: Trash emptied."
        except Exception as e:
            return f"Error: {str(e)}"