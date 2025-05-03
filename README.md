
- **Agents**: YAML-configured, each with specific LLM, tools, and goals.
- **MCP**: Handles all tool invocations, rate limiting, logging, and access.
- **External MCPs**: Gumloop (Google, Slack, Web), Shopify, Senso, Goose.
- **Storage**: MinIO (S3), Chroma (vector), Postgres (relational), Redis (cache).

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ru_twin.git
cd ru_twin
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in all required API keys and secrets (see below).

### 3. Build and Run with Docker Compose

```bash
docker compose up --build
```

This will start:
- Ollama (LLM server)
- Postgres (DB)
- Chroma (vector DB)
- MinIO (object storage)
- Redis (cache)
- SearxNG (optional search)
- CrewAI app
- Shopify MCP server

### 4. Add API Keys

Edit your `.env` file with the following (see `.env.example` for all required keys):

- `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- `PINECONE_API_KEY`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `SENSO_API_KEY`
- `GUMLOOP_API_KEY`
- `VAPI_API_KEY`
- `SHOPIFY_API_KEY`, etc.

### 5. Access the App

- Main app: [http://localhost:3000](http://localhost:3000)
- MinIO console: [http://localhost:9001](http://localhost:9001)
- SearxNG: [http://localhost:8080](http://localhost:8080)
- Shopify MCP: [http://localhost:5005](http://localhost:5005)

---

## Agents & Tasks

- **Digital Twin**: Coordinator, final decision-maker (Claude-3 Opus).
- **CPG Researcher**: Market/competitor research (Llama-3).
- **CPG Salesperson**: Sales strategy (Claude-3 Sonnet).
- **CFO**: Financial planning (Claude-3 Opus).
- **Legal Advisor**: Compliance/risk (Claude-3 Opus).
- **PR Strategist**: PR/content/media (Claude-3 Opus).
- **Goose Coding Agent**: Automated coding/dev (Goose LLM).
- **Voice Assistant**: Voice/phone escalation (Vapi, Claude-3 Sonnet).
- **Executive Assistant, Accountability Buddy, Writer**: Support roles.

Tasks and workflows are defined in `src/ru_twin/config/tasks.yaml`.

---

## Integrations

- **Goose**: Autonomous coding, project scaffolding, code review.
- **Shopify MCP**: Dev docs search, admin GraphQL, schema introspection.
- **Gumloop**: Google Sheets, Gmail, Slack, web scraping.
- **Senso**: Persistent memory and knowledge base.
- **Vapi**: Voice/phone call management.

---

## Storage & Memory

- **MinIO**: S3-compatible object storage (local, with cloud backup).
- **Chroma**: Vector DB for semantic memory.
- **Postgres**: Structured data.
- **Redis**: Caching layer.

---

## Deployment

- Designed for a mid-range VPS ($20-50/mo).
- All services orchestrated via Docker Compose.
- Easily extensible for new agents, tools, or integrations.

---

## Security

- All secrets in `.env` (never commit this file).
- Access control and rate limiting via MCP.
- Encrypted storage and regular backups.

---

## Contributing

1. Fork and clone the repo.
2. Add new agents/tools in `src/ru_twin/config/agents.yaml` and `src/ru_twin/tools/`.
3. Add new MCP clients in `src/ru_twin/mcp_clients/`.
4. Update `docker-compose.yml` if new services are needed.
5. Submit a PR!

---

## License

MIT

---

## Acknowledgements

- [CrewAI](https://github.com/joaomdmoura/crewai)
- [Goose](https://block.github.io/goose/)
- [Shopify Dev MCP](https://github.com/Shopify/dev-mcp)
- [Gumloop](https://docs.gumloop.com/)
- [Senso](https://docs.senso.ai/)
- [Vapi](https://docs.vapi.ai/)
