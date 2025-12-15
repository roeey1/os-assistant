import sys
sys.path.append(".")
from src.backend.core.assistant import OSAssistant

try:
    assistant = OSAssistant()
    # Simulate the input that caused the issue
    user_input = "move ID from desktop to test2 folder"
    print(f"Processing: {user_input}")
    response = assistant.process_request(user_input)
    print("Response:", response)
except Exception as e:
    print(f"Crashed: {e}")
    import traceback
    traceback.print_exc()
