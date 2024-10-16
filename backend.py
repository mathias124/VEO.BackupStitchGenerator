import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import ffmpeg
import requests
import subprocess

app = Flask(__name__)
CORS(app)


@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()  # Extract the JSON data
    video_url = data.get('url')  # Get the video URL
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    input_path = 'temp_input.ts'
    output_path = 'output.mp4'

    # Download the video first
    try:
        print("Downloading video...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses

        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Video downloaded to {input_path}.")
    except Exception as e:
        return jsonify({"error": f"Failed to download video: {str(e)}"}), 500

    # Now process the downloaded video
    try:
        print("Starting video processing...")
        process = subprocess.run(
            ['ffmpeg', '-i', input_path, '-vf', 'scale=1920:1080', output_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Print FFmpeg output to console for debugging
        print(process.stdout.decode())
        print(process.stderr.decode())

        if process.returncode != 0:
            raise Exception(f"FFmpeg failed with error code: {process.returncode}")

        print("Video processed successfully.")
    except Exception as e:
        return jsonify({"error": f"Error during processing: {str(e)}"}), 500

    # Check if the output file exists
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file does not exist."}), 500

    # Send the processed video back to the client
    try:
        with open(output_path, 'rb') as f:
            video_data = f.read()

        # Clean up temporary files
        os.remove(input_path)
        os.remove(output_path)

        return jsonify({"message": "Video processed successfully"})
    except Exception as e:
        return jsonify({"error": f"Error while sending the file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)
