import os
from pathlib import Path
from enum import Enum
from typing import Dict, Tuple


class RiskLevel(Enum):
    SAFE = "SAFE"  # Read-only (List, Get Info)
    MODERATE = "MODERATE"  # Non-destructive write (Create, Copy)
    HIGH = "HIGH"  # Destructive (Delete, Move, Rename, Empty Trash)
    BLOCKED = "BLOCKED"  # System paths / unauthorized areas


class SecurityManager:
    """
    Guardrails for OS Assistant.
    Validates paths and classifies operation risks before execution.
    """

    def __init__(self):
        self.user_home = Path.home().resolve()

        # 1. Define Risk Levels for every tool we built
        self.tool_risks = {
            # Files
            "list_directory": RiskLevel.SAFE,
            "read_file": RiskLevel.SAFE,
            "get_file_info": RiskLevel.SAFE,
            "create_file": RiskLevel.MODERATE,
            "create_folder": RiskLevel.MODERATE,
            "copy_file": RiskLevel.MODERATE,
            "move_file": RiskLevel.HIGH,  # Moving to wrong place is bad
            "rename_item": RiskLevel.HIGH,  # Renaming critical files is bad
            "delete_file": RiskLevel.HIGH,  # Destructive

            # System Info (All Safe)
            "get_system_specs": RiskLevel.SAFE,
            "get_disk_usage": RiskLevel.SAFE,
            "get_running_processes": RiskLevel.SAFE,
            "get_user_context": RiskLevel.SAFE,

            # System Ops
            "open_app": RiskLevel.MODERATE,
            "open_settings": RiskLevel.MODERATE,
            "show_file_properties": RiskLevel.SAFE,
            "get_trash_items": RiskLevel.SAFE,
            "close_app": RiskLevel.HIGH,  # Closing unsaved work is dangerous
            "close_settings": RiskLevel.SAFE,
            "close_file_properties": RiskLevel.SAFE,
            "empty_trash": RiskLevel.HIGH  # Irreversible
        }

        # 2. Define Restricted Paths (Blacklist)
        # These are paths the AI should NEVER touch.
        self.restricted_paths = [
            Path("/System"),  # macOS System
            Path("/usr"),  # Unix binaries
            Path("/bin"),
            Path("/etc"),
            Path("/var"),
            Path("C:\\Windows"),  # Windows System
            Path("C:\\Program Files"),
            Path("C:\\Program Files (x86)"),
        ]

    def validate_action(self, tool_name: str, args: Dict) -> Tuple[bool, str, RiskLevel]:
        """
        Main entry point. Checks if the action is allowed and returns its risk level.
        Returns: (is_allowed, reason, risk_level)
        """
        # 1. Unknown Tool Check
        if tool_name not in self.tool_risks:
            return False, f"Unknown tool '{tool_name}' blocked.", RiskLevel.BLOCKED

        risk = self.tool_risks[tool_name]

        # 2. Path Safety Check
        # We extract any argument that looks like a path
        paths_to_check = []
        if 'path' in args: paths_to_check.append(args['path'])
        if 'source' in args: paths_to_check.append(args['source'])
        if 'destination' in args: paths_to_check.append(args['destination'])
        if 'old_path' in args: paths_to_check.append(args['old_path'])

        for p in paths_to_check:
            is_safe, reason = self._is_path_safe(p)
            if not is_safe:
                return False, reason, RiskLevel.BLOCKED

        # 3. Approved
        return True, "Action permitted.", risk

    def _is_path_safe(self, path_str: str) -> Tuple[bool, str]:
        """
        Internal logic to check if a path is within allowed bounds.
        """
        try:
            # Resolve resolves symlinks and '..' (preventing traversal attacks)
            # expanduser handles '~'
            target = Path(path_str).expanduser().resolve()

            # Rule 1: Root protection
            # Prevent operations directly on "/" or "C:\"
            if target.parent == target:  # This checks if it's a root
                return False, f"Access denied: Cannot operate on system root '{target}'."

            # Rule 2: Check Blacklist
            for blocked in self.restricted_paths:
                # We check if the target IS the blocked path or IS INSIDE it
                # e.g. /System/Library is inside /System
                try:
                    # check if 'blocked' is a parent of 'target' or equal
                    if target == blocked or blocked in target.parents:
                        return False, f"Access denied: '{target}' is a restricted system path."
                except Exception:
                    continue

            return True, "Safe"

        except Exception as e:
            # If we can't parse the path, block it to be safe
            return False, f"Invalid path format: {str(e)}"