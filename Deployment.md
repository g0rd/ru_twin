# RuTwin Crew Deployment Guide

This document provides comprehensive instructions for deploying the RuTwin Crew system, a multi-agent AI system designed for automated task management using the CrewAI framework.

## Overview

RuTwin Crew is an internal application built with:
- CrewAI orchestration framework
- MCP (Master Control Program) and A2A (Agent-to-Agent) architecture
- Docker-based microservices
- Arize Phoenix for monitoring and observability

## Prerequisites

- Docker and Docker Compose installed (v20.10+ recommended)
- Git
- 8GB+ RAM available for running the services
- Access to required API keys for external services

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/g0rd/ru_twin.git
cd ru_twin
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=your_llm_base_url
LLM_MODEL=your_preferred_model

# Database Configuration
DB_USER=database_username
DB_PASSWORD=database_password
DB_HOST=database_host
DB_PORT=database_port
DB_NAME=database_name

# Vector Database Configuration
VECTOR_DB_URL=vector_db_url
VECTOR_DB_API_KEY=vector_db_api_key

# External Service API Keys
SENSO_API_KEY=your_senso_api_key
GUMLOOP_API_KEY=your_gumloop_api_key
SLACK_BOT_TOKEN=your_slack_bot_token
GMAIL_API_KEY=your_gmail_api_key
GOOGLE_SHEETS_API_KEY=your_google_sheets_api_key

# Arize Phoenix Configuration
PHOENIX_PORT=6006
PHOENIX_HOST=0.0.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://phoenix:4317
```

> ⚠️ **Security Note**: The `.env` file contains sensitive information and should never be committed to version control.

## Docker Deployment

### 1. Build and Start the Services

```bash
docker-compose build
docker-compose up -d
```

This will start all the required microservices:
- LLM service
- Database
- Vector database
- Object storage
- Search engine
- Arize Phoenix for monitoring

### 2. Verify Service Startup

```bash
docker-compose ps
```

Ensure all services are in the "Up" state.

## Arize Phoenix Integration

RuTwin Crew uses [Arize Phoenix](https://docs.arize.com/phoenix) for monitoring and observability of the AI agents.

### 1. Access the Phoenix Dashboard

After deployment, access the Phoenix dashboard at:
```
http://localhost:6006
```

### 2. Instrumenting RuTwin with Phoenix

The system is pre-configured to send traces to Phoenix using OpenTelemetry. Key monitoring aspects include:

- **LLM Traces**: All LLM interactions are automatically traced
- **Agent Activities**: Agent actions and decisions are logged
- **Task Execution**: Task performance and completion status

### 3. Using the Phoenix Dashboard

The Phoenix dashboard provides several key features for monitoring RuTwin:

- **Prompt Playground**: Test and refine prompts used by the agents
- **Tracing**: View detailed traces of agent activities and LLM calls
- **Evaluation**: Assess the performance of your agents
- **Datasets & Experiments**: Store relevant traces for analysis

### 4. Setting Up Alerts (Optional)

For critical issues, configure alerts in the Phoenix dashboard:
1. Navigate to Settings → Alerts
2. Create new alert rules based on error rates or latency thresholds
3. Configure notification channels (email is recommended for a 2-user system)

## Post-Deployment Verification

### 1. Test Agent Functionality

Run a basic test to ensure the agents are functioning:

```bash
docker-compose exec app python -m src.ru_twin.main --test
```

### 2. Verify External Service Connections

Check the logs to ensure connections to external services are working:

```bash
docker-compose logs app
```

Look for successful connection messages to Senso.ai, Gumloop, Slack, etc.

## Maintenance

### Updating the System

To update the system with new code:

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup Procedures

For data persistence, the following volumes should be backed up regularly:
- Database data
- Vector database embeddings
- Object storage files

Example backup command:
```bash
docker-compose exec database pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Common Issues

1. **Service Connection Errors**:
   - Check the `.env` file for correct API keys and endpoints
   - Verify network connectivity to external services

2. **Agent Failures**:
   - Check Phoenix traces for error details
   - Verify the YAML configuration files in `src/ru_twin/config/`

3. **Out of Memory Errors**:
   - Increase Docker memory allocation
   - Consider optimizing the number of concurrent agents

### Logs

Access service logs for debugging:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs phoenix
```

## Support

For internal support, contact the development team at:
- Email: dev-team@internal.example.com
- Slack: #rutwin-support channel
