from enum import Enum
from typing import Tuple


class RiskLevel(Enum):
    SAFE = "SAFE"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


class SecurityManager:
    def __init__(self):
        self.risk_policy = {
            # --- SAFE (Read/Open) ---
            'read_file': RiskLevel.SAFE,
            'list_directory': RiskLevel.SAFE,
            'get_file_info': RiskLevel.SAFE,
            'count_lines': RiskLevel.SAFE,
            'get_file_hash': RiskLevel.SAFE,
            'compare_files': RiskLevel.SAFE,
            'find_files_by_name': RiskLevel.SAFE,
            'find_files_containing_text': RiskLevel.SAFE,
            'get_system_specs': RiskLevel.SAFE,
            'get_disk_usage': RiskLevel.SAFE,
            'get_user_context': RiskLevel.SAFE,
            'get_running_processes': RiskLevel.SAFE,
            'chat': RiskLevel.SAFE,

            # Apps & Windows
            'open_app': RiskLevel.SAFE,
            'open_terminal': RiskLevel.SAFE,
            'open_browser': RiskLevel.SAFE,
            'open_file_explorer': RiskLevel.SAFE,
            'open_task_manager': RiskLevel.SAFE,
            'open_settings': RiskLevel.SAFE,
            'show_file_properties': RiskLevel.SAFE,
            'minimize_all_windows': RiskLevel.SAFE,
            'get_trash_items': RiskLevel.SAFE,

            # --- HIGH (Modify/Close/Lock) ---
            'create_file': RiskLevel.HIGH,
            'create_folder': RiskLevel.HIGH,
            'move_file': RiskLevel.HIGH,
            'copy_file': RiskLevel.HIGH,
            'rename_item': RiskLevel.HIGH,
            'delete_file': RiskLevel.HIGH,
            'append_to_file': RiskLevel.HIGH,
            'prepend_to_file': RiskLevel.HIGH,
            'replace_text': RiskLevel.HIGH,
            'compress_item': RiskLevel.HIGH,
            'extract_archive': RiskLevel.HIGH,
            'create_symlink': RiskLevel.HIGH,
            'open_file': RiskLevel.SAFE,
            'download_file': RiskLevel.HIGH,

            # System State
            'close_app': RiskLevel.SAFE,
            'close_terminal': RiskLevel.SAFE,
            'close_browser': RiskLevel.SAFE,
            'close_settings': RiskLevel.SAFE,
            'close_file_properties': RiskLevel.SAFE,  # Safe to close info windows
            'lock_screen': RiskLevel.HIGH,
            'empty_trash': RiskLevel.HIGH,

            # --- CRITICAL ---
            'permanently_delete': RiskLevel.HIGH,
            'empty_folder': RiskLevel.HIGH,
        }

    def validate_action(self, action: str, intent: dict) -> Tuple[bool, str, RiskLevel]:
        if action not in self.risk_policy:
            return False, f"Unknown action '{action}'", RiskLevel.BLOCKED

        risk = self.risk_policy[action]
        if action == 'permanently_delete':
            path = intent.get('path', '')
            if any(x in path for x in ['Windows', 'System32', '/etc', '/var']):
                return False, "Targeting system directories blocked.", RiskLevel.BLOCKED

        return True, "Action allowed.", risk