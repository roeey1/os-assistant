import json
import ollama
class LocalLLMClient:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name

    def parse_intent(self, user_input: str) -> dict:
        """
        Sends the user input to the local llm and parses the JSON response
        to determine what tool to call.
        """

        # 1. Define the System Prompt
        # This tells the llm exactly how to behave and what tools are available.
        system_prompt = """
        You are an OS Assistant. Your job is to translate user natural language into JSON commands.

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
        - delete_file(path) - Deletes file

        --- SYSTEM OPERATIONS (Active) ---
        - open_app(app_name) - e.g. "Calculator", "Spotify"
        - close_app(app_name)
        - open_settings()
        - close_settings()
        - show_file_properties(path) - Opens "Get Info" / "Properties" window
        - close_file_properties()
        - get_trash_items() - Lists items in Recycle Bin/Trash
        - empty_trash(self) - empty trash

        --- SYSTEM INFO (Passive) ---
        - get_system_specs() - RAM, CPU, OS details
        - get_disk_usage() - Storage stats (default to Home if path empty)
        - get_user_context() - Current user, home dir, hostname
        - get_running_processes(limit) - Top memory consuming apps (default limit=20)

        RULES:
        - You MUST output ONLY valid JSON.
        - Do not add explanations or markdown text (like ```json).
        - If the user request is unclear or unsafe, return {"action": "error", "message": "reason"}.
        - For 'path' arguments, you can use simple names (e.g., "notes.txt") or folders ("Downloads").

        EXAMPLE 1:
        User: "Rename report.txt to final.txt"
        Response: {"action": "rename_item", "path": "report.txt", "new_name": "final.txt"}

        EXAMPLE 2:
        User: "Open the Calculator app"
        Response: {"action": "open_app", "app_name": "Calculator"}

        EXAMPLE 3:
        User: "How much RAM do I have?"
        Response: {"action": "get_system_specs"}

        EXAMPLE 4:
        User: "Show me what is in the Trash"
        Response: {"action": "get_trash_items"}
        
        EXAMPLE 5:
        User: "Create a folder called Projects"
        Response: {"action": "create_folder", "path": "Projects"}
        """

        try:
            # 2. Call the Local Model
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input},
            ])

            raw_content = response['message']['content']

            # 3. Clean the response (Local models often wrap code in ```json ... ```)
            cleaned_content = self._clean_json_string(raw_content)

            # 4. Parse JSON
            parsed_intent = json.loads(cleaned_content)
            return parsed_intent

        except json.JSONDecodeError:
            return {"action": "error", "message": "Failed to parse llm response as JSON", "raw": raw_content}
        except Exception as e:
            return {"action": "error", "message": str(e)}

    def _clean_json_string(self, text: str) -> str:
        """
        Helper to strip markdown formatting if the llm adds it.
        """
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

# --- Testing Section ---
if __name__ == "__main__":
    # Make sure Ollama app is running in the background!
    client = LocalLLMClient(model_name="llama3")
    assistant = OSAssistant()
    print("hello! please enter your request:")
    test_input = input("Enter your input: ")
    print(f"--- Testing Model: {client.model_name} ---")
    while (test_input != "close"):
        result = client.parse_intent(test_input)
        print(f"Parsed Intent: {result}")#delete later
        response = assistant.execute_intent(result)
        print(response)
        test_input = input("Enter your input: ")


