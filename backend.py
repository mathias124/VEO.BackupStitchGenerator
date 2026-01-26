import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import os
import cv2
import json
import numpy as np
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


def _download_to(path, url_or_path, timeout=60):
    if url_or_path.startswith("http"):
        with requests.get(url_or_path, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(path, "wb") as o:
                for ch in r.iter_content(1<<15):
                    o.write(ch)
        return path
    # local path
    if not os.path.exists(url_or_path):
        raise FileNotFoundError(url_or_path)
    return url_or_path

def _parse_matrix(s, dim):
    arr = np.fromstring(s, sep=",", dtype=np.float32)
    return arr.reshape(dim)

def _parse_dist(s):
    # OpenCV accepts up to 14 coeffs in the classic model; your JSON provides many.
    return np.fromstring(s, sep=",", dtype=np.float32).reshape(-1, 1)

def _undistort(img, K, D):
    h, w = img.shape[:2]
    newK, _ = cv2.getOptimalNewCameraMatrix(K, D, (w, h), alpha=0)
    map1, map2 = cv2.initUndistortRectifyMap(K, D, None, newK, (w, h), cv2.CV_32FC1)
    return cv2.remap(img, map1, map2, cv2.INTER_LINEAR), newK

def _corners_from_json(calib, w, h, half="left"):
    """
    Returns pixel coordinates for left/right corners from calib['selected_corners'].
    We expect normalized coords in [0..1] per-lens frame.
    """
    ptsL, ptsR = [], []
    corners = (calib.get("selected_corners") or {}).get("corners_stacked") or {}
    keys = ["cl","cr","fl","fr"]
    for k in keys:
        node = corners.get(k) or {}
        L = node.get("left", {})
        R = node.get("right", {})
        if L.get("valid", 0) and R.get("valid", 0):
            xL, yL = L["stacked"]
            xR, yR = R["stacked"]
            # clamp and convert to pixel coords inside each half
            xL = np.clip(xL, 0.0, 1.0) * w
            yL = np.clip(yL, 0.0, 1.0) * h
            xR = np.clip(xR, 0.0, 1.0) * w
            yR = np.clip(yR, 0.0, 1.0) * h
            ptsL.append([xL, yL])
            ptsR.append([xR, yR])
    if len(ptsL) >= 4:
        return np.float32(ptsL), np.float32(ptsR)
    return None, None

def _align_right_to_left(imgL, imgR, ptsL=None, ptsR=None):
    # If we have at least 4 corner pairs, compute H from them; else fallback to ORB match.
    if ptsL is not None and ptsR is not None and len(ptsL) >= 4:
        H, m = cv2.findHomography(ptsR, ptsL, cv2.RANSAC, 3.0)
    else:
        # ORB fallback
        orb = cv2.ORB_create(3000)
        k1, d1 = orb.detectAndCompute(cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY), None)
        k2, d2 = orb.detectAndCompute(cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY), None)
        if d1 is None or d2 is None:
            raise RuntimeError("Feature detection failed")
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(d2, d1), key=lambda m: m.distance)[:500]
        if len(matches) < 12:
            raise RuntimeError("Not enough matches")
        src = np.float32([k2[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
        dst = np.float32([k1[m.trainIdx].pt for m in matches]).reshape(-1,1,2)
        H, m = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    return H

def _feather_blend(base, warped, offset=(0,0)):
    # Simple feather: alpha ramp across overlap
    xoff, yoff = offset
    h, w = base.shape[:2]
    wb = warped.shape[1]
    # Compute overlap mask
    mask_warp = (warped.sum(axis=2) > 0).astype(np.uint8) * 255
    # distance transform for feather
    dist1 = cv2.distanceTransform((255 - mask_warp), cv2.DIST_L2, 3)
    dist2 = cv2.distanceTransform((255 - (cv2.cvtColor(base, cv2.COLOR_BGR2GRAY) > 0).astype(np.uint8)*255), cv2.DIST_L2, 3)
    alpha = dist2 / (dist1 + dist2 + 1e-6)
    alpha = np.clip(alpha, 0, 1)[..., None]
    out = (alpha * warped + (1 - alpha) * base).astype(np.uint8)
    return out

def _process_video(stacked_path, json_path, top_is_left=True, crf="20"):
    cap = cv2.VideoCapture(stacked_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open stacked video")

    # Grab first frame to determine sizes
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError("Empty video")

    h, w = frame.shape[:2]
    half_h = h // 2
    left_raw  = frame[:half_h, :, :] if top_is_left else frame[half_h:, :, :]
    right_raw = frame[half_h:, :, :] if top_is_left else frame[:half_h, :, :]

    # Load calibration
    with open(json_path, "r") as f:
        J = json.load(f)
    calib = J["alignment"]
    K_L = _parse_matrix(calib["intrinsic_left"],  (3,3))
    K_R = _parse_matrix(calib["intrinsic_right"], (3,3))
    D_L = _parse_dist(calib["distortion_left"])
    D_R = _parse_dist(calib["distortion_right"])

    # Undistort first frame to estimate canvas
    undL0, newK_L = _undistort(left_raw,  K_L, D_L)
    undR0, newK_R = _undistort(right_raw, K_R, D_R)

    # Corner pairs (pixel coords in undistorted domain). We assume corners are normalized per-lens.
    ptsL_norm, ptsR_norm = _corners_from_json(J, undL0.shape[1], undL0.shape[0])
    # If corner points exist, they refer to pre-undistorted pixels.
    # A pragmatic approach: treat them as undistorted already (often close enough if intrinsics are okay).
    H = _align_right_to_left(undL0, undR0, ptsL_norm, ptsR_norm)

    # Prepare writer (we’ll write raw frames to a temp .mp4 with ffmpeg)
    out_hash = str(uuid.uuid4())
    raw_dir = os.path.join(TEMP_DIR, f"raw_{out_hash}")
    os.makedirs(raw_dir, exist_ok=True)

    # First frame process & save
    canvas_w = undL0.shape[1] * 2
    canvas_h = undL0.shape[0]
    warped0 = cv2.warpPerspective(undR0, H, (canvas_w, canvas_h))
    base0 = np.zeros_like(warped0)
    base0[0:undL0.shape[0], 0:undL0.shape[1]] = undL0
    out0 = _feather_blend(base0, warped0)
    cv2.imwrite(os.path.join(raw_dir, "f000000.png"), out0)

    # Process remaining frames
    idx = 1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        left_raw  = frame[:half_h, :, :] if top_is_left else frame[half_h:, :, :]
        right_raw = frame[half_h:, :, :] if top_is_left else frame[:half_h, :, :]

        undL, _ = _undistort(left_raw,  K_L, D_L)
        undR, _ = _undistort(right_raw, K_R, D_R)

        warped = cv2.warpPerspective(undR, H, (canvas_w, canvas_h))
        base = np.zeros_like(warped)
        base[0:undL.shape[0], 0:undL.shape[1]] = undL
        out = _feather_blend(base, warped)

        cv2.imwrite(os.path.join(raw_dir, f"f{idx:06d}.png"), out)
        idx += 1

    cap.release()

    # Encode with ffmpeg (copy your style)
    output_file = os.path.join(TEMP_DIR, f"{out_hash}.mp4")
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-framerate", "30",                     # you can probe real fps if needed
        "-i", os.path.join(raw_dir, "f%06d.png"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_file
    ]
    subprocess.run(cmd, check=True)

    # cleanup pngs to save space (optional)
    for fn in os.listdir(raw_dir):
        try: os.remove(os.path.join(raw_dir, fn))
        except: pass
    try: os.rmdir(raw_dir)
    except: pass

    return out_hash, output_file

@app.route('/panorama-stitch', methods=['POST'])
def panorama_stitch():
    """
    Accept:
      A) multipart/form-data:
         - stacked_file: .mp4 (required) OR stacked_url: http(s) or local path
         - calib_file: .json (required) OR calib_url: http(s) or local path
         - top_is: left|right (default: left)
      B) JSON:
         { "stacked_url": "...", "calib_url": "...", "top_is": "left" }
    Returns: {"hash": "..."}
    """
    top_is = "left"
    tmpdir = tempfile.mkdtemp(dir=TEMP_DIR)

    try:
        # --- Inputs: allow both multipart and JSON ---
        if request.files:
            # video
            if 'stacked_file' in request.files:
                f = request.files['stacked_file']
                if not f or not f.filename.lower().endswith('.mp4'):
                    return jsonify({"error": "stacked_file must be .mp4"}), 400
                stacked_path = os.path.join(tmpdir, f.filename)
                f.save(stacked_path)
            else:
                stacked_url = request.form.get("stacked_url")
                if not stacked_url:
                    return jsonify({"error": "Provide stacked_file or stacked_url"}), 400
                stacked_path = os.path.join(tmpdir, "stacked.mp4")
                _download_to(stacked_path, stacked_url)

            # json
            if 'calib_file' in request.files:
                j = request.files['calib_file']
                if not j or not j.filename.lower().endswith('.json'):
                    return jsonify({"error": "calib_file must be .json"}), 400
                json_path = os.path.join(tmpdir, j.filename)
                j.save(json_path)
            else:
                calib_url = request.form.get("calib_url")
                if not calib_url:
                    return jsonify({"error": "Provide calib_file or calib_url"}), 400
                json_path = os.path.join(tmpdir, "calibration.json")
                _download_to(json_path, calib_url)

            top_is = (request.form.get("top_is") or "left").lower()

        else:
            data = request.get_json(silent=True) or {}
            stacked_url = data.get("stacked_url")
            calib_url   = data.get("calib_url")
            calib_obj   = data.get("calib")
            top_is      = (data.get("top_is") or "left").lower()
            if not stacked_url:
                return jsonify({"error": "stacked_url is required"}), 400
            if not calib_url and calib_obj is None:
                return jsonify({"error": "Provide calib_url or calib"}), 400

            stacked_path = os.path.join(tmpdir, "stacked.mp4")
            json_path    = os.path.join(tmpdir, "calibration.json")

            _download_to(stacked_path, stacked_url)

            if calib_obj is not None:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(calib_obj, f)
            else:
                _download_to(json_path, calib_url)


    # --- Process with OpenCV using your JSON ---
        out_hash, output_file = _process_video(stacked_path, json_path, top_is_left=(top_is=="left"))
        video_storage[out_hash] = output_file




        return jsonify({"hash": out_hash}), 200

    except Exception as e:
        print("panorama-stitch (opencv) error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
