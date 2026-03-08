import json
import os

from openai import OpenAI


def _get_openai_client() -> OpenAI:
    """Create an OpenAI client from environment configuration.

    Returns:
        OpenAI: Configured OpenAI API client instance.

    Raises:
        RuntimeError: If `OPENAI_API_KEY` is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def _parse_json_output(content: str) -> dict:
    """Parse model output into a JSON dictionary.

    This helper strips optional fenced code block markers before parsing.

    Args:
        content: Raw text returned by the LLM.

    Returns:
        dict: Parsed JSON object.

    Raises:
        json.JSONDecodeError: If the cleaned content is not valid JSON.
    """
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def check_if_medical_text(transcript: str) -> dict:
    """Classify whether a transcript contains medical documentation text.

    Args:
        transcript: Raw transcript text to classify.

    Returns:
        dict: Classification payload with keys `is_medical_text` and `message`.
    """
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
    """Extract structured medical fields from a German transcript.

    Args:
        transcript: Raw German transcript from speech-to-text.

    Returns:
        dict: Normalized JSON object with keys:
            `aktuelle_anamnese`, `vorerkrankungen`, `voroperationen`,
            and `medikation`.
    """
    client = _get_openai_client()

    prompt = f"""
You are a medical documentation assistant.

Extract structured data from the following German medical dictation.

Return valid JSON with exactly these keys:
- aktuelle_anamnese
- vorerkrankungen
- voroperationen
- medikation

Rules:
- Return only JSON
- Do not invent details
- Keep the content concise
- Preserve the original language of the transcript
- `aktuelle_anamnese` must be a string
- `vorerkrankungen` must be a JSON array of strings
- `voroperationen` must be a JSON array of strings
- `medikation` must be a JSON array of strings (current medications only)
- If no information exists for a list field, return an empty array []
- If no information exists for `aktuelle_anamnese`, return an empty string
- If information is uncertain, ambiguous, or not explicitly stated, omit it

Field extraction instructions:
- `aktuelle_anamnese`:
  Briefly summarize the current presentation/reason for encounter and relevant current findings.
  Include current symptoms, event (e.g. fall), and immediate clinical status if mentioned.
  Do not include chronic history lists or medication lists here.
- `vorerkrankungen`:
  List only pre-existing diseases/diagnoses or chronic conditions from past history.
  Do not include surgeries, current acute event, or medications.
- `voroperationen`:
  List only prior operations/procedures from history.
  Include approximate year/body site if present in transcript text.
- `medikation`:
  List only medications the patient currently takes.
  Prefer one item per medication, optionally with dose/frequency only if explicitly stated.
  Exclude medications that are merely planned, stopped, denied, or uncertain.

Output format example (must match this shape exactly):
{{
  "aktuelle_anamnese": "string",
  "vorerkrankungen": ["string"],
  "voroperationen": ["string"],
  "medikation": ["string"]
}}

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

    parsed = _parse_json_output(content)

    def to_list(value) -> list[str]:
        """Normalize arbitrary values into a clean list of strings.

        Args:
            value: Candidate list-like value returned by the LLM.

        Returns:
            list[str]: Trimmed non-empty string items, or an empty list.
        """
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    return {
        "aktuelle_anamnese": str(parsed.get("aktuelle_anamnese", "")).strip(),
        "vorerkrankungen": to_list(parsed.get("vorerkrankungen", [])),
        "voroperationen": to_list(parsed.get("voroperationen", [])),
        "medikation": to_list(parsed.get("medikation", [])),
    }
