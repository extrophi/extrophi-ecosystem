# Sovereign Backend – Code Review Report

_Last updated: 2025-09-17_

## Executive Summary

- Status: Advanced scaffold with solid foundations; not production‑complete.
- Strengths: Clean FastAPI layering, async DB/cache, feature flags, rich diagnostics, strong security intent, and broad test coverage goals.
- Gaps: Auth/user dependency mismatch, a few settings/cache bugs, stubbed endpoints (vector, users/me), incomplete health/readiness, and some security/CORS hardening needs.
- Fit for Ubuntu/GCP: Good fit. Requires PostgreSQL, Redis/Valkey, optional Qdrant. Python 3.12 as per `pyproject.toml`.
- Readiness: Pre‑production skeleton. Estimated 3–5 days to MVP prod with focused fixes.

## Architecture Overview

- Framework: FastAPI (`src/main.py`) with routers under `src/api/v1`.
- Core services: `src/core` (config, database, security, cache, vector, diagnostics).
- Data models: `SQLModel` in `src/models` (notably `User`).
- Async-first design: Async Postgres via `sqlmodel`/`asyncpg`, Valkey/Redis via `valkey.asyncio`, Qdrant client for vectors.
- Feature flags: `Settings` toggles for multi‑tenant, vector, websockets, file uploads.
- Diagnostics: `DiagnosticError` family with a global exception handler and contextual reports.

## What’s Implemented

- Auth: Register, login, refresh, logout, me, password reset flows (`src/api/v1/endpoints/auth.py`).
- Users: List/search/get/update/delete(soft)/activate/deactivate/role (`src/api/v1/endpoints/users.py`).
- DB: Engine/session lifecycle, multi‑tenant context helper, CRUD base (filtering, pagination, bulk ops) (`src/core/database.py`, `src/core/crud_base.py`).
- Cache: TTL KV, pattern clear, increment, locks, pub/sub, health (`src/core/cache.py`).
- Vector: Collection management, upsert, search, recommend, payload updates, indices, health (`src/core/vector_db.py`).
- Websocket: Simple channel broadcast manager (`src/api/v1/endpoints/websocket.py`).
- Health: `/` status + placeholders for `/health` and `/ready` in `src/main.py`.

## Good Patterns

- Clear separation of concerns; consistent async/await usage.
- Pydantic Settings with validators and feature flags; dev-friendly defaults.
- Transaction handling with commit/rollback; context managers for sessions.
- Security groundwork: bcrypt, JWT with `exp`/`iat`/`jti`, OAuth2 bearer, API key scaffolding, tenant checks.
- Diagnostics with actionable suggestions and correlation-friendly context.

## Gaps & Issues (High Priority)

1) Auth/user dependency mismatch
- `get_current_user` returns a dict; endpoints expect a `User` model (accessing `current_user.role`, `.id`, `.email`). This will 500 at runtime.
- Fix: Load `User` from DB using `sub` and return the model instance; normalize role(s).

2) Token type and claims consistency
- Manual compare mixes Enum vs string; prefer `decode_token(token, TokenType.ACCESS)` or compare to `.value`.
- Claims use `role` in some places and `roles` elsewhere; standardize (e.g., single `role`, and derive `roles=[role]` for RBAC helpers).

3) Settings & cache API bugs
- `auth.py` uses lowercase `settings.access_token_expire_minutes`/`refresh_token_expire_days`; actual fields are uppercase (`ACCESS_TOKEN_EXPIRE_MINUTES`/`REFRESH_TOKEN_EXPIRE_DAYS`).
- Uses `cache_manager.delete_pattern(...)`; implemented method is `clear_pattern(...)`.
- Tests set `REDIS_URL`; code uses `VALKEY_URL`. Support both or settle on one.

4) Endpoint coverage gaps
- `PUT /api/v1/users/me` referenced in tests/security is not implemented.
- `vector.py` returns mock results; not wired to `vector_manager` or embeddings.

5) Health/readiness are placeholders
- Wire `/health` and `/ready` to real checks (DB, cache, vector if enabled).

6) CORS/security headers
- `allow_origins=["*"]` with `allow_credentials=True` is invalid. Use explicit origins or set credentials to False.
- HSTS always set; restrict to prod/HTTPS. Consider adding CSP/Referrer‑Policy/Permissions‑Policy.

7) Pydantic v2 cleanup
- Some `@validator` usages remain; prefer `@field_validator` or compute `jti` in `create_token`.

## Vector Database Status

- Manager is comprehensive (create/upsert/search/recommend/indices/health) and supports in‑memory mode for dev.
- API not integrated: `/vector/search` currently returns mock data; no embeddings pipeline.
- Deployment choices:
  - Qdrant service (best performance/features) adds another component to run.
  - `pgvector` (already in deps) reduces ops by keeping vectors in Postgres; requires a lighter manager path.

## Database Layer

- Engine pool strategy switches per env; session lifecycle with rollback on error; simple tenant context via `SET LOCAL` (requires DB‑side RLS/policies to matter).
- CRUD base provides filtering/pagination/bulk patterns.
- No migrations included; recommend Alembic.

## Cache Layer

- Rich capability set (TTL, pattern clear, locks, pub/sub, health checks).
- Uses `valkey` client; Ubuntu can run `redis-server` (compatible). Align env var naming.

## API Surface Notes

- Auth is feature‑complete in shape; email sending is stubbed (logs URLs).
- Users endpoints are robust; ensure tenant filters applied everywhere.
- Websocket lacks auth/tenant isolation; add before production if used.
- Vector endpoint needs real integration.

## Security Posture

- Password policy enforced; bcrypt rounds 12; JWTs with `jti`; tenant checks in auth.
- To harden before prod:
  - Enforce trusted proxy headers for rate‑limiting IPs.
  - Disable docs/OpenAPI in prod; keep staging flag.
  - Strict tenant header validation (format/allowlist).
  - Implement API key lookup/validation in DB and revocation.

## Ubuntu/GCP Fit

- Services: Postgres, Redis/Valkey, optional Qdrant (container). Consider `pgvector` on small VMs.
- Python 3.12 (per `pyproject.toml`), run `uvicorn` behind Nginx, systemd unit.
- Firewall: expose 80/443 only; keep 5432/6379 private (localhost/VPC).

## Effort & Timeline (Rough)

- Auth/settings/cache fixes: 0.5–1 day
- `/users/me` and unify user deps: 0.5 day
- Health/readiness wiring: 0.5 day
- CORS/security hardening + request IDs: 0.5 day
- Minimal vector integration (embeddings + real search): 1–2 days
- Alembic migrations + RLS/policy notes: 0.5 day
- CI/CD to GCP (lint/tests/deploy): 0.5–1 day
- Total to MVP prod: ~3–5 days focused

## Prioritized Next Steps

1) Fix breaking inconsistencies
- Return `User` from `get_current_user`; unify `role`/`roles` usage.
- Use `decode_token(..., TokenType.ACCESS)`; correct settings names; replace `delete_pattern`→`clear_pattern`.

2) Add missing endpoints and unify dependencies
- Implement `PUT /api/v1/users/me`; ensure all endpoints use the same user dependency.

3) Wire real health/readiness
- DB: `check_database_health()`; cache: `cache_manager.health_check()`; vector: `vector_manager.health_check()` when enabled.

4) Harden CORS/security
- Explicit `BACKEND_CORS_ORIGINS`; set HSTS only in prod/HTTPS; add Request‑ID middleware; consider CSP/Referrer‑Policy.

5) Decide vector backend
- Start with `pgvector` for small VM; or keep Qdrant and containerize.
- Implement `/vector/search` end‑to‑end with embeddings (can stub initially).

6) Add migrations & DB guidance
- Alembic baseline; document tenant/rls policies if using `SET LOCAL` approach.

7) CI/CD & Deploy
- GitHub Actions: ruff/mypy/tests; build & deploy to GCP VM; systemd unit + Nginx reverse proxy.

## Acceptance Criteria

- Auth endpoints operate with `current_user` as a `User` model; role checks pass; refresh/reset flows work.
- `/health` and `/ready` reflect real dependency states; CI smoke test passes.
- CORS configured with explicit origins; HSTS only on HTTPS/prod; request IDs present in logs/errors.
- Vector search returns real results and respects tenant filters.
- Migrations run cleanly on fresh DB; repeatable systemd deploy.

## Environment Prereqs (Ubuntu)

- Packages: `python3.12`, `python3.12-venv` (or `uv`), `postgresql`, `redis-server` (or Valkey), `nginx`.
- Env vars: `DATABASE_URL`, `VALKEY_URL` or `REDIS_URL`, `SECRET_KEY`, `BACKEND_CORS_ORIGINS`, `ENABLE_MULTI_TENANT`, vector flags.
- Uvicorn: `uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers N` with `DEBUG=False`.

## CI/CD Outline

- CI (GitHub Actions)
  - Setup Python 3.12 → `uv sync` → ruff/ruff‑format → mypy (ignore missing imports) → `pytest -m "unit or security"`.
  - Cache `.venv`/`uv` cache for speed.
- CD
  - SSH deploy to VM: pull repo, `uv sync`, restart systemd service; or
  - Container build → Artifact Registry → run via systemd/docker-compose.

## Decisions & Risks

- Vector engine: Qdrant is powerful but heavier on small free‑tier VMs; `pgvector` simplifies ops.
- Multi‑tenancy: DB‑level RLS requires policy work; app‑level checks are simpler but less ironclad.
- Docs exposure: disable OpenAPI/docs in prod; keep a staging flag.

---

_Reviewer notes drawn from code paths: `src/main.py`, `src/core/{config,database,cache,security,vector_db,crud_base,diagnostics}.py`, `src/api/v1/endpoints/{auth,users,vector,websocket}.py`, tests under `tests/`._

