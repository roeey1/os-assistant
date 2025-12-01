# import os
# from pathlib import Path
# from src.backend.tools.files import FileManager
# from src.backend.tools.system_ops import SystemOps
# from src.backend.tools.sys_info import SystemInfo
#
#
# class OSAssistant:
#     def __init__(self):
#         self.files = FileManager()
#         self.sys_ops = SystemOps()
#         self.sys_info = SystemInfo()
#
#     def execute_intent(self, intent: dict) -> str:
#         """
#         Executes the intent and returns a descriptive message.
#         """
#         action = intent.get('action')
#
#         if action == 'error':
#             return f"Error from LLM: {intent.get('message')}"
#
#         try:
#             # =======================================================
#             # 1. PRE-RESOLVE PATHS
#             # =======================================================
#
#             resolved_path = None
#             resolved_src = None
#             resolved_dst = None
#
#             if 'path' in intent:
#                 resolved_path = self._resolve_path(intent['path'])
#
#             if 'source' in intent:
#                 resolved_src = self._resolve_path(intent['source'])
#             if 'destination' in intent:
#                 resolved_dst = self._resolve_path(intent['destination'])
#
#             # =======================================================
#             # 2. CENTRALIZED VALIDATION & NORMALIZATION
#             # =======================================================
#
#             # --- Group A: Actions requiring the item to EXIST ---
#             if action in ['read_file', 'open_file', 'get_file_info', 'rename_item', 'show_file_properties']:
#                 if resolved_path == "NOT FOUND":
#                     return f"Error: File or item '{intent.get('path')}' not found."
#
#                 # Extra check for rename
#                 if action == 'rename_item' and not intent.get('new_name'):
#                     return "Error: No 'new_name' provided for rename action."
#
#             # --- Group B: Creation actions (Default to Home if path not found) ---
#             elif action in ['create_file', 'create_folder']:
#                 if resolved_path == "NOT FOUND":
#                     # Assume creating new file relative to Home
#                     resolved_path = Path.home() / intent['path']
#
#             # --- Group C: Listing / Disk Usage (Default to Home/Root if path empty/not found) ---
#             elif action in ['list_directory', 'get_disk_usage']:
#                 if resolved_path == "NOT FOUND":
#                     resolved_path = Path.home()
#
#             # --- Group D: Transfer Actions (Move/Copy) ---
#             elif action in ['move_file', 'copy_file']:
#                 # Source MUST exist
#                 if resolved_src == "NOT FOUND":
#                     return f"Error: Source file '{intent.get('source')}' could not be found."
#
#                 # Destination defaults to Home if not found
#                 if resolved_dst == "NOT FOUND":
#                     resolved_dst = Path.home() / intent['destination']
#
#             # --- Group E: Application Ops (Require app_name) ---
#             elif action in ['open_app', 'close_app']:
#                 if not intent.get('app_name'):
#                     return f"Error: Action '{action}' requires an 'app_name' parameter."
#
#             # =======================================================
#             # 3. EXECUTE ACTIONS (Clean Calls)
#             # =======================================================
#
#             # --- FILE OPS ---
#             if action == 'move_file':
#                 print(f"DEBUG: Move {resolved_src} -> {resolved_dst}")
#                 return self.files.move_file(str(resolved_src), str(resolved_dst))
#
#             elif action == 'copy_file':
#                 print(f"DEBUG: Copy {resolved_src} -> {resolved_dst}")
#                 return self.files.copy_file(str(resolved_src), str(resolved_dst))
#
#             elif action == 'create_file':
#                 content = intent.get('content', '')
#                 return self.files.create_file(str(resolved_path), content)
#
#             elif action == 'create_folder':
#                 return self.files.create_folder(str(resolved_path))
#
#             elif action == 'rename_item':
#                 return self.files.rename_item(str(resolved_path), intent['new_name'])
#
#             elif action == 'list_directory':
#                 return self.files.list_directory(str(resolved_path))
#
#             elif action == 'read_file':
#                 return self.files.read_file(str(resolved_path))
#
#             elif action == 'open_file':
#                 return self.files.open_file(str(resolved_path))
#
#             elif action == 'get_file_info':
#                 return self.files.get_file_info(str(resolved_path))
#
#             # --- SYSTEM OPS (Active) ---
#             elif action == 'open_app':
#                 return self.sys_ops.open_app(intent['app_name'])
#
#             elif action == 'close_app':
#                 return self.sys_ops.close_app(intent['app_name'])
#
#             elif action == 'open_settings':
#                 return self.sys_ops.open_settings()
#
#             elif action == 'close_settings':
#                 return self.sys_ops.close_settings()
#
#             elif action == 'show_file_properties':
#                 return self.sys_ops.show_file_properties(str(resolved_path))
#
#             elif action == 'close_file_properties':
#                 return self.sys_ops.close_file_properties()
#
#             elif action == 'get_trash_items':
#                 return self.sys_ops.get_trash_items()
#
#             # --- SYSTEM INFO (Passive) ---
#             elif action == 'get_system_specs':
#                 # Convert dict to string for LLM readability
#                 return str(self.sys_info.get_system_specs())
#
#             elif action == 'get_disk_usage':
#                 # Uses resolved_path (defaults to Home if not provided)
#                 return self.sys_info.get_disk_usage(str(resolved_path))
#
#             elif action == 'get_user_context':
#                 return str(self.sys_info.get_user_context())
#
#             elif action == 'get_running_processes':
#                 # Optional: You could check intent for a 'limit' parameter
#                 limit = intent.get('limit', 20)
#                 return self.sys_info.get_running_processes(limit=limit)
#
#             else:
#                 return f"Error: Unknown action '{action}'."
#
#         except Exception as e:
#             return f"Error: {str(e)}"
#
#     def _resolve_path(self, path_str: str) -> Path:
#         """
#         Smart path resolver.
#         """
#         if not path_str: return "NOT FOUND"
#
#         path = Path(path_str)
#         home = Path.home()
#
#         # 1. Absolute path
#         if path.is_absolute():
#             return path
#
#         # 2. Relative path with known folders (e.g., "Downloads/file.txt")
#         if len(path.parts) > 1:
#             full_path = home / path
#             if full_path.exists():
#                 return full_path
#             parent = full_path.parent
#             if parent.exists():
#                 match = next(parent.glob(f"{full_path.name}.*"), None)
#                 if match: return match
#             return full_path
#
#         # 3. Simple name search
#         found = self._find_path_by_name(path_str)
#         if found:
#             return found
#
#         return "NOT FOUND"
#
#     def _find_path_by_name(self, filename: str) -> Path:
#         """
#         Recursively scans common directories.
#         """
#         home = Path.home()
#         search_dirs = [
#             home / 'Desktop', home / 'Downloads', home / 'Documents', home / 'Pictures'
#         ]
#         patterns = [filename, f"{filename}.*"]
#
#         for directory in search_dirs:
#             if not directory.exists(): continue
#             try:
#                 for pattern in patterns:
#                     found = next(directory.rglob(pattern), None)
#                     if found: return found
#             except (PermissionError, OSError):
#                 continue
#
#         if (home / filename).exists():
#             return home / filename
#
#         return None

import os
from pathlib import Path
from typing import Optional

# Tools
from src.backend.tools.files import FileManager
from src.backend.tools.system_ops import SystemOps
from src.backend.tools.sys_info import SystemInfo

# Security
from src.backend.core.guard import SecurityManager, RiskLevel


class OSAssistant:
    def __init__(self):
        self.files = FileManager()
        self.sys_ops = SystemOps()
        self.sys_info = SystemInfo()

        # NEW: Initialize Security Guard
        self.safety = SecurityManager()

    def execute_intent(self, intent: dict, confirm: bool = False) -> str:
        """
        Executes the intent and returns a descriptive message.

        Args:
            intent: The parsed JSON from the LLM.
            confirm: If True, user has approved a High Risk action.
        """
        action = intent.get('action') or intent.get('tool')  # Handle both formats

        if action == 'error':
            return f"Error from LLM: {intent.get('message')}"

        try:
            # =======================================================
            # 1. PRE-RESOLVE PATHS (Your Smart Logic)
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
            if action in ['read_file', 'open_file', 'get_file_info', 'rename_item', 'show_file_properties',
                          'delete_file']:
                if str(resolved_path) == "NOT FOUND":
                    return f"Error: File or item '{intent.get('path')}' not found."

                if action == 'rename_item' and not intent.get('new_name'):
                    return "Error: No 'new_name' provided for rename action."

            # --- Group B: Creation actions (Default to Home if path not found) ---
            elif action in ['create_file', 'create_folder']:
                if str(resolved_path) == "NOT FOUND":
                    resolved_path = Path.home() / intent['path']

            # --- Group C: Listing (Default to Home if path empty) ---
            elif action in ['list_directory', 'get_disk_usage']:
                if str(resolved_path) == "NOT FOUND":
                    resolved_path = Path.home()

            # --- Group D: Transfer Actions (Move/Copy) ---
            elif action in ['move_file', 'copy_file']:
                if str(resolved_src) == "NOT FOUND":
                    return f"Error: Source file '{intent.get('source')}' could not be found."

                if str(resolved_dst) == "NOT FOUND":
                    # If destination doesn't exist, assume it's a new path relative to Home
                    resolved_dst = Path.home() / intent['destination']

            # --- Group E: Application Ops ---
            elif action in ['open_app', 'close_app']:
                if not intent.get('app_name'):
                    return f"Error: Action '{action}' requires an 'app_name' parameter."

            # =======================================================
            # 3. SECURITY CHECK (The New Guard Layer)
            # =======================================================

            # We reconstruct the arguments with the RESOLVED paths to check *real* locations
            safety_args = intent.copy()
            if resolved_path and str(resolved_path) != "NOT FOUND": safety_args['path'] = str(resolved_path)
            if resolved_src and str(resolved_src) != "NOT FOUND": safety_args['source'] = str(resolved_src)
            if resolved_dst and str(resolved_dst) != "NOT FOUND": safety_args['destination'] = str(resolved_dst)

            allowed, reason, risk = self.safety.validate_action(action, safety_args)

            # 1. Blocked Actions
            if not allowed:
                return f"🚫 Security Alert: {reason}"

            # 2. High Risk Confirmation
            if risk == RiskLevel.HIGH and not confirm:
                return f"⚠️ CONFIRMATION_NEEDED: {action}. Reason: {reason}"

            # =======================================================
            # 4. EXECUTE ACTIONS
            # =======================================================

            # --- FILE OPS ---
            if action == 'move_file':
                return self.files.move_file(str(resolved_src), str(resolved_dst))

            elif action == 'copy_file':
                return self.files.copy_file(str(resolved_src), str(resolved_dst))

            elif action == 'create_file':
                content = intent.get('content', '')
                return self.files.create_file(str(resolved_path), content)

            elif action == 'create_folder':
                return self.files.create_folder(str(resolved_path))

            elif action == 'rename_item':
                return self.files.rename_item(str(resolved_path), intent['new_name'])

            elif action == 'delete_file':
                return self.files.delete_file(str(resolved_path))

            elif action == 'list_directory':
                return self.files.list_directory(str(resolved_path))

            elif action == 'read_file':
                return self.files.read_file(str(resolved_path))

            elif action == 'open_file':
                return self.files.open_file(str(resolved_path))

            elif action == 'get_file_info':
                return self.files.get_file_info(str(resolved_path))

            # --- SYSTEM OPS (Active) ---
            elif action == 'open_app':
                return self.sys_ops.open_app(intent['app_name'])

            elif action == 'close_app':
                return self.sys_ops.close_app(intent['app_name'])

            elif action == 'open_settings':
                return self.sys_ops.open_settings()

            elif action == 'close_settings':
                return self.sys_ops.close_settings()

            elif action == 'show_file_properties':
                return self.sys_ops.show_file_properties(str(resolved_path))

            elif action == 'close_file_properties':
                return self.sys_ops.close_file_properties()

            elif action == 'get_trash_items':
                return self.sys_ops.get_trash_items()

            elif action == 'empty_trash':
                return self.sys_ops.empty_trash()

            # --- SYSTEM INFO (Passive) ---
            elif action == 'get_system_specs':
                return str(self.sys_info.get_system_specs())

            elif action == 'get_disk_usage':
                return self.sys_info.get_disk_usage(str(resolved_path))

            elif action == 'get_user_context':
                return str(self.sys_info.get_user_context())

            elif action == 'get_running_processes':
                limit = intent.get('limit', 20)
                return self.sys_info.get_running_processes(limit=limit)

            else:
                return f"Error: Unknown action '{action}'."

        except Exception as e:
            return f"Error: {str(e)}"

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """
        Smart path resolver. Returns Path object or "NOT FOUND" (kept as string for logic).
        """
        if not path_str: return "NOT FOUND"

        path = Path(path_str)
        home = Path.home()

        # 1. Absolute path
        if path.is_absolute():
            return path

        # 2. Relative path with known folders
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

    def _find_path_by_name(self, filename: str) -> Optional[Path]:
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