import os
import shutil
import subprocess
import platform
import hashlib
import filecmp
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Dict, Union, List, Optional
from send2trash import send2trash


class FileManager:
    """
    A comprehensive file management toolset for the OS Assistant.
    Organized by functionality:
    1. Core Operations (Create, Copy, Move, Rename, Delete)
    2. Reading & Inspection (Read, Info, Listing, Hashing)
    3. Content Modification (Edit, Append, Replace)
    4. Search & Organization (Find, Archive, Empty)
    5. System & Network (Open, Download, Links)
    """

    # ==========================================
    # 1. CORE OPERATIONS (CRUD)
    # ==========================================

    def create_file(self, path: str, content: str = "") -> str:
        """Creates a new file with optional content."""
        file_path = Path(path)
        if file_path.exists():
            raise FileExistsError(f"The file '{path}' already exists.")

        # Ensure parent exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Success: File created at {file_path.absolute()}"

    def create_folder(self, path: str) -> str:
        """Creates a new directory."""
        folder_path = Path(path)
        if folder_path.exists():
            return f"Info: The folder '{path}' already exists."

        folder_path.mkdir(parents=True, exist_ok=True)
        return f"Success: Folder created at {folder_path.absolute()}"

    def copy_file(self, source: str, destination: str) -> str:
        """Copies a file. Raises errors if paths are invalid."""
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source '{src_path.name}' not found.")

        # Logic to ensure destination folder exists
        if src_path.suffix and not dst_path.suffix:
            # Destination is a folder
            if not dst_path.exists():
                raise FileNotFoundError(f"Destination folder '{destination}' not found.")
        elif dst_path.suffix:
            # Destination is a file
            if not dst_path.parent.exists():
                raise FileNotFoundError(f"Destination directory '{dst_path.parent}' not found.")

        shutil.copy2(str(src_path), str(dst_path))
        return f"Success: Copied '{src_path.name}' to '{destination}'"

    def move_file(self, source: str, destination: str) -> str:
        """Moves a file. Checks destination validity."""
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source '{src_path.name}' not found.")

        if src_path.suffix and not dst_path.suffix:
            if not dst_path.exists():
                raise FileNotFoundError(f"Destination folder '{destination}' not found.")
        elif dst_path.suffix:
            if not dst_path.parent.exists():
                raise FileNotFoundError(f"Destination directory '{dst_path.parent}' not found.")

        shutil.move(str(src_path), str(dst_path))
        return f"Success: Moved '{src_path.name}' to '{dst_path.name}'"

    def rename_item(self, old_path: str, new_name: str) -> str:
        """Renames a file or folder in place."""
        target_path = Path(old_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Item '{old_path}' not found.")

        new_path = target_path.parent / new_name
        if new_path.exists():
            raise FileExistsError(f"Item '{new_name}' already exists here.")

        target_path.rename(new_path)
        return f"Success: Renamed to '{new_name}'"

    def delete_file(self, path: str) -> str:
        """Moves item to Trash (Safe Delete)."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Item '{path}' not found.")

        try:
            send2trash(str(target_path.absolute()))
            return f"Success: Moved '{target_path.name}' to Trash."
        except Exception as e:
            return f"Error: {str(e)}"

    def permanently_delete(self, path: str) -> str:
        """
        Permanently deletes a file or folder (Unrecoverable).
        Use with caution.
        """
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Item '{path}' not found.")

        try:
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            return f"Success: Permanently deleted '{target_path.name}'"
        except Exception as e:
            return f"Error deleting: {str(e)}"

    def empty_folder(self, path: str) -> str:
        """Deletes all contents of a folder but keeps the folder."""
        folder = Path(path)
        if not folder.exists() or not folder.is_dir():
            raise NotADirectoryError(f"'{path}' is not a valid folder.")

        deleted_count = 0
        for item in folder.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_count += 1
            except Exception:
                continue

        return f"Success: Emptied '{folder.name}'. Removed {deleted_count} items."

    # ==========================================
    # 2. READING & INSPECTION
    # ==========================================

    def list_directory(self, path: str) -> str:
        """Lists directory contents."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Directory '{path}' not found.")

        items = []
        try:
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{prefix} {item.name}")
        except PermissionError:
            raise PermissionError(f"Access denied: '{path}'")

        if not items:
            return "Directory is empty."
        return "\n".join(items)

    def read_file(self, path: str, max_chars: int = 5000) -> str:
        """Reads text content. Caps output size."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        if target_path.stat().st_size > 10 * 1024 * 1024:
            return "Error: File is too large (over 10MB)."

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read(max_chars)

            if len(content) == max_chars:
                content += "\n\n...[Content Truncated]..."
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def get_file_info(self, path: str) -> Dict:
        """Returns detailed metadata."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        stats = p.stat()
        return {
            "name": p.name,
            "path": str(p.absolute()),
            "type": "Directory" if p.is_dir() else "File",
            "size": f"{round(stats.st_size / 1024, 2)} KB",
            "created": datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            "modified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            "hidden": p.name.startswith('.')
        }

    def count_lines(self, path: str) -> str:
        """Counts lines in a text file."""
        p = Path(path)
        if not p.exists() or p.is_dir():
            raise FileNotFoundError("Target is not a file.")

        try:
            with open(p, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            return f"File '{p.name}' has {count} lines."
        except Exception as e:
            return f"Error: {str(e)}"

    def get_file_hash(self, path: str) -> str:
        """Calculates SHA256 hash of a file."""
        p = Path(path)
        if not p.exists() or p.is_dir():
            return "Error: Invalid file for hashing."

        sha256 = hashlib.sha256()
        try:
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return f"SHA256: {sha256.hexdigest()}"
        except Exception as e:
            return f"Error hashing: {str(e)}"

    def compare_files(self, file1: str, file2: str) -> str:
        """Checks if two files have identical content."""
        if not (Path(file1).exists() and Path(file2).exists()):
            return "Error: One or both files not found."

        match = filecmp.cmp(file1, file2, shallow=False)
        return "Files are identical." if match else "Files are different."

    # ==========================================
    # 3. CONTENT MODIFICATION
    # ==========================================

    def append_to_file(self, path: str, content: str) -> str:
        """Adds text to the end of a file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        try:
            with open(p, 'a', encoding='utf-8') as f:
                f.write(f"\n{content}")
            return f"Success: Appended to '{p.name}'"
        except Exception as e:
            return f"Error: {str(e)}"

    def prepend_to_file(self, path: str, content: str) -> str:
        """Adds text to the beginning of a file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        try:
            with open(p, 'r', encoding='utf-8') as f:
                original = f.read()
            with open(p, 'w', encoding='utf-8') as f:
                f.write(content + "\n" + original)
            return f"Success: Prepended to '{p.name}'"
        except Exception as e:
            return f"Error: {str(e)}"

    def replace_text(self, path: str, old_text: str, new_text: str) -> str:
        """Replaces all occurrences of a string in a file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        try:
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_text not in content:
                return f"Info: Text '{old_text}' not found in file."

            new_content = content.replace(old_text, new_text)

            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return f"Success: Replaced text in '{p.name}'"
        except Exception as e:
            return f"Error: {str(e)}"

    # ==========================================
    # 4. SEARCH & ORGANIZATION
    # ==========================================

    def search_files_ranked(self, term: str) -> str:
        """
        Smart search: Scans User folders (Desktop, Documents, etc.)
        Ranks results: Exact Match > Starts With > Contains.
        """
        term = term.lower()
        candidates = []
        home = Path.home()
        # Directories to scan (recursive)
        search_dirs = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]

        for d_name in search_dirs:
            d_path = home / d_name
            if not d_path.exists(): continue

            try:
                for path in d_path.rglob("*"):
                    if not path.is_file(): continue
                    name = path.name.lower()

                    score = 0
                    if name == term:
                        score = 100
                    elif name.startswith(term):
                        score = 80
                    elif term in name:
                        score = 50

                    if score > 0:
                        # Store tuple: (Score, Path)
                        candidates.append((score, path))
            except Exception:
                continue

        # Sort: Highest Score first, then Shortest name length (heuristic for relevance)
        candidates.sort(key=lambda x: (-x[0], len(x[1].name)))

        if not candidates:
            return f"No files found matching '{term}'."

        top_results = [f"{c[1]} (Rank: {c[0]})" for c in candidates[:15]]
        return f"Found {len(candidates)} matches. Top results:\n" + "\n".join(top_results)

    def find_files_by_name(self, root_path: str, pattern: str) -> str:
        """Recursive search for files matching a pattern."""
        root = Path(root_path)
        if not root.exists(): return "Error: Root path not found."
        matches = list(root.rglob(pattern))
        if not matches: return "No matching files found."
        return "\n".join([str(p) for p in matches[:50]])

    def find_files_containing_text(self, root_path: str, text: str) -> str:
        """Simple grep: Finds files containing specific text."""
        root = Path(root_path)
        matches = []
        for path in root.rglob('*'):
            if path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        if text in f.read(): matches.append(path.name)
                except:
                    continue
        return f"Found in: {', '.join(matches[:20])}" if matches else f"No files containing '{text}'."

    def compress_item(self, path: str, format: str = "zip") -> str:
        """Compresses a file or folder."""
        src = Path(path)
        if not src.exists(): return "Error: Source not found."
        try:
            base_name = str(src.parent / src.name)
            archive_path = shutil.make_archive(base_name, format, src.parent, src.name)
            return f"Success: Created archive '{Path(archive_path).name}'"
        except Exception as e:
            return f"Error compressing: {str(e)}"

    def extract_archive(self, path: str, destination: str) -> str:
        """Extracts a zip/tar archive."""
        src = Path(path)
        dst = Path(destination)
        if not src.exists(): return "Error: Archive not found."
        try:
            shutil.unpack_archive(str(src), str(dst))
            return f"Success: Extracted to '{dst.name}'"
        except Exception as e:
            return f"Error extracting: {str(e)}"

    # ==========================================
    # 5. SYSTEM & NETWORK
    # ==========================================

    def open_file(self, path: str) -> str:
        """Opens file in default OS app."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File '{path}' not found.")

        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', str(p)))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(str(p))
            else:  # Linux
                subprocess.call(('xdg-open', str(p)))
            return f"Success: Opened '{p.name}'"
        except Exception as e:
            return f"Error opening file: {str(e)}"

    def download_file(self, url: str, destination: str) -> str:
        """Downloads a file from a URL."""
        try:
            dst = Path(destination)
            if dst.is_dir():
                filename = url.split('/')[-1] or "downloaded_file"
                dst = dst / filename

            urllib.request.urlretrieve(url, str(dst))
            return f"Success: Downloaded to '{dst.absolute()}'"
        except Exception as e:
            return f"Download failed: {str(e)}"

    def create_symlink(self, target: str, link_path: str) -> str:
        """Creates a symbolic link (Shortcut)."""
        tgt = Path(target)
        lnk = Path(link_path)
        if not tgt.exists(): return "Error: Target file does not exist."
        try:
            os.symlink(str(tgt), str(lnk))
            return f"Success: Created link at '{lnk.name}'"
        except Exception as e:
            return f"Error: {str(e)}"