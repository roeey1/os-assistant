from src.backend.tools.files import FileManager
import os


def interactive_search_test():
    fm = FileManager()

    print("==================================================")
    print("   OS Assistant Smart Search (Backend Test)       ")
    print("==================================================")
    print("Type a partial filename (e.g., 'fo') to search.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("Search > ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting search test.")
                break

            if not user_input:
                continue

            # 1. Run the logic matching your "Picture" requirement
            # The function 'search_files_ranked' already does the heavy lifting:
            # - Scans Desktop, Downloads, Documents, etc.
            # - Ranks by relevance (100=Exact, 80=Starts With, 50=Contains)
            # - Limits to Top 15 items
            results = fm.search_files_ranked(user_input)

            print(f"\n{results}\n")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    interactive_search_test()