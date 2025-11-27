import json
import ollama
from src.core.assistant import OSAssistant
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
        1. create_file(path, content)
        2. move_file(source, destination)
        3. copy_file(source, destination)
        4. get_file_info(path)

        RULES:
        - You MUST output ONLY valid JSON.
        - Do not add explanations or markdown text (like ```json).
        - If the user request is unclear or unsafe, return {"action": "error", "message": "reason"}.

        EXAMPLE 1:
        User: "Create a note called hello.txt saying hello world"
        Response: {"action": "create_file", "path": "hello.txt", "content": "hello world"}

        EXAMPLE 2:
        User: "Move data.csv to the backup folder"
        Response: {"action": "move_file", "source": "data.csv", "destination": "backup/data.csv"}

        EXAMPLE 3:
        User: "Tell me about report.pdf"
        Response: {"action": "get_file_info", "path": "report.pdf"}
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
    print("hello! please enter your reqwest:")
    test_input = input("Enter your input: ")
    print(f"--- Testing Model: {client.model_name} ---")
    while (test_input != "close"):
        result = client.parse_intent(test_input)
        print(f"Parsed Intent: {result}")#delete later
        response = assistant.execute_intent(result)
        print(response)
        test_input = input("Enter your input: ")


