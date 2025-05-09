import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import os
import requests

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
    video_url = data.get('url')
    start = data.get('start')
    duration = data.get('duration')

    if not video_url or start is None or duration is None:
        return jsonify({"error": "Video URL, start, and duration must be provided"}), 400

    try:
        start = float(start)
        duration = float(duration)
    except ValueError:
        return jsonify({"error": "Start and duration must be numeric"}), 400

    output_hash = str(uuid.uuid4())
    output_file = os.path.join(TEMP_DIR, f"{output_hash}.mp4")

    trim_command = [
        FFMPEG_PATH,
        "-ss", str(start),
        "-i", video_url,
        "-t", str(duration),
        "-c", "copy",
        output_file
    ]

    try:
        subprocess.run(trim_command, check=True)
        video_storage[output_hash] = output_file
        return jsonify({"hash": output_hash}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error trimming video: {e}")
        return jsonify({"error": "Failed to trim video"}), 500

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



if __name__ == '__main__':
    app.run(port=5000, debug=True)
