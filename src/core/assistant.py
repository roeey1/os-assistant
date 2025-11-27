import os
from pathlib import Path

# Import the tools we created earlier
# Note: PyCharm might underline these if your folders aren't marked as 'Sources Root',
# but python will run them fine if run as a module.
from src.backend.tools.files import FileManager



def _resolve_path(path_str: str) -> Path:
    """
    Smart path resolver.
    """
    path = Path(path_str)
    home = Path.home()

    if path.is_absolute():
        return path

    parts = path.parts
    # Handle common OS folders relative to Home
    if parts[0].lower() in ['downloads', 'documents', 'desktop', 'music', 'pictures', 'videos']:
        return home / path

    # Default to Home
    return home / path


class OSAssistant:
    def __init__(self):
        self.files = FileManager()


    def execute_intent(self, intent: dict) -> str:
        """
        Executes the intent and returns a descriptive message (Success or Error)
        to be sent back to the LLM or UI.
        """
        action = intent.get('action')

        # 1. Handle Pre-existing LLM Errors (e.g. invalid JSON)
        if action == 'error':
            return f"Error from LLM: {intent.get('message')}"

        try:
            # --- ACTION: MOVE FILE ---
            if action == 'move_file':
                try:
                    src = _resolve_path(intent['source'])
                    dst = _resolve_path(intent['destination'])

                    # Log for debugging
                    print(f"DEBUG: Attempting move {src} -> {dst}")

                    # Execute
                    self.files.move_file(str(src), str(dst))

                    # Return Detailed Success Message
                    return f"Success: Moved file '{src.name}' from '{src.parent}' to '{dst.parent}'."

                except FileNotFoundError:
                    return f"Error: Could not move file. The source file '{intent['source']}' does not exist."
                except FileExistsError:
                    return f"Error: Could not move file. A file already exists at the destination '{intent['destination']}'."

            # --- ACTION: CREATE FILE ---
            elif action == 'create_file':
                try:
                    path = _resolve_path(intent['path'])
                    content = intent.get('content', '')

                    self.files.create_file(str(path), content)

                    return f"Success: Created new file at '{path}'."

                except FileExistsError:
                    return f"Error: Could not create file. A file already exists at '{intent['path']}'."

            # --- ACTION: COPY FILE ---
            elif action == 'copy_file':
                try:
                    src = _resolve_path(intent['source'])
                    dst = _resolve_path(intent['destination'])

                    self.files.copy_file(str(src), str(dst))

                    return f"Success: Copied file '{src.name}' to '{dst}'."

                except FileNotFoundError:
                    return f"Error: Could not copy. The source file '{intent['source']}' was not found."

            # --- ACTION: GET INFO ---
            elif action == 'get_file_info':
                try:
                    path = _resolve_path(intent['path'])
                    info = self.files.get_file_info(str(path))
                    return f"Success: Retrieved info for '{path.name}': {info}"

                except FileNotFoundError:
                    return f"Error: Could not get info. The file '{intent['path']}' does not exist."

            else:
                return f"Error: Unknown action '{action}' requested. I do not know how to handle this."

        # 3. Catch-all for unexpected crashes (e.g., Permissions, System errors)
        except PermissionError:
            return "Error: Permission denied. I do not have access rights to perform that action on this path."
        except Exception as e:
            return f"Critical Error: An unexpected error occurred while executing '{action}': {str(e)}"

#
# # --- Testing Section ---
# if __name__ == "__main__":
#
#
#     # This is the exact output you got from your llm
#     mock_intent = {
#         'action': 'move_file',
#         'source': 'Downloads/timeline3.pptx',
#         'destination': 'Desktop/test/timeline3.pptx'
#     }
#
#     print("--- Executing Intent ---")
#     result = assistant.execute_intent(mock_intent)
#     print(result)