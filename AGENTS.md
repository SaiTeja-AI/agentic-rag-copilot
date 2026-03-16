# AGENTS.md

## Project Goal
Build an AI-enabled web application called **Agentic RAG Copilot**.

The system demonstrates:

- Context Engineering
- Retrieval Augmented Generation
- Agentic workflows
- AI-assisted development using Codex CLI

---

# Architecture

Backend:
FastAPI

Frontend:
React + TypeScript

Vector Database:
Chroma

Embeddings:
sentence-transformers

---

# Project Structure

Codex should generate the following structure:

backend/
  app/
    main.py
    api/
    services/
    rag/
    context/
    memory/
    tools/

frontend/
  src/
    components/
    pages/
    api/

data/
  knowledge_base/

docs/

---

# RAG Pipeline

Follow this ingestion flow:

PDF documents
→ chunk
→ embed
→ store in Chroma
→ retrieve top-k

Chunk configuration:

chunk_size = 800
chunk_overlap = 100

---

# Prompt Organization

Create prompt files:

prompts/system.md
prompts/rules.md
prompts/fewshots.md

---

# Coding Rules

Use Python type hints.

Separate API routes from business logic.

API layer must remain thin.

Business logic belongs in services.

---

# Development Workflow

Codex must follow this process:

1. Read AGENTS.md
2. Propose architecture
3. Generate project structure
4. Implement milestone by milestone
5. Ensure code compiles