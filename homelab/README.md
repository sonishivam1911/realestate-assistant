# Deploy CMA Assistant on homelab-contabo

**Yes — this fits the existing Contabo stack.** Same Postgres (`supabase_db`), Traefik, and deploy pattern as `minaki_api`.

## Architecture

```
Browser → https://cma.minaki.me (Traefik → cma_frontend Next.js)
              ↓ proxy /api/*
         cma_api FastAPI :8080
              ↓
         supabase_db (realestate schema)
```

## Local dev with Contabo Postgres

1. In `.env`:
   ```env
   CONTABO_TUNNEL=true
   CONTABO_LOCAL_PG_PORT=5433
   POSTGRES_URI_CONTABO=postgresql://postgres:YOUR_HOMELAB_POSTGRES_PASSWORD@127.0.0.1:5433/postgres
   SUPABASE_STUDIO_URL=https://supabase.minaki.me
   ```
   `POSTGRES_PASSWORD` is in `homelab-contabo/.env` on the VPS.

2. `homelab-contabo/homelab.env` is auto-read for `SERVER_IP` / `SSH_KEY`.

3. Run `./start_dev.sh` — opens SSH tunnel + starts API + UI.

4. **Postgres UI:** open https://supabase.minaki.me (Studio). Login = `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` from homelab `.env`. No tunnel needed for the browser UI.

## Production deploy (homelab-contabo)

### One-time setup

1. Copy Dockerfiles to homelab image path:
   ```bash
   mkdir -p homelab-contabo/images/cma-assistant
   cp homelab/Dockerfile.api homelab-contabo/images/cma-assistant/
   cp homelab/Dockerfile.frontend homelab-contabo/images/cma-assistant/
   ```
   Adjust Dockerfiles to `COPY ${CMA_SOURCE}/...` if building from homelab root (see `minaki_api` pattern).

2. Merge `cma-compose-snippet.yml` into `homelab-contabo/docker-compose.yml`.

3. Add DNS A records: `cma.minaki.me`, `cma-api.minaki.me` → VPS IP.

4. Rsync app + `.env` to VPS `sources/cma-assistant/` (same as `deploy-contabo.sh` does for Minaki API).

5. `docker compose build cma_api cma_frontend && docker compose up -d cma_api cma_frontend`

### Env on VPS (`sources/cma-assistant/.env`)

- `OPENROUTER_API_KEY` (required)
- Email vars (same as Minaki — Brevo/SendGrid/Gmail)
- `CORS_ORIGINS=https://cma.minaki.me`

Postgres URI is injected by compose (`supabase_db:5432`).

## Cost

Deploying on **existing** Contabo homelab: **$0 extra VPS**. Only OpenRouter usage per CMA (~$0.03–0.15 each).
