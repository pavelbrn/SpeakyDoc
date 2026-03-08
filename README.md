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
docker build -t speakydoc .
```

Run the project with your OpenAI API key and Whisper model:
```bash
docker run -p 4173:4173 -p 8000:8000 \
-e OPENAI_API_KEY="sk-xxxxx" \
-e WHISPER_MODEL="base" \
speakydoc
```

Example Whisper models: `base`, `small`, `medium`, `large-v3`.

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
