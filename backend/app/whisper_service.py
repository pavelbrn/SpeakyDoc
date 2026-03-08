from faster_whisper import WhisperModel
import os


# Quality-first defaults (override via env vars).
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE
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
        language="de",
        beam_size=5,
        best_of=5,
        temperature=0.0,
        vad_filter=True
    )

    print(
        f"[INFO] model={WHISPER_MODEL}, detected_language={info.language}, "
        f"device={WHISPER_DEVICE}, compute_type={WHISPER_COMPUTE_TYPE}"
    )

    transcript_parts = []

    for segment in segments:
        transcript_parts.append(segment.text.strip())

    transcript = " ".join(transcript_parts)

    print("[TRANSCRIPT]")
    print(transcript)

    return transcript
