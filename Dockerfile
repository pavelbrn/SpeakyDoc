FROM node:22-bookworm

WORKDIR /app

# Install Python + curl
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip curl && rm -rf /var/lib/apt/lists/*

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

EXPOSE 4173
EXPOSE 8000

CMD ["sh", "-c", "cd /app/backend && uv run python app/main.py & cd /app/frontend/speaky-doc-app && npm run preview -- --host 0.0.0.0 --port 4173"]