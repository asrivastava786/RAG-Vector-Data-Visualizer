# RAG Visual Optimizer

RAG Visual Optimizer is an enterprise SaaS platform for visual analysis, debugging, evaluation, and optimization of retrieval-augmented generation pipelines. It is intentionally not a generic chat-with-PDF app: the product centers on chunking strategy inspection, retrieval experiments, semantic visualizations, score breakdowns, and RBAC-safe retrieval.

## Current Status

Implemented in this scaffold:

- Monorepo with `backend` FastAPI service and `frontend` Next.js app.
- Docker Compose for PostgreSQL with pgvector, Redis, MinIO, backend, worker, and frontend.
- FastAPI settings, CORS, health check, OpenAPI docs, JWT auth, Argon2 password hashing, audit log writing.
- SQLAlchemy 2 models for users, workspaces, members, projects, documents, chunking strategies, chunks, experiments, query runs, audit logs, and API keys.
- Workspace membership and role enforcement for workspace/project APIs.
- Document upload, S3-compatible object storage integration, extraction service, document processing endpoint, access-scoped document listing/detail APIs.
- Chunking strategy APIs for fixed, recursive, heading, semantic-placeholder, and table-aware chunkers.
- Deterministic local embedding provider abstraction, sparse term extraction, pgvector-backed chunk storage, and strategy indexing.
- RBAC-scoped chunk listing so non-admin users only receive chunks matching their workspace role or explicit user grant.
- RBAC-safe query analysis APIs with dense similarity, sparse keyword scoring, hybrid fusion, no-op reranker abstraction, heuristic metrics, and query-run audit persistence.
- Rule-based query optimization endpoint with deterministic synonym and use-case expansion.
- Query-run visualization APIs for semantic scatter, query-to-chunk graph, and retrieval funnel data.
- Experiment APIs for creating and running strategy comparisons across query sets.
- Leaderboard aggregation, best-strategy recommendation, experiment reports, and project recommendation config output.
- RBAC simulator, access matrix APIs, admin user/audit/settings APIs, and multi-format config exports.
- Next.js App Router shell with auth pages, workspace dashboard, project dashboard, document upload, document preview, strategy builder, chunk inspector, query analysis, strategy comparison, RBAC safety, reports, admin settings, Plotly scatter, Cytoscape graph, status badges, and enterprise navigation.
- Seed and test scaffolding.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Set a strong `JWT_SECRET_KEY`.
3. Start the stack:

```bash
make docker-up
```

4. Apply migrations:

```bash
make migrate
```

5. Seed demo data:

```bash
make seed
```

The frontend runs at `http://localhost:3000`. The backend runs at `http://localhost:8000`, with OpenAPI docs at `http://localhost:8000/api/docs`.

## Security Notes

- Backend authorization is enforced through workspace membership checks. Frontend navigation is convenience only.
- Project access is workspace-scoped, and project mutation requires elevated workspace roles.
- Strategy indexing copies document access rules onto every chunk. Chunk inspection and future retrieval APIs must filter on `workspace_id`, `project_id`, `strategy_id`, `allowed_roles`, and `allowed_users` before returning, logging, visualizing, or sending context to an answer generator.
- Query analysis applies RBAC filters before scoring and persists only authorized chunks in `query_runs`.
- Visualization endpoints read from authorized query-run payloads and do not refetch or expose unauthorized chunks.
- Experiment runs call the same RBAC-safe query-analysis service and aggregate only persisted authorized query-run metrics.
- RBAC simulation shows blocked chunk metadata without returning blocked chunk text previews.
- Secrets are read from environment variables. No API keys should be committed.
- Refresh-token persistence and rotation are shaped in the API contract and will be hardened in a later phase.

## Roadmap

- Phase 8: broader tests, CI hardening, operational runbooks.

## Known Limitations

- Phase 3 uses deterministic local embeddings for offline-safe development. Hosted OpenAI-compatible, BGE, and sentence-transformers providers are interface-ready but not wired to external services.
- Dense scoring currently runs in the service layer over RBAC-authorized chunks; production pgvector ANN indexes and tuning are still planned.
- Scatter projection is an MVP deterministic 2D projection from score features; PCA/UMAP can replace this service contract later.
- Hosted/local rerankers, richer report exports, and CI hardening remain upcoming phases.
- Email delivery, OAuth, billing, API key management, and refresh-token rotation are placeholders.
- Frontend data is partly demo-oriented until seed data and authenticated API bootstrapping are wired through the full app shell.
