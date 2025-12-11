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
        self.llm = LocalLLMClient(model_name="llama3")
        self.files = FileManager()
        self.sys_ops = SystemOps()
        self.sys_info = SystemInfo()
        self.filter_engine = FilterEngine()
        self.guard = SecurityManager()
        self._pending_actions = {}
        self.short_term_memory = []

    def process_request(self, user_input: str) -> dict:
        recent_history = "\n".join(self.short_term_memory[-10:])
        intent = self.llm.parse_intent(user_input, history_context=recent_history)

        action = intent.get('action')
        if action == 'error':
            return {"status": "ERROR", "message": f"LLM Error: {intent.get('message')}", "intent": intent}

        try:
            # PATH RESOLUTION
            if 'destination' in intent:
                p = self._resolve_path(intent['destination'])
                if p == "NOT FOUND": p = Path.home() / intent['destination']
                intent['resolved_dst'] = str(p)
                intent['destination'] = str(p)

            if 'filters' in intent:
                # Batch Mode
                search_str = intent.get('source') or intent.get('path') or "."
                search_root = self._resolve_path(search_str)
                if search_root == "NOT FOUND":
                    return {"status": "ERROR", "message": f"Folder '{search_str}' not found.", "intent": intent}

                matching_files = self.filter_engine.apply_filters(search_root, intent['filters'])
                if not matching_files:
                    self._add_to_memory(action, "INFO", "No matching files.")
                    return {"status": "SUCCESS", "message": "No matching files.", "intent": intent}

                intent['batch_targets'] = [str(f) for f in matching_files]
                return self._trigger_confirmation(intent, f"Batch {action} on {len(matching_files)} items.",
                                                  RiskLevel.HIGH.value)

            else:
                # Single Mode
                for key in ['source', 'path']:
                    if key in intent:
                        p = self._resolve_path(intent[key])
                        intent[key] = str(p) if p != "NOT FOUND" else "NOT FOUND"
                        if key == 'source': intent['resolved_src'] = intent[key]
                        if key == 'path': intent['resolved_path'] = intent[key]

                is_allowed, reason, risk = self.guard.validate_action(action, intent)
                if not is_allowed or risk == RiskLevel.BLOCKED:
                    self._add_to_memory(action, "BLOCKED", reason)
                    return {"status": "BLOCKED", "message": reason, "risk": risk.value, "intent": intent}
                if risk == RiskLevel.HIGH:
                    return self._trigger_confirmation(intent, reason, risk.value)

            result = self._run_execution(intent)
            return {"status": "SUCCESS", "message": result, "intent": intent}

        except Exception as e:
            return {"status": "ERROR", "message": str(e), "intent": intent}

    def execute_confirmed_action(self, action_id: str) -> dict:
        if action_id not in self._pending_actions:
            return {"status": "ERROR", "message": "Timeout."}
        intent = self._pending_actions.pop(action_id)
        try:
            result = self._run_execution(intent)
            return {"status": "SUCCESS", "message": result}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def _trigger_confirmation(self, intent, reason, risk):
        aid = str(uuid.uuid4())[:8]
        self._pending_actions[aid] = intent
        return {"status": "NEEDS_CONFIRMATION", "message": reason, "action_id": aid, "risk": risk, "intent": intent}

    def _run_execution(self, intent):
        action = intent.get('action')
        if action == 'chat':
            msg = intent.get('message', "")
            self._add_to_memory("chat", "SUCCESS", msg)
            return msg

        final_msg = ""
        if 'batch_targets' in intent:
            results = []
            for fp in intent['batch_targets']:
                s_intent = intent.copy()
                s_intent['resolved_src'] = fp
                s_intent['resolved_path'] = fp
                results.append(f"{Path(fp).name}: {self._run_single_tool(s_intent)}")
            final_msg = f"Batch Complete.\n" + "\n".join(results[:5])
        else:
            final_msg = self._run_single_tool(intent)

        self._add_to_memory(action, "SUCCESS", final_msg)
        return final_msg

    def _run_single_tool(self, intent):
        action = intent.get('action')
        path = intent.get('resolved_path')
        src = intent.get('resolved_src')
        dst = intent.get('resolved_dst')

        # --- FILES ---
        if action == 'move_file': return self.files.move_file(src, dst)
        if action == 'copy_file': return self.files.copy_file(src, dst)
        if action == 'create_file': return self.files.create_file(path, intent.get('content', ''))
        if action == 'create_folder': return self.files.create_folder(path)
        if action == 'rename_item': return self.files.rename_item(path, intent.get('new_name'))
        if action == 'delete_file': return self.files.delete_file(path)
        if action == 'permanently_delete': return self.files.permanently_delete(path)
        if action == 'empty_folder': return self.files.empty_folder(path)
        if action == 'list_directory': return self.files.list_directory(path)
        if action == 'read_file': return self.files.read_file(path)
        if action == 'get_file_info': return str(self.files.get_file_info(path))
        if action == 'count_lines': return self.files.count_lines(path)
        if action == 'get_file_hash': return self.files.get_file_hash(path)
        if action == 'compare_files': return self.files.compare_files(path, dst)
        if action == 'append_to_file': return self.files.append_to_file(path, intent.get('content', ''))
        if action == 'prepend_to_file': return self.files.prepend_to_file(path, intent.get('content', ''))
        if action == 'replace_text': return self.files.replace_text(path, intent.get('old_text'),
                                                                    intent.get('new_text'))
        if action == 'search_files': return self.files.search_files_ranked(intent.get('term', ''))
        if action == 'find_files_by_name': return self.files.find_files_by_name(path, intent.get('pattern'))
        if action == 'find_files_containing_text': return self.files.find_files_containing_text(path,
                                                                                                intent.get('text'))
        if action == 'compress_item': return self.files.compress_item(path, intent.get('format', 'zip'))
        if action == 'extract_archive': return self.files.extract_archive(path, dst)
        if action == 'download_file': return self.files.download_file(intent.get('url'), dst)
        if action == 'create_symlink': return self.files.create_symlink(src, dst)

        # --- SYSTEM OPS ---
        if action == 'open_app': return self.sys_ops.open_app(intent.get('app_name'))
        if action == 'close_app': return self.sys_ops.close_app(intent.get('app_name'))
        if action == 'open_terminal': return self.sys_ops.open_terminal()
        if action == 'close_terminal': return self.sys_ops.close_terminal()
        if action == 'open_browser': return self.sys_ops.open_browser(intent.get('url', 'https://google.com'))
        if action == 'close_browser': return self.sys_ops.close_browser()
        if action == 'open_file_explorer': return self.sys_ops.open_file_explorer(path or ".")
        if action == 'open_task_manager': return self.sys_ops.open_task_manager()
        if action == 'minimize_all_windows': return self.sys_ops.minimize_all_windows()
        if action == 'lock_screen': return self.sys_ops.lock_screen()
        # UPDATED: Passing page_name or setting_name
        if action == 'open_settings': return self.sys_ops.open_settings(
            intent.get('page') or intent.get('setting_name'))
        if action == 'close_settings': return self.sys_ops.close_settings()
        if action == 'show_file_properties': return self.sys_ops.show_file_properties(path)
        if action == 'close_file_properties': return self.sys_ops.close_file_properties()
        if action == 'get_trash_items': return self.sys_ops.get_trash_items()
        if action == 'empty_trash': return self.sys_ops.empty_trash()
        if action == 'open_file': return self.sys_ops.open_app(intent.get('app_name')) if intent.get(
            'app_name') else self.files.open_file(path)

        # --- SYSTEM INFO ---
        if action == 'get_system_specs': return str(self.sys_info.get_system_specs())
        if action == 'get_disk_usage': return self.sys_info.get_disk_usage(path)
        if action == 'get_user_context': return str(self.sys_info.get_user_context())
        if action == 'get_running_processes': return self.sys_info.get_running_processes(intent.get('limit', 20))

        return f"Error: Unknown action '{action}'"

    def _add_to_memory(self, action, status, details):
        self.short_term_memory.append(f"[{status}] Action: {action} | Result: {str(details)[:200]}")

    def _resolve_path(self, path_str: str) -> Path:
        if not path_str: return "NOT FOUND"
        path = Path(path_str)
        home = Path.home()
        if path.is_absolute(): return path
        if len(path.parts) > 1:
            full_path = home / path
            if full_path.exists(): return full_path
            return full_path
        found = self._find_path_by_name(path_str)
        return found if found else "NOT FOUND"

    def _find_path_by_name(self, filename: str) -> Path:
        home = Path.home()
        for d in [home / 'Desktop', home / 'Downloads', home / 'Documents']:
            if d.exists():
                found = next(d.rglob(filename), None) or next(d.rglob(f"{filename}.*"), None)
                if found: return found
        return home / filename if (home / filename).exists() else None