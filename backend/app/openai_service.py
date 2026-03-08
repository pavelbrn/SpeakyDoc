import json
import os

from openai import OpenAI


def structure_medical_text(transcript: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

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

    return json.loads(content)