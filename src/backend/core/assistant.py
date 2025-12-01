import uuid
from pathlib import Path

# Imports
from src.llm.Client import LocalLLMClient  # <--- Moved here
from src.backend.tools.files import FileManager
from src.backend.tools.system_ops import SystemOps
from src.backend.tools.sys_info import SystemInfo
from src.backend.core.guard import SecurityManager, RiskLevel


class OSAssistant:
    def __init__(self):
        # Initialize the Brain (LLM) inside the Assistant
        self.llm = LocalLLMClient(model_name="llama3")

        # Initialize Tools & Safety
        self.files = FileManager()
        self.sys_ops = SystemOps()
        self.sys_info = SystemInfo()
        self.guard = SecurityManager()

        # Secure storage for pending actions
        self._pending_actions = {}

    def process_request(self, user_input: str) -> dict:
        """
        PHASE 1: ANALYSIS & SAFETY CHECK
        1. Calls LLM to parse intent.
        2. Resolves paths.
        3. Validates security.

        Returns a dict containing 'status', 'message', and the parsed 'intent'.
        """
        # 1. PARSE INTENT (LLM)
        intent = self.llm.parse_intent(user_input)
        print(f"DEBUG: Parsed Intent from LLM: {intent}")
        # Check for LLM errors
        action = intent.get('action')
        if action == 'error':
            return {
                "status": "ERROR",
                "message": f"LLM Error: {intent.get('message')}",
                "intent": intent
            }

        try:
            # 2. RESOLVE PATHS & INJECT INTO INTENT
            if 'path' in intent:
                p = self._resolve_path(intent['path'])
                intent['path'] = str(p) if p != "NOT FOUND" else "NOT FOUND"
                intent['resolved_path'] = intent['path']

            if 'source' in intent:
                p = self._resolve_path(intent['source'])
                intent['source'] = str(p) if p != "NOT FOUND" else "NOT FOUND"
                intent['resolved_src'] = intent['source']

            if 'destination' in intent:
                p = self._resolve_path(intent['destination'])
                if p == "NOT FOUND":
                    p = Path.home() / intent['destination']
                intent['destination'] = str(p)
                intent['resolved_dst'] = intent['destination']

            # 3. SECURITY CHECK
            is_allowed, reason, risk = self.guard.validate_action(action, intent)

            if not is_allowed or risk == RiskLevel.BLOCKED:
                return {
                    "status": "BLOCKED",
                    "message": reason,
                    "risk": risk.value,
                    "intent": intent
                }

            if risk == RiskLevel.HIGH:
                # PAUSE FOR CONFIRMATION
                action_id = str(uuid.uuid4())[:8]
                self._pending_actions[action_id] = intent

                return {
                    "status": "NEEDS_CONFIRMATION",
                    "message": f"Security Check: {reason} (Risk: {risk.value})",
                    "action_id": action_id,
                    "risk": risk.value,
                    "intent": intent
                }

            # 4. IF SAFE, EXECUTE IMMEDIATELY
            result = self._run_execution(intent)
            return {
                "status": "SUCCESS",
                "message": result,
                "intent": intent
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "message": str(e),
                "intent": intent
            }

    def execute_confirmed_action(self, action_id: str) -> dict:
        """
        PHASE 2: EXECUTION
        Called by Main/UI when user confirms a HIGH risk action.
        """
        if action_id not in self._pending_actions:
            return {"status": "ERROR", "message": "Transaction timed out or invalid ID."}

        intent = self._pending_actions.pop(action_id)

        try:
            result = self._run_execution(intent)
            return {"status": "SUCCESS", "message": result}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def _run_execution(self, intent: dict) -> str:
        """
        Private method: The actual tool execution logic.
        """
        action = intent.get('action')
        path = intent.get('resolved_path')
        src = intent.get('resolved_src')
        dst = intent.get('resolved_dst')

        # --- VALIDATION ---
        if action in ['read_file', 'open_file', 'get_file_info', 'rename_item', 'show_file_properties']:
            if path == "NOT FOUND": return f"Error: File '{intent.get('path')}' not found."

        if action in ['move_file', 'copy_file']:
            if src == "NOT FOUND": return f"Error: Source '{intent.get('source')}' not found."

        # --- EXECUTE TOOLS ---
        # Files
        if action == 'move_file': return self.files.move_file(src, dst)
        if action == 'copy_file': return self.files.copy_file(src, dst)
        if action == 'create_file': return self.files.create_file(path, intent.get('content', ''))
        if action == 'create_folder': return self.files.create_folder(path)
        if action == 'rename_item': return self.files.rename_item(path, intent['new_name'])
        if action == 'list_directory': return self.files.list_directory(path)
        if action == 'read_file': return self.files.read_file(path)
        if action == 'open_file': return self.files.open_file(path)
        if action == 'get_file_info': return str(self.files.get_file_info(path))
        if action == 'delete_file': return self.files.delete_file(path)

        # System Ops
        if action == 'open_app': return self.sys_ops.open_app(intent['app_name'])
        if action == 'close_app': return self.sys_ops.close_app(intent['app_name'])
        if action == 'open_settings': return self.sys_ops.open_settings()
        if action == 'close_settings': return self.sys_ops.close_settings()
        if action == 'show_file_properties': return self.sys_ops.show_file_properties(path)
        if action == 'close_file_properties': return self.sys_ops.close_file_properties()
        if action == 'get_trash_items': return self.sys_ops.get_trash_items()

        # System Info
        if action == 'get_system_specs': return str(self.sys_info.get_system_specs())
        if action == 'get_disk_usage': return self.sys_info.get_disk_usage(path)
        if action == 'get_user_context': return str(self.sys_info.get_user_context())
        if action == 'get_running_processes': return self.sys_info.get_running_processes(intent.get('limit', 20))

        return f"Error: Unknown action '{action}'."

    def _resolve_path(self, path_str: str) -> Path:
        if not path_str: return "NOT FOUND"
        path = Path(path_str)
        home = Path.home()
        if path.is_absolute(): return path
        if len(path.parts) > 1:
            full_path = home / path
            if full_path.exists(): return full_path
            parent = full_path.parent
            if parent.exists():
                match = next(parent.glob(f"{full_path.name}.*"), None)
                if match: return match
            return full_path
        found = self._find_path_by_name(path_str)
        if found: return found
        return "NOT FOUND"

    def _find_path_by_name(self, filename: str) -> Path:
        home = Path.home()
        search_dirs = [home / 'Desktop', home / 'Downloads', home / 'Documents', home / 'Pictures']
        patterns = [filename, f"{filename}.*"]
        for directory in search_dirs:
            if not directory.exists(): continue
            try:
                for pattern in patterns:
                    found = next(directory.rglob(pattern), None)
                    if found: return found
            except (PermissionError, OSError):
                continue
        if (home / filename).exists(): return home / filename
        return None