import json
import re
import ollama


class LocalLLMClient:
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name

    def parse_intent(self, user_input: str, history_context: str = "", model: str = None) -> dict:
        """
        Sends the user input to the local llm.
        'history_context' is a string containing logs of previous actions in this session.
        """
        # Determine which model to use for this specific call
        target_model = model if model else self.model_name

        # ==========================================
        # THE MASTER SYSTEM PROMPT
        # ==========================================
        base_system_prompt = """
        You are an OS Assistant. Your job is to translate user natural language into JSON commands or answer questions.

        You have access to these tools:

        --- FILE OPERATIONS (Core) ---
        - create_file(path, content) - Creates new file (overwrites if exists).
        - create_folder(path)
        - move_file(source, destination)
        - copy_file(source, destination)
        - rename_item(path, new_name) - new_name is filename only (e.g. "new.txt")
        - delete_file(path) - Moves to Trash (Recoverable).
        - permanently_delete(path) - WARNING: Unrecoverable delete.
        - empty_folder(path) - Deletes all files inside a folder.

        --- FILE OPERATIONS (Content & Edit) ---
        - read_file(path) - Returns text content.
        - append_to_file(path, content) - Adds text to the end of a file.
        - prepend_to_file(path, content) - Adds text to the beginning of a file.
        - replace_text(path, old_text, new_text) - Replaces specific string in file.
        - count_lines(path) - Returns the number of lines.

        --- FILE OPERATIONS (Advanced) ---
        - list_directory(path)
        - get_file_info(path) - Size, created date, etc.
        - get_file_hash(path) - Returns SHA256 hash.
        - compare_files(path, destination) - Returns True if content is identical.
        - search_files(term) - Smart search (ranked by relevance).
        - find_files_by_name(path, pattern) - Recursive search (e.g. pattern="*.py").
        - find_files_containing_text(path, text) - Search inside files.
        - compress_item(path, format) - format: 'zip', 'tar'.
        - extract_archive(path, destination)
        - download_file(url, destination) - Downloads from internet.
        - create_symlink(source, destination) - Creates a shortcut/link.
        - open_file(path) - Opens in default OS app (Preview, Word, etc).

        --- SYSTEM OPERATIONS (Apps & Windows) ---
        - open_app(app_name) - Generic launcher (e.g. "Spotify").
        - close_app(app_name) - Force quits app.
        - open_terminal()
        - close_terminal()
        - open_browser(url) - Defaults to Google if URL empty.
        - close_browser()
        - open_task_manager()
        - open_settings(page) - e.g. "battery", "display", "wifi", "sound", "update".
        - close_settings()
        - minimize_all_windows() - Shows Desktop.
        - lock_screen()

        --- SYSTEM OPERATIONS (Properties & Trash) ---
        - show_file_properties(path) - Opens "Get Info" / "Properties" window.
        - close_file_properties()
        - get_trash_items() - Lists items in Recycle Bin/Trash.
        - empty_trash() - Permanently deletes everything in Trash.

        --- SYSTEM INFO (Passive) ---
        - get_system_specs() - RAM, CPU, OS details.
        - get_disk_usage() - Storage stats.
        - get_user_context() - Current user, home dir, hostname.
        - get_running_processes(limit) - Top memory consuming apps (default limit=20).

        --- GENERAL ---
        - chat - Use this to reply to the user, answer questions, or summarize history.

        RULES:
        - NEVER output a path with a wildcard({'action': 'copy_file', 'source': 'yan/', 'destination': 'test'} *.pdf for example cannot be in "source" or "destination")
        1. CRITICAL: You MUST output ONLY the raw JSON string.
           - NO conversational text (e.g., "Here is the command", "Sure", "I did this").
           - NO markdown formatting (e.g., do NOT use ```json or ```).
           - The response must start with { and end with }.
        2. If the user request is unclear or unsafe, return {"action": "error", "message": "reason"}.
        3. HISTORY: If the user asks about previous actions (e.g., "what did I just do?", "what was my last action"), look at the history provided and use the 'chat' tool to answer.

        4. BATCH/FILTERING (CRITICAL): 
           If the user asks to operate on "all files", "every pdf", "all images" or uses criteria (size, date):
           - YOU MUST use "scope": "batch" and a "filters" object.
           - NEVER output a path with a wildcard (e.g. "folder/*.txt" is FORBIDDEN).
           - Set "source" to the folder path only.

           Filter Keys Allowed:
           - "extensions": List of strings (e.g. ["jpg", "png", "gif"])
           - "extension": Single string (e.g. "txt")
           - "name_contains": String (substring match)
           - "name_exact": String (exact filename match)
           - "min_size": String with unit (e.g. "500 KB", "5 MB", "1 GB")
           - "max_size": String with unit
           - "modified_after": Date String (YYYY-MM-DD)
           - "modified_before": Date String (YYYY-MM-DD)
           - "created_after": Date String (YYYY-MM-DD)
           - "created_before": Date String (YYYY-MM-DD)

           Set "source" to the folder to search in (default "cwd" if not specified).

        --- EXAMPLES ---

        EXAMPLE 1 (Standard Action):
        User: "Rename report.txt to final.txt"
        Response: {"action": "rename_item", "path": "report.txt", "new_name": "final.txt"}

        EXAMPLE 2 (Content Editing):
        User: "Add 'Reviewed by John' to the end of notes.txt"
        Response: {"action": "append_to_file", "path": "notes.txt", "content": "Reviewed by John"}

        EXAMPLE 3 (Complex Filter/Batch Request):
        User: "Delete all jpg and png images larger than 10MB in Downloads modified after July 1st 2024"
        Response: {
          "action": "delete_file",
          "scope": "batch",
          "source": "Downloads",
          "filters": {
            "extensions": ["jpg", "png"],
            "min_size": "10 MB",
            "modified_after": "2024-07-01"
          }
        }

        EXAMPLE 4 (System Ops):
        User: "Open battery settings"
        Response: {"action": "open_settings", "page": "battery"}

        EXAMPLE 5 (Archive):
        User: "Zip the Photos folder"
        Response: {"action": "compress_item", "path": "Photos", "format": "zip"}

        
        EXAMPLE 6 (Batch Move):
        User: "Move all pdf files from Desktop to Documents"
        Response: {
          "action": "move_file",
          "scope": "batch",
          "source": "Desktop",
          "destination": "Documents",
          "filters": {
            "extension": "pdf"
          }
        }
        """
        # 2. Inject History (The "Memory")
        if history_context:
            final_system_prompt = f"{base_system_prompt}\n\n=== HISTORY OF ACTIONS (Use this to answer user questions) ===\n{history_context}\n============================================================"
        else:
            final_system_prompt = base_system_prompt

        raw_content = ""
        try:
            # 3. Call the Local Model
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': final_system_prompt},
                {'role': 'user', 'content': user_input},
            ])

            raw_content = response['message']['content']

            # Use the robust cleaning method (now returns the JSON string or raises error)
            cleaned_json_string = self._extract_json_string(raw_content)
            parsed_intent = json.loads(cleaned_json_string)
            parsed_intent = self._sanitize_wildcards(parsed_intent)

            # Debug Print
            print(f"\n[DEBUG] LLM Raw JSON Response: {parsed_intent}\n")

            return parsed_intent

        except (ValueError, json.JSONDecodeError) as e:
            return {
                "action": "error",
                "message": f"Failed to parse llm response: {str(e)}",
                "raw": raw_content
            }
        except Exception as e:
            return {"action": "error", "message": str(e)}



    def _extract_json_string(self, text: str) -> str:
        """
        Robustly extracts the JSON block from the LLM response.
        Handles Markdown fences and conversational prefixes.
        """
        if not text:
            raise ValueError("Empty response from LLM")

        # 1. Try to find a JSON block inside Markdown fences (```json ... ``` or just ``` ... ```)
        # The pattern looks for ``` followed optionally by 'json' (case insensitive),
        # then captures content inside the fences.
        pattern = r"```(?:json)?\s*(.*?)```"
        fenced_json = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if fenced_json:
            candidate = fenced_json.group(1).strip()
            try:
                # Validation: Check if it actually parses
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass  # Fall through to try other methods if the fenced content was invalid

        # 2. Look for ANY JSON object in the entire text
        # This regex looks for the first occurrence of { followed by anything, ending with the last }
        brace_json = re.search(r"(\{[\s\S]*\})", text, re.DOTALL)
        if brace_json:
            candidate = brace_json.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # 3. Last resort fallback: Simple strip
        # (if the whole text is just JSON with no braces detected or parsing failed previously)
        try:
            json.loads(text.strip())
            return text.strip()
        except json.JSONDecodeError:
            pass

        raise ValueError("No valid JSON object found in LLM response")
    def _sanitize_wildcards(self, intent: dict) -> dict:
        """
        Fixes LLM mistakes where it puts wildcards (e.g., /path/*.pdf) directly in the path.
        Converts them into proper 'batch' scope and 'filters'.
        """
        import re
        
        # Keys that might contain paths
        path_keys = ['source', 'path', 'destination']
        
        # Regex to catch path ending in /*.ext or \*.ext
        # Group 1: The clean path
        # Group 2: The extension (without dot)
        wildcard_pattern = r"^(.*)[/\\]\*\.(\w+)$"

        for key in path_keys:
            if key not in intent:
                continue

            value = intent[key]
            match = re.search(wildcard_pattern, value)

            if match:
                clean_path = match.group(1)
                extension = match.group(2)

                # 1. Clean the path in the JSON
                intent[key] = clean_path
                
                # 2. Only apply filters if the wildcard was in 'source' or 'path'
                # (Wildcards in destination are usually just errors to be removed)
                if key in ['source', 'path']:
                    intent['scope'] = 'batch'
                    
                    if 'filters' not in intent:
                        intent['filters'] = {}
                    
                    # Add extension to filters
                    # We use a list to be safe, or just append if it exists
                    if 'extensions' not in intent['filters']:
                         intent['filters']['extensions'] = []
                    
                    if extension not in intent['filters']['extensions']:
                        intent['filters']['extensions'].append(extension)

        return intent