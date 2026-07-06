# BACKLOG — D&D Play-by-Post Platform

**Last updated:** 2026-07-06
**Scope:** Everything required to reach MVP, plus explicitly-parked post-MVP items.

## MVP Definition (source of truth)

The MVP is done when:

1. **Sessions & players** — GMs can manage their game sessions and the players within them.
2. **Compendium builder** — a person can use in-app tools to create all the rules of D&D 5e as an interactive compendium (races, feats, classes, subclasses, level-up tables, equipment, spells, monsters, backgrounds, conditions, etc.), and compendiums can be exported and imported.
3. **Module builder** — a person can use in-app tools to create an adventure/module from a compendium: places, events, NPCs, rollable tables, etc.
4. **Play** — games can be played using compendiums + adventures or on the fly; characters can be imported and exported.

**Status tracking:** when an item is complete, prefix its ID with ✅ (e.g. `✅ F-01`). Autonomous sessions must tick items here in the same commit that completes them.

**Priorities:** `P0` = required for MVP · `P1` = strongly desired for MVP, cut if needed · `P2` = post-MVP.
**Size:** S (≤1 day) · M (2–5 days) · L (1–3 weeks) · XL (3+ weeks). Sizes assume hobbyist pace with AI assistance; treat as relative weight, not promises.

---

## EPIC 0 — Foundation & Infrastructure

The repo currently has docker-compose, `database.py`, an empty `core` package, and a frontend that calls endpoints that don't exist. Everything below is missing.

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| ✅ F-01 | FastAPI app skeleton: `main.py`, router mounting, CORS from env, `/health` endpoint | P0 | S | — |
| ✅ F-02 | Backend `Dockerfile` + `requirements.txt` (compose references a Dockerfile that doesn't exist — `docker compose up` fails today) | P0 | S | — |
| ✅ F-03 | Alembic migrations wired to the async engine; initial migration | P0 | S | F-01 |
| ✅ F-04 | Settings module (pydantic-settings) replacing raw `os.getenv`; fail fast on missing config | P0 | S | F-01 |
| ✅ F-05 | Pytest harness + test database fixture; CI script (even just a bash script) that runs tests | P0 | M | F-03 |
| ✅ F-06 | Consistent API error envelope + validation error formatting | P1 | S | F-01 |
| ✅ F-07 | Frontend API client module (`$lib/api.js`): base URL from env (kill hardcoded `http://localhost:8000`), error handling, JSON helpers | P0 | S | — |
| F-08 | Seed/reset scripts: `make seed`, `make reset-db` (or bash equivalents) | P1 | S | F-03 |
| F-09 | Structured logging (request logs, slow query logs); disable SQLAlchemy `echo=True` outside debug | P1 | S | F-04 |
| ✅ F-10 | `.gitignore` hygiene: remove `.venv`, `.svelte-kit`, `.env` from the repo | P0 | S | — |

## EPIC 1 — Schema Engine (the extensibility core)

The `ObjectRegistration` + field-types design from RESTART_PLAN.md. This is the layer that makes "build any TTRPG system in-app" possible, so it must be data-driven, not Python-code-driven — otherwise MVP criterion 2 ("a person could use the tools within the app to create all the rules") fails for non-programmers.

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| ✅ S-01 | `FieldType` base + primitives: short_text, long_text, markdown, integer, decimal, boolean, select(options) | P0 | M | F-01 |
| ✅ S-02 | `ObjectRegistration`: fields → Pydantic model (validation) + JSON form schema (frontend) | P0 | M | S-01 |
| ✅ S-03 | Reference field types: `compendium_link` (query by type/tag/prefix), `compendium_link_list` (multi-select), `parent_link` | P0 | M | S-02 |
| ✅ S-04 | Composite field types: `list_of(field)` (e.g. list of damage entries), `table` (rows × typed columns — needed for class level tables, rollable tables), `dice_expression` (validated, e.g. "2d6+3") | P0 | L | S-02 |
| ✅ S-05 | Choice/grant field types for character building: `choice(n, from)` (pick 2 skills…), `grant` (this race grants darkvision) — the machine-readable hooks the wizard consumes | P0 | L | S-03 |
| S-06 | **Template-type editor UI**: create/edit entry *types* (their fields) in-app and store them as data, so users can define new content types without writing Python. Python-defined built-ins become seed data for this system | P0 | L | S-04 |
| S-07 | Schema versioning: template changes don't corrupt existing entries; entries record the template version they were written against | P1 | M | S-06 |
| S-08 | Computed fields (formula strings evaluated against entry/character data, e.g. `floor((str-10)/2)`); safe evaluator, no `eval` | P1 | L | S-04 |

## EPIC 2 — Compendium Core

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| ✅ C-01 | `CompendiumEntry` model per RESTART_PLAN (guid PK, system, entry_type, name, JSONB data, homebrew, source, parent_guid, timestamps) + migration. Use real `JSONB`, add GIN index | P0 | S | F-03 |
| ✅ C-02 | `Compendium` container model: a named compendium (e.g. "D&D 5e 2014 SRD", "Ben's homebrew") owning entries; entries belong to a compendium, games subscribe to compendiums | P0 | M | C-01 |
| ✅ C-03 | CRUD API: create/read/update/delete entries; validation against the entry-type template; PATCH support | P0 | M | S-02, C-01 |
| ✅ C-04 | List/query API: filter by system, type, tag, homebrew, parent_guid, guid_prefix; text search on name; pagination (tag filter deferred to C-06) | P0 | M | C-01 |
| ✅ C-05 | GUID service: slugify names, collision handling, custom suffix support, rename = new guid + redirect record | P0 | S | C-01 |
| C-06 | Tags on entries + tag filtering (rarity, spell school, weapon category live better as tags/fields than as types) | P1 | S | C-04 |
| C-07 | Cross-reference integrity: warn (not block) when deleting an entry that other entries link to; "what links here" endpoint | P1 | M | C-04 |
| C-08 | Entry detail rendering: markdown rendering, resolved links (damage_type guid → clickable "Slashing"), stat-block style layout per type | P0 | M | C-04 |
| C-09 | Compendium browser v2: browse by compendium → type → entry; search-as-you-type (debounced — current code fires a request per keystroke); edit + delete from UI | P0 | M | C-08, F-07 |
| C-10 | Duplicate/clone entry ("copy official Longsword → my homebrew variant") | P1 | S | C-03 |

## EPIC 3 — D&D 5e Content Templates & Seed Data

Criterion 2 lists the content types explicitly. Each needs: a template (fields), an editor form that works, and at least SRD-level seed data to prove it.

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| D-01 | Foundational lookup types: damage types, conditions, skills, abilities, languages, creature types, sizes, currencies | P0 | M | S-06 |
| D-02 | Equipment templates: weapon (damage, properties, mastery), armor, gear, tool, mount/vehicle, magic item (rarity, attunement, charges) | P0 | M | D-01 |
| D-03 | Spell template: level, school, casting time, range, components, duration, ritual/concentration flags, class lists, damage/heal dice, scaling | P0 | M | D-01 |
| D-04 | Species/race template: traits, ability bonuses (2014) / background-based (2024), speed, senses, subraces via parent_link, granted spells/proficiencies as `grant` fields | P0 | M | S-05, D-01 |
| D-05 | Class template: hit die, proficiencies, saving throws, equipment choices, spellcasting type, **level table** (features/slots/resources per level 1–20) | P0 | L | S-04, S-05 |
| D-06 | Subclass template: parent class link, features by level | P0 | M | D-05 |
| D-07 | Feat template: prerequisites (machine-checkable), effects/grants | P0 | M | S-05 |
| D-08 | Background template: proficiencies, equipment, feature; (2024: ability scores + feat) | P0 | S | D-07 |
| D-09 | Monster/stat-block template: full 5e stat block — AC, HP formula, speeds, abilities, saves, skills, resistances/immunities, senses, CR, traits, actions (with attack/damage dice), legendary/lair actions | P0 | L | D-01 |
| D-10 | Rules-text template: hierarchical rules chapters/sections (parent_link tree) for basic rules reference | P0 | S | D-01 |
| D-11 | SRD 5.2 seed import: script that loads SRD content (spells, ~monsters, items, classes…) from the SRD_CC_v5.2.md / Fight Club XML data already collected (2,929 entries from previous iteration) into the templates above | P0 | L | D-02…D-10 |
| D-12 | Second-system smoke test: define a 1-page RPG (Lasers & Feelings) entirely via the in-app template editor to prove system-agnosticism | P1 | M | S-06 |

## EPIC 4 — Compendium Import/Export (MVP criterion 2b)

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| X-01 | Export format spec: single JSON file containing compendium metadata, **entry-type templates**, and entries (templates must travel with data or imports break) | P0 | M | C-02, S-06 |
| X-02 | Export API + UI: whole compendium, or filtered subset (type/tag/homebrew-only) | P0 | M | X-01 |
| X-03 | Import API + UI: validate file, dry-run report (new / changed / conflicting guids), conflict strategies (skip, overwrite, import-as-copy) | P0 | L | X-01 |
| X-04 | Fight Club 5e XML import (reuse prior iteration's importer) | P1 | M | X-03 |
| X-05 | Format versioning + migration hooks for future format changes | P1 | S | X-01 |

## EPIC 5 — Users, GMs, Sessions & Players (MVP criterion 1)

Deliberately skipped in the restart plan; required for MVP. Keep it simple: email+password, no OAuth.

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| U-01 | User model + auth: register, login, session cookies or JWT, password hashing (argon2/bcrypt); no email verification for MVP (self-hosted) | P0 | M | F-03 |
| U-02 | Roles per game: GM, Player, (Observer P2). RBAC middleware/dependency | P0 | M | U-01 |
| U-03 | Game (session container) model: name, description, GM(s), subscribed compendiums, attached module(s), status (recruiting/active/paused/finished) | P0 | M | U-02, C-02 |
| U-04 | Invites: GM generates invite code/link; player joins with code; GM can remove players | P0 | M | U-03 |
| U-05 | GM dashboard: my games, players in each, pending invites, quick links | P0 | M | U-03 |
| U-06 | Player dashboard: my games, my characters | P0 | S | U-03 |
| U-07 | Content ownership & permissions: compendiums/modules have owners; private vs shared-on-server visibility | P1 | M | U-03 |
| U-08 | Account basics: change password, display name, avatar | P1 | S | U-01 |

## EPIC 6 — Module / Adventure Builder (MVP criterion 3)

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| M-01 | Module container model: name, description, linked compendium(s), version, author | P0 | M | C-02 |
| M-02 | Places: hierarchical locations (parent_link tree), markdown description, GM-only secrets section, links to compendium entries and NPCs | P0 | M | M-01 |
| M-03 | NPCs: built on the monster stat-block template + personality/role/faction fields; unique NPCs vs generic monsters; portrait image | P0 | M | D-09, M-01 |
| M-04 | Events/scenes: ordered or free-form scenes with trigger notes, read-aloud text, GM notes, links to places/NPCs/items | P0 | M | M-02 |
| M-05 | Rollable tables: die expression + weighted rows; rows can be text or compendium/module references; nested table rolls; "roll" button | P0 | M | S-04, M-01 |
| M-06 | Encounters: monster list (from compendium) + place + notes; used later by gameplay | P1 | M | M-03 |
| M-07 | Handouts: markdown/image documents the GM can reveal to players | P1 | S | M-01 |
| M-08 | Module browser/editor UI: tree navigation (places), tabbed sections (NPCs, events, tables, handouts) | P0 | L | M-02…M-05 |
| M-09 | Module export/import (same architecture as X-01/X-03; module references compendium guids, import warns on missing refs) | P0 | M | X-03, M-01 |

## EPIC 7 — Characters (MVP criterion 4b)

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| P-01 | Character model: owner, game, system, JSONB sheet data (abilities, HP, class levels, proficiencies, inventory, spells, resources, notes), portrait | P0 | M | U-03, C-02 |
| P-02 | Derived-stats engine: modifiers, proficiency bonus, AC, save DCs, skill bonuses, spell slots — computed from sheet + compendium grants (uses S-08 formulas where possible) | P0 | L | S-08, P-01 |
| P-03 | Character creation wizard: species → class → abilities (point buy / standard array / manual) → background → skills → equipment → spells; driven by compendium `choice`/`grant` data, not hardcoded D&D logic | P0 | XL | S-05, D-04…D-08, P-01 |
| P-04 | Level-up wizard: HP roll/average, new class features, subclass selection, ASI/feat choice, new spells; multiclass support P1 | P0 | L | P-03 |
| P-05 | Interactive character sheet: view/edit, click-to-roll any check/save/attack, HP & death saves, conditions, resource pips (rage, ki…), rest buttons (short/long) applying recovery rules | P0 | XL | P-02 |
| P-06 | Inventory: add from compendium (search + click or **drag-and-drop**), equip/unequip affecting AC/attacks, quantity, weight/encumbrance, currency | P0 | L | P-05, D-02 |
| P-07 | Spell management: known/prepared lists from class rules, slot tracking, cast-at-level prompt, concentration flag | P0 | L | P-05, D-03 |
| P-08 | Character import/export: single JSON file, self-contained enough to re-import on another server (embed or reference compendium guids; import reports missing refs) | P0 | M | P-01, X-01 |
| P-09 | On-the-fly / manual mode: create a character with free-typed values, no compendium required (supports "just play" games) | P0 | M | P-01 |
| P-10 | NPC quick-sheet: GM instantiates a monster/NPC from compendium into the game with tracked HP | P1 | M | P-01, D-09 |

## EPIC 8 — Gameplay: Play-by-Post (MVP criterion 4)

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| G-01 | Message model + API: game-scoped posts, author (user + optional character), message types (IC dialogue / action / GM narration / OOC / system), markdown, edit with history | P0 | L | U-03 |
| G-02 | Game chat UI: threaded or linear feed, color-coded by type, character avatars, pagination/infinite scroll | P0 | L | G-01 |
| G-03 | Live updates: polling for MVP (simple, Pi-friendly); WebSockets P2 | P0 | M | G-02 |
| G-04 | Dice service integration (port the preserved dice roller): roll API, roll log, rolls render as structured chat messages (expression, result breakdown, crit highlight) | P0 | M | G-01 |
| G-05 | Sheet→chat actions: clicking attack/check/save/spell on the sheet posts the roll with modifiers into the game feed and consumes resources (spell slots, ammo) | P0 | L | G-04, P-05 |
| G-06 | GM tools in-game: secret rolls, whisper to player, roll on module rollable tables into chat, reveal handouts, award XP/milestone | P0 | L | G-04, M-05 |
| G-07 | Scenes/channels within a game (e.g. split party): named channels, character membership; single channel is the MVP floor, multi-channel P1 | P1 | M | G-01 |
| G-08 | Turn/initiative helper: initiative list with sort, current-turn marker, round counter; manual, no automation | P1 | M | G-04, P-10 |
| G-09 | Game log export (markdown transcript) | P2 | S | G-01 |

## EPIC 9 — Frontend App Shell & UX

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| W-01 | App layout: nav (Dashboard / Compendiums / Modules / Games), auth-aware header, mobile-usable | P0 | M | F-07 |
| W-02 | DynamicForm v2: nested/list fields, table editor widget, dice-expression input, searchable async reference picker (current `<select>` won't survive 500 spells), client-side validation from schema | P0 | L | S-04 |
| W-03 | Drag-and-drop primitives (equipment to inventory, spells to prepared list); click-to-add fallback for mobile | P1 | M | W-02 |
| W-04 | Markdown editor with preview (used by compendium, modules, chat) | P0 | S | W-01 |
| W-05 | Toasts/error surfaces (replace `alert()` in current code) | P1 | S | W-01 |
| W-06 | Loading/empty/skeleton states, optimistic updates where cheap | P1 | S | W-01 |

## EPIC 10 — Ops & Docs

| ID | Item | Pri | Size | Depends on |
|----|------|-----|------|------------|
| O-01 | Production compose profile: non-debug, restart policies, resource limits sized for Pi 4 | P1 | S | F-02 |
| O-02 | Backup/restore: pg_dump cron into ./data/backups + documented restore; UI button P2 | P1 | S | O-01 |
| O-03 | README: setup, architecture overview, how to add a content template, how to contribute | P1 | M | — |
| O-04 | Versioned releases + DB migration policy (never break user data) | P1 | S | F-03 |

## Post-MVP parking lot (explicitly out)

OAuth providers & 2FA · observer role · campaign calendar/timeline system · automatic event logging · eavesdropping/whisper-radius mechanics · combat automation (auto-apply damage, condition effects on rolls) · encounter balancing/CR calculator · maps/tokens/VTT · notifications/email · localization · text-to-speech · graph visualization of world relationships · marketplace/community content hub · mobile apps · AI assistance.

---

## Traceability: MVP criterion → epics

| MVP criterion | Covered by |
|---|---|
| 1. GM sessions & player management | EPIC 5 (U-01…U-08) |
| 2. Compendium creation tools, all D&D 5e content | EPIC 1 (S-01…S-08), EPIC 2 (C-01…C-10), EPIC 3 (D-01…D-12) |
| 2b. Compendium export/import | EPIC 4 (X-01…X-05) |
| 3. Module builder (places, events, NPCs, rollable tables) | EPIC 6 (M-01…M-09) |
| 4. Play with compendium/module or on the fly | EPIC 8 (G-01…G-08), P-09 |
| 4b. Character import/export | P-08 |
| Cross-cutting: calculation lifting, drag-and-drop, level-up wizard | P-02…P-07, W-02, W-03 |
