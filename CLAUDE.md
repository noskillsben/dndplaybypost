# CLAUDE.md — Working agreement for autonomous sessions

You are working through BACKLOG.md in the order defined by ROADMAP.md. Work as autonomously as possible; the owner (Ben) reviews when he returns.

## Workflow loop

1. Read PROGRESS.md to see where the last session stopped. If it doesn't exist, create it and start at Phase 0 of ROADMAP.md.
2. Pick the next unfinished backlog item (respect the `Depends on` column; P0 before P1).
3. Implement it, including tests.
4. Run the relevant verification (see Commands). Fix until green.
5. Commit (see Git policy), append an entry to PROGRESS.md (item ID, what was done, decisions made, anything Ben should review). In the same commit: tick the item in BACKLOG.md (prefix its ID with ✅) and, when a phase completes, tick the phase checklist + milestone table in ROADMAP.md.
6. Repeat. When a ROADMAP phase's exit criteria all pass, record that in PROGRESS.md, then continue to the next phase unless told otherwise.

If genuinely blocked (ambiguous requirement, missing credential), record the question in PROGRESS.md under "Questions for Ben", skip to the next unblocked item, and keep going.

## Hard rules — environment

- **Backend Python ALWAYS runs in the venv at `backend/.venv`.** Never `pip install` globally, never use system python. If the venv is missing or broken: `python3 -m venv backend/.venv`, then `backend/.venv/bin/pip install -r backend/requirements.txt`.
- Backend tests run in the venv: `backend/.venv/bin/pytest` (from `backend/`). Keep `requirements.txt` (runtime) and `requirements-dev.txt` (pytest etc.) up to date whenever you add a dependency.
- **Docker compose is torn down and rebuilt for integration verification**: `docker compose down && docker compose up -d --build`, then wait for health checks before hitting endpoints.
- **Frontend tests run inside the compose environment**, not on the host: `docker compose run --rm frontend npm run test`. If frontend test tooling doesn't exist yet (it doesn't at the start), setting up Vitest + a `test` script in `frontend/package.json` is part of item F-05.
- Prefer `make` targets (see Makefile) over retyping raw commands, and keep the Makefile updated as commands evolve.

## Hard rules — git

- Work on branch `autopilot` (create from current branch if it doesn't exist).
- **One commit per completed backlog item.** Message format: `[F-01] FastAPI app skeleton with /health`. Multi-commit items are fine if each commit is coherent.
- **NEVER push. NEVER force-push. Never rewrite history of existing commits.**
- Never commit: `.env`, `backend/.venv/`, `node_modules/`, `frontend/.svelte-kit/`, `data/`. Fix `.gitignore` first (item F-10) if they're tracked.

## Hard rules — scope & design

- The MVP definition at the top of BACKLOG.md is the source of truth. Don't build post-MVP parking-lot items.
- Entry-type templates must be data-driven (in-app editable), not hardcoded Python — see S-06. If you catch yourself writing `if class == "fighter"`, push the rule into compendium data instead.
- Ask "would this work for a non-D&D system?" at every design decision in EPIC 1/2.
- Don't refactor beyond the current item's needs. Over-engineering killed iteration 1 of this project.
- New endpoints need tests. Bug fixes need a regression test.

## Commands

```bash
make venv            # create/refresh backend venv + deps
make test-backend    # backend/.venv/bin/pytest inside backend/
make rebuild         # docker compose down + up -d --build, wait healthy
make test-frontend   # docker compose run --rm frontend npm run test
make verify          # all of the above, in order — run before every commit
```

## Definition of done for a backlog item

- Acceptance implied by the item's description is met.
- `make verify` passes from a clean rebuild.
- PROGRESS.md updated; commit made.
