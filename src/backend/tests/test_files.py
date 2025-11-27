import unittest
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import patch

# --- FIX IMPORTS ---
# This allows the test to see the 'src' folder even if run from a subfolder
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Now we import using the full path from the root
from src.backend.tools.files import FileManager


class TestFileManager(unittest.TestCase):

    def setUp(self):
        """
        Runs BEFORE every test.
        Creates a clean sandbox environment.
        """
        self.test_dir = Path("test_sandbox")

        # Ensure we start clean
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.test_dir.mkdir()

        # Initialize the tool
        self.fm = FileManager()

    def tearDown(self):
        """
        Runs AFTER every test.
        Cleans up the sandbox.
        """
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    # ==========================================
    # 1. TEST CREATION
    # ==========================================

    def test_create_file_success(self):
        """Test creating a simple file with content."""
        target = self.test_dir / "notes.txt"
        msg = self.fm.create_file(str(target), "Hello World")

        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding='utf-8'), "Hello World")
        self.assertIn("Success", msg)

    def test_create_file_already_exists(self):
        """Test that creating a file that exists raises an error."""
        target = self.test_dir / "duplicate.txt"
        target.touch()  # Create empty file manually

        with self.assertRaises(FileExistsError):
            self.fm.create_file(str(target), "New Content")

    def test_create_folder(self):
        """Test creating a folder and nested folders."""
        target = self.test_dir / "Photos" / "2025"
        msg = self.fm.create_folder(str(target))

        self.assertTrue(target.is_dir())
        self.assertIn("Success", msg)

    # ==========================================
    # 2. TEST LISTING & READING
    # ==========================================

    def test_list_directory(self):
        """Test listing files and folders."""
        # Setup: Create 1 folder and 2 files
        (self.test_dir / "SubFolder").mkdir()
        (self.test_dir / "file1.txt").touch()
        (self.test_dir / "file2.txt").touch()

        result = self.fm.list_directory(str(self.test_dir))

        # Check output format
        self.assertIn("SubFolder/", result)  # Check folder indicator
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)

    def test_read_file_truncation(self):
        """Test reading a file and ensuring max_chars limit works."""
        target = self.test_dir / "long.txt"

        # Create a file with 300 characters
        long_content = "A" * 300
        target.write_text(long_content, encoding='utf-8')

        # Read with limit of 50
        result = self.fm.read_file(str(target), max_chars=50)

        self.assertEqual(len(result), 50 + len("\n...[Content Truncated]..."))
        self.assertTrue(result.startswith("AAAAA"))

    # ==========================================
    # 3. TEST MANIPULATION (Move, Copy, Rename)
    # ==========================================

    def test_rename_item(self):
        """Test renaming a file."""
        original = self.test_dir / "old_name.txt"
        original.touch()

        self.fm.rename_item(str(original), "new_name.txt")

        self.assertFalse(original.exists())
        self.assertTrue((self.test_dir / "new_name.txt").exists())

    def test_move_file(self):
        """Test moving a file to a subfolder."""
        # Setup
        src = self.test_dir / "mover.txt"
        src.write_text("move me")

        dest_folder = self.test_dir / "Archive"
        dest_folder.mkdir()

        dest_file = dest_folder / "mover.txt"

        # Action
        self.fm.move_file(str(src), str(dest_file))

        # Check
        self.assertFalse(src.exists())
        self.assertTrue(dest_file.exists())

    def test_copy_file(self):
        """Test copying a file."""
        src = self.test_dir / "original.txt"
        src.write_text("copy me")

        dest = self.test_dir / "copy.txt"

        self.fm.copy_file(str(src), str(dest))

        self.assertTrue(src.exists())  # Original still there
        self.assertTrue(dest.exists())  # Copy exists
        self.assertEqual(dest.read_text(), "copy me")

    # ==========================================
    # 4. TEST OPEN (Mocked)
    # ==========================================

    @patch('subprocess.call')  # Mock Linux/Mac calls
    @patch('os.startfile', create=True)
    def test_open_file(self, mock_startfile, mock_subprocess):
        """
        Test open_file without actually opening an app window.
        We check if the system command was CALLED.
        """
        target = self.test_dir / "open_me.txt"
        target.touch()

        # Run the function
        msg = self.fm.open_file(str(target))

        # Check success message
        self.assertIn("Success", msg)

        # Check if the code TRIED to open the file
        # We check both because tests run on one OS, but code handles both
        is_windows = os.name == 'nt'
        if is_windows:
            self.assertTrue(mock_startfile.called or mock_subprocess.called)
        else:
            mock_subprocess.assert_called()


if __name__ == '__main__':
    print("Running File System Tests...")
    unittest.main()