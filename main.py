import sys

# Add the current directory to Python path so 'src' imports work correctly
sys.path.append(".")

from src.backend.llm.client import LocalLLMClient
from src.backend.core.assistant import OSAssistant
from src.backend.utils.logger import AuditLogger


def main():
    print("--- OS Assistant Initializing ---")

    # 1. Initialize Components
    try:
        client = LocalLLMClient(model_name="llama3")
        assistant = OSAssistant()
        logger = AuditLogger()
        print("--- System Ready. Type 'exit' to quit. ---")
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return

    # 2. Main Loop
    while True:
        try:
            user_input = input("\nUser: ").strip()

            if user_input.lower() in ['exit', 'quit', 'close']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # A. Parse Intent (LLM)
            print("Thinking...")
            intent = client.parse_intent(user_input)

            # B. Execute Action (Assistant)
            result = assistant.execute_intent(intent)

            # C. Log Everything (Logger)
            logger.log_action(user_input, intent, result)

            # D. Output Result
            print(f"Assistant: {result}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Critical Error: {e}")


if __name__ == "__main__":
    main()