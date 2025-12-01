import json
import os
from datetime import datetime
from pathlib import Path


class AuditLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create a specific log file for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{timestamp}.jsonl"

    def log_action(self, user_request: str, intent: dict, result: str):
        """
        Logs a specific tool execution including the original request,
        the parsed intent, and the execution result.
        """
        # Automatically determine status (our tools return strings starting with "Success" or "Error")
        if isinstance(result, str) and result.startswith("Success"):
            status = "SUCCESS"
        else:
            status = "ERROR"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "action_execution",
            "user_request": user_request,
            "parsed_intent": intent,
            "action": intent.get('action'),
            "status": status,
            "result": result
        }
        self._write_entry(entry)

    def _write_entry(self, entry: dict):
        """Appends a line of JSON to the log file."""
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")