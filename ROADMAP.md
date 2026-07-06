# ROADMAP — D&D Play-by-Post Platform → MVP

**Last updated:** 2026-07-06
**Companion document:** BACKLOG.md (item IDs referenced below)

Phases are sequential because each one's exit criteria de-risk the next. Durations are rough relative weights at hobbyist pace — expect the character phase to be the long one. **Rule: don't start a phase until the previous phase's exit criteria pass.** That's the discipline that prevents the over-engineering spiral from iteration 1.

---

## Phase 0 — Make it run (Foundation)

**Goal:** `docker compose up` gives a working, testable skeleton.
**Backlog:** F-01, F-02, F-03, F-04, F-05, F-07, F-10

Today the compose file references a backend Dockerfile that doesn't exist and the frontend calls APIs that were never written. This phase ends that: FastAPI app boots, Alembic migrates, one trivial test passes in CI, frontend fetches `/health` through the env-driven API client.

**Exit criteria**
- Fresh clone + `./setup.sh` → all containers healthy.
- `pytest` green locally and in CI script.
- No secrets or build artifacts tracked in git.

## Phase 1 — Schema engine v1

**Goal:** Define an entry type in data, get validation + a working form from it.
**Backlog:** S-01, S-02, S-03, C-01, C-03, C-04, C-05, F-06

Rebuild `ObjectRegistration` + field types (primitives and reference fields), the compendium table, and CRUD. The existing DynamicForm.svelte is a usable starting point — fix it to match the real API.

**Exit criteria**
- Create a "damage type" and an "item" template in Python seed code; create/edit/list/delete entries through the UI.
- Invalid data is rejected server-side with readable errors in the form.

## Phase 2 — Schema engine v2: composite fields + in-app template editor

**Goal:** A non-programmer can create a new content type in the browser.
**Backlog:** S-04, S-05, S-06, W-02, C-02, C-06

This is the make-or-break phase for MVP criterion 2 ("use the tools within the app to create all the rules"). Tables, lists, dice expressions, choice/grant fields, and the template editor UI. Compendium containers land here too.

**Exit criteria**
- Build the D&D "class" type — including its level 1–20 table — entirely in the browser, no Python edits.
- DynamicForm v2 renders nested lists, tables, and searchable reference pickers.
- **Smoke test (D-12):** define Lasers & Feelings in-app in under an hour.

## Phase 3 — D&D 5e content + import/export

**Goal:** A real D&D 5e compendium exists in the app and survives a round trip.
**Backlog:** D-01 … D-11, C-07, C-08, C-09, C-10, X-01, X-02, X-03, W-04, (X-04 if time)

Build all the D&D templates, seed the SRD (reuse the 2,929-entry Fight Club import work), polish the browser into something you'd actually reference at the table, and ship the export/import format — templates travel inside the file.

**Exit criteria**
- Every criterion-2 content type (race, class, subclass, level tables, feat, spell, equipment, monster, background, condition, rules text) has a template, working editor, and SRD examples.
- Export compendium → wipe DB → import → identical content (checksum the entries).
- Import dry-run correctly reports conflicts on a second import.

## Phase 4 — Users, GMs, sessions

**Goal:** MVP criterion 1 done.
**Backlog:** U-01 … U-06, W-01, (U-07, U-08 if time)

Auth is deliberately boring: email + password, hashed, session cookie. Games subscribe to compendiums. Invite codes bring players in.

**Exit criteria**
- Two browsers: GM creates a game, generates invite; player registers, joins; GM sees them, can remove them.
- A game lists which compendiums it uses.

## Phase 5 — Module / adventure builder

**Goal:** MVP criterion 3 done.
**Backlog:** M-01 … M-05, M-08, M-09, (M-06, M-07 if time)

Places tree, NPCs (stat block + personality), events/scenes, rollable tables, and the module editor UI. Module export/import reuses the Phase 3 format architecture.

**Exit criteria**
- Author a small 3-location adventure with 4 NPCs, 2 events, and a random-encounter table using only compendium content.
- Export it, import it on a clean DB alongside the compendium, everything resolves.
- Rollable table "roll" button returns weighted results, including nested tables.

## Phase 6 — Characters

**Goal:** MVP criterion 4b + the "calculation lifting" promise. The longest phase.
**Backlog:** P-01, P-02, S-08, P-03, P-04, P-05, P-06, P-07, P-08, P-09, W-03, (P-10 if time)

Order within the phase: model → derived-stats engine → creation wizard → sheet → inventory → spells → level-up wizard → import/export → manual mode. The wizard must be driven by compendium `choice`/`grant` data — if you find yourself hardcoding "if class == fighter", stop and push the rule into the data.

**Exit criteria**
- Create a level-1 SRD character (e.g. dwarf cleric) fully through the wizard; AC, saves, skills, slots all auto-correct.
- Level them 1→3 via the level-up wizard, including subclass choice.
- Drag a longsword from the compendium into inventory; equipping changes attack options.
- Export the character, import on a clean server with the SRD compendium, sheet identical.
- Create a "manual mode" character with no compendium in under 2 minutes.

## Phase 7 — Play-by-post gameplay

**Goal:** MVP criterion 4 done — a real game can be played.
**Backlog:** G-01 … G-06, W-05, W-06, (G-07, G-08 if time)

Message model with typed, color-coded posts; polling for liveness; ported dice roller; and the signature feature: sheet actions that post rolls to chat and consume resources.

**Exit criteria**
- GM + 2 players run a scripted 20-post scene: narration, dialogue, a perception check clicked from a sheet, a spell cast that consumes a slot, a secret GM roll, and a rollable-table result — all appearing correctly for the right audiences.
- Message history paginates; a player on a phone can post.

## Phase 8 — MVP hardening & release

**Goal:** Someone who isn't Ben can self-host this.
**Backlog:** O-01, O-02, O-03, O-04, F-08, F-09, remaining P1 stragglers

Full end-to-end dogfood: run a real one-shot play-by-post with friends using only the app. Fix what hurts. Deploy on the Raspberry Pi 4 and verify performance with the full SRD loaded.

**Exit criteria (= MVP done)**
1. GM manages sessions and players in them. ✅ criterion 1
2. D&D 5e rules built in-app as an interactive compendium; export/import round-trips. ✅ criterion 2
3. Module built in-app from the compendium: places, events, NPCs, rollable tables; exportable. ✅ criterion 3
4. A game played with compendium + module, another on the fly; characters imported/exported. ✅ criterion 4
5. Runs on the Pi; backup/restore documented and tested; README lets a stranger deploy.

---

## Milestone map

| Milestone | You can demo… | Phases |
|---|---|---|
| M1 "It boots" | Healthy stack, tests, CI | 0 |
| M2 "Forms from data" | Entry types → validated forms | 1–2 |
| M3 "The compendium" | Full SRD browsable, round-trip export | 3 |
| M4 "Multiplayer shell" | GM + players in a game | 4 |
| M5 "The adventure" | Authored module, rollable tables | 5 |
| M6 "The character" | Wizard → sheet → level-up → export | 6 |
| M7 "The game" | Live play-by-post with sheet-driven rolls | 7 |
| **MVP** | A stranger self-hosts and runs a campaign | 8 |

## Standing risks & mitigations

- **Template editor scope creep (Phase 2).** The generic engine is where iteration 1 died. Mitigation: the Lasers & Feelings timebox test — if the engine can't express a 1-page RPG simply, it's too complicated, not too weak.
- **Character wizard complexity (Phase 6).** 5e's choice web is the hardest data-modeling problem here. Mitigation: `choice`/`grant` fields are designed in Phase 2 and validated against class/race templates in Phase 3 — the wizard consumes them, it doesn't invent them.
- **Hardcoding D&D into the engine.** Every phase exit includes the question: "would this work for a non-D&D system?" D-12 exists to keep this honest.
- **Solo-dev stall.** Each phase ships something demoable; if motivation dips, cut P1s, never P0s, and keep the exit-criteria demos as the reward loop.
