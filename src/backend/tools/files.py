import os
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Union, List
from send2trash import send2trash


class FileManager:
    """
    Handles direct file system operations.
    """

    # --- 1. FILE CREATION & COPYING ---

    def create_file(self, path: str, content: str = "") -> str:
        """
        Creates a new file with the specified content.
        Raises an error if the file already exists.
        """
        file_path = Path(path)
        if file_path.exists():
            raise FileExistsError(f"The file '{path}' already exists.")

        # For creating NEW files, we generally still want to allow creating parents,
        # otherwise 'create file in new folder X' will always fail.
        # If you want to restrict this too, comment out the next line.
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Success: File created at {file_path.absolute()}"

    def create_folder(self, path: str) -> str:
        """
        Creates a new folder.
        """
        folder_path = Path(path)

        if folder_path.exists():
            return f"Info: The folder '{path}' already exists."

        folder_path.mkdir(parents=True, exist_ok=True)
        return f"Success: Folder created at {folder_path.absolute()}"

    def copy_file(self, source: str, destination: str) -> str:
        """
        Copies a file from source to destination.
        STRICT MODE: Destination folder must exist.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        # 1. Validation Source
        if not src_path.exists():
            raise FileNotFoundError(f"Source file '{src_path.name}' not found.")

        # Case A: Destination looks like a folder (no extension, e.g. "Backup")
        if src_path.suffix and not dst_path.suffix:
            if not dst_path.exists():
                # CHANGED: Raise error instead of creating it
                raise FileNotFoundError(f"Destination folder '{destination}' not found.")

        # Case B: Destination looks like a file (has extension, e.g. "Backup/file.txt")
        # We must ensure the PARENT directory exists.
        elif dst_path.suffix:
            if not dst_path.parent.exists():
                # CHANGED: Raise error instead of creating parent
                raise FileNotFoundError(f"Destination directory '{dst_path.parent}' not found.")

        # 3. Execute Copy
        shutil.copy2(str(src_path), str(dst_path))

        return f"Success: Copied '{src_path.name}' to '{destination}'"

    # --- 2. MOVING & RENAMING ---

    def move_file(self, source: str, destination: str) -> str:
        """
        Moves a file from source to destination.
        STRICT MODE: Destination folder must exist.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        # 1. Validation Source
        if not src_path.exists():
            raise FileNotFoundError(f"Source file '{src_path.name}' not found.")

        # 2. Check Destination Folder Logic

        # Case A: Destination looks like a folder (no extension)
        if src_path.suffix and not dst_path.suffix:
            if not dst_path.exists():
                # CHANGED: Raise error instead of creating it
                raise FileNotFoundError(f"Destination folder '{destination}' not found.")

        # Case B: Destination looks like a file path (has extension)
        elif dst_path.suffix:
            if not dst_path.parent.exists():
                # CHANGED: Raise error instead of creating parent
                raise FileNotFoundError(f"Destination directory '{dst_path.parent}' not found.")

        # 3. Execute Move
        shutil.move(str(src_path), str(dst_path))

        return f"Success: Moved '{src_path.name}' to '{dst_path.name}'"

    def rename_item(self, old_path: str, new_name: str) -> str:
        """
        Renames a file or folder in place.
        """
        target_path = Path(old_path)

        if not target_path.exists():
            raise FileNotFoundError(f"Item '{old_path}' not found.")

        # Create the new full path (keeping the same parent directory)
        new_path = target_path.parent / new_name

        if new_path.exists():
            raise FileExistsError(f"Cannot rename. An item named '{new_name}' already exists in this location.")

        target_path.rename(new_path)
        return f"Success: Renamed '{target_path.name}' to '{new_name}'"

    # --- 3. READING & LISTING ---

    def list_directory(self, path: str) -> str:
        """
        Lists the contents of a directory.
        """
        target_path = Path(path)

        if not target_path.exists():
            raise FileNotFoundError(f"Directory '{path}' not found.")
        if not target_path.is_dir():
            raise NotADirectoryError(f"'{path}' is not a directory.")

        items = []
        try:
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                name = f"{item.name}/" if item.is_dir() else item.name
                items.append(name)
        except PermissionError:
            raise PermissionError(f"Permission denied accessing '{path}'.")

        if not items:
            return "Directory is empty."

        return f"Contents of '{target_path.name}': {', '.join(items)}"

    def read_file(self, path: str, max_chars: int = 2000) -> str:
        """
        Reads the text content of a file.
        """
        target_path = Path(path)

        if not target_path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")
        if target_path.is_dir():
            raise IsADirectoryError(f"'{path}' is a directory, not a text file.")

        try:
            if target_path.stat().st_size > 10 * 1024 * 1024:
                return "Error: File is too large to read (over 10MB)."

            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read(max_chars)

            if len(content) == max_chars:
                content += "\n...[Content Truncated]..."

            return content

        except UnicodeDecodeError:
            return "Error: Unable to read file. It appears to be binary."
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def open_file(self, path: str) -> str:
        """
        Opens the file in the default OS application.
        """
        target_path = Path(path)

        if not target_path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        try:
            current_os = platform.system()
            if current_os == 'Darwin':
                subprocess.call(('open', str(target_path)))
            elif current_os == 'Windows':
                os.startfile(str(target_path))
            else:
                subprocess.call(('xdg-open', str(target_path)))
            return f"Success: Opened '{target_path.name}'"
        except Exception as e:
            return f"Error: Could not open file. {str(e)}"

    def get_file_info(self, path: str) -> Dict[str, Union[str, int]]:
        """
        Returns metadata about the file.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        stats = file_path.stat()
        created_time = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = round(stats.st_size / 1024, 2)

        return {
            "name": file_path.name,
            "absolute_path": str(file_path.absolute()),
            "size_kb": size_kb,
            "created": created_time,
            "modified": modified_time,
            "is_directory": file_path.is_dir()
        }

    def delete_file(self, path: str) -> str:
        """
        Moves a file or folder to the Trash/Recycle Bin.
        Safe deletion (recoverable).
        """
        target_path = Path(path)

        if not target_path.exists():
            raise FileNotFoundError(f"Item '{path}' not found.")

        # send2trash handles both files and folders safely
        try:
            send2trash(str(target_path.absolute()))
            return f"Success: Moved '{target_path.name}' to Trash."
        except Exception as e:
            return f"Error deleting item: {str(e)}"


# --- Testing Section ---
if __name__ == "__main__":
    tool = FileManager()
    # Manual Test
    # This should now FAIL if 'NonExistentFolder' does not exist
    try:
        # tool.create_file("test.txt", "content")
        # tool.move_file("test.txt", "NonExistentFolder")
        pass
    except Exception as e:
        print(f"Test caught expected error: {e}")