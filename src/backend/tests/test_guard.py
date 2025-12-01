import unittest
import sys
import shutil
import os
from pathlib import Path

# Adjust import path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.core.guard import SecurityManager, RiskLevel


class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.sec = SecurityManager()

        # Create a sandbox folder for safe testing
        self.test_dir = Path("safety_sandbox").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

    def tearDown(self):
        # Cleanup after tests
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_safe_path(self):
        """Test a standard user path."""
        # list_directory doesn't require the path to exist in our logic, so this is fine
        allowed, reason, risk = self.sec.validate_action("list_directory", {"path": "~/Documents"})
        self.assertTrue(allowed)
        self.assertEqual(risk, RiskLevel.SAFE)

    def test_restricted_path(self):
        """Test accessing a system root folder."""
        # We test a path we know is in the restricted list
        bad_path = "/bin/bash"
        if os.name == 'nt': bad_path = "C:\\Windows\\System32\\cmd.exe"

        allowed, reason, risk = self.sec.validate_action("delete_file", {"path": bad_path})

        # Should be blocked
        self.assertFalse(allowed)
        self.assertEqual(risk, RiskLevel.BLOCKED)
        self.assertIn("Access denied", reason)

    def test_high_risk_tool(self):
        """Test that delete_file is correctly marked HIGH risk."""
        # FIX: We must create the file first, otherwise Integrity Check fails!
        target = self.test_dir / "junk.txt"
        target.touch()

        # Now validate action on an EXISTING file
        allowed, reason, risk = self.sec.validate_action("delete_file", {"path": str(target)})

        self.assertTrue(allowed, f"Should be allowed but got: {reason}")
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_race_condition_delete(self):
        """
        Simulate a Race Condition:
        1. User requests delete (Valid).
        2. Time passes... file is deleted by someone else.
        3. User confirms delete.
        4. Security should BLOCK it because the file is gone.
        """
        # Setup: Create a temp file
        target_file = self.test_dir / "race_test.txt"
        target_file.touch()

        # 1. First Check (File exists)
        allowed, _, _ = self.sec.validate_action("delete_file", {"path": str(target_file)})
        self.assertTrue(allowed, "Should allow delete initially")

        # 2. The Race Condition Event: File disappears!
        target_file.unlink()

        # 3. Second Check (User says 'Yes')
        allowed_retry, reason, _ = self.sec.validate_action("delete_file", {"path": str(target_file)})

        # 4. Assert: Should FAIL now
        self.assertFalse(allowed_retry, "Should block because file is gone")
        self.assertIn("no longer exists", reason)

    def test_unknown_tool(self):
        """Test that unknown tools are blocked."""
        allowed, reason, risk = self.sec.validate_action("format_hard_drive", {})
        self.assertFalse(allowed)
        self.assertEqual(risk, RiskLevel.BLOCKED)


if __name__ == "__main__":
    unittest.main()