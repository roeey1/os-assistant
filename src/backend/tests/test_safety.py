import unittest
import sys
from pathlib import Path

# Adjust import path so Python finds 'src'
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.core.safety import SecurityManager, RiskLevel


class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.sec = SecurityManager()

    def test_safe_path(self):
        """Test a standard user path."""
        allowed, reason, risk = self.sec.validate_action("list_directory", {"path": "~/Documents"})
        self.assertTrue(allowed)
        self.assertEqual(risk, RiskLevel.SAFE)

    def test_restricted_path(self):
        """Test accessing a system root folder."""
        # We test a path we know is in the restricted list
        # Using /bin as it exists on Mac/Linux usually
        bad_path = "/bin/bash"

        allowed, reason, risk = self.sec.validate_action("delete_file", {"path": bad_path})

        # Should be blocked
        self.assertFalse(allowed)
        self.assertEqual(risk, RiskLevel.BLOCKED)
        self.assertIn("Access denied", reason)

    def test_high_risk_tool(self):
        """Test that delete_file is correctly marked HIGH risk."""
        # Even on a safe path, the TOOL itself is high risk
        allowed, reason, risk = self.sec.validate_action("delete_file", {"path": "~/Documents/junk.txt"})
        self.assertTrue(allowed)
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_unknown_tool(self):
        """Test that unknown tools are blocked."""
        allowed, reason, risk = self.sec.validate_action("format_hard_drive", {})
        self.assertFalse(allowed)
        self.assertEqual(risk, RiskLevel.BLOCKED)


if __name__ == "__main__":
    unittest.main()