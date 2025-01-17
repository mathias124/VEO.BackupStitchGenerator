import subprocess
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import imageio_ffmpeg as ffmpeg


ffmpeg_path = ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)
CORS(app)


@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video1_url = data.get('url1')
    video2_url = data.get('url2')

    if not video1_url or not video2_url:
        return jsonify({"error": "Both video URLs must be provided"}), 400

    return Response(
        stream_merged_videos(video1_url, video2_url),
        content_type='video/mp4'
    )


def stream_merged_videos(url1, url2):
    try:
        # Use FFmpeg to merge streams and output to stdout
        command = [
            "C:/Users/veouser//Downloads/ffmpeg-2025-01-08-git-251de1791e-full_build/ffmpeg-2025-01-08-git-251de1791e-full_build/bin/ffmpeg.exe",  # Replace with the full path to FFmpeg
            "-i", url1,
            "-i", url2,
            "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-f", "mp4",
            "-movflags", "frag_keyframe+empty_moov",
            "pipe:1"
        ]

        # Use subprocess to run the FFmpeg command and yield the output
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            chunk = process.stdout.read(8192)
            if not chunk:
                break
            yield chunk

        process.stdout.close()
        process.wait()
    except Exception as e:
        print(f"Error merging streams: {e}")
        yield b''


if __name__ == '__main__':
    app.run(port=5000, debug=True)
