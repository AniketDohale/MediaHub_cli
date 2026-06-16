import os, json, subprocess, hashlib, re
from datetime import timedelta
from threading import Lock

from .config import (
    MEDIA_ROOT,
    VIDEO_EXTENSIONS,
    METADATA_CACHE_FILE,
    THUMB_DIR,
    SUBTITLE_DIR
)

thumb_lock = Lock()

THUMB_TIME = "00:00:10"

VIDEO_INDEX = {}

def get_Video_Metadata(path, cache):
    mtime = os.path.getmtime(path)
    cache_key = os.path.abspath(path)

    if (cache_key in cache and cache[cache_key].get("mtime") == mtime):
        return cache[cache_key]["metadata"]

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

        duration = float(format_info.get("duration", 0))
        size = int(format_info.get("size", 0))

        bitrate_mbps = 0
        if duration > 0:
            bitrate_mbps = round((size * 8) / duration / 1024 / 1024, 2)

        width = video_stream.get("width")
        height = video_stream.get("height")

        metadata = {
            "duration": str(timedelta(seconds=int(duration))),
            "size_mb": round(size / (1024 * 1024), 2),
            "resolution": (f"{width}x{height}" if width and height else "Unknown"),
            "width": width,
            "height": height,
            "bitrate_mbps": bitrate_mbps
        }

        if cache_key not in cache:
            cache[cache_key] = {
                "mtime": mtime,
                "metadata": metadata,
                "category": "Normal",
                "tags": [],
                "allowed_roles": []
            }
        else:
            cache[cache_key]["mtime"] = mtime
            cache[cache_key]["metadata"] = metadata

        if "allowed_roles" not in cache[cache_key]:
            cache[cache_key]["allowed_roles"] = []

        return metadata
    except:
        return {
            "duration": "Unknown",
            "size_mb": 0,
            "resolution": "Unknown"
        }

def load_Metadata_Cache():
    if not os.path.exists(METADATA_CACHE_FILE):
        return {}
    try:
        with open(METADATA_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}
    
def save_Metadata_Cache(cache):
    try:
        with open(METADATA_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except:
        pass

def scan_Media():
    grouped_videos = {}
    quality_rank = {
        "480p": 1,
        "720p": 2,
        "1080p": 3,
        "1440p": 4,
        "4K": 5
    }
    cache = load_Metadata_Cache()

    existing_files = set()
    valid_video_ids = set()

    for root, dirs, files in os.walk(MEDIA_ROOT):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                full_path = os.path.abspath(os.path.join(root, file))
                existing_files.add(full_path)
                raw_name = os.path.splitext(file)[0]
                clean_name = re.sub(r'(?i)\b(1080p|4k|2160p|720p)\b', '', raw_name)
                clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                video_id = hashlib.md5(clean_name.encode()).hexdigest()[:10]
                valid_video_ids.add(video_id)
                metadata = get_Video_Metadata(full_path, cache)

                cache_key = os.path.abspath(full_path)
                category = cache.get(cache_key, {}).get("category", "Normal")
                allowed_roles = cache.get(cache_key, {}).get("allowed_roles", [])

                width = metadata.get("width", 0)

                if width >= 3840:
                    res_tag = "4K"
                elif width >= 2560:
                    res_tag = "1440p"
                elif width >= 1920:
                    res_tag = "1080p"
                elif width >= 1280:
                    res_tag = "720p"
                elif width >= 854:
                    res_tag = "480p"
                else:
                    res_tag = metadata.get("resolution", "Unknown")
                    
                thumb_path = get_Thumbnail_Path(video_id)
                subtitle_path = find_Subtitle(full_path)

                if video_id not in grouped_videos:
                    grouped_videos[video_id] = {
                        "id": video_id,
                        "name": clean_name,
                        "full_path": full_path,
                        "relative": os.path.relpath(full_path, MEDIA_ROOT).replace("\\", "/"),
                        "thumbnail": thumb_path,
                        "subtitle_path": subtitle_path if subtitle_path and os.path.exists(subtitle_path) else None,
                        "has_subtitle": bool(subtitle_path and os.path.exists(subtitle_path)),
                        "sources": {},
                        "group_quality": float("inf"),
                        "category": category,
                        "allowed_roles": allowed_roles
                    }

                grouped_videos[video_id]["sources"][res_tag] = {
                    "path": full_path,
                    "metadata": metadata
                }

                current_rank = grouped_videos[video_id].get("group_quality", float("inf"))
                new_rank = quality_rank.get(res_tag, float("inf"))

                if new_rank < current_rank:
                    grouped_videos[video_id]["full_path"] = full_path
                    grouped_videos[video_id]["metadata"] = metadata
                    grouped_videos[video_id]["group_quality"] = new_rank

    cleanup_Orphans(cache, valid_video_ids, existing_files)
    save_Metadata_Cache(cache)
    for video in grouped_videos.values():
        if video["sources"]:
            video["default_quality"] = min(video["sources"].keys(), key=lambda q: quality_rank.get(q, 0))
    return sorted(list(grouped_videos.values()), key=lambda v: v["name"].lower())

def get_Video_By_ID(video_id):
    return VIDEO_INDEX.get(video_id)

def generate_Thumbnail(video_path, video_id):
    thumb_path = os.path.join(THUMB_DIR, f"{video_id}.jpg")

    if os.path.exists(thumb_path):
        return thumb_path

    command = [
        "ffmpeg",
        "-ss", THUMB_TIME,
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        thumb_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return thumb_path

def get_Thumbnail_Path(video_id):
    return os.path.join(THUMB_DIR, f"{video_id}.jpg")

def ensure_Thumbnail(video_path, video_id):
    thumb_path = get_Thumbnail_Path(video_id)

    if os.path.exists(thumb_path):
        return thumb_path
    
    with thumb_lock:
        if not os.path.exists(thumb_path):
            generate_Thumbnail(video_path, video_id)
    return thumb_path

def find_Subtitle(video_file):
    base = os.path.splitext(os.path.basename(video_file))[0]
    path = os.path.join(SUBTITLE_DIR, f"{base}.vtt")
    return path if os.path.exists(path) else None

def refresh_Video_Index():
    videos = scan_Media()

    VIDEO_INDEX.clear()
    VIDEO_INDEX.update({v["id"]: v for v in videos})

    return videos

def cleanup_Orphans(cache, valid_video_ids, existing_files):
    # Cache Cleanup
    for path in list(cache.keys()):
        if path not in existing_files:
            del cache[path]

    # Thumbnail Cleanup
    if os.path.isdir(THUMB_DIR):
        for file in os.listdir(THUMB_DIR):
            if file.lower().endswith(".jpg"):
                video_id = os.path.splitext(file)[0]

                if video_id not in valid_video_ids:
                    try:
                        os.remove(os.path.join(THUMB_DIR, file))
                    except OSError:
                        pass