import os, platform
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Folder
DATA_DIR = os.path.join(BASE_DIR, "data")

# users.json
USERS_FILE = os.path.join(DATA_DIR, "users.json")
# Metadata Cache
METADATA_CACHE_FILE = os.path.join(DATA_DIR, "metadata_cache.json")

# For Windows
if platform.system() == "Windows":
    MEDIA_ROOTS = [
        Path(r"D:\Media"),
        # Add More Directories Here
        Path(r"E:\Videos"),
    ]

# For Linux
elif platform.system() == "Linux":
    MEDIA_ROOTS = [
        Path("/home/radxa/Shared"),
        # Add More Directories Here
        # Path("/media/raspberry/BackupDrive"),
    ]

else:
    MEDIA_ROOTS = []

# Central app folder
APP_DIR = Path(DATA_DIR) / ".MediaHub"

# Subfolders
THUMB_DIR = APP_DIR / ".thumbnails"
SUBTITLE_DIR = APP_DIR / "subtitles"

# Video Format Extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}

# Ensure Folders Exist
THUMB_DIR.mkdir(parents=True, exist_ok=True)
SUBTITLE_DIR.mkdir(parents=True, exist_ok=True)