from flask import Flask, request, Response
from flask_cors import CORS  # Import CORS
import imageio_ffmpeg as ffmpeg
import tempfile
import os
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return {'error': 'No video URL provided'}, 400

    try:
        print("Starting video processing...")

        # Get ffmpeg executable path
        ffmpeg_path = ffmpeg.get_ffmpeg_exe()

        # Create a temporary file for output
        temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

        # Create a command to process the video and stream it
        command = [
            ffmpeg_path,
            '-i', video_url,  # Input URL
            '-c:v', 'libx264',  # Video codec
            '-preset', 'fast',  # Preset for compression
            temp_output_file.name,  # Output file
        ]

        # Run the ffmpeg command
        process = subprocess.run(command, capture_output=True)

        # Check if there was an error during processing
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {process.stderr.decode()}")

        print("Video processed successfully.")

        # Stream the video back to the client
        with open(temp_output_file.name, 'rb') as f:
            video_data = f.read()

        # Clean up the temporary file
        os.unlink(temp_output_file.name)

        return Response(video_data, mimetype='video/mp4')

    except Exception as e:
        print(f"Error during processing: {e}")
        return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
