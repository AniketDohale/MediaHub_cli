import json
from pathlib import Path

from .config import MEDIA_ROOTS, DATA_DIR

MEDIA_ROOTS_FILE = Path(DATA_DIR) / "media_roots.json"

# Load Saved Directories, or Use the Original Defaults
def get_Media_Roots():
    try:
        with open(MEDIA_ROOTS_FILE, "r", encoding="utf-8") as file:
            paths = json.load(file)

        if not isinstance(paths, list):
            raise ValueError("Invalid Media Directory Configuration")

        return [
            Path(path)
            for path in paths
            if isinstance(path, str) and path.strip()
        ]

    except FileNotFoundError:
        return list(MEDIA_ROOTS)


# Save Directory Configuration to JSON
def save_Media_Roots(paths):
    MEDIA_ROOTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = MEDIA_ROOTS_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump([str(path) for path in paths], file, indent=4)

    temp_file.replace(MEDIA_ROOTS_FILE)


# Add an Existing Directory
def add_Media_Root(directory):
    path = Path(directory).expanduser().resolve(strict=True)

    if not path.is_dir():
        raise ValueError("The specified path is not a directory.")

    roots = get_Media_Roots()

    if any(root.resolve() == path for root in roots):
        raise ValueError("Directory already Exists")

    roots.append(path)
    save_Media_Roots(roots)

    return roots


# Remove a Directory without Deleting its Files
def remove_Media_Root(directory):
    target = Path(directory).expanduser().resolve(strict=False)
    roots = get_Media_Roots()

    updated = [
        root for root in roots
        if root.resolve(strict=False) != target
    ]

    if len(updated) == len(roots):
        raise ValueError("Directory not Found")

    save_Media_Roots(updated)

    return updated