import unittest
import sys
from pathlib import Path

# Fix imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.backend.tools.sys_info import SystemInfo


class TestSystemInfo(unittest.TestCase):

    def setUp(self):
        self.tool = SystemInfo()

    def test_get_system_specs(self):
        """Check if we get a dictionary with the right keys."""
        specs = self.tool.get_system_specs()

        self.assertIsInstance(specs, dict)
        self.assertIn("os_name", specs)
        self.assertIn("ram_total_gb", specs)
        # RAM should be a string containing "GB"
        self.assertIn("GB", specs["ram_total_gb"])

    def test_get_disk_usage(self):
        """Check disk usage for the current directory."""
        usage = self.tool.get_disk_usage(".")

        self.assertIsInstance(usage, str)
        self.assertIn("Total:", usage)
        self.assertIn("Free:", usage)
        self.assertIn("GB", usage)

    def test_get_disk_usage_invalid(self):
        """Check error handling for fake paths."""
        usage = self.tool.get_disk_usage("/path/to/nothing")
        self.assertIn("Error", usage)

    def test_get_user_context(self):
        """Check if user info is retrieved."""
        ctx = self.tool.get_user_context()

        self.assertIsInstance(ctx, dict)
        self.assertIn("username", ctx)
        self.assertIn("home_dir", ctx)
        self.assertTrue(len(ctx["username"]) > 0)

    def test_get_running_processes(self):
        """Check if we get a list of processes."""
        procs = self.tool.get_running_processes(limit=5)

        self.assertIsInstance(procs, str)
        self.assertIn("Top 5 Processes", procs)
        self.assertIn("PID:", procs)
        self.assertIn("MB", procs)


if __name__ == "__main__":
    unittest.main()