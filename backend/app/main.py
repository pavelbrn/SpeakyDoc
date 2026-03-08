from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import sys
import os

# Ensure project root is on sys.path when this file is run directly in VS Code.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.whisper_service import transcribe_wav_file
from app.openai_service import structure_medical_text, check_if_medical_text

app = Flask(__name__)
CORS(app)

RECORDINGS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "recordings")
)
os.makedirs(RECORDINGS_DIR, exist_ok=True)


@app.route("/api/health")
def health():
    """Return a basic health-check status for the API.

    Returns:
        dict: A JSON-serializable status payload.
    """
    return {"status": "ok"}


@app.route("/api/process", methods=["POST"])
def process():
    """Process an uploaded audio file and return extracted medical information.

    The endpoint validates the multipart payload, stores the uploaded file,
    transcribes it with Whisper, checks whether the transcript is medical, and
    optionally returns structured medical fields.

    Returns:
        flask.Response | tuple[flask.Response, int]:
            JSON response containing transcription and extraction results.
            Returns HTTP 400 for invalid input and HTTP 500 on unexpected errors.
    """
    try:
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
        medical_check = check_if_medical_text(transcript)
        is_medical_text = medical_check.get("is_medical_text", False)
        medical_message = medical_check.get("message", "")

        if not is_medical_text:
            return jsonify({
                "transcript": transcript,
                "is_medical_text": False,
                "message": medical_message or "This is not a medical text.",
                "saved_file": os.path.relpath(
                    saved_path,
                    start=os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..")
                    )
                )
            })

        structured_data = structure_medical_text(transcript)

        return jsonify({
            "transcript": transcript,
            "is_medical_text": True,
            "message": medical_message or "Medical text detected.",
            "structured_data": structured_data,
            "saved_file": os.path.relpath(
                saved_path,
                start=os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..")
                )
            )
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
