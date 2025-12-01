import sys

# Add the current directory to Python path so 'src' imports work correctly
sys.path.append(".")

from src.llm.Client import LocalLLMClient
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

    # NEW: State variable to remember what the user needs to confirm
    pending_intent = None

    # 2. Main Loop
    while True:
        try:
            user_input = input("\nUser: ").strip()

            if user_input.lower() in ['exit', 'quit', 'close']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # ==========================================
            # A. CONFIRMATION FLOW (New Logic)
            # ==========================================
            # If we are waiting for a "yes/no" on a dangerous action
            if pending_intent:
                if user_input.lower() in ["y", "yes", "confirm", "ok", "sure"]:
                    print("🔄 Executing confirmed action...")

                    # Re-run the SAVED intent with confirm=True
                    result = assistant.execute_intent(pending_intent, confirm=True)

                    # Log the successful execution
                    logger.log_action(f"[CONFIRMED] {user_input}", pending_intent, result)
                    print(f"Assistant: {result}")

                else:
                    # User said 'no' (or anything else)
                    print("❌ Action cancelled.")
                    logger.log_action(f"[CANCELLED] {user_input}", pending_intent, "User cancelled high-risk action")

                # Reset state so we go back to normal mode
                pending_intent = None
                continue

            # ==========================================
            # B. STANDARD FLOW
            # ==========================================

            # 1. Parse Intent (LLM)
            print("Thinking...")
            intent = client.parse_intent(user_input)

            # Check if LLM failed to give JSON
            if intent.get("action") == "error":
                print(f"Assistant: {intent.get('message')}")
                continue

            # 2. Execute Action (Assistant)
            # This might return "Success", "Error", or "⚠️ CONFIRMATION_NEEDED"
            result = assistant.execute_intent(intent)

            # 3. Check for Confirmation Request
            if "CONFIRMATION_NEEDED" in result:
                # The Assistant blocked it because it's High Risk.
                # We show the warning and SAVE the intent for the next loop.
                print(f"Assistant: {result}")
                print("👉 Type 'yes' to proceed, or anything else to cancel.")

                pending_intent = intent

                # Log the attempt
                logger.log_action(user_input, intent, result)

            else:
                # Standard success, error, or security block
                logger.log_action(user_input, intent, result)
                print(f"Assistant: {result}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Critical Error: {e}")


if __name__ == "__main__":
    main()