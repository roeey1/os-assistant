import uuid
from pathlib import Path

# Imports
from src.llm.Client import LocalLLMClient
from src.backend.tools.files import FileManager
from src.backend.tools.system_ops import SystemOps
from src.backend.tools.sys_info import SystemInfo
from src.backend.core.filter import FilterEngine
from src.backend.core.guard import SecurityManager, RiskLevel


class OSAssistant:
    def __init__(self):
        # 1. The Brain
        self.llm = LocalLLMClient(model_name="llama3")

        # 2. The Tools
        self.files = FileManager()
        self.sys_ops = SystemOps()
        self.sys_info = SystemInfo()
        self.filter_engine = FilterEngine()

        # 3. The Shield
        self.guard = SecurityManager()

        # 4. State Management
        self._pending_actions = {}
        self.short_term_memory = []

    def process_request(self, user_input: str) -> dict:
        """
        PHASE 1: ANALYSIS & SAFETY CHECK
        """
        # --- A. CALL LLM ---
        recent_history = "\n".join(self.short_term_memory[-10:])
        intent = self.llm.parse_intent(user_input, history_context=recent_history)

        action = intent.get('action')
        if action == 'error':
            return {"status": "ERROR", "message": f"LLM Error: {intent.get('message')}", "intent": intent}

        try:
            # --- B. PATH RESOLUTION ---
            # 1. Always resolve Destination if present (Used in both Batch and Single)
            if 'destination' in intent:
                p = self._resolve_path(intent['destination'])
                if p == "NOT FOUND":
                    # If dest doesn't exist, assume relative to home
                    p = Path.home() / intent['destination']
                intent['resolved_dst'] = str(p)
                intent['destination'] = str(p)  # Update for Guard check

            # 2. Handle Batch vs Single Source Resolution
            if 'filters' in intent:
                # Batch: Source is just a search root
                search_str = intent.get('source') or intent.get('path') or "."
                search_root = self._resolve_path(search_str)

                if search_root == "NOT FOUND":
                    return {"status": "ERROR", "message": f"Search folder '{search_str}' not found.", "intent": intent}

                # Run Filter Engine
                matching_files = self.filter_engine.apply_filters(search_root, intent['filters'])

                if not matching_files:
                    msg = "No files found matching criteria."
                    self._add_to_memory(action, "INFO", msg)
                    return {"status": "SUCCESS", "message": msg, "intent": intent}

                # Store targets
                intent['batch_targets'] = [str(f) for f in matching_files]

                # Batch is always High Risk
                return self._trigger_confirmation(
                    intent,
                    reason=f"Batch Operation: {action} on {len(matching_files)} files.",
                    risk=RiskLevel.HIGH.value
                )

            else:
                # Single: Source/Path are specific targets
                for key in ['source', 'path']:
                    if key in intent:
                        p = self._resolve_path(intent[key])
                        intent[key] = str(p) if p != "NOT FOUND" else "NOT FOUND"
                        intent[f'resolved_{key[:3]}'] = intent[
                            key]  # resolved_src / resolved_pat... wait, let's correspond
                        # Mapping: 'source' -> 'resolved_src', 'path' -> 'resolved_path'
                        if key == 'source': intent['resolved_src'] = intent[key]
                        if key == 'path': intent['resolved_path'] = intent[key]

                # --- C. SECURITY CHECK (Single Only - Batch checked above) ---
                is_allowed, reason, risk = self.guard.validate_action(action, intent)

                if not is_allowed or risk == RiskLevel.BLOCKED:
                    self._add_to_memory(action, "BLOCKED", reason)
                    return {"status": "BLOCKED", "message": reason, "risk": risk.value, "intent": intent}

                if risk == RiskLevel.HIGH:
                    return self._trigger_confirmation(intent, reason, risk.value)

            # --- D. EXECUTE (If Safe) ---
            result = self._run_execution(intent)
            return {"status": "SUCCESS", "message": result, "intent": intent}

        except Exception as e:
            return {"status": "ERROR", "message": str(e), "intent": intent}

    def execute_confirmed_action(self, action_id: str) -> dict:
        """PHASE 2: EXECUTION (Post-Confirmation)"""
        if action_id not in self._pending_actions:
            return {"status": "ERROR", "message": "Transaction timed out."}

        intent = self._pending_actions.pop(action_id)

        try:
            result = self._run_execution(intent)
            return {"status": "SUCCESS", "message": result}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # --- INTERNAL HELPERS ---

    def _trigger_confirmation(self, intent: dict, reason: str, risk: str) -> dict:
        action_id = str(uuid.uuid4())[:8]
        self._pending_actions[action_id] = intent
        return {
            "status": "NEEDS_CONFIRMATION",
            "message": f"Security Check: {reason}",
            "action_id": action_id,
            "risk": risk,
            "intent": intent
        }

    def _run_execution(self, intent: dict) -> str:
        """
        Manager: Decides if we run a Loop or a Single Action.
        Delegates work to _run_single_tool to avoid code duplication.
        """
        action = intent.get('action')

        if action == 'chat':
            msg = intent.get('message', "")
            self._add_to_memory("chat", "SUCCESS", msg)
            return msg

        final_result_msg = ""

        # 1. BATCH MODE
        if 'batch_targets' in intent:
            results = []

            for file_path in intent['batch_targets']:
                # Clone intent and override target paths for this specific file
                single_intent = intent.copy()
                single_intent['resolved_src'] = file_path
                single_intent['resolved_path'] = file_path
                # Destination is already in single_intent['resolved_dst']

                # Execute Logic
                res = self._run_single_tool(single_intent)
                results.append(f"{Path(file_path).name}: {res}")

            final_result_msg = f"Batch Processed {len(results)} items.\n" + "\n".join(results[:5])
            if len(results) > 5: final_result_msg += "\n...and more."

        # 2. SINGLE MODE
        else:
            final_result_msg = self._run_single_tool(intent)

        # 3. MEMORY UPDATE (Once per high-level request)
        status = "SUCCESS" if "Success" in final_result_msg or "Disk" in final_result_msg or "Process" in final_result_msg else "ERROR"
        self._add_to_memory(action, status, final_result_msg)

        return final_result_msg

    def _run_single_tool(self, intent: dict) -> str:
        """
        The Worker: Contains the logic for mapping Actions to Tools.
        Called once for single ops, or N times for batch ops.
        """
        action = intent.get('action')

        # Get paths (populated either by resolve_path OR by batch loop)
        path = intent.get('resolved_path')
        src = intent.get('resolved_src')
        dst = intent.get('resolved_dst')

        # --- VALIDATION ---
        if action in ['read_file', 'open_file', 'get_file_info', 'rename_item', 'show_file_properties', 'delete_file']:
            if path == "NOT FOUND": return f"Error: File '{intent.get('path')}' not found."
        if action in ['move_file', 'copy_file']:
            if src == "NOT FOUND": return f"Error: Source '{intent.get('source')}' not found."

        # --- TOOL MAPPING ---
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
        if action == 'open_app': return self.sys_ops.open_app(intent.get('app_name'))
        if action == 'close_app': return self.sys_ops.close_app(intent.get('app_name'))
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

        return f"Error: Unknown action '{action}'"

    def _add_to_memory(self, action, status, details):
        clean_details = str(details).replace('\n', ' ')[:200]
        entry = f"[{status}] Action: {action} | Result: {clean_details}"
        self.short_term_memory.append(entry)
        print(f"DEBUG: Memory Added -> {entry}")

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