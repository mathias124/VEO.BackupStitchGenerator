import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import os
import requests
import tempfile
from werkzeug.utils import secure_filename

from urllib.parse import urlparse, parse_qs


app = Flask(__name__)
CORS(app)

FFMPEG_PATH = "C:/Users/veouser/Downloads/ffmpeg-2025-01-08-git-251de1791e-full_build/ffmpeg-2025-01-08-git-251de1791e-full_build/bin/ffmpeg.exe"
TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

video_storage = {}

@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video1_url = data.get('url1')
    video2_url = data.get('url2')

    if not video1_url or not video2_url:
        return jsonify({"error": "Both video URLs must be provided"}), 400

    # Download videos locally as temp .mp4 files
    video1_temp = os.path.join(TEMP_DIR, f"temp1_{uuid.uuid4()}.mp4")
    video2_temp = os.path.join(TEMP_DIR, f"temp2_{uuid.uuid4()}.mp4")

    try:
        # Download videos using requests
        for url, path in [(video1_url, video1_temp), (video2_url, video2_temp)]:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

        # Create concat file list
        concat_file = os.path.join(TEMP_DIR, f"concat_{uuid.uuid4()}.txt")
        with open(concat_file, 'w') as f:
            f.write(f"file '{os.path.abspath(video1_temp)}'\n")
            f.write(f"file '{os.path.abspath(video2_temp)}'\n")

        video_hash = str(uuid.uuid4())
        output_file = os.path.join(TEMP_DIR, f"{video_hash}.mp4")

        merge_command = [
            FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_file
        ]

        subprocess.run(merge_command, check=True)
        video_storage[video_hash] = output_file


        os.remove(video1_temp)
        os.remove(video2_temp)
        os.remove(concat_file)

        return jsonify({"hash": video_hash}), 200

    except Exception as e:
        print(f"Error during fast merge: {e}")
        return jsonify({"error": "Failed to process and merge videos"}), 500


@app.route('/trim-video', methods=['POST'])
def trim_video():
    data = request.get_json()
    url1 = data.get('url1')
    url2 = data.get('url2')
    start = data.get('start')
    duration = data.get('duration')

    if not url1 or not url2 or start is None or duration is None:
        return jsonify({"error": "url1, url2, start, and duration must all be provided"}), 400

    try:
        start = float(start)
        duration = float(duration)
    except ValueError:
        return jsonify({"error": "Start and duration must be numeric"}), 400

    hash1 = str(uuid.uuid4())
    hash2 = str(uuid.uuid4())
    path1 = os.path.join(TEMP_DIR, f"{hash1}.mp4")
    path2 = os.path.join(TEMP_DIR, f"{hash2}.mp4")

    cmd1 = [
        FFMPEG_PATH, "-ss", str(start), "-i", url1,
        "-t", str(duration), "-c", "copy", path1
    ]
    cmd2 = [
        FFMPEG_PATH, "-ss", str(start), "-i", url2,
        "-t", str(duration), "-c", "copy", path2
    ]

    try:
        p1 = subprocess.Popen(cmd1)
        p2 = subprocess.Popen(cmd2)
        p1.wait()
        p2.wait()

        if p1.returncode != 0 or p2.returncode != 0:
            raise subprocess.CalledProcessError(p1.returncode or p2.returncode, cmd1 if p1.returncode else cmd2)

        video_storage[hash1] = path1
        video_storage[hash2] = path2

        return jsonify({"hash1": hash1, "hash2": hash2}), 200

    except subprocess.CalledProcessError as e:
        print(f"Trimming error: {e}")
        return jsonify({"error": "One or both trims failed"}), 500


@app.route('/stream/<hash_link>', methods=['GET'])
def stream_video(hash_link):
    file_path = video_storage.get(hash_link)
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Video not found"}), 404

    def generate():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return Response(generate(), content_type="video/mp4")

from flask import stream_with_context
import requests

@app.route('/proxy-video')
def proxy_video():
    remote_url = request.args.get('url')
    if not remote_url or not remote_url.startswith("http"):
        return jsonify({"error": "Missing or invalid URL"}), 400

    try:
        headers = {}
        # Forward Range header if present
        if 'Range' in request.headers:
            headers['Range'] = request.headers['Range']

        r = requests.get(remote_url, stream=True, headers=headers, timeout=10)
        status_code = 206 if 'Range' in request.headers else 200

        response = Response(stream_with_context(r.iter_content(chunk_size=8192)),
                            status=status_code,
                            content_type=r.headers.get("Content-Type", "video/mp4"))

        # Forward essential headers
        response.headers["Content-Length"] = r.headers.get("Content-Length", "")
        response.headers["Accept-Ranges"] = r.headers.get("Accept-Ranges", "bytes")
        response.headers["Content-Range"] = r.headers.get("Content-Range", "")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        return response

    except Exception as e:
        print(f"Proxy error: {e}")
        return jsonify({"error": "Failed to fetch remote video"}), 500


def ffmpeg_split_vertical(src_path, left_out, right_out, top_is_left=True):
    top_crop = "crop=iw:floor(ih/2):0:0"
    bottom_crop = "crop=iw:floor(ih/2):0:floor(ih/2)"
    L, R = (top_crop, bottom_crop) if top_is_left else (bottom_crop, top_crop)

    cmd = [
        FFMPEG_PATH, "-i", src_path, "-filter_complex",
        f"[0:v]{L}[L];[0:v]{R}[R]",
        "-map", "[L]", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", left_out,
        "-map", "[R]", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", right_out
    ]
    subprocess.run(cmd, check=True)

def do_hstack_and_return(url1, url2):
    out_hash = str(uuid.uuid4())
    output_file = os.path.join(TEMP_DIR, f"{out_hash}.mp4")
    cmd = [
        FFMPEG_PATH, "-i", url1, "-i", url2,
        "-filter_complex", "[0:v][1:v]hstack=inputs=2[v]",
        "-map", "[v]", "-map", "0:a?",            # keep audio from left if present
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-shortest", "-movflags", "+faststart",
        output_file
    ]
    try:
        subprocess.run(cmd, check=True)
        video_storage[out_hash] = output_file
        return jsonify({"hash": out_hash}), 200
    except Exception as e:
        print(f"Panorama stitch error: {e}")
        return jsonify({"error": "Failed to stitch panorama"}), 500

def _pick(d, *keys):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None

# ---------- route ----------

@app.route('/panorama-stitch', methods=['POST'])
def panorama_stitch():
    """
    Accept:
      a) multipart/form-data: field "stacked_file" (.mp4), optional "layout" (vertical) and "top_is" (left|right)
      b) JSON: {"stacked_url":"...", "layout":"vertical", "top_is":"left"}
      c) Legacy: {"settings": {"url1":"...", "url2":"..."}}
    """
    # ---- A) multipart: uploaded stacked file ----
    if 'stacked_file' in request.files:
        f = request.files['stacked_file']
        if not f or not f.filename.lower().endswith('.mp4'):
            return jsonify({"error": "stacked_file must be an .mp4"}), 400

        layout = (request.form.get('layout') or 'vertical').lower()
        top_is = (request.form.get('top_is') or 'left').lower()

        if layout != 'vertical':
            return jsonify({"error": "only vertical stacks supported"}), 400

        tmpdir = tempfile.mkdtemp(dir=TEMP_DIR)
        in_path = os.path.join(tmpdir, secure_filename(f.filename))
        f.save(in_path)

        left_path  = os.path.join(tmpdir, "left.mp4")
        right_path = os.path.join(tmpdir, "right.mp4")
        ffmpeg_split_vertical(in_path, left_path, right_path, top_is_left=(top_is == 'left'))

        return do_hstack_and_return(left_path, right_path)   # <- IMPORTANT

    # ---- B) JSON body ----
    data = request.get_json(silent=True) or {}
    settings = data.get('settings') or {}
    stacked_url = data.get('stacked_url')
    layout = (data.get('layout') or 'vertical').lower()
    top_is = (data.get('top_is') or 'left').lower()

    # Legacy two-URL inputs
    url1 = _pick(settings, "url1", "left_url", "left")
    url2 = _pick(settings, "url2", "right_url", "right")

    # Single stacked_url -> download & split
    if (not url1 or not url2) and stacked_url:
        if layout != 'vertical':
            return jsonify({"error": "only vertical stacks supported"}), 400

        tmpdir = tempfile.mkdtemp(dir=TEMP_DIR)
        stacked_path = os.path.join(tmpdir, "stacked.mp4")

        # allow local path or http(s)
        if stacked_url.startswith("http"):
            with requests.get(stacked_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(stacked_path, "wb") as o:
                    for chunk in r.iter_content(1 << 15):
                        o.write(chunk)
        else:
            # treat as filesystem path
            if not os.path.exists(stacked_url):
                return jsonify({"error": f"stacked_url path not found: {stacked_url}"}), 400
            stacked_path = stacked_url

        left_path  = os.path.join(tmpdir, "left.mp4")
        right_path = os.path.join(tmpdir, "right.mp4")
        ffmpeg_split_vertical(stacked_path, left_path, right_path, top_is_left=(top_is == 'left'))
        return do_hstack_and_return(left_path, right_path)   # <- IMPORTANT

    # Final legacy guard
    if not url1 or not url2:
        return jsonify({"error": "Could not resolve both source URLs"}), 400

    return do_hstack_and_return(url1, url2)



if __name__ == '__main__':
    app.run(port=5000, debug=True)
