from faster_whisper import WhisperModel
import os


# Model can be overridden at container runtime, defaults to the previous stable setup.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
LOADED_WHISPER_MODEL = WHISPER_MODEL

try:
    model = WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8"
    )
except Exception as exc:
    print(
        f"[WARN] Failed to load WHISPER_MODEL='{WHISPER_MODEL}'. "
        f"Falling back to 'base'. Error: {exc}"
    )
    LOADED_WHISPER_MODEL = "base"
    model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )


def transcribe_wav_file(file_path: str) -> str:
    """Transcribe a WAV file with Faster-Whisper.

    Args:
        file_path: Absolute or relative path to the WAV file.

    Returns:
        str: Full transcript text assembled from recognized segments.
    """

    segments, info = model.transcribe(
        file_path,
        language="de"
    )

    print(f"[INFO] model={LOADED_WHISPER_MODEL}, detected_language={info.language}")

    transcript_parts = []

    for segment in segments:
        transcript_parts.append(segment.text.strip())

    transcript = " ".join(transcript_parts)

    print("[TRANSCRIPT]")
    print(transcript)

    return transcript
