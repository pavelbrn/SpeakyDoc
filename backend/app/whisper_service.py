from faster_whisper import WhisperModel


model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


def transcribe_wav_file(file_path: str) -> str:
    """
    Transcribe a WAV file and print the transcript.
    """

    segments, info = model.transcribe(
        file_path,
        language="de"
    )

    print(f"[INFO] detected language: {info.language}")

    transcript_parts = []

    for segment in segments:
        transcript_parts.append(segment.text.strip())

    transcript = " ".join(transcript_parts)

    print("[TRANSCRIPT]")
    print(transcript)

    return transcript