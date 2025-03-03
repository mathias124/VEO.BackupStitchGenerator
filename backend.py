import uuid
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)

FFMPEG_PATH = "C:/Users//Downloads/ffmpeg-2025-01-08-git-251de1791e-full_build/ffmpeg-2025-01-08-git-251de1791e-full_build/bin/ffmpeg.exe"
TEMP_DIR = "temp_videos"
#Just making sure the file folder is correct(for new git clones).
os.makedirs(TEMP_DIR, exist_ok=True)

#Store hash-to-file mapping list.
video_storage = {}

@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video1_url = data.get('url1')
    video2_url = data.get('url2')

    if not video1_url or not video2_url:
        return jsonify({"error": "Both video URLs must be provided"}), 400

    #Generate unique ID for preprocessing
    video1_temp = os.path.join(TEMP_DIR, f"temp1_{uuid.uuid4()}.ts")
    video2_temp = os.path.join(TEMP_DIR, f"temp2_{uuid.uuid4()}.ts")

    #Experimental, for orginal filetype 4x files to see if it reduces time when merging, so far no, about 3x slower. Preprocess .ts files to ensure 1920x1080 resolution
    preprocess_command1 = [
        FFMPEG_PATH,
        "-i", video1_url,
        "-vf", "scale=1920:1080",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-strict", "experimental",
        video1_temp
    ]
    preprocess_command2 = [
        FFMPEG_PATH,
        "-i", video2_url,
        "-vf", "scale=1920:1080",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-strict", "experimental",
        video2_temp
    ]

    try:
        #Preprocess the first video & Preprocess the second video
        subprocess.run(preprocess_command1, check=True)
        subprocess.run(preprocess_command2, check=True)

        #Merge the preprocessed videos into 1.
        video_hash = str(uuid.uuid4())  # Generate a unique hash
        output_file = os.path.join(TEMP_DIR, f"{video_hash}.mp4")

        merge_command = [
            FFMPEG_PATH,
            "-i", video1_temp,
            "-i", video2_temp,
            "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-f", "mp4",
            "-movflags", "frag_keyframe+empty_moov",
            output_file
        ]

        subprocess.run(merge_command, check=True)
        video_storage[video_hash] = output_file  # Store hash-to-file mapping

        # Clean up temp files
        os.remove(video1_temp)
        os.remove(video2_temp)

        return jsonify({"hash": video_hash}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error processing video: {e}")
        return jsonify({"error": "Failed to preprocess or merge videos"}), 500

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


if __name__ == '__main__':
    app.run(port=5000, debug=True)
