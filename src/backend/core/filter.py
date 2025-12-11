import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Union


class FilterEngine:
    """
    Advanced file filtering logic.
    Decouples selection logic from the LLM, ensuring 100% accurate sorting/filtering.
    """

    def apply_filters(self, source_dir: str, filters: Dict) -> List[Path]:
        """
        Scans source_dir and returns a list of paths that match ALL provided filters.
        """
        root = Path(source_dir).expanduser().resolve()

        if not root.exists():
            print(f"Filter Warning: Source directory '{root}' not found.")
            return []

        matched_files = []

        try:
            for item in root.iterdir():
                if not item.is_file():
                    continue

                # Check 1: Name & Extension (Updated for Lists)
                if not self._check_name_and_type(item, filters):
                    continue

                # Get stats once
                try:
                    stats = item.stat()
                except FileNotFoundError:
                    continue

                    # Check 2: Size
                if not self._check_size(stats, filters):
                    continue

                # Check 3: Time
                if not self._check_time(stats, filters):
                    continue

                matched_files.append(item)

            return matched_files

        except Exception as e:
            print(f"Critical Filter Error: {str(e)}")
            return []

    # ==========================================
    # 1. NAME & TYPE CHECKS (UPDATED)
    # ==========================================
    def _check_name_and_type(self, item: Path, filters: Dict) -> bool:
        """
        Checks file name and extension.
        Supports both 'extension': 'jpg' AND 'extensions': ['jpg', 'png']
        """
        # Gather all allowed extensions into one list
        allowed_exts = []

        # Case A: Plural list from LLM (e.g. ["jpg", "png"])
        if 'extensions' in filters and isinstance(filters['extensions'], list):
            allowed_exts.extend(filters['extensions'])

        # Case B: Singular string from LLM (e.g. "jpg")
        if 'extension' in filters and isinstance(filters['extension'], str):
            allowed_exts.append(filters['extension'])

        # If we have any extension constraints, check them
        if allowed_exts:
            # Normalize input: strip spaces, lowercase, ensure dot
            cleaned_exts = []
            for ext in allowed_exts:
                ext = ext.lower().strip()
                if not ext.startswith("."):
                    ext = "." + ext
                cleaned_exts.append(ext)

            # The Check: Does the file end with ANY of the allowed extensions?
            if item.suffix.lower() not in cleaned_exts:
                return False

        # Filter: Name Contains
        if 'name_contains' in filters:
            if filters['name_contains'].lower() not in item.name.lower():
                return False

        # Filter: Exact Name
        if 'name_exact' in filters:
            if item.name != filters['name_exact']:
                return False

        return True

    # ==========================================
    # 2. SIZE CHECKS
    # ==========================================
    def _check_size(self, stats, filters: Dict) -> bool:
        if 'min_size' in filters:
            min_bytes = self._parse_size(filters['min_size'])
            if stats.st_size < min_bytes:
                return False

        if 'max_size' in filters:
            max_bytes = self._parse_size(filters['max_size'])
            if stats.st_size > max_bytes:
                return False

        return True

    # ==========================================
    # 3. TIME CHECKS
    # ==========================================
    def _check_time(self, stats, filters: Dict) -> bool:
        # MODIFIED TIME
        if 'modified_after' in filters:
            limit = self._parse_date(filters['modified_after'])
            if stats.st_mtime < limit: return False

        if 'modified_before' in filters:
            limit = self._parse_date(filters['modified_before'])
            if stats.st_mtime > limit: return False

        # CREATED TIME
        if 'created_after' in filters:
            limit = self._parse_date(filters['created_after'])
            if stats.st_ctime < limit: return False

        if 'created_before' in filters:
            limit = self._parse_date(filters['created_before'])
            if stats.st_ctime > limit: return False

        return True

    # ==========================================
    # HELPERS
    # ==========================================
    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.lower().strip().replace(" ", "")
        units = {"gb": 1024 ** 3, "mb": 1024 ** 2, "kb": 1024, "b": 1}

        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    num_str = size_str.replace(unit, "")
                    return int(float(num_str) * multiplier)
                except ValueError:
                    return 0
        try:
            return int(float(size_str))
        except:
            return 0

    def _parse_date(self, date_str: str) -> float:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.timestamp()
        except ValueError:
            print(f"Filter Error: Invalid date format '{date_str}'. Use YYYY-MM-DD.")
            return 0.0


if __name__ == "__main__":
    # Test the multi-extension logic
    engine = FilterEngine()
    print("Filter Engine Loaded.")