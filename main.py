import sys

# Add the current directory to Python path so 'src' imports work correctly
sys.path.append(".")

# Updated imports: Main only talks to Assistant and Logger
try:
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger
except ImportError:
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger


def main():
    print("--- OS Assistant Initializing ---")

    # 1. Initialize Components
    try:
        # Assistant now owns the LLM Client internally
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

            print("Thinking...")

            # ==========================================
            # PROCESS REQUEST
            # ==========================================
            # We pass RAW TEXT. Assistant handles LLM parsing + Safety + Logic
            response = assistant.process_request(user_input)

            status = response.get('status')
            message = response.get('message')
            intent = response.get('intent', {})  # Retrieve intent for logging

            # ==========================================
            # HANDLE OUTCOMES
            # ==========================================

            # CASE A: Security Check triggered a Pause
            if status == 'NEEDS_CONFIRMATION':
                action_id = response.get('action_id')
                risk_level = response.get('risk')

                print(f"\n⚠️  SECURITY ALERT: {message}")
                print(f"   Risk Level: {risk_level}")
                print(f"   Action: {intent.get('action')}")

                target = intent.get('resolved_path') or \
                         intent.get('resolved_src') or \
                         "Unknown Target"
                print(f"   Target: {target}")

                confirm = input("   Are you sure you want to proceed? (y/n): ").strip().lower()

                if confirm in ['y', 'yes', 'ok', 'confirm']:
                    print("🔄 Executing confirmed action...")

                    final_result = assistant.execute_confirmed_action(action_id)
                    final_msg = final_result.get('message')

                    logger.log_action(user_input, intent, f"[CONFIRMED] {final_msg}")
                    print(f"Assistant: {final_msg}")
                else:
                    print("❌ Action cancelled by user.")
                    logger.log_action(user_input, intent, "User cancelled high-risk action")

            # CASE B: Action was blocked
            elif status == 'BLOCKED':
                print(f"⛔ BLOCKED: {message}")
                logger.log_action(user_input, intent, f"BLOCKED: {message}")

            # CASE C: Success
            elif status == 'SUCCESS':
                print(f"Assistant: {message}")
                logger.log_action(user_input, intent, message)

            # CASE D: Error
            else:
                print(f"Assistant: Error - {message}")
                logger.log_action(user_input, intent, f"Error: {message}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Critical Error: {e}")


if __name__ == "__main__":
    main()