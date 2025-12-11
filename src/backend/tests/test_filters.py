import unittest
import shutil
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# --- Fix Imports to find the 'src' folder ---
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.core.filter import FilterEngine


class TestFilterEngine(unittest.TestCase):

    def setUp(self):
        """
        Sets up a complex sandbox with specific file types, sizes, and dates.
        """
        self.test_dir = Path("filter_sandbox").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        self.engine = FilterEngine()

        # --- 1. Create Files with Specific Extensions ---
        (self.test_dir / "image.jpg").touch()
        (self.test_dir / "photo.png").touch()
        (self.test_dir / "document.pdf").touch()
        (self.test_dir / "notes.txt").touch()
        (self.test_dir / "script.PY").touch()  # Test case sensitivity

        # --- 2. Create Files with Specific Sizes ---
        # 1 KB File
        with open(self.test_dir / "small_1kb.dat", "wb") as f:
            f.write(b'\0' * 1024)

            # 1 MB File
        with open(self.test_dir / "large_1mb.dat", "wb") as f:
            f.write(b'\0' * 1024 * 1024)

        # --- 3. Create Files with Specific Dates ---
        # We use os.utime to backdate files

        # File from 2020
        old_file = self.test_dir / "old_2020.txt"
        old_file.touch()
        date_2020 = datetime(2020, 1, 1).timestamp()
        os.utime(old_file, (date_2020, date_2020))  # Set access and modified time

        # File from 2025 (Future/Recent)
        new_file = self.test_dir / "new_2025.txt"
        new_file.touch()
        date_2025 = datetime(2025, 1, 1).timestamp()
        os.utime(new_file, (date_2025, date_2025))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    # =========================================================
    # TESTS
    # =========================================================

    def test_extension_single(self):
        """Test filtering by a single extension."""
        filters = {"extension": "jpg"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "image.jpg")

    def test_extension_list(self):
        """Test filtering by a list of extensions (Plural)."""
        filters = {"extensions": ["jpg", "png", "py"]}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        filenames = [f.name for f in results]
        self.assertEqual(len(results), 3)
        self.assertIn("image.jpg", filenames)
        self.assertIn("photo.png", filenames)
        self.assertIn("script.PY", filenames)  # Should handle .PY vs .py

    def test_name_contains(self):
        """Test substring matching."""
        filters = {"name_contains": "doc"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "document.pdf")

    def test_size_min(self):
        """Test min_size (Find files larger than X)."""
        # Filter: > 500KB
        filters = {"min_size": "500kb"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        # Should only find the 1MB file
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "large_1mb.dat")

    def test_size_max(self):
        """Test max_size (Find files smaller than X)."""
        # Filter: < 500KB
        filters = {"max_size": "500kb"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        filenames = [f.name for f in results]
        self.assertIn("small_1kb.dat", filenames)
        self.assertNotIn("large_1mb.dat", filenames)

    def test_date_modified_after(self):
        """Test modified_after (Find newer files)."""
        # Find files modified after 2024
        filters = {"modified_after": "2024-01-01"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        filenames = [f.name for f in results]
        self.assertIn("new_2025.txt", filenames)
        self.assertNotIn("old_2020.txt", filenames)

    def test_date_modified_before(self):
        """Test modified_before (Find older files)."""
        # Find files modified before 2021
        filters = {"modified_before": "2021-01-01"}
        results = self.engine.apply_filters(str(self.test_dir), filters)

        filenames = [f.name for f in results]
        self.assertIn("old_2020.txt", filenames)
        self.assertNotIn("new_2025.txt", filenames)

    def test_combined_filters(self):
        """Test combining multiple logic (Size AND Extension)."""
        # Create a specific target for this test
        # 1. A large text file (Should match size, fail extension)
        with open(self.test_dir / "large.txt", "wb") as f:
            f.write(b'\0' * 1024 * 1024)  # 1MB

        # 2. A small JPG (Should fail size, match extension)
        (self.test_dir / "small.jpg").touch()

        # 3. A large JPG (Should match BOTH)
        with open(self.test_dir / "target.jpg", "wb") as f:
            f.write(b'\0' * 1024 * 1024)  # 1MB

        filters = {
            "extension": "jpg",
            "min_size": "500kb"
        }

        results = self.engine.apply_filters(str(self.test_dir), filters)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "target.jpg")

    def test_parse_helpers(self):
        """Directly test the helper functions for edge cases."""
        # Test Size Parser
        self.assertEqual(self.engine._parse_size("100kb"), 102400)
        self.assertEqual(self.engine._parse_size("  1 MB "), 1048576)  # Spaces
        self.assertEqual(self.engine._parse_size("invalid"), 0)

        # Test Date Parser
        ts = self.engine._parse_date("2025-01-01")
        self.assertTrue(ts > 0)
        self.assertEqual(self.engine._parse_date("bad-date"), 0.0)


if __name__ == "__main__":
    unittest.main()