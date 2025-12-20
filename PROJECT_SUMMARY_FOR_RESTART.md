# Project Summary: D&D Play-by-Post (v2.0)

This document summarizes the current state of the project as of December 2025, capturing the tech stack, architecture, implemented features, and lessons learned across three iterations.

## 🛠 Tech Stack

### Backend (Python/FastAPI)
- **Framework:** FastAPI
- **Database:** PostgreSQL 15 (via SQLAlchemy + asyncpg)
- **Cache/WebSockets:** Redis 7
- **Auth:** JWT (Python-jose + Passlib/Bcrypt)
- **Models:** Pydantic for validation, SQLAlchemy for ORM.
- **Key Patterns:** Service-oriented architecture (partial), Async/Await throughout.

### Frontend (JS/SvelteKit)
- **Framework:** SvelteKit + Vite
- **Styling:** Tailwind CSS (Vanilla CSS for some components)
- **State Management:** Svelte Stores + Native Fetch
- **Communication:** HTTP REST + WebSockets (custom `websocket.js` handler)

### Infrastructure
- **Orchestration:** Docker Compose
- **Proxy/Web Server:** Nginx (Reverse proxying `/api` and `/ws`)
- **SSL:** Certbot / Let's Encrypt
- **Database UI:** Adminer (development profile)

---

## 🏗 Architecture & Data Strategy

### 1. The "Flexible Data" Approach
The project heavily uses **PostgreSQL JSONB** columns for character sheets and compendium items. 
- **Character Model:** Stores `sheet_data` as JSONB. Includes `schema_version` to handle structural evolution.
- **Compendium Model:** Stores `data` as JSONB. Supports multiple game systems (e.g., "D&D 5.2 (2024)") in the same table.
- **Component Templates:** A meta-system designed to define validation schemas (JSON Schema) for different character parts (resources, attacks, etc.).

### 2. Messaging System
- **Real-time:** Driven by FastAPI WebSockets + Redis for broadcast.
- **Masquerading:** Supports posting messages as a specific `character_id`.
- **IC/OOC:** Metadata field to toggle "In-Character" vs "Out-of-Character" styling.
- **Implementation Note:** Contrary to early plans for "SQLite per campaign," messages are currently unified in a single PostgreSQL `messages` table for easier querying and cross-campaign notifications.

### 3. SRD Content Pipeline
- **Auto-Import:** The backend includes an `ImportService` that parses SRD JSON files and populates the database on first run.
- **Extensibility:** Designed to allow "Homebrew" flags on items to separate official from user-generated content.

---

## ✅ Implemented Features

| Feature | Description | Status |
|---------|-------------|--------|
| **User Auth** | Registration, Login, JWT-based persistence. | Fully Working |
| **Campaigns** | Create, Join, Leave. Member roles (DM/Player). | Fully Working |
| **Messenger** | Real-time chat, dice rolling integration, edit/delete (15m limit). | Fully Working |
| **Compendium** | Search, filter by type/system, stats overview, detail views. | Fully Working |
| **Character Creation** | Basic form creation; requires manual JSON input for sheet data. | MVP/Clunky |
| **Site Settings** | Admin-controlled branding, registration toggles, etc. | Implemented |
| **SRD Import** | Automatic population of spells, classes, and items. | Fully Working |

---

## 💡 Lessons Learned & "The Restart Logic"

### What Went Well (The "Likes")
- **FastAPI/SvelteKit Combo:** The development speed is high, and the type-safety (even if manual on the bridge) helps.
- **Dockerized Dev Environment:** Makes it trivial to spin up the whole stack (DB, Redis, Nginx) with one command.
- **Compendium Design:** The ability to handle multiple "Systems" (D&D 5e vs 5.2) in one schema is a keeper.
- **Unified Messaging:** While "SQLite per campaign" sounds portable, the PostgreSQL approach was much easier to implement and didn't suffer the "N+1 database connections" problem.

### The Pain Points (The "Dislikes")
- **The "Wizard" Lie:** The `ARCHITECTURE.md` promises a "Character Creation Wizard," but the implementation is just a textarea for JSON. This is a primary driver for the restart—the UI/UX for character creation is currently too technical.
- **JSONB Versioning:** Handling "Dynamic Data" without a strict contract between Frontend and Backend leads to "undefined" errors in the UI whenever the schema changes. 
- **Folder Bloat:** `backend/api/` and `backend/services/` logic is starting to bleed into each other without clear boundaries.
- **SSR vs Client API:** SvelteKit SSR has had several "404" or "API unreachable" issues because of how Docker internode communication works (URL mapping differences inside vs outside the container).

### Strategy for Version 3.0
1. **Schema-First Characters:** Instead of a generic blob, use the `ComponentTemplate` system more strictly to generate UI forms automatically.
2. **True SvelteKit Power:** Move more logic into SvelteKit `load` functions and server-side actions to reduce "loading spinners."
3. **Advanced Messaging:** Implement real "Threaded" conversations or "Whispers" which were deferred in v2.0.

---

## 📂 Key File Map for Claude
- `backend/models/`: Core data structures.
- `backend/services/import_service.py`: How data gets into the system.
- `frontend/src/lib/api.js`: How the frontend talks to the backend.
- `frontend/src/lib/websocket.js`: Real-time logic.
- `ARCHITECTURE.md`: The "vision" document (mostly accurate, but check implementation for discrepancies).
