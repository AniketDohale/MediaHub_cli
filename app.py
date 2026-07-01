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
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from core.users import authenticate
from core.cast import discover_TV_List, cast_to_TV, stop_Cast

app = Flask(__name__)

load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# MAJOR.MINOR.PATCH
APP_VERSION = "v1.3.2"

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
    print(video.get("tags", []))

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

    category = request.form.get("category", "").strip()
    if not category:
        category = "Normal"

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
# @login_Required
def media_Stream(video_id):
    video = get_Video_By_ID(video_id)
    
    if not video:
        abort(404)

    cast_token = request.args.get("cast_token")

    if cast_token:
        try:
            data = serializer.loads(cast_token, max_age=300)
            if data.get("video_id") != video_id:
                abort(403)

        except (BadSignature, SignatureExpired):
            abort(403)

    else:
        if "user" not in session:
            return redirect(url_for("login"))

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
    flash(f"Scan Complete")
    return redirect(url_for("index"))

# Hidden Videos from Player
@app.route("/toggle-admin-videos", methods=["POST"])
@login_Required
def toggle_admin_videos():
    if session.get("role") != "admin":
        abort(403)
    session["show_admin_videos"] = not session.get("show_admin_videos", False)
    return jsonify({"enabled": session["show_admin_videos"]})


# Discover Devices
@app.route("/cast/devices", methods=["GET"])
def cast_devices():
    devices = discover_TV_List()

    return jsonify([
        {
            "name": d.friendly_name,
            "udn": d.udn,
        }
        for d in devices
    ])

# Cast File Path to TV
@app.route("/cast/<video_id>")
def cast_stream(video_id):
    video = get_Video_By_ID(video_id)
    if not video:
        return "Not Found", 404
    return send_file(video["full_path"], mimetype="video/mp4", conditional=True)

# Casting Video to Smart TV
@app.route("/cast-start/<video_id>", methods=["POST"])
def cast_start(video_id):
    quality = request.args.get("quality")
    udn = request.args.get("udn")

    base_url = request.host_url.rstrip("/")
    token = serializer.dumps({"video_id": video_id})

    VIDEO_URL = (
        f"{base_url}/media/stream/{video_id}"
        f"?quality={quality}&cast_token={token}"
        if quality
        else f"{base_url}/media/stream/{video_id}?cast_token={token}"
    )

    result = cast_to_TV(VIDEO_URL, title=video_id, udn=udn)
    return jsonify(result)

# Stop Casting
@app.route("/cast-stop", methods=["POST"])
def cast_stop():
    data = request.get_json(silent=True) or {}
    udn = data.get("udn")

    result = stop_Cast(udn)
    return jsonify(result)


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