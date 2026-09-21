# Services

Extraction points for work that will outgrow the API process. Each directory
becomes an independently deployable worker without changing its callers,
because the API talks to them through interfaces rather than imports.

| Service | Owns | Phase |
| --- | --- | --- |
| `document-processing/` | Validation, text and OCR extraction, cleaning, chunking, metadata | 3 |
| `rag/` | Embedding, vector storage, retrieval, reranking, citation assembly | 3 |
| `agent-orchestrator/` | Intent detection, agent routing, tool calling, verification | 2 and 4 |

Until a service is implemented, its responsibilities stay in `apps/api` behind
the same interface, so moving it out later is a deployment change rather than a
rewrite.
