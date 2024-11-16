import requests
from flask import Flask, request, jsonify
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/process-video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    return jsonify({'output_url': video_url})


@app.route('/stream/<path:video_filename>', methods=['GET'])
def stream_video(video_filename):
    # Mocking the behavior for demonstration
    video_url = f"c6cf4c5d-31c6-4cad-ad32-6b24484b8ddb/standard/machine/0213a5f1/{video_filename}"

    response = requests.get(video_url, stream=True)
    if response.status_code != 200:
        return jsonify({"error": "Video not found"}), 404

    return response.content, 200, {'Content-Type': 'video/mp4'}


if __name__ == '__main__':
    app.run(port=5000, debug=True)
