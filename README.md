# ولتاژ — Electrical Projects Management API

Production-ready, async FastAPI backend for the ولتاژ (Voltage) electrical
projects management system. This repository contains **backend only** — the
front-end is a separate, already-implemented project.

> **Scope note:** Per project requirements, all *database read/query bodies*
> are intentionally left as `TODO` / `raise NotImplementedError` stubs inside
> the `app/repositories/*.py` files. Every other layer — routing, validation,
> auth, security, middleware, services, schemas, exception handling — is fully
> implemented and production-shaped.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL (asyncpg)
· Pydantic v2 · JWT (python-jose) · Argon2 (passlib) · Redis · SlowAPI ·
Structlog · Docker

## Architecture

```
app/
  api/v1/        version-scoped router aggregation
  auth/          get_current_user and related auth dependencies
  config/        environment-driven settings
  core/          logging, constants, rate limiter
  database/      SQLAlchemy engine/session/base
  dependencies/  DB session, Redis, pagination DI providers
  exceptions/    custom exception classes + global handlers
  middleware/    request id, request time, logging, security headers
  models/        SQLAlchemy ORM models
  permissions/   RBAC roles + PBAC permission checker dependency
  repositories/  data-access layer (Repository Pattern) — query bodies TODO
  responses/     standardized success/error/pagination envelopes
  routes/        FastAPI routers per resource
  schemas/       Pydantic request/response models with full validation
  security/      password hashing, JWT, token blacklist
  services/      business logic (Service Layer), orchestrates repositories
  storage/       local filesystem file storage backend
  uploads/       uploaded file storage root (gitignored)
  utils/         datetime/file helper functions
  validators/    reusable field validators (phone, amount, file, etc.)
  main.py        FastAPI app factory + lifecycle
migrations/      Alembic migration environment
scripts/         one-off scripts (e.g. RBAC seeding)
```

## Getting started

### 1. Configure environment

```bash
cp .env.example .env
# then edit .env — at minimum set SECRET_KEY, REFRESH_SECRET_KEY, DATABASE_URL
```

Generate strong secrets:

```bash
openssl rand -hex 64
```

### 2. Run with Docker (recommended)

```bash
docker compose up --build
```

This starts the API, PostgreSQL, and Redis together. API available at
`http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

### 3. Run locally (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Requires a locally running PostgreSQL and Redis matching your `.env`.

### 4. Database migrations

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 5. Seed default roles/permissions

```bash
python -m scripts.seed_roles
```

## Authentication flow

1. `POST /api/v1/auth/login` → access token (15 min) + refresh token (7 or 30 days with `remember_me`).
2. Send `Authorization: Bearer <access_token>` on subsequent requests.
3. `POST /api/v1/auth/refresh` before/when the access token expires — implements rotation with reuse detection.
4. `POST /api/v1/auth/logout` blacklists the current access token and revokes the refresh token.

## Authorization model

Role-Based (`admin`, `manager`, `employee`, `viewer`) layered with fine-grained
Permission-Based Access Control (`project:create`, `payment:delete`, ...). See
`app/permissions/roles.py` for the full matrix, and `app/permissions/checker.py`
for the `RequirePermission` / `RequireRole` FastAPI dependencies used on routes.

## Security highlights

- Argon2 password hashing (bcrypt fallback verification for migration)
- Access/refresh JWT separation with distinct signing secrets
- Refresh token rotation + reuse detection (auto-revokes the token family)
- Redis-backed access-token blacklist for immediate logout
- Brute-force lockout after 5 failed attempts (15 min lockout)
- Generic auth error messages (no user enumeration)
- SlowAPI rate limiting (per-route overrides for login/reset)
- Strict file upload validation: extension allow-list, MIME cross-check,
  magic-byte sniffing, size cap, UUID-based storage filenames, path-traversal
  guards
- Standardized error envelope with no internal detail leakage on 500s
- Security response headers (CSP, X-Frame-Options, HSTS in production, etc.)
- Request-ID correlation across structured logs

## Completing the implementation

Search the codebase for `TODO` to find every stubbed repository method. Each
docstring documents the intended SQLAlchemy query shape.

```bash
grep -rn "TODO" app/repositories
```
