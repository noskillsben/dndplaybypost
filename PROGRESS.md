# PROGRESS

Session log for autonomous work through BACKLOG.md / ROADMAP.md. Newest entries at the bottom.

## Questions for Ben

- ~~Two Docker daemons~~ — resolved 2026-07-06: native dockerd disabled, Docker Desktop is canonical.
- ~~Actors API sync/async mismatch~~ — resolved 2026-07-06: router unmounted from `main.py`; file kept for EPIC 7.
- Persisted postgres volumes still hold seed entries with old `{"name": "PHB"}` sources; seeding is create-or-ignore, so SRD source edits only apply to fresh DBs.

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

### 2026-07-06 — Housekeeping (Ben's instructions, start of Phase 2 session)

- Ben resolved the dual-daemon issue (native dockerd disabled); Docker Desktop stack is canonical. `dnd52.py` deletion was intentional pre-reboot cleanup — not restored.
- Unmounted the broken actors router from `main.py` (sync/async DB mismatch); `api/routes/actors.py` kept on disk, returns in EPIC 7.
- Phase 2 order per Ben: C-02, S-04, S-05, C-06, S-06, W-02; exit test D-12 (Lasers & Feelings via in-app template editor). Design constraint: templates are data, editable in-browser; `schemas/systems/` Python definitions become seed data, not source of truth.

### 2026-07-06 — Phase 2 in progress

- **C-02**: `Compendium` container model (`compendiums` table: slug guid, name, description, system) + `compendium_guid` FK on entries (nullable — loose entries allowed). Migration `f3a1c9d40b17` backfills a `{system}-core` compendium per distinct system and assigns existing entries (verified on live PG: 11 entries → `d&d5.0-core`). New `/api/compendiums` CRUD (list includes entry_count; delete blocked with 409 while non-empty); entry create/PUT/PATCH accept `compendium_guid`; list API gains `compendium` filter; rename preserves membership; seeding assigns `{system}-core`. Games "subscribe" to compendiums when the Game model lands (U-03). 15 tests.

### 2026-07-06 — Phase 1 complete

- **S-01** (committed earlier): decimal/boolean/select primitive field types in schema builder + tests.
- **S-02**: ObjectRegistration model + form generation tests.
- **S-03**: reference fields — `compendium_link`/`compendium_link_list` query semantics (`parent_guid`, `guid_prefix`).
- **C-01** (5e9c591): filled the empty `a029aec7731a` migration — `compendium.data` json→jsonb (`postgresql_using`) + GIN index `idx_compendium_data_gin`; model `__table_args__` matches; verified upgrade/downgrade round-trip on Postgres.
- **C-05** (8c00d22): `core/guids.py` — slugify (unicode-folding), `generate_unique_guid` (-2/-3 collision suffixes, optional `guid_suffix` e.g. "srd"), `guid_redirects` table (migration `862d31ca28a0`) with rename → new guid + redirect; redirect chains flattened to one hop; children re-parented; GET/PUT/PATCH follow redirects. 21 tests.
- **C-03** (aeaf1da): PUT (full replace) + PATCH (merge into `data`, re-validate merged doc; `model_fields_set` so `parent_guid` is clearable) endpoints; frontend compendium page gained Edit (prefilled DynamicForm → PUT) and Delete (confirm → DELETE). 15 tests.
- **C-04** (24ddbc0): list endpoint — `guid_prefix` filter (escaped LIKE), `limit`(1–500)/`offset` pagination, response `{entries, total, limit, offset}`. 13 tests. Tag filtering deferred to C-06 (no tags field yet).
- **F-06** (e110758): `core/errors.py` — every error is `{"error": {code, message, details}}`; schema validation returns 400 with per-field details and a readable message ("Validation failed — level: Input should be less than or equal to 9"); FastAPI request validation (422) wrapped in the same envelope. Frontend `ApiError` already parses it (F-07). 5 tests.
- **Exit criteria** (verified over HTTP against the stack serving localhost after the dual-daemon fix, plus 108 backend / 9 frontend tests green, `make verify` from clean rebuild):
  - damage-type + item templates seeded and listable ✅
  - create → edit (PATCH) → list (paginated) → rename (old guid redirects) → delete, all through the API the UI uses ✅
  - invalid data rejected server-side with readable, field-level errors in the envelope the form displays ✅
- **Incident during verification**: host requests to `localhost:8000` returned raw 500s on any guid_redirects path while in-container requests succeeded. Root cause: the duplicate native-dockerd stack (see Questions) answering host ports with an unmigrated postgres. Resolved by migrating that DB directly; debug scaffolding removed; verification rows cleaned from both DBs.
