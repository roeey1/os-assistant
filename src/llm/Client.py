import json
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
        You are an OS Assistant. Your job is to translate user natural language into JSON commands or answer qustions.

        You have access to these tools:

        --- FILE OPERATIONS ---
        - create_file(path, content)
        - create_folder(path)
        - move_file(source, destination)
        - copy_file(source, destination)
        - rename_item(path, new_name) - new_name is filename only (e.g. "new.txt")
        - list_directory(path)
        - read_file(path) - Returns text content
        - open_file(path) - Opens in default OS app (Preview, Word, etc)
        - get_file_info(path) - Size, created date, etc.
        - delete_file(path) - Deletes file to Trash

        --- SYSTEM OPERATIONS (Active) ---
        - open_app(app_name) - e.g. "Calculator", "Spotify"
        - close_app(app_name)
        - open_settings()
        - close_settings()
        - show_file_properties(path) - Opens "Get Info" / "Properties" window
        - close_file_properties()
        - get_trash_items() - Lists items in Recycle Bin/Trash

        --- SYSTEM INFO (Passive) ---
        - get_system_specs() - RAM, CPU, OS details
        - get_disk_usage() - Storage stats (default to Home if path empty)
        - get_user_context() - Current user, home dir, hostname
        - get_running_processes(limit) - Top memory consuming apps (default limit=20)

        --- GENERAL ---
        - chat - Use this to reply to the user, answer questions, or summarize history.

        RULES:
        1. You MUST output ONLY valid JSON. Do not add markdown (```json).
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

        EXAMPLE 2 (History/Chat Question):
        User: "What was the last file I moved?"
        Response: {"action": "chat", "message": "You just moved 'data.csv' to the 'backup' folder."}

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

        EXAMPLE 4 (Wildcard Correction - Move):
        User: "Move all pdf files from test folder to yan folder"
        Response: {
          "action": "move_file",
          "scope": "batch",
          "source": "test",
          "destination": "yan",
          "filters": {
            "extensions": ["pdf"]
          }
        }

        EXAMPLE 5 (Wildcard Correction - Open):
        User: "Open all text files in Documents"
        Response: {
          "action": "open_file",
          "scope": "batch",
          "source": "Documents",
          "filters": {
            "extensions": ["txt"]
          }
        }
        """

        # 2. Inject History (The "Memory")
        if history_context:
            final_system_prompt = f"{base_system_prompt}\n\n=== HISTORY OF ACTIONS (Use this to answer user questions) ===\n{history_context}\n============================================================"
        else:
            final_system_prompt = base_system_prompt

        try:
            # 3. Call the Local Model
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': final_system_prompt},
                {'role': 'user', 'content': user_input},
            ])

            raw_content = response['message']['content']
            cleaned_content = self._clean_json_string(raw_content)
            parsed_intent = json.loads(cleaned_content)

            # Debug Print
            print(f"\n[DEBUG] LLM Raw JSON Response: {parsed_intent}\n")

            return parsed_intent

        except json.JSONDecodeError:
            return {"action": "error", "message": "Failed to parse llm response as JSON", "raw": raw_content}
        except Exception as e:
            return {"action": "error", "message": str(e)}

    def _clean_json_string(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()