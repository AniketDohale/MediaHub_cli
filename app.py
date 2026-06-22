import os, mimetypes
from flask import (
    Flask,
    request,
    session,
    render_template,
    redirect,
    url_for,
    send_file,
    flash,
    abort,
    jsonify
)

from core.utils import (
    VIDEO_INDEX,
    refresh_Video_Index,
    get_Video_By_ID,
    ensure_Thumbnail,
    get_Visible_Videos,
    load_Metadata_Cache,
    save_Metadata_Cache
)

from core.auth import (
    login_Required,
    require_Video_Access
)

from dotenv import load_dotenv

from core.users import authenticate

app = Flask(__name__)

load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# MAJOR.MINOR.PATCH
APP_VERSION = "v1.2.0"

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("login")
        password = request.form.get("password")

        user = authenticate(username, password)

        if user and user["password"] == password:
            session["user"] = username
            session["role"] = user["role"]

            flash("Login Successful!")
            return redirect(url_for("index"))
        
        flash("Invalid Credentials!")
        return redirect(url_for("login"))
    return render_template("login.html", app_version=APP_VERSION)

# Logout
@app.route("/logout", methods=["POST"])
@login_Required
def logout():
    session.clear()
    flash("Logged Out Successfully.")
    return redirect(url_for("login"))

# Video Player
@app.route("/media/player/<video_id>")
@login_Required
def media_Player(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    videos = get_Visible_Videos(session.get("role"), session.get("show_admin_videos", False))

    current_index = next((i for i, v in enumerate(videos) if v["id"] == video_id), None)
    prev_video = (videos[current_index - 1] if current_index and current_index > 0 else None)
    next_video = ( videos[current_index + 1] if current_index is not None and current_index < len(videos) - 1 else None)

    return render_template("media_Player.html", video=video, prev_video=prev_video, next_video=next_video, app_version=APP_VERSION)

# Update Metadata Cache
@app.route("/video/settings/<video_id>", methods=["POST"])
@login_Required
def update_Video_Settings(video_id):
    if session.get("role") != "admin":
        abort(403)

    video = get_Video_By_ID(video_id)
    if not video:
        abort(404)

    cache = load_Metadata_Cache()

    video_path = os.path.abspath(video["full_path"])

    if video_path not in cache:
        abort(404)

    category = request.form.get("category", "Normal").strip()
    tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    allowed_roles = [r.strip() for r in request.form.get("allowed_roles", "").split(",") if r.strip()]

    cache[video_path]["category"] = category
    cache[video_path]["tags"] = tags
    cache[video_path]["allowed_roles"] = allowed_roles

    save_Metadata_Cache(cache)
    
    if video_id in VIDEO_INDEX:
        VIDEO_INDEX[video_id]["category"] = category
        VIDEO_INDEX[video_id]["tags"] = tags
        VIDEO_INDEX[video_id]["allowed_roles"] = allowed_roles

    flash("Metadata Updated Successfully")
    return redirect(url_for("media_Player", video_id=video_id))

# Stream Route
@app.route("/media/stream/<video_id>")
@login_Required
def media_Stream(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    requested_quality = request.args.get("quality")
    if requested_quality and requested_quality in video["sources"]:
        file_path = video["sources"][requested_quality]["path"]
    else:
        file_path = video["full_path"]

    mime_type = mimetypes.guess_type(file_path)[0]
    return send_file(file_path, conditional=True, mimetype=mime_type or "application/octet-stream")

# Video Thumbnail
@app.route("/thumbnail/<video_id>")
@login_Required
def thumbnail(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    thumb_path = video["thumbnail"]
    if not os.path.exists(thumb_path):
        ensure_Thumbnail(video["full_path"], video_id)
    return send_file(thumb_path)

# Video Download
@app.route("/media/download/<video_id>")
@login_Required
def media_Download(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    quality = request.args.get("quality")
    if quality and quality in video["sources"]:
        file_path = video["sources"][quality]["path"]
    else:
        file_path = video["full_path"]
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

# Video Subtitles 
@app.route("/media/subtitles/<video_id>")
@login_Required
def media_Subtitles(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    if not video or not video.get("subtitle_path"):
        abort(404)
    return send_file(video["subtitle_path"], mimetype="text/vtt", conditional=True)

# Metadata of Source
@app.route("/media/metadata/<video_id>")
@login_Required
def media_Metadata(video_id):
    video = get_Video_By_ID(video_id)

    require_Video_Access(video)

    quality = request.args.get("quality")
    if quality and quality in video["sources"]:
        return jsonify(video["sources"][quality]["metadata"])

    first_source = next(iter(video["sources"].values()))
    return jsonify(first_source["metadata"])

# Scan Media Route
@app.route("/scan-media", methods=["POST"])
@login_Required
def scan_Media_Route():
    refresh_Video_Index()
    flash(f"Scan Complete.")
    return redirect(url_for("index"))

# Hidden Videos from Player
@app.route("/toggle-admin-videos", methods=["POST"])
@login_Required
def toggle_admin_videos():
    if session.get("role") != "admin":
        abort(403)
    session["show_admin_videos"] = not session.get("show_admin_videos", False)
    return jsonify({"enabled": session["show_admin_videos"]})

# Media Library
@app.route("/")
@login_Required
def index():
    videos = get_Visible_Videos(session.get("role"), session.get("show_admin_videos", False))
    return render_template("media.html", videos=videos, username=session.get("user"), app_version=APP_VERSION)

# Initial Scan
refresh_Video_Index()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)