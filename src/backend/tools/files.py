import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Union


class FileManager:
    """
    Handles direct file system operations.
    NOTE: This class assumes permissions have already been checked by the Safety layer.
    """

    def create_file(self, path: str, content: str = "") -> str:
        """
        Creates a new file with the specified content.
        Raises an error if the file already exists to prevent accidental overwrites.
        """
        file_path = Path(path)

        # 1. Check if file already exists
        if file_path.exists():
            raise FileExistsError(f"The file '{path}' already exists.")

        # 2. Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 3. Write content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Success: File created at {file_path.absolute()}"

    def move_file(self, source: str, destination: str) -> str:
        """
        Moves a file from source to destination.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source file '{source}' not found.")

        # shutil.move handles both files and directories
        shutil.move(str(src_path), str(dst_path))

        return f"Success: Moved '{source}' to '{destination}'"

    def copy_file(self, source: str, destination: str) -> str:
        """
        Copies a file from source to destination.
        Preserves metadata (timestamps) using copy2.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source file '{source}' not found.")

        # copy2 preserves file metadata (creation time, etc)
        shutil.copy2(str(src_path), str(dst_path))

        return f"Success: Copied '{source}' to '{destination}'"

    def get_file_info(self, path: str) -> Dict[str, Union[str, int]]:
        """
        Returns a dictionary containing metadata about the file.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        stats = file_path.stat()

        # Convert timestamps to readable strings
        created_time = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

        # Calculate size in KB
        size_kb = round(stats.st_size / 1024, 2)

        return {
            "name": file_path.name,
            "absolute_path": str(file_path.absolute()),
            "size_kb": size_kb,
            "created": created_time,
            "modified": modified_time,
            "is_directory": file_path.is_dir()
        }


# --- Testing Section (Run this file directly to test) ---
if __name__ == "__main__":
    tool = FileManager()

    # 1. Test Create
    try:
        print(tool.create_file("test_note.txt", "Hello OS Assistant!"))
    except Exception as e:
        print(e)

    # 2. Test Get Info
    try:
        info = tool.get_file_info("test_note.txt")
        print(f"File Info: {info}")
    except Exception as e:
        print(e)

    # try:
    #     tool.move_file(source="/Users/roeeyanoos/Downloads/timeline3.pptx", destination="/Users/roeeyanoos/Desktop/test")
    # except Exception as e:
    #     print(e)
    try:
        tool.copy_file(source="/Users/roeeyanoos/Desktop/test/timeline3.pptx", destination="/Users/roeeyanoos/Downloads")
    except Exception as e:
        print(e)