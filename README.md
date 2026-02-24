# LifeOS AI Personal Planner

LifeOS is a premium, AI-powered personal planner designed to optimize your daily routine. It is currently configured to use your **Native Ollama** for 100% private, local AI.

## Features
- **Local AI Brain**: Uses your native Ollama to run `mistral:7b`.
- **RAG Memory**: Uses `nomic-embed-text` for a searchable "Rules of Life" knowledge base.
- **Smart Scheduling**: Integration with Google Calendar for seamless sync.

## Quick Start (Linux)

> **Deep Dive**: For a detailed explanation of how the Chatbot and Files work, see [ARCHITECTURE.md](ARCHITECTURE.md).

### 1. Start the Stack
```bash
cd infrastructure
docker compose up --build
```
*(Note: Use `docker compose` with a space on your system).*

### 2. Initialize the Memory (RAG)
Since you already have Ollama and models, just build the search index:
```bash
docker exec -it infrastructure-backend-1 python3 -m rag.manager
```

## Configuration

Your stack is optimized to talk to the Ollama instance running on your host machine (`host.docker.internal`). 

- **Rules of Life**: Add your patterns to [backend/rag/data.json](file:///home/vinti/LifeOS/backend/rag/data.json).
- **Env Settings**: Managed in [backend/.env](file:///home/vinti/LifeOS/backend/.env).

## Tech Stack
- **Frontend**: Next.js (Port 3000)
- **Backend**: FastAPI (Port 8000)
- **Database**: PostgreSQL (Port 5432)
- **Memory**: FAISS + Nomic Embeddings
# LifeOs
