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
    MEDIA_ROOT = Path(r"D:\Media")
# For RaspberryPI
elif platform.system() == "Linux":
    MEDIA_ROOT = Path("/home/raspberry_cli/Shared/USB")

# Central app folder
APP_DIR = os.path.join(MEDIA_ROOT, ".MediaHub")

# Subfolders
THUMB_DIR = os.path.join(APP_DIR, ".thumbnails")
SUBTITLE_DIR = os.path.join(APP_DIR, "subtitles")

# Video Format Extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}

# Ensure Folders Exist
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(SUBTITLE_DIR, exist_ok=True)