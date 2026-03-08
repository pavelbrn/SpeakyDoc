FROM node:22-bookworm

WORKDIR /app
ARG WHISPER_PRELOAD_MODEL=medium

# Install system dependencies once (including ffmpeg for audio decoding).
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip curl ffmpeg && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project
COPY . .

# Install frontend deps and build frontend
WORKDIR /app/frontend/speaky-doc-app
RUN npm install
RUN npm run build

# Install backend deps
WORKDIR /app/backend
RUN uv sync
ENV WHISPER_MODEL=${WHISPER_PRELOAD_MODEL}
RUN uv run python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_PRELOAD_MODEL}', device='cpu', compute_type='int8'); print('Preloaded model:', '${WHISPER_PRELOAD_MODEL}')"

EXPOSE 4173
EXPOSE 8000

CMD ["sh", "-c", "cd /app/backend && uv run python app/main.py & cd /app/frontend/speaky-doc-app && npm run preview -- --host 0.0.0.0 --port 4173"]
