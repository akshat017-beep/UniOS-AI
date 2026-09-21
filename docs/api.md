# API reference

Base URL: `http://localhost:8000` · All routes are versioned under `/api/v1`.
Interactive documentation: `/docs` (Swagger) and `/redoc`.

## Conventions

- Authentication: `Authorization: Bearer <access_token>`.
- Errors: `{ "detail": "human readable message" }` with a meaningful status code.
- Validation errors return 422 with the offending fields.

## Implemented (Phase 1)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | — | Service and database health |
| `POST` | `/api/v1/auth/register` | — | Create an account, returns a token pair |
| `POST` | `/api/v1/auth/login` | — | Sign in, returns a token pair |
| `POST` | `/api/v1/auth/refresh` | — | Exchange a refresh token for a new pair |
| `POST` | `/api/v1/auth/logout` | Bearer | Audit the sign-out; client discards tokens |
| `GET` | `/api/v1/auth/me` | Bearer | Current user and academic profile |
| `GET` | `/api/v1/users/me` | Bearer | Same as above, under the users module |
| `PATCH` | `/api/v1/users/me/profile` | Bearer | Update academic context |
| `GET` | `/api/v1/users` | Admin | List users (403 for other roles) |

### Example

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@university.edu","password":"StrongPass123","full_name":"A Student"}'
```

## Implemented (Phase 2 — AI core)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/agents` | — | The nine agents and what each one does |
| `POST` | `/api/v1/agents/route` | Bearer | Preview which agent would answer, with matched signals |
| `GET` | `/api/v1/agents/status` | Bearer | Whether an AI provider is configured |
| `GET` | `/api/v1/chat/conversations` | Bearer | The caller's conversations, newest first |
| `GET` | `/api/v1/chat/conversations/{id}` | Bearer | One conversation with its messages |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Bearer | Delete a conversation and its messages |
| `POST` | `/api/v1/chat/messages` | Bearer | Send a message, get the full reply |
| `POST` | `/api/v1/chat/stream` | Bearer | Same, streamed as server-sent events |

Conversations are scoped to their owner: another user's id returns 404, never data.
Without provider configuration the chat endpoints return **503** with the exact
environment variables to set — they never return a fabricated answer.

### Streaming format

```text
event: meta   data: {"conversation_id": "...", "routing": {"agent": "coding", ...}}
event: token  data: {"text": "..."}
event: done   data: {"conversation_id": "..."}
event: error  data: {"detail": "..."}
```

## Planned modules

`/api/v1/chat`, `/agents`, `/documents`, `/rag`, `/research`, `/coding`,
`/career`, `/campus`, `/academics`, `/events`, `/notifications`, `/admin`.
Each arrives with the phase that implements it, together with its tests.
