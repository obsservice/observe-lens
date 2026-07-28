# ObserveLens Knowledge Base

`observelens-knowledge-base` manages knowledge bases, documents, document versions,
indexing tasks, hybrid retrieval, citations, and retrieval feedback for ObserveLens.

## Run

```bash
uv sync
uv run uvicorn observelens_knowledge_base.main:app --host 0.0.0.0 --port 3085
```

The API is mounted at `/api/v1`.
