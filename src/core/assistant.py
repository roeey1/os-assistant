import os
from pathlib import Path
from src.backend.tools.files import FileManager


class OSAssistant:
    def __init__(self):
        self.files = FileManager()

    def execute_intent(self, intent: dict) -> str:
        """
        Executes the intent and returns a descriptive message.
        """
        action = intent.get('action')

        if action == 'error':
            return f"Error from LLM: {intent.get('message')}"

        try:
            # =======================================================
            # 1. PRE-RESOLVE PATHS
            # =======================================================

            resolved_path = None
            resolved_src = None
            resolved_dst = None

            if 'path' in intent:
                resolved_path = self._resolve_path(intent['path'])

            if 'source' in intent:
                resolved_src = self._resolve_path(intent['source'])
            if 'destination' in intent:
                resolved_dst = self._resolve_path(intent['destination'])

            # =======================================================
            # 2. CENTRALIZED VALIDATION & NORMALIZATION
            # =======================================================

            # --- Group A: Actions requiring the item to EXIST ---
            if action in ['read_file', 'open_file', 'get_file_info', 'rename_item']:
                if resolved_path == "NOT FOUND":
                    return f"Error: File or item '{intent.get('path')}' not found."

                # Extra check for rename
                if action == 'rename_item' and not intent.get('new_name'):
                    return "Error: No 'new_name' provided for rename action."

            # --- Group B: Creation actions (Default to Home if path not found) ---
            elif action in ['create_file', 'create_folder']:
                if resolved_path == "NOT FOUND":
                    # Assume creating new file relative to Home
                    resolved_path = Path.home() / intent['path']

            # --- Group C: Listing (Default to Home if path empty/not found) ---
            elif action == 'list_directory':
                if resolved_path == "NOT FOUND":
                    resolved_path = Path.home()

            # --- Group D: Transfer Actions (Move/Copy) ---
            elif action in ['move_file', 'copy_file']:
                # Source MUST exist
                if resolved_src == "NOT FOUND":
                    return f"Error: Source file '{intent.get('source')}' could not be found."

                # Destination defaults to Home if not found
                if resolved_dst == "NOT FOUND":
                    resolved_dst = Path.home() / intent['destination']

            # =======================================================
            # 3. EXECUTE ACTIONS (Clean Calls)
            # =======================================================

            if action == 'move_file':
                print(f"DEBUG: Move {resolved_src} -> {resolved_dst}")
                return self.files.move_file(str(resolved_src), str(resolved_dst))

            elif action == 'copy_file':
                print(f"DEBUG: Copy {resolved_src} -> {resolved_dst}")
                return self.files.copy_file(str(resolved_src), str(resolved_dst))

            elif action == 'create_file':
                content = intent.get('content', '')
                return self.files.create_file(str(resolved_path), content)

            elif action == 'create_folder':
                return self.files.create_folder(str(resolved_path))

            elif action == 'rename_item':
                return self.files.rename_item(str(resolved_path), intent['new_name'])

            elif action == 'list_directory':
                return self.files.list_directory(str(resolved_path))

            elif action == 'read_file':
                return self.files.read_file(str(resolved_path))

            elif action == 'open_file':
                return self.files.open_file(str(resolved_path))

            elif action == 'get_file_info':
                return self.files.get_file_info(str(resolved_path))

            else:
                return f"Error: Unknown action '{action}'."

        except Exception as e:
            return f"Error: {str(e)}"

    def _resolve_path(self, path_str: str) -> Path:
        """
        Smart path resolver.
        """
        if not path_str: return "NOT FOUND"

        path = Path(path_str)
        home = Path.home()

        # 1. Absolute path
        if path.is_absolute():
            return path

        # 2. Relative path with known folders (e.g., "Downloads/file.txt")
        if len(path.parts) > 1:
            full_path = home / path
            if full_path.exists():
                return full_path
            parent = full_path.parent
            if parent.exists():
                match = next(parent.glob(f"{full_path.name}.*"), None)
                if match: return match
            return full_path

        # 3. Simple name search
        found = self._find_path_by_name(path_str)
        if found:
            return found

        return "NOT FOUND"

    def _find_path_by_name(self, filename: str) -> Path:
        """
        Recursively scans common directories.
        """
        home = Path.home()
        search_dirs = [
            home / 'Desktop', home / 'Downloads', home / 'Documents', home / 'Pictures'
        ]
        patterns = [filename, f"{filename}.*"]

        for directory in search_dirs:
            if not directory.exists(): continue
            try:
                for pattern in patterns:
                    found = next(directory.rglob(pattern), None)
                    if found: return found
            except (PermissionError, OSError):
                continue

        if (home / filename).exists():
            return home / filename

        return None