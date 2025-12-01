import sys
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.append(".")

# Updated imports to match your actual directory structure (src/llm/Client.py and src/core/assistant.py)
try:
    from src.backend.llm.client import LocalLLMClient
    from src.backend.core.assistant import OSAssistant
except ImportError:
    # Fallback to the structure observed in your traceback
    from src.llm.Client import LocalLLMClient
    from src.core.assistant import OSAssistant

# --- CONFIGURATION ---
SANDBOX_NAME = "os_assistant_test_sandbox"
SANDBOX_PATH = Path.home() / SANDBOX_NAME


# --- TEST DATA GENERATOR ---
# 10 variations for every action
def get_test_cases():
    return {
        "create_file": [
            f"Create a file named test1.txt in {SANDBOX_NAME} with content hello",
            f"Make a new text doc called note.md inside {SANDBOX_NAME}",
            f"Generate a python script main.py in the {SANDBOX_NAME} folder",
            f"Write 'important data' to data.json in {SANDBOX_NAME}",
            f"I need a new file log.txt in {SANDBOX_NAME}",
            f"Save a file named config.yaml to {SANDBOX_NAME}",
            f"Please create instructions.txt in {SANDBOX_NAME} saying 'read me'",
            f"Construct a file list.csv inside {SANDBOX_NAME}",
            f"Add a file named todo.list to {SANDBOX_NAME}",
            f"Start a new file draft.doc in {SANDBOX_NAME}"
        ],
        "create_folder": [
            f"Create a folder named subfolder in {SANDBOX_NAME}",
            f"Make a directory called images inside {SANDBOX_NAME}",
            f"New folder named backup in {SANDBOX_NAME}",
            f"Generate a directory structure for logs in {SANDBOX_NAME}",
            f"I want a folder named private inside {SANDBOX_NAME}",
            f"Construct a directory named temp in {SANDBOX_NAME}",
            f"Add a new folder music to {SANDBOX_NAME}",
            f"mkdir stuff in {SANDBOX_NAME}",
            f"Please make a path for archive in {SANDBOX_NAME}",
            f"Build a folder named project_files in {SANDBOX_NAME}"
        ],
        "move_file": [
            f"Move {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/moved_here.txt",
            f"Relocate {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/archive",
            f"Cut {SANDBOX_NAME}/move_me.txt and paste it in {SANDBOX_NAME}/trash",
            f"Shift the file {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/destination",
            f"Transfer {SANDBOX_NAME}/move_me.txt into {SANDBOX_NAME}/completed",
            f"Please move {SANDBOX_NAME}/move_me.txt to the {SANDBOX_NAME}/done folder",
            f"Take {SANDBOX_NAME}/move_me.txt and put it in {SANDBOX_NAME}/old",
            f"Change location of {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/new_loc",
            f"Send {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/outgoing",
            f"Migrate {SANDBOX_NAME}/move_me.txt to {SANDBOX_NAME}/storage"
        ],
        "copy_file": [
            f"Copy {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/backup_copy.txt",
            f"Duplicate {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/copies",
            f"Make a copy of {SANDBOX_NAME}/copy_me.txt in {SANDBOX_NAME}/replica",
            f"Clone {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/clones",
            f"Replicate {SANDBOX_NAME}/copy_me.txt into {SANDBOX_NAME}/mirror",
            f"Copy and paste {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/paste_bin",
            f"Create a duplicate of {SANDBOX_NAME}/copy_me.txt in {SANDBOX_NAME}/2",
            f"Back up {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/safe",
            f"Cp {SANDBOX_NAME}/copy_me.txt to {SANDBOX_NAME}/dest",
            f"Make another version of {SANDBOX_NAME}/copy_me.txt in {SANDBOX_NAME}/v2"
        ],
        "rename_item": [
            f"Rename {SANDBOX_NAME}/rename_me.txt to new_name.txt",
            f"Change the name of {SANDBOX_NAME}/rename_me.txt to updated.txt",
            f"Call {SANDBOX_NAME}/rename_me.txt final.txt instead",
            f"Modify filename of {SANDBOX_NAME}/rename_me.txt to draft_v2.txt",
            f"Rename item {SANDBOX_NAME}/rename_me.txt to done.txt",
            f"Make {SANDBOX_NAME}/rename_me.txt be called old.txt",
            f"Switch name of {SANDBOX_NAME}/rename_me.txt to archive.txt",
            f"Re-label {SANDBOX_NAME}/rename_me.txt as important.txt",
            f"Set name of {SANDBOX_NAME}/rename_me.txt to report.txt",
            f"Title {SANDBOX_NAME}/rename_me.txt as summary.txt"
        ],
        "list_directory": [
            f"List files in {SANDBOX_NAME}",
            f"Show me contents of {SANDBOX_NAME}",
            f"What is inside {SANDBOX_NAME}?",
            f"Display files in directory {SANDBOX_NAME}",
            f"List directory {SANDBOX_NAME}",
            f"Show files for {SANDBOX_NAME}",
            f"Get content listing of {SANDBOX_NAME}",
            f"Tell me what files are in {SANDBOX_NAME}",
            f"ls {SANDBOX_NAME}",
            f"Enumerate items in {SANDBOX_NAME}"
        ],
        "read_file": [
            f"Read {SANDBOX_NAME}/read_me.txt",
            f"Show content of {SANDBOX_NAME}/read_me.txt",
            f"Display text from {SANDBOX_NAME}/read_me.txt",
            f"What does {SANDBOX_NAME}/read_me.txt say?",
            f"Open and read {SANDBOX_NAME}/read_me.txt",
            f"Print content of {SANDBOX_NAME}/read_me.txt",
            f"Cat {SANDBOX_NAME}/read_me.txt",
            f"Get text from {SANDBOX_NAME}/read_me.txt",
            f"Read the file {SANDBOX_NAME}/read_me.txt",
            f"View {SANDBOX_NAME}/read_me.txt"
        ],
        "get_file_info": [
            f"Get info for {SANDBOX_NAME}/info.txt",
            f"Show metadata of {SANDBOX_NAME}/info.txt",
            f"How big is {SANDBOX_NAME}/info.txt?",
            f"When was {SANDBOX_NAME}/info.txt created?",
            f"File properties for {SANDBOX_NAME}/info.txt",
            f"Tell me about {SANDBOX_NAME}/info.txt",
            f"Get size of {SANDBOX_NAME}/info.txt",
            f"Details for {SANDBOX_NAME}/info.txt",
            f"Inspect {SANDBOX_NAME}/info.txt",
            f"Stats for {SANDBOX_NAME}/info.txt"
        ],
        "open_file": [
            f"Open {SANDBOX_NAME}/open_me.txt",
            f"Launch file {SANDBOX_NAME}/open_me.txt",
            f"Open {SANDBOX_NAME}/open_me.txt in default app",
            f"View {SANDBOX_NAME}/open_me.txt",
            f"Run {SANDBOX_NAME}/open_me.txt",
            f"Execute {SANDBOX_NAME}/open_me.txt",
            f"Bring up {SANDBOX_NAME}/open_me.txt",
            f"Start {SANDBOX_NAME}/open_me.txt",
            f"Pop open {SANDBOX_NAME}/open_me.txt",
            f"Show {SANDBOX_NAME}/open_me.txt"
        ],
        # --- SYSTEM OPS (Note: execution might be annoying as it opens apps) ---
        "open_app": [
            "Open Calculator",
            "Launch Calculator",
            "Start the Calculator app",
            "Run Calculator",
            "Bring up Calculator",
            "Open application Calculator",
            "Turn on Calculator",
            "Please open Calculator",
            "Execute Calculator app",
            "Initialize Calculator"
        ],
        "close_app": [
            "Close Calculator",
            "Quit Calculator",
            "Exit Calculator",
            "Shut down Calculator",
            "Kill Calculator process",
            "Stop Calculator",
            "Terminate Calculator",
            "Close the app Calculator",
            "End Calculator",
            "Turn off Calculator"
        ],
        "open_settings": [
            "Open Settings",
            "Launch System Settings",
            "Go to Settings",
            "Show Preferences",
            "Open configuration",
            "Start Settings app",
            "Bring up System Preferences",
            "View Settings",
            "Access Settings",
            "Open Control Panel"
        ],
        "close_settings": [
            "Close Settings",
            "Quit System Settings",
            "Exit Settings",
            "Shut down Settings window",
            "Close Preferences",
            "Stop Settings app",
            "Hide Settings",
            "Kill Settings",
            "Dismiss Settings",
            "Leave Settings"
        ],
        "get_trash_items": [
            "What is in the trash?",
            "List trash items",
            "Show recycle bin contents",
            "Get trash contents",
            "Check the trash",
            "List deleted items",
            "View trash",
            "Read trash",
            "Inspect recycle bin",
            "Whats inside the bin?"
        ],
        "get_system_specs": [
            "Get system specs",
            "Show computer details",
            "How much RAM do I have?",
            "What CPU is this?",
            "OS version info",
            "System information",
            "Hardware specs",
            "Tell me about my computer",
            "Machine specifications",
            "Display system properties"
        ],
        "get_disk_usage": [
            "Check disk usage",
            "How much space is left?",
            "Storage stats",
            "Disk free space",
            "Check hard drive",
            "Memory availability on disk",
            "Volume status",
            "Show disk capacity",
            "HDD usage",
            "Get storage info"
        ],
        "get_user_context": [
            "Who am I logged in as?",
            "Get current user",
            "What is my home directory?",
            "User context info",
            "Show username and hostname",
            "Who is the active user?",
            "Get user details",
            "Where am I working?",
            "Current session info",
            "Identity info"
        ],
        "get_running_processes": [
            "Show running processes",
            "List top apps by memory",
            "What is using my RAM?",
            "Get process list",
            "Task manager info",
            "Check active processes",
            "Who is eating memory?",
            "List running tasks",
            "Top memory hogs",
            "Process monitor"
        ]
    }


class TestRunner:
    def __init__(self):
        self.client = LocalLLMClient(model_name="llama3")
        self.assistant = OSAssistant()
        self.stats = {}

    def setup_sandbox(self):
        """Creates a clean sandbox folder for testing."""
        if SANDBOX_PATH.exists():
            shutil.rmtree(SANDBOX_PATH)
        SANDBOX_PATH.mkdir()
        print(f"Created Sandbox: {SANDBOX_PATH}")

    def prepare_file_for_action(self, action, prompt):
        """
        Creates dummy files needed for specific actions (Move, Copy, Rename, Read)
        so the execution doesn't fail on 'File Not Found'.
        """
        # A simple way to ensure the target file exists before we try to manipulate it
        filename = None

        if "move_me.txt" in prompt:
            filename = "move_me.txt"
        elif "copy_me.txt" in prompt:
            filename = "copy_me.txt"
        elif "rename_me.txt" in prompt:
            filename = "rename_me.txt"
        elif "read_me.txt" in prompt:
            filename = "read_me.txt"
        elif "info.txt" in prompt:
            filename = "info.txt"
        elif "open_me.txt" in prompt:
            filename = "open_me.txt"

        if filename:
            path = SANDBOX_PATH / filename
            if not path.exists():
                with open(path, "w") as f:
                    f.write("Dummy content for testing.")

    def run_all(self):
        self.setup_sandbox()
        test_data = get_test_cases()
        total_actions = len(test_data)

        print(f"\n--- STARTING TEST SUITE ({total_actions} Actions x 10 Prompts) ---")
        print("Note: This may take a while depending on Local LLM speed.\n")

        for action_name, prompts in test_data.items():
            print(f"\n>> Testing Action: {action_name}")
            self.stats[action_name] = {"parse_success": 0, "exec_success": 0, "total": 0}

            for prompt in prompts:
                self.stats[action_name]["total"] += 1

                # 1. Setup Pre-requisites (create dummy files if needed)
                self.prepare_file_for_action(action_name, prompt)

                # 2. Test LLM Parsing
                print(f"   Prompt: '{prompt}'", end=" ... ")
                try:
                    intent = self.client.parse_intent(prompt)
                    parsed_action = intent.get('action')

                    if parsed_action == action_name:
                        self.stats[action_name]["parse_success"] += 1
                        print("PARSE OK", end=" | ")
                    else:
                        print(f"PARSE FAIL (Got: {parsed_action})", end=" | ")
                        # If parsing failed, we can't really test execution of the *correct* thing
                        print("EXEC SKIP")
                        continue

                except Exception as e:
                    print(f"PARSE ERROR {e}")
                    continue

                # 3. Test Execution
                try:
                    # Special handling for "Open App" / "Close App" to avoid chaos?
                    # We will run them, but user should know windows might pop up.

                    result = self.assistant.execute_intent(intent)

                    if result.startswith(
                            "Success") or "Disk Usage" in result or "RAM" in result or "Process" in result or "Trash" in result:
                        self.stats[action_name]["exec_success"] += 1
                        print("EXEC OK")
                    else:
                        print(f"EXEC FAIL ({result[:20]}...)")

                except Exception as e:
                    print(f"EXEC ERROR {e}")

    def print_report(self):
        print("\n" + "=" * 50)
        print(f"{'ACTION':<25} | {'PARSE %':<10} | {'EXEC %':<10}")
        print("=" * 50)

        for action, data in self.stats.items():
            total = data['total']
            if total == 0: continue

            p_rate = (data['parse_success'] / total) * 100
            e_rate = (data['exec_success'] / total) * 100

            print(f"{action:<25} | {p_rate:>6.1f}%    | {e_rate:>6.1f}%")
        print("=" * 50)


if __name__ == "__main__":
    runner = TestRunner()
    try:
        runner.run_all()
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        runner.print_report()