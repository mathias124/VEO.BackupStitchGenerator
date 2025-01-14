import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Temporary in-memory store for video URLs
video_store = {}

@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    # Generate a unique ID for the video
    video_id = os.path.basename(video_url)
    video_store[video_id] = video_url  # Save the video URL in the store

    return jsonify({'output_url': video_id})


@app.route('/stream/<path:video_id>', methods=['GET'])
def stream_video(video_id):
    # Retrieve the video URL from the store
    video_url = video_store.get(video_id)

    if not video_url:
        return jsonify({"error": "Video not found"}), 404

    # Fetch the video from the URL
    response = requests.get(video_url, stream=True)
    if response.status_code != 200:
        return jsonify({"error": "Error fetching the video"}), 500

    # Stream the video content to the client
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk

    return Response(generate(), content_type='video/mp4')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
