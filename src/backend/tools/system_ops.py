import os
import subprocess
import platform
import shutil
from pathlib import Path


class SystemOps:
    """
    Active system operations.
    These tools INTERACT with the OS (launching apps, opening windows, managing trash).
    """

    def _is_mac(self):
        return platform.system() == "Darwin"

    def _is_windows(self):
        return platform.system() == "Windows"

    def open_app(self, app_name: str) -> str:
        """
        Opens an application by name.
        Example: "Calculator", "Spotify", "Google Chrome"
        """
        try:
            if self._is_mac():
                # macOS: 'open -a "App Name"'
                subprocess.run(["open", "-a", app_name], check=True)
            elif self._is_windows():
                # Windows: 'start app_name' (shell=True is needed for start)
                subprocess.run(f"start {app_name}", shell=True, check=True)
            else:
                return "Error: Unsupported OS for launching apps."

            return f"Success: Launched '{app_name}'"
        except Exception as e:
            return f"Error: Could not launch '{app_name}'. {str(e)}"

    def open_settings(self) -> str:
        """
        Opens the main System Settings/Preferences window.
        """
        try:
            if self._is_mac():
                subprocess.run(["open", "-b", "com.apple.systempreferences"], check=True)
            elif self._is_windows():
                subprocess.run("start ms-settings:", shell=True, check=True)
            return "Success: Opened System Settings."
        except Exception as e:
            return f"Error opening settings: {str(e)}"

    def show_file_properties(self, path: str) -> str:
        """
        Opens the native 'Get Info' (macOS) or 'Properties' (Windows) window for a file.
        """
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: File '{path}' not found."

        try:
            if self._is_mac():
                # FIXED: We construct the script to force 'alias' resolution.
                # This fixes the (-1728) error by ensuring Finder resolves the file ID first.
                script = (
                    f'set targetFile to (POSIX file "{str(target)}") as alias\n'
                    'tell application "Finder"\n'
                    '    activate\n'
                    '    open information window of targetFile\n'
                    'end tell'
                )

                # Pass the multi-line script properly to osascript
                subprocess.run(["osascript", "-e", script], check=True)

            elif self._is_windows():
                # Windows: Select file in Explorer (Properties dialog is hard to automate via cmd)
                subprocess.run(f'explorer /select,"{str(target)}"', shell=True)
                return f"Success: Opened folder with '{target.name}' selected."

            return f"Success: Opened properties for '{target.name}'"
        except Exception as e:
            return f"Error showing properties: {str(e)}"

    def get_trash_items(self) -> str:
        """
        Lists items currently in the Trash/Recycle Bin.
        """
        items = []
        try:
            if self._is_mac():
                # macOS: List contents of ~/.Trash
                trash_path = Path.home() / ".Trash"
                if trash_path.exists():
                    items = [f.name for f in trash_path.iterdir() if f.name != ".DS_Store"]

            elif self._is_windows():
                # Windows: Use PowerShell to list Recycle Bin
                cmd = "powershell -command \"(New-Object -ComObject Shell.Application).NameSpace(0xa).Items() | Select-Object -ExpandProperty Name\""
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                items = result.stdout.strip().split('\n')
                # Filter empty strings
                items = [i.strip() for i in items if i.strip()]

            if not items:
                return "Trash is empty."

            return f"Trash contains {len(items)} items: {', '.join(items[:10])}" + ("..." if len(items) > 10 else "")

        except PermissionError:
            return "Error: Permission denied. The Assistant needs Full Disk Access to view Trash."
        except Exception as e:
            return f"Error listing trash: {str(e)}"

        # --- CLOSING ACTIONS ---

    def close_app(self, app_name: str) -> str:
        """
        Closes an application.
        """
        try:
            if self._is_mac():
                # AppleScript 'quit' allows the app to save data/exit gracefully
                script = f'quit app "{app_name}"'
                subprocess.run(["osascript", "-e", script], check=True)

            elif self._is_windows():
                # Windows: taskkill. We try to be smart about the .exe extension.
                # If user says "Notepad", we try "Notepad.exe"
                proc_name = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
                subprocess.run(f"taskkill /IM \"{proc_name}\" /F", shell=True, check=True)

            return f"Success: Closed '{app_name}'"
        except subprocess.CalledProcessError:
            return f"Error: Could not close '{app_name}'. Is it running?"
        except Exception as e:
            return f"Error closing app: {str(e)}"

    def close_settings(self) -> str:
        """
        Closes the System Settings (or System Preferences) window.
        """
        try:
            if self._is_mac():
                # Try closing the modern "System Settings" first
                try:
                    subprocess.run(["osascript", "-e", 'quit app "System Settings"'], check=True,
                                   stderr=subprocess.DEVNULL)
                except:
                    # Fallback for older macOS "System Preferences"
                    subprocess.run(["osascript", "-e", 'quit app "System Preferences"'], check=True)

            elif self._is_windows():
                # The modern Settings app process name
                subprocess.run("taskkill /IM SystemSettings.exe /F", shell=True, check=True)

            return "Success: Closed System Settings."
        except Exception as e:
            return f"Error closing settings: {str(e)}"

    def close_file_properties(self) -> str:
        """
        Closes 'Get Info' windows.
        """
        try:
            if self._is_mac():
                # FIXED: Target the specific 'information window' class directly.
                # This fixes the (-10010) error because Finder knows exactly how to close these.
                script = 'tell application "Finder" to close every information window'
                subprocess.run(["osascript", "-e", script], check=True)
                return "Success: Closed Info windows."

            elif self._is_windows():
                return "Info: Closing Properties windows is not currently supported on Windows."

        except Exception as e:
            return f"Error closing properties: {str(e)}"

    def empty_trash(self) -> str:
        """
        Empties the Trash/Recycle Bin.
        WARNING: Irreversible.
        """
        try:
            if self._is_mac():
                # AppleScript ensures we get the native sound effect and behavior
                script = 'tell application "Finder" to empty trash'
                subprocess.run(["osascript", "-e", script], check=True)

            elif self._is_windows():
                # PowerShell: Clear-RecycleBin -Force
                cmd = "powershell -command \"Clear-RecycleBin -Force\""
                subprocess.run(cmd, shell=True, check=True)

            return "Success: Trash emptied."
        except Exception as e:
            return f"Error emptying trash: {str(e)}"



# --- Manual Test ---
if __name__ == "__main__":
    ops = SystemOps()
    # Be careful running this! It will actually open apps.
    print(ops.open_app("Calculator"))
    print(ops.get_trash_items())
    print(ops.open_settings())
    print(ops.show_file_properties("/Users/raananpevzner/Desktop/ID.jpg"))
    print(ops.close_app("Calculator"))
    print(ops.close_file_properties())
    print(ops.close_settings())


