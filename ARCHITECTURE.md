# Architecture Overview

**Version:** 2.0 - Fresh Start  
**Date:** 2025-11-19

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              SvelteKit Frontend                        │ │
│  │  • Compendium Browser                                  │ │
│  │  • Character Creation Wizard                           │ │
│  │  • Character Sheet Viewer                              │ │
│  │  • Dice Roller UI                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↕ HTTP/WebSocket                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Nginx Reverse Proxy                     │
│  • Routes /api → Backend                                     │
│  • Routes / → Frontend                                       │
│  • Serves static files                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────┬──────────────────────────────────────┐
│   FastAPI Backend    │        Static Services               │
│  ┌────────────────┐  │  ┌────────────┬─────────────────┐   │
│  │  API Routes    │  │  │ PostgreSQL │     Redis       │   │
│  │ • /compendium  │  │  │            │                 │   │
│  │ • /characters  │  │  │ • users    │ • sessions      │   │
│  │ • /campaigns   │  │  │ • campaigns│ • cache         │   │
│  │ • /dice        │  │  │ • compendium• websockets   │   │
│  └────────────────┘  │  │ • characters                │   │
│  ┌────────────────┐  │  │            │                 │   │
│  │   Services     │  │  └────────────┴─────────────────┘   │
│  │ • dice_roller  │  │                                      │
│  │ • calculator   │  │  ┌──────────────────────────────┐   │
│  │ • auth         │  │  │   File Storage               │   │
│  └────────────────┘  │  │ • /uploads (images)          │   │
│                      │  │ • /exports (JSON/XML)        │   │
│                      │  │ • /campaigns (SQLite DBs)    │   │
│                      │  │ • /graphs (NetworkX future)  │   │
│                      │  └──────────────────────────────┘   │
└──────────────────────┴──────────────────────────────────────┘
```

## Technology Stack

### Frontend (SvelteKit)
- **Framework:** SvelteKit + TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Svelte Stores
- **HTTP Client:** Fetch API
- **WebSocket:** Native WebSocket API
- **Build Tool:** Vite
- **Testing:** Playwright

**Why SvelteKit?**
- Less boilerplate than React
- Great for learning (clear, readable syntax)
- Excellent performance
- Built-in routing
- Server-side rendering capability

### Backend (FastAPI)
- **Framework:** FastAPI 0.104+
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy 2.0 with asyncpg
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **WebSocket:** FastAPI native
- **Auth:** JWT tokens

**Why FastAPI?**
- Async/await support (great for real-time)
- Automatic API documentation
- Type hints everywhere
- Fast development
- Excellent for learning APIs

### Data Storage Strategy

#### PostgreSQL (Structured Data)
```sql
-- Core entities
users
campaigns
campaign_members
characters (with JSONB sheet_data)
compendium_entries (with JSONB content)
```

**Why PostgreSQL?**
- JSONB for flexibility (character sheets, compendium)
- Strong ACID guarantees
- Excellent indexing
- Full-text search
- Battle-tested reliability

#### SQLite (Per-Campaign Messages)
```
/data/campaigns/{campaign_id}/messages.db
```

**Why SQLite for messages?**
- Portability (entire campaign is one file)
- No network overhead
- Easy backups (copy one file)
- Can open with any SQLite tool
- Scales well for chat history

#### Redis (Session & Real-Time)
```
sessions:{user_id}
websocket:connections
cache:compendium:{type}
```

**Why Redis?**
- Fast session lookups
- WebSocket connection management
- Cache frequently accessed data
- Pub/sub for real-time events

#### NetworkX Graphs (Future: Relationships)
```
/data/graphs/{campaign_id}.gpickle
```

**Why NetworkX (not Neo4j)?**
- No licensing issues (Neo4j requires Enterprise for commercial)
- Simpler deployment (pure Python)
- Rich graph algorithms built-in
- Can visualize with matplotlib/plotly
- Easy to serialize (pickle)

## Data Flow Examples

### Example 1: Load Character Sheet

```
Browser                Frontend              Backend            Database
  │                       │                     │                  │
  │  Click "Character"    │                     │                  │
  │─────────────────────→ │                     │                  │
  │                       │  GET /characters/123│                  │
  │                       │────────────────────→ │                  │
  │                       │                     │  SELECT * FROM   │
  │                       │                     │  characters      │
  │                       │                     │─────────────────→│
  │                       │                     │  sheet_data JSON │
  │                       │                     │←─────────────────│
  │                       │  Character JSON     │                  │
  │                       │←────────────────────│                  │
  │                       │                     │                  │
  │  [Calculate modifiers]│                     │                  │
  │  [Render sheet]       │                     │                  │
  │←─────────────────────│                     │                  │
```

### Example 2: Roll Attack

```
Browser                Frontend              Backend            Dice Roller
  │                       │                     │                  │
  │  Click "Greataxe"     │                     │                  │
  │─────────────────────→ │                     │                  │
  │                       │  POST /dice/roll    │                  │
  │                       │  {                  │                  │
  │                       │   expr: "1d20+@str" │                  │
  │                       │   values: {str: 5}  │                  │
  │                       │  }                  │                  │
  │                       │────────────────────→│                  │
  │                       │                     │  roll("1d20+5")  │
  │                       │                     │─────────────────→│
  │                       │                     │  RollResult      │
  │                       │                     │  total: 23       │
  │                       │                     │  details: [18]+5 │
  │                       │                     │←─────────────────│
  │                       │  RollResult JSON    │                  │
  │                       │←────────────────────│                  │
  │                       │                     │                  │
  │  [Display: 23 hit]    │                     │                  │
  │←─────────────────────│                     │                  │
```

### Example 3: Use Feature (Rage)

```
Browser           Frontend        Backend         Database        Character
  │                  │                │               │             Calculator
  │  Click [Rage]    │                │               │                │
  │─────────────────→│                │               │                │
  │                  │  PATCH         │               │                │
  │                  │  /characters/  │               │                │
  │                  │    123/        │               │                │
  │                  │    features/   │               │                │
  │                  │    rage/use    │               │                │
  │                  │───────────────→│               │                │
  │                  │                │  UPDATE       │                │
  │                  │                │  characters   │                │
  │                  │                │  SET sheet_   │                │
  │                  │                │  data = ...   │                │
  │                  │                │──────────────→│                │
  │                  │                │               │                │
  │                  │                │  Calculate    │                │
  │                  │                │  new stats    │                │
  │                  │                │──────────────────────────────→│
  │                  │                │               │  Apply effects:│
  │                  │                │               │  • uses: 2→1   │
  │                  │                │               │  • +2 damage   │
  │                  │                │               │  • advantage   │
  │                  │                │               │  • resistance  │
  │                  │                │  Updated JSON │←───────────────│
  │                  │                │←──────────────│                │
  │                  │  Character     │               │                │
  │                  │  with active   │               │                │
  │                  │  Rage effects  │               │                │
  │                  │←───────────────│               │                │
  │                  │                │               │                │
  │  [Show Rage      │                │               │                │
  │   active badge]  │                │               │                │
  │  [Update attack  │                │               │                │
  │   bonuses]       │                │               │                │
  │←─────────────────│                │               │                │
```

## API Design Principles

### RESTful Endpoints

```
GET    /api/v1/compendium/classes          # List classes
GET    /api/v1/compendium/classes/fighter  # Get Fighter details
POST   /api/v1/characters                  # Create character
GET    /api/v1/characters/123              # Get character
PATCH  /api/v1/characters/123              # Update character
POST   /api/v1/dice/roll                   # Roll dice
```

### Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-19T10:30:00Z",
    "version": "2.0"
  }
}
```

### Error Format

```json
{
  "success": false,
  "error": {
    "code": "CHARACTER_NOT_FOUND",
    "message": "Character with ID 123 not found",
    "details": {}
  }
}
```

## Security Architecture

### Authentication Flow

```
1. User logs in → receives JWT token
2. Frontend stores token in localStorage
3. Every request includes: Authorization: Bearer <token>
4. Backend validates token on each request
5. Token expires after 7 days (configurable)
```

### Authorization (RBAC)

```python
# Role hierarchy
DM > Player > Observer

# DM can:
- Modify any character
- View hidden content
- Control game state
- Manage campaign

# Player can:
- View/edit own characters
- View public content
- Post messages

# Observer can:
- View public content only
- Read-only access
```

### Data Protection

- **Passwords:** Bcrypt hashing
- **JWTs:** Signed with secret key
- **Database:** Parameterized queries (SQL injection protection)
- **Input:** Validated with Pydantic models
- **CORS:** Restricted to known origins

## Performance Considerations

### Backend Optimization

```python
# Use async/await everywhere
async def get_character(character_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    return result.scalar_one_or_none()

# Eager loading to avoid N+1
result = await db.execute(
    select(Character)
    .options(selectinload(Character.player))
    .where(Character.campaign_id == campaign_id)
)
```

### Frontend Optimization

```typescript
// Lazy load heavy components
const CharacterSheet = lazy(() => import('./CharacterSheet.svelte'));

// Cache API responses
let cachedClasses = null;
if (!cachedClasses) {
  cachedClasses = await getClasses();
}

// Debounce search
let searchTimeout;
function handleSearch(query) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    performSearch(query);
  }, 300);
}
```

### Database Indexing

```sql
-- Critical indexes for Phase 0
CREATE INDEX idx_characters_campaign ON characters(campaign_id);
CREATE INDEX idx_compendium_type ON compendium_entries(entry_type);
CREATE INDEX idx_compendium_name ON compendium_entries(name);
CREATE INDEX idx_compendium_search ON compendium_entries USING GIN(search_vector);
```

## Deployment Architecture

### Docker Compose Layout

```
┌─────────────────────────────────────────────────────────┐
│                      Host Machine                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Docker Network: dnd-network           │ │
│  │                                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │ │
│  │  │  nginx   │  │ backend  │  │   frontend    │   │ │
│  │  │  :80     │→ │  :8000   │  │    :3000      │   │ │
│  │  │  :443    │  └──────────┘  └───────────────┘   │ │
│  │  └──────────┘        ↓              ↓             │ │
│  │                      ↓              ↓             │ │
│  │  ┌──────────────────┴──────────────┘             │ │
│  │  │                                                │ │
│  │  ↓                                                │ │
│  │  ┌──────────┐  ┌──────────┐                      │ │
│  │  │ postgres │  │  redis   │                      │ │
│  │  │  :5432   │  │  :6379   │                      │ │
│  │  └──────────┘  └──────────┘                      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Volumes:                                                │
│  • postgres_data → /var/lib/postgresql/data             │
│  • redis_data → /data                                    │
│  • ./data/uploads → /app/data/uploads                    │
│  • ./data/campaigns → /app/data/campaigns                │
└─────────────────────────────────────────────────────────┘
```

### Port Mapping

```
Host           Container      Service
80     →       80             nginx (HTTP)
443    →       443            nginx (HTTPS)
5432   →       5432           postgres
6379   →       6379           redis
```

## Scaling Considerations (Future)

### Horizontal Scaling

```
When you need to scale:

1. Multiple backend containers
   ├─ backend-1
   ├─ backend-2
   └─ backend-3
   
2. Load balancer in front
   nginx → round-robin to backends
   
3. Shared state in Redis
   - All backends share Redis
   - WebSocket pub/sub for syncing
   
4. Database connection pooling
   - Each backend has connection pool
   - PostgreSQL handles concurrent connections
```

### Vertical Scaling (Easier)

```
For small-medium deployments:

1. Raspberry Pi 4 (4GB RAM): ~10 concurrent users
2. VPS (8GB RAM): ~50 concurrent users
3. Dedicated server (16GB RAM): ~200 concurrent users
```

## Development vs Production

### Development Mode

```yaml
# docker-compose.yml
environment:
  - DEBUG=true
  - ENVIRONMENT=development
  
volumes:
  - ./backend:/app  # Hot reload
  - ./frontend:/app # Hot reload
```

### Production Mode

```yaml
# docker-compose.yml
environment:
  - DEBUG=false
  - ENVIRONMENT=production
  
# No volume mounts (use built images)
restart: unless-stopped
```

## Monitoring & Health Checks

### Health Check Endpoints

```
GET /health
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "disk_space": "45.2 GB free"
}

GET /metrics
{
  "active_users": 5,
  "total_characters": 23,
  "total_campaigns": 4,
  "uptime_seconds": 86400
}
```

## Backup Strategy

```
Daily backups:
1. PostgreSQL dump → /backups/db_YYYYMMDD.sql.gz
2. Campaign SQLite files → /backups/campaigns_YYYYMMDD.tar.gz
3. Uploaded files → /backups/uploads_YYYYMMDD.tar.gz

Retention: 30 days
Storage: Local + optional cloud sync
```

## Summary

This architecture provides:
- ✅ Simple deployment (Docker Compose)
- ✅ Easy development (hot reload, clear separation)
- ✅ Good performance (async, caching, indexes)
- ✅ Data portability (SQLite messages, JSON export)
- ✅ Extensibility (plugins, custom content)
- ✅ Reliability (health checks, backups, restarts)

**Next Step:** Implement Phase 0.1 - Compendium Browser

See CLAUDE.MD for detailed implementation guide.
