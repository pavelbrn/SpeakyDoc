import json
import os

from openai import OpenAI


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _parse_json_output(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def check_if_medical_text(transcript: str) -> dict:
    client = _get_openai_client()

    prompt = f"""
You are a strict medical text classifier.

Decide if the following transcript is medical documentation content
(e.g. patient history, physician notes, clinical findings, diagnosis, treatment plan).

Return valid JSON only with exactly these keys:
- is_medical_text (boolean)
- message (string)

Rules:
- If the text is not medical, set is_medical_text to false and set message to:
  "This is not a medical text."
- If the text is medical, set is_medical_text to true and message to:
  "Medical text detected."

Transcript:
{transcript}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    content = response.output_text
    print("[OPENAI MEDICAL CHECK RAW OUTPUT]")
    print(content)

    parsed = _parse_json_output(content)
    return {
        "is_medical_text": bool(parsed.get("is_medical_text", False)),
        "message": str(parsed.get("message", "This is not a medical text."))
    }


def structure_medical_text(transcript: str) -> dict:
    client = _get_openai_client()

    prompt = f"""
You are a medical documentation assistant.

Extract a structured clinical summary from the following German medical dictation.

Return valid JSON with exactly these keys:
- patient_complaint
- findings
- diagnosis
- next_steps

Rules:
- Return only JSON
- Do not invent details
- If something is missing, return an empty string
- Keep the content concise
- Preserve the original language of the transcript

Transcript:
{transcript}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    content = response.output_text
    print("[OPENAI RAW OUTPUT]")
    print(content)

    return _parse_json_output(content)
