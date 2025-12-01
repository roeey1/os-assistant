import os
from pathlib import Path
from enum import Enum
from typing import Dict, Tuple


class RiskLevel(Enum):
    SAFE = "SAFE"  # Read-only
    MODERATE = "MODERATE"  # Creation/Open App
    HIGH = "HIGH"  # Destructive
    BLOCKED = "BLOCKED"  # Forbidden


class SecurityManager:
    """
    Guardrails for OS Assistant.
    Validates paths and classifies operation risks before execution.
    """

    def __init__(self):
        self.user_home = Path.home().resolve()

        # 1. Define Risk Levels
        self.tool_risks = {
            # Files
            "list_directory": RiskLevel.SAFE,
            "open_file": RiskLevel.SAFE,
            "read_file": RiskLevel.SAFE,
            "get_file_info": RiskLevel.SAFE,
            "create_file": RiskLevel.MODERATE,
            "create_folder": RiskLevel.MODERATE,
            "copy_file": RiskLevel.MODERATE,
            "move_file": RiskLevel.HIGH,  # Moving to wrong place is bad
            "rename_item": RiskLevel.HIGH,  # Renaming critical files is bad
            "delete_file": RiskLevel.HIGH,  # Destructive

            # System Info
            "get_system_specs": RiskLevel.SAFE,
            "get_disk_usage": RiskLevel.SAFE,
            "get_running_processes": RiskLevel.SAFE,
            "get_user_context": RiskLevel.SAFE,

            # System Ops
            "open_app": RiskLevel.MODERATE,
            "open_settings": RiskLevel.MODERATE,
            "show_file_properties": RiskLevel.SAFE,
            "get_trash_items": RiskLevel.SAFE,
            "close_app": RiskLevel.MODERATE,  # Closing unsaved work is dangerous
            "close_settings": RiskLevel.SAFE,
            "close_file_properties": RiskLevel.SAFE,
            "empty_trash": RiskLevel.HIGH  # Irreversible
        }

        # 2. Define Restricted Paths (Blacklist)
        # These are paths the AI should NEVER touch.
        self.restricted_paths = [
            Path("/System"),
            Path("/usr"),
            Path("/bin"),
            Path("/etc"),
            Path("/var"),
            Path("C:\\Windows"),
            Path("C:\\Program Files"),
            Path("C:\\Program Files (x86)"),
        ]

    def validate_action(self, tool_name: str, args: Dict) -> Tuple[bool, str, RiskLevel]:
        """
        """
        # 1. Unknown Tool Check
        if tool_name not in self.tool_risks:
            return False, f"Unknown tool '{tool_name}' blocked.", RiskLevel.BLOCKED

        risk = self.tool_risks[tool_name]

        # 2. Path Safety Check
        paths_to_check = []
        if 'path' in args: paths_to_check.append(args['path'])
        if 'source' in args: paths_to_check.append(args['source'])
        if 'destination' in args: paths_to_check.append(args['destination'])
        if 'old_path' in args: paths_to_check.append(args['old_path'])

        for p in paths_to_check:
            # Skip validation if path wasn't found (Integrity check will catch this later if crucial)
            if p == "NOT FOUND": continue

            is_safe, reason = self._is_path_safe(p)
            if not is_safe:
                return False, reason, RiskLevel.BLOCKED

        # 3. State Integrity Check (NEW)
        # Verifies the file still exists (or doesn't exist) right before execution
        is_valid_state, state_reason = self._validate_state_integrity(tool_name, args)
        if not is_valid_state:
            return False, f"State Error: {state_reason}", RiskLevel.BLOCKED

        # 4. Approved
        return True, "Action permitted.", risk

    def _is_path_safe(self, path_str: str) -> Tuple[bool, str]:
        """
        Internal logic to check if a path is within allowed bounds.
        """
        try:
            target = Path(path_str).expanduser().resolve()

            # Rule 1: Root protection
            if target.parent == target:
                return False, f"Access denied: Cannot operate on system root '{target}'."

            # Rule 2: Check Blacklist
            for blocked in self.restricted_paths:
                try:
                    if target == blocked or blocked in target.parents:
                        return False, f"Access denied: '{target}' is a restricted system path."
                except Exception:
                    continue

            return True, "Safe"

        except Exception as e:
            return False, f"Invalid path format: {str(e)}"

    def _validate_state_integrity(self, tool: str, args: Dict) -> Tuple[bool, str]:
        """
        Ensures the environment state matches the tool's requirements.
        Handles race conditions where a file might disappear between confirmation and execution.
        """
        try:
            # 1. Requirements for Deletion/Move/Read (Source MUST exist)
            if tool in ['delete_file', 'move_file', 'copy_file', 'read_file', 'get_file_info', 'rename_item',
                        'open_file']:
                # Determine which arg holds the source path
                path_key = 'source' if tool in ['move_file', 'copy_file'] else 'path'
                if tool == 'rename_item': path_key = 'old_path'

                path_val = args.get(path_key)
                if path_val == "NOT FOUND":
                    return False, f"The item '{path_key}' could not be located."

                target = Path(path_val).resolve()
                if not target.exists():
                    return False, f"The item '{target.name}' no longer exists (it may have been deleted externally)."

            # 2. Requirements for Creation (Target SHOULD NOT exist)
            # This prevents overwriting if a file appeared during the wait time
            if tool in ['create_file', 'create_folder']:
                path_val = args.get('path')
                if path_val != "NOT FOUND":
                    target = Path(path_val).resolve()
                    if target.exists():
                        return False, f"A item named '{target.name}' was created while waiting. Operation aborted to prevent overwrite."

            return True, "State Valid"

        except Exception as e:
            # If path resolution fails during this check, assume unsafe
            return False, f"Path resolution error during integrity check: {str(e)}"