# PROGRESS

Session log for autonomous work through BACKLOG.md / ROADMAP.md. Newest entries at the bottom.

## Questions for Ben

(none yet)

## Log

### 2026-07-06 — Session start (Phase 0)

- Created PROGRESS.md. Repo is further along than BACKLOG's "Everything below is missing" baseline: FastAPI app, backend Dockerfile, Alembic (3 migrations), compendium model/API, schema builder, and DynamicForm already exist. Treating F-01/F-02/F-03 as "verify, don't rebuild".
- Found uncommitted WIP in the working tree: RESTART_PLAN.md deleted, `dnd50.py` edited (PHB→SRD sources, new "Beyond 1rst Level" rule) with a **syntax error** (`source=srd_source.`) that would prevent the backend from booting. Fixed the syntax error, kept the WIP content, committing it as housekeeping so the tree starts clean.

### 2026-07-06 — Phase 0 complete

- **F-01/F-02/F-03**: already existed (FastAPI app with `/health`, backend Dockerfile, Alembic with 3 migrations run by `start.sh`). Verified via clean `make rebuild`: all containers healthy, migrations + seed run, `/health` and `/api/compendium/` respond, frontend serves on :3000.
- **F-10**: verified no `.env`/`.venv`/`node_modules`/`.svelte-kit`/`data/` tracked in git; added `.claude/settings.local.json` to `.gitignore`, committed shared `.claude/settings.json` (deny git push etc.).
- **F-04**: new `core/config.py` (pydantic-settings). `database.py`/`main.py` now consume it; fails fast on missing `DATABASE_URL`; SQLAlchemy `echo` tied to `DEBUG`. `alembic/env.py` still reads env directly (runs standalone — fine).
- **F-05**: pytest harness at `backend/tests/` (async SQLite in-memory DB via `aiosqlite` + `StaticPool`, httpx ASGI client with `get_db` override). Compendium JSONB columns became `JSON().with_variant(JSONB, "postgresql")` so SQLite tests work — no Postgres behavior change. `requirements-dev.txt`, `pytest.ini`, root `ci.sh` (CI_FULL=1 adds docker rebuild + frontend tests). Frontend: Vitest 0.34 (vite 4-compatible) + `npm run test`.
- **F-07**: `frontend/src/lib/api.js` — base URL from `VITE_API_URL`, JSON helpers, `ApiError` parsing both FastAPI `detail` and the upcoming F-06 envelope. DynamicForm + compendium page refactored onto it. Also fixed: page sent `source` as a string but the API expects an object — now sends `{name: ...}`.
- **Exit criteria**: `make rebuild` healthy ✅ · backend pytest 6 passed ✅ · frontend vitest 9 passed in compose ✅ · no secrets/artifacts tracked ✅.
- Decisions Ben may want to review:
  - Kept the actors API as-is, but note it mixes sync `Session`/`db.query` with the async `get_db` dependency — it will fail at request time. Not in Phase 0/1 scope; flagged for whenever actors work resumes (EPIC 7 revisit).
  - The persisted Postgres volume still holds seed entries with the old `{"name": "PHB"}` sources; seeding is create-or-ignore, so the SRD source edits only apply to fresh databases.
