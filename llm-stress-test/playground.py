import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

# CONFIGURATION
TARGET_DIR = Path("Checking").resolve()


def create_dummy_file(name, size_mb=0, date_str=None, is_empty=False):
    """
    Creates a file with a specific size and modification date.
    """
    file_path = TARGET_DIR / name

    # 1. Create File
    with open(file_path, "wb") as f:
        if is_empty:
            pass  # Write nothing (0 bytes)
        elif size_mb > 0:
            # Write dummy bytes
            size_bytes = int(size_mb * 1024 * 1024)
            f.write(b'\0' * size_bytes)
        else:
            # Write a tiny bit of text (default small file)
            f.write(b'This is a small text file for testing.')

    # 2. Modify Date (Time Travel)
    if date_str:
        # Parse YYYY-MM-DD
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            timestamp = dt.timestamp()
            os.utime(file_path, (timestamp, timestamp))
        except ValueError:
            print(f"Error parsing date for {name}")

    print(f"Created: {name:<25} | Size: {size_mb:>6} MB | Date: {date_str or 'Today'}")


def main():
    # 1. Reset Directory
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir()

    print(f"--- Setting up Massive Test Environment in '{TARGET_DIR}' ---\n")

    # --- 1. DOCUMENTS (Mixed Dates) ---
    create_dummy_file("financial_report_2020.pdf", size_mb=2.5, date_str="2020-05-10")
    create_dummy_file("thesis_draft.docx", size_mb=0.8, date_str="2023-11-01")
    create_dummy_file("budget_planning.xlsx", size_mb=1.5, date_str="2024-01-15")
    create_dummy_file("presentation.pptx", size_mb=12.0, date_str="2024-06-20")
    create_dummy_file("readme.md", size_mb=0.01)  # Today

    # --- 2. IMAGES (Various Formats) ---
    create_dummy_file("vacation.jpg", size_mb=3.2, date_str="2022-07-04")
    create_dummy_file("profile_pic.png", size_mb=0.5, date_str="2023-02-14")
    create_dummy_file("design_mockup.bmp", size_mb=5.0)
    create_dummy_file("icon.gif", size_mb=0.1)
    create_dummy_file("vector_logo.svg", size_mb=0.05)

    # --- 3. DEVELOPER FILES (Code) ---
    create_dummy_file("index.html", size_mb=0.02)
    create_dummy_file("style.css", size_mb=0.01)
    create_dummy_file("app.js", size_mb=0.05)
    create_dummy_file("backend.py", size_mb=0.03)
    create_dummy_file("config.json", size_mb=0.01)
    create_dummy_file("database.sql", size_mb=15.0)  # Large SQL dump

    # --- 4. SYSTEM & LOGS (Recent/Temporary) ---
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    create_dummy_file("error.log", size_mb=0.5, date_str=yesterday)
    create_dummy_file("debug.log", size_mb=2.0)  # Today
    create_dummy_file("temp_cache.tmp", size_mb=0.0)
    create_dummy_file("session_cookies.dat", size_mb=0.01)

    # --- 5. MEDIA (Large Files) ---
    create_dummy_file("movie_4k.mkv", size_mb=550.0)  # 550 MB
    create_dummy_file("podcast_episode.mp3", size_mb=45.0)
    create_dummy_file("raw_footage.mov", size_mb=120.0)

    # --- 6. EDGE CASES ---
    create_dummy_file("empty_file.txt", is_empty=True)  # 0 Bytes
    create_dummy_file(".hidden_config", size_mb=0.01)  # Hidden file (on Unix)
    create_dummy_file("archive.tar.gz", size_mb=10.0)

    print("\n--- Done! ---")
    print(f"Location: {TARGET_DIR}")
    print("\nTry these new prompts:")
    print("1. 'Delete all empty files'")
    print("2. 'List all code files (js, py, html, css)'")
    print("3. 'Move files larger than 100MB to a Movies folder'")
    print("4. 'Find all logs from yesterday'")


if __name__ == "__main__":
    main()