import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.backend.tools.system_ops import SystemOps


class TestSystemOps(unittest.TestCase):

    def setUp(self):
        self.ops = SystemOps()

    @patch('subprocess.run')
    def test_open_app(self, mock_run):
        """Test if it tries to launch an app."""
        result = self.ops.open_app("Calculator")

        self.assertIn("Success", result)
        self.assertTrue(mock_run.called)

        # Verify arguments based on OS
        args = mock_run.call_args[0][0]
        if self.ops._is_mac():
            self.assertEqual(args, ["open", "-a", "Calculator"])
        elif self.ops._is_windows():
            self.assertIn("start Calculator", args)

    @patch('subprocess.run')
    def test_open_settings(self, mock_run):
        """Test opening settings."""
        result = self.ops.open_settings()
        self.assertIn("Success", result)
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    def test_show_file_properties_success(self, mock_run):
        """Test showing properties for a file that exists."""
        # Create a fake file path that definitely exists (this file itself)
        existing_file = str(Path(__file__).resolve())

        result = self.ops.show_file_properties(existing_file)

        self.assertIn("Success", result)
        self.assertTrue(mock_run.called)

        # Check if AppleScript was used on Mac
        if self.ops._is_mac():
            args = mock_run.call_args_list[0][0][0]  # First call, first arg
            self.assertEqual(args[0], "osascript")

    def test_show_file_properties_not_found(self):
        """Test error when file missing."""
        result = self.ops.show_file_properties("non_existent_ghost_file.txt")
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_get_trash_items_mac(self, mock_exists, mock_iterdir):
        """Mock test for reading trash items on Mac."""
        # Force the test to think it's running on Mac for logic check
        if not self.ops._is_mac():
            return  # Skip if running on Windows

        mock_exists.return_value = True

        # Mock file objects
        f1 = MagicMock();
        f1.name = "deleted_doc.txt"
        f2 = MagicMock();
        f2.name = "old_pic.jpg"
        mock_iterdir.return_value = [f1, f2]

        result = self.ops.get_trash_items()

        self.assertIn("deleted_doc.txt", result)
        self.assertIn("old_pic.jpg", result)

    @patch('subprocess.run')
    def test_empty_trash(self, mock_run):
        """Test emptying trash command."""
        result = self.ops.empty_trash()

        self.assertIn("Success", result)
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    def test_close_app(self, mock_run):
        """Test closing an application."""
        result = self.ops.close_app("Calculator")

        self.assertIn("Success", result)
        self.assertTrue(mock_run.called)

        args = mock_run.call_args[0][0]  # First arg of first call

        if self.ops._is_mac():
            # Should look like: osascript -e 'quit app "Calculator"'
            self.assertIn("quit app", args[2])
            self.assertIn("Calculator", args[2])
        elif self.ops._is_windows():
            # Should look like: taskkill /IM "Calculator.exe" /F
            cmd = args  # Windows args are often passed as a single string if shell=True
            if isinstance(cmd, list): cmd = cmd[0]
            self.assertIn("taskkill", cmd)
            self.assertIn("Calculator.exe", cmd)

    @patch('subprocess.run')
    def test_close_settings(self, mock_run):
        """Test closing settings."""
        self.ops.close_settings()
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    def test_close_file_properties(self, mock_run):
        """Test closing info windows."""
        result = self.ops.close_file_properties()

        if self.ops._is_mac():
            self.assertIn("Success", result)
            self.assertTrue(mock_run.called)
            # Check for AppleScript logic
            args = mock_run.call_args[0][0]
            self.assertIn("tell application \"Finder\"", args[2])
        elif self.ops._is_windows():
            self.assertIn("not currently supported", result)

if __name__ == "__main__":
    unittest.main()