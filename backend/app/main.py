from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import sys

# Ensure project root is on sys.path when this file is run directly in VS Code.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.whisper_service import transcribe_wav_file

import os

app = Flask(__name__)
CORS(app)

RECORDINGS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "recordings")
)
os.makedirs(RECORDINGS_DIR, exist_ok=True)


@app.route("/api/health")
def health():
    return {"status": "ok"}


@app.route("/api/process", methods=["POST"])
def process():

    if "audio" not in request.files:
        return {"error": "no audio uploaded"}, 400

    audio_file = request.files["audio"]
    safe_name = secure_filename(audio_file.filename or "audio.wav")

    if "." not in safe_name:
        safe_name = f"{safe_name}.wav"

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{safe_name}"
    saved_path = os.path.join(RECORDINGS_DIR, filename)
    audio_file.save(saved_path)

    transcript = transcribe_wav_file(saved_path)

    return jsonify({
        "transcript": transcript,
        "patient_name": "PATIENT_NAME",
        "chief_complaint": "Brustschmerzen seit 2 Tagen",
        "assessment": "Verdacht auf Angina pectoris",
        "saved_file": os.path.relpath(saved_path, start=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
