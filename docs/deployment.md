# Deployment

## Environments

| Environment | Purpose | Notes |
| --- | --- | --- |
| development | Local work | Docker Compose, hot reload, seeded test data |
| staging | Pre-release verification | Production build, separate database |
| production | Live university deployment | Managed PostgreSQL, TLS termination, backups |

## Local with Docker

```bash
cp .env.example .env
docker compose up --build
```

The API container runs `alembic upgrade head` before starting, so the schema is
always current. Data persists in the `postgres_data` volume.

## Production checklist

- Set a long random `JWT_SECRET`; rotate it on any suspected exposure.
- Set `ENVIRONMENT=production` and restrict `CORS_ORIGINS` to real origins.
- Use managed PostgreSQL with automated backups and point-in-time recovery.
- Terminate TLS at the load balancer or reverse proxy; never serve tokens over
  plain HTTP.
- Run migrations as a separate step in the release pipeline before rolling out
  new containers.
- Ship structured logs to a central collector and alert on 5xx rate, auth
  failure spikes, AI latency and token spend.
- Keep provider API keys in the platform secret store; they are only ever read
  by the API process.

## CI/CD

`.github/workflows/ci.yml` runs linting, type-checking, tests and builds for
both applications plus a dependency audit on every pull request. Deployment
pipelines publish the two container images and run migrations before the new
revision receives traffic.
