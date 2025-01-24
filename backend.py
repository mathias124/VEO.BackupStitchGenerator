import uuid
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)

FFMPEG_PATH = "C:/Users/veouser/Downloads/ffmpeg-2025-01-08-git-251de1791e-full_build/ffmpeg-2025-01-08-git-251de1791e-full_build/bin/ffmpeg.exe"
TEMP_DIR = "temp_videos"

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# Store hash-to-file mapping
video_storage = {}

@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video1_url = data.get('url1')
    video2_url = data.get('url2')

    if not video1_url or not video2_url:
        return jsonify({"error": "Both video URLs must be provided"}), 400

    video_hash = str(uuid.uuid4())  # Generate a unique hash
    output_file = os.path.join(TEMP_DIR, f"{video_hash}.mp4")

    # Run FFmpeg command to merge videos
    command = [
        FFMPEG_PATH,
        "-i", video1_url,
        "-i", video2_url,
        "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]",
        "-map", "[outa]",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov",
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        video_storage[video_hash] = output_file  # Store hash-to-file mapping
        return jsonify({"hash": video_hash}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error processing video: {e}")
        return jsonify({"error": "Failed to merge videos"}), 500


@app.route('/stream/<hash_link>', methods=['GET'])
def stream_video(hash_link):
    file_path = video_storage.get(hash_link)
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Video not found"}), 404

    # Stream the video file
    def generate():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return Response(generate(), content_type="video/mp4")


if __name__ == '__main__':
    app.run(port=5000, debug=True)
