# SpeakyDoc

SpeakyDoc is a small full-stack demo that uploads an audio file, sends it to a Flask backend, and returns structured JSON in a SvelteKit web app.

## Stack

- SvelteKit frontend
- Flask backend
- Python dependency management with `uv`
- Single Docker container

## Run with Docker

From the project root:

Build the container:
```bash
docker build --platform linux/amd64 -t speakydoc .
```

Set the Whisper model name in two places:
- Build time (model preload into the image): `--build-arg WHISPER_PRELOAD_MODEL=...`
- Run time (model used by backend): `-e WHISPER_MODEL=...`

Preload a specific Whisper model into the image at build time:
```bash
docker build --build-arg WHISPER_PRELOAD_MODEL=medium -t speakydoc .
```

Larger models (`medium`, `large-v3`) will make the container build take much longer and produce a bigger image and will take longer to process a .wav file during run time, but the quality of the transcription and LLM summary will be better.

Run the project with your OpenAI API key and Whisper model:
```bash
docker run -p 4173:4173 -p 8000:8000 \
-e OPENAI_API_KEY="sk-xxxxx" \
speakydoc
```

Example Whisper models: `base`, `small`, `medium`, `large-v3`.

Full example (matching build + run):
```bash
docker build --build-arg WHISPER_PRELOAD_MODEL=small -t speakydoc .
docker run -p 4173:4173 -p 8000:8000 \
  -e OPENAI_API_KEY="sk-xxxxx" \
  -e WHISPER_MODEL="small" \
  speakydoc
```

Open:

- Frontend: http://localhost:4173
- Backend: http://localhost:8000

## Local Development

### Backend

```bash
cd backend
uv sync
uv run python app/main.py
```

Runs on http://localhost:8000

### Frontend

```bash
cd frontend/speaky-doc-app
npm install
npm run dev
```

Runs on http://localhost:5173

## API

### Health check

GET /api/health

Example response:

```json
{
  "status": "ok"
}
```

### Process endpoint

POST /api/process

Current example response:
TODO: finish this, this is a placeholder for now
s
```json
{
  "patient_name": "PATIENT_NAME",
  "chief_complaint": "Brustschmerzen seit 2 Tagen",
  "assessment": "Verdacht auf Angina pectoris"
}
```

## Notes

This project is designed to run locally via Docker.
