---

## Running with Docker

This project is fully containerized and orchestrated via Docker Compose. The setup includes all required services (app, databases, vector store, object storage, LLM server, and more) for local or server deployment.

### Requirements
- **Docker** and **Docker Compose** installed
- Python 3.11 (used in the Docker image)

### Environment Variables
Before running, copy `.env.example` to `.env` and fill in all required secrets. Key variables (see `.env.example` for full list):
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` (Postgres)
- `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` (MinIO)
- `PINECONE_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `SENSO_API_KEY`, `GUMLOOP_API_KEY`, `VAPI_API_KEY`, `SHOPIFY_API_KEY`, etc.

### Build and Run

```bash
docker compose up --build
```

This will build the Python app (using Python 3.11-slim) and start all services defined in `docker-compose.yml`:
- **python-app**: Main app (FastAPI, port 8000)
- **postgres-db**: Postgres database (port 5432)
- **redis-cache**: Redis cache (port 6379)
- **minio**: S3-compatible object storage (ports 9000, 9001)
- **chroma-db**: Chroma vector DB (port 8001)
- **ollama**: LLM server (port 11434)
- **searxng**: Search engine (port 8080)
- **shopify-mcp**: Shopify MCP API (port 5005)

All services are connected via the `backend` Docker network. Data is persisted using Docker volumes for Postgres and MinIO.

#### Ports Summary
- App (FastAPI): **8000**
- Postgres: **5432**
- Redis: **6379**
- MinIO API: **9000**
- MinIO Console: **9001**
- Chroma DB: **8001**
- Ollama: **11434**
- SearxNG: **8080**
- Shopify MCP: **5005**

### Special Notes
- The Dockerfile uses a multi-stage build for efficient dependency management and security (non-root user).
- The app runs from `src/ru_twin/main.py` and expects all configuration and secrets via environment variables.
- If you add new services or dependencies, update `docker-compose.yml` and rebuild.
- The `.env` file is required for secrets and should never be committed.

---
