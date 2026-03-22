# Agentic RAG Copilot Architecture

## 1. System Overview

Agentic RAG Copilot is a prototype AI web application for grounded question
answering over a local PDF knowledge base. It demonstrates:

- context engineering
- retrieval augmented generation
- agent-oriented backend structure
- AI-assisted development with Codex CLI

The system has four primary runtime parts:

- a React + TypeScript frontend for chat and ingestion controls
- a FastAPI backend for orchestration and API delivery
- a Chroma vector store for chunk retrieval
- a local document corpus under `data/knowledge_base`

Prototype request flow:

1. The user submits a question from the frontend.
2. The backend embeds the query and retrieves top document chunks from Chroma.
3. The backend assembles runtime context from prompts, retrieved chunks, and
   bounded memory.
4. The backend calls an LLM service through a small abstraction layer.
5. The backend returns a grounded answer with citations.

Design priorities:

- thin API layer
- explicit service orchestration
- auditable context assembly
- local-first prototype operation
- easy extension into tools, agents, and evaluation

## 2. Backend Architecture

The backend is organized by responsibility so transport, orchestration,
retrieval, context construction, and future tool execution stay separate.

### Structure

- `backend/app/main.py`
  Creates the FastAPI app, registers routers, and wires startup configuration.
- `backend/app/api/`
  Defines HTTP endpoints, request validation, response models, and status code
  handling. This layer stays thin.
- `backend/app/services/`
  Contains application workflows such as chat handling, ingestion orchestration,
  health reporting, and future agent coordination.
- `backend/app/rag/`
  Contains PDF loading, chunking, embedding, Chroma persistence, and retrieval.
- `backend/app/context/`
  Builds prompt-ready runtime context from prompts, memory, and retrieved
  evidence.
- `backend/app/memory/`
  Stores conversation history abstractions and future long-term memory support.
- `backend/app/tools/`
  Holds future tool registry and tool adapter logic.

### Responsibilities

- API routes validate requests and delegate immediately to services.
- Services coordinate retrieval, prompt assembly, LLM calls, and response
  shaping.
- RAG modules are reusable from APIs, jobs, or future background workers.
- Context modules enforce prompt ordering and context caps.
- Memory modules are separate from document retrieval and should not share the
  same storage model.

## 3. Frontend Architecture

The frontend is a React + TypeScript application with page-level state
coordination and a small API client layer.

### Structure

- `frontend/src/pages/`
  Page-level flows such as chat and future admin or evaluation screens.
- `frontend/src/components/`
  Reusable UI elements such as chat transcript, input box, citation list,
  ingestion panel, and status banners.
- `frontend/src/api/`
  Typed client wrappers around backend endpoints.
- `frontend/src/App.tsx`
  Application shell and route composition.
- `frontend/src/main.tsx`
  App bootstrap and shared providers.

### State management decisions

For the prototype, local React state is sufficient. No global state library is
required yet.

- Chat state
  Managed in the chat page component: question draft, message history, current
  answer, and citations.
- Loading state
  Separate booleans for chat submission and ingestion actions.
- Error state
  Store the last API error per workflow and render it near the affected UI.
- Citation state
  Keep citation metadata on each assistant response so the UI can expand or
  collapse source details.
- Ingestion progress
  Poll `/ingest/status` while ingestion is running and show a simple status
  badge or progress section.

If state becomes shared across multiple pages, promote it to React context
rather than adding a heavier state library immediately.

## 4. RAG Pipeline

The ingestion flow follows `AGENTS.md`:

PDF documents -> chunk -> embed -> store in Chroma -> retrieve top-k

### Ingestion flow

1. Scan `data/knowledge_base` recursively for PDF files.
2. Compute a content hash for each source file.
3. Extract text page by page.
4. Normalize whitespace and chunk content with:
   - `chunk_size = 800`
   - `chunk_overlap = 100`
5. Generate embeddings using `sentence-transformers`.
6. Upsert chunks and metadata into Chroma.

### Retrieval flow

1. Accept a user query.
2. Embed the query with the same embedding model used for ingestion.
3. Query Chroma for the nearest chunks.
4. Return the top 5 chunks by default, including metadata required for
   citations and debugging.

### Retrieval semantics

- Default `top_k = 5`
- Similarity search uses Chroma's nearest-neighbor query behavior for one
  primary collection.
- Metadata filtering is supported at the service layer for future narrowing by:
  - source document
  - document hash
  - workspace or tenant identifier
- The prototype does not use reranking yet.

## 5. Context Engineering Components

Context assembly is explicit and ordered. The backend should build runtime
prompt context from the following sources:

- `prompts/system.md`
- `prompts/rules.md`
- `prompts/fewshots.md`
- bounded conversation memory
- retrieved document chunks
- the current user question

### Runtime context contract

Prompt assembly order:

1. system prompt
2. rules prompt
3. few-shot examples
4. recent conversation memory
5. retrieved document context
6. current user question

Prototype runtime rules:

- Memory limit
  Keep at most the last 4 user/assistant turns in prompt memory.
- Retrieved context cap
  Use at most 5 retrieved chunks and trim each chunk if prompt size requires
  it.
- Citation enforcement
  Every factual answer should cite the retrieved chunks used to support it.
- Weak evidence behavior
  If retrieval returns no useful support, answer with uncertainty and state
  that the knowledge base does not contain enough evidence.
- Conflicting evidence behavior
  If retrieved chunks conflict, the answer should surface the disagreement
  rather than merge it silently.

## 6. LLM Service Boundary

The prototype should isolate answer generation behind a service abstraction so
the rest of the backend does not depend on a specific model provider.

### Boundary design

- `services` orchestrate chat workflows
- a dedicated LLM client module or service method performs model invocation
- prompt assembly happens before the LLM boundary
- post-processing and citation shaping happen after the LLM response

### Prototype decisions

- Model abstraction
  Use one interface such as `generate_answer(context, question)` so providers
  can be swapped later.
- Provider assumption
  Start with one configured provider or one local deterministic fallback.
- Timeout
  Use a 20 second request timeout for LLM calls.
- Retry policy
  Retry once on transient network or provider errors, with no retry on prompt
  validation errors.
- Token budgeting
  Reserve a fixed prompt budget by limiting memory and retrieved chunks first.
  Keep response generation capped to a moderate answer size suitable for chat.
- Fallback behavior
  If the LLM call fails, return a grounded fallback response built from the top
  retrieved chunks and include citations. Do not fail the entire request unless
  retrieval also fails.

## 7. Document Lifecycle Controls

The prototype needs explicit document lifecycle rules so Chroma stays in sync
with the files under `data/knowledge_base`.

### Hashing

- Compute a file content hash for every PDF during ingestion.
- Store the hash in Chroma metadata for every derived chunk.

### Idempotent ingestion

- If a file path and content hash already exist in the vector store, skip
  re-embedding that document.
- Chunk identifiers should be deterministic per file hash, page, and chunk
  index.

### Update behavior

- If a file path exists but the file hash changes, delete all existing chunks
  for that source and re-ingest the document.

### Deletion behavior

- If a previously indexed source no longer exists on disk, mark its vectors as
  stale and remove them during cleanup.

### Stale-vector cleanup

- Each ingestion run should compare indexed sources against current filesystem
  state.
- Chunks whose source path is missing locally should be deleted from Chroma.
- Cleanup should run at the end of ingestion, not lazily during chat requests.

## 8. Vector Database Design

Chroma is the prototype vector database for semantic retrieval.

### Collection strategy

- Use one persistent local Chroma database under `data/chroma`.
- Use one primary collection named for the knowledge base.
- Keep collection metadata simple and local-first.

### Stored fields

- `id`
  Deterministic chunk identifier
- `document`
  Chunk text
- `metadata.source`
  Relative PDF path
- `metadata.page_number`
  Source page number
- `metadata.document_hash`
  Source file hash
- `metadata.chunk_index`
  Chunk order within the document
- `metadata.tenant_id`
  Prototype tenant identifier, defaulting to a single local tenant

### Multi-tenancy assumptions

The prototype is effectively single-tenant.

- `tenant_id` may still be stored in metadata for forward compatibility.
- All requests operate in one local workspace unless tenant scoping is added
  later.
- Real tenant isolation is deferred until there is a multi-user requirement.

## 9. API Contracts

The prototype backend should expose the following endpoints.

### `GET /health`

Purpose:
Return service liveness information.

Response:

- `status: str`
- `service: str`

Example response:

```json
{
  "status": "ok",
  "service": "agentic-rag-copilot-backend"
}
```

### `POST /chat`

Purpose:
Accept a user question, retrieve evidence, generate a grounded answer, and
return citations.

Request body:

- `question: str`
- optional future fields:
  - `conversation_id: str`
  - `debug: bool`

Response body:

- `answer: str`
- `citations: list`
- `context: str` for prototype debugging

Citation item:

- `chunk_id: str`
- `source: str`
- `page_number: int`

Error behavior:

- `400` for invalid request payloads
- `500` for unexpected backend failures
- `503` if retrieval or LLM dependencies are unavailable

### `POST /ingest`

Purpose:
Start or trigger ingestion of the local PDF knowledge base.

Prototype request body:

- empty body or optional `force: bool`

Response body:

- `status: str`
- `job_id: str`
- `message: str`

Prototype behavior:

- synchronous ingestion is acceptable initially
- if synchronous, `job_id` can still be returned for compatibility

### `GET /ingest/status`

Purpose:
Report ingestion status for the current or last run.

Response body:

- `status: str`
- `documents_processed: int`
- `chunks_created: int`
- `started_at: datetime | null`
- `finished_at: datetime | null`
- `message: str | null`

Status values:

- `idle`
- `running`
- `completed`
- `failed`

## 10. API Flow

Chat request flow:

1. frontend sends `POST /chat`
2. API route validates the payload
3. chat service retrieves top chunks from Chroma
4. context builder assembles prompt layers and retrieved evidence
5. LLM service generates the grounded answer
6. service applies fallback if the LLM fails
7. response formatter returns answer, citations, and optional debug context

Ingestion flow:

1. frontend sends `POST /ingest`
2. ingestion service scans local PDFs
3. documents are hashed, chunked, embedded, and upserted
4. stale vectors are deleted
5. status becomes available through `GET /ingest/status`

## 11. Folder Structure Explanation

### Backend

- `backend/app/main.py`
  FastAPI entry point
- `backend/app/api/`
  HTTP routes and transport validation
- `backend/app/services/`
  chat, ingestion, health, and future agent orchestration
- `backend/app/rag/`
  document ingestion and vector retrieval
- `backend/app/context/`
  prompt and runtime context assembly
- `backend/app/memory/`
  bounded conversation memory abstractions
- `backend/app/tools/`
  future tool registry and integrations

### Frontend

- `frontend/src/components/`
  reusable UI components
- `frontend/src/pages/`
  page-level state and workflow coordination
- `frontend/src/api/`
  typed backend client functions

### Shared assets

- `data/knowledge_base/`
  source PDFs
- `data/chroma/`
  persistent vector store
- `prompts/`
  prompt assets
- `docs/`
  project documentation

## 12. Non-Functional Requirements

Prototype-friendly targets:

- Latency
  Chat responses should usually complete within 10 seconds excluding cold model
  startup. Health checks should return quickly.
- Observability
  Log request start, request end, ingestion start, ingestion end, retrieval hit
  count, and major failure points.
- Logging
  Use structured logs where practical. Do not log full prompts or sensitive user
  content by default.
- Secrets and config
  Read model names, API keys, timeouts, top-k, and storage paths from
  environment variables or a settings module.
- Authentication assumptions
  The prototype is single-user and local-first, so authentication is not
  required initially. This must be stated explicitly in the code and docs.
- Testing strategy
  Add unit tests for chunking, hashing, retrieval result shaping, context
  assembly, and API schemas. Add integration tests for ingestion and chat with a
  small fixture corpus.

## 13. Future Extensibility

The structure should support gradual expansion without reshaping the whole
project.

### Tools

- add tool adapters in `backend/app/tools/`
- register tool metadata and execution handlers centrally
- inject tool outputs into the same context pipeline used by retrieval

### Agents

- add planner or controller logic above services when multi-step reasoning is
  needed
- support retrieve -> tool use -> validate -> answer workflows
- keep tool calls auditable and bounded by explicit rules

### Evaluation

- add offline retrieval evaluation datasets
- score citation correctness and groundedness
- track regression metrics as prompts and retrieval settings change

## Summary

This architecture is intentionally prototype-friendly but implementation-ready:

- FastAPI owns HTTP transport
- services own orchestration
- RAG modules own ingestion and retrieval
- context modules own prompt assembly
- the LLM boundary is isolated behind a service abstraction
- Chroma stores traceable chunk data
- the frontend manages chat and ingestion state locally

That gives the project a practical baseline for grounded chat today and a clear
path to tools, agents, evaluation, and multi-user concerns later.
