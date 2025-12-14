# Quick Test Guide for Compendium System

## Testing the Implementation

### 1. Start the Backend

```bash
cd /home/ben/dndplaybypost
docker-compose up backend -d
docker-compose logs -f backend
```

**Expected Output:**
- Tables created successfully
- "Compendium is empty. Auto-importing SRD content..."
- "Component templates imported"
- "SRD import complete: {...stats...}"

### 2. Test API Endpoints

#### Get Compendium Stats
```bash
curl http://localhost:8000/api/v1/compendium/stats
```

**Expected Response:**
```json
{
  "total_items": 5,
  "by_type": {
    "class": 1,
    "race": 1,
    "spell": 1,
    "item": 1,
    "background": 1
  },
  "official_count": 5,
  "homebrew_count": 0
}
```

#### List All Classes
```bash
curl http://localhost:8000/api/v1/compendium/items/type/class
```

#### Search for Fireball
```bash
curl "http://localhost:8000/api/v1/compendium/items?query=fireball"
```

#### Get Component Templates
```bash
curl http://localhost:8000/api/v1/compendium/templates
```

### 3. Test Admin Endpoints

#### Check Import Status
```bash
curl http://localhost:8000/api/v1/admin/compendium/status
```

#### Reimport SRD (if needed)
```bash
curl -X POST http://localhost:8000/api/v1/admin/compendium/import/srd
```

### 4. Verify Database

```bash
docker-compose exec postgres psql -U dnd -d dnd_pbp -c "SELECT type, COUNT(*) FROM compendium_items GROUP BY type;"
```

**Expected Output:**
```
   type    | count 
-----------+-------
 class     |     1
 race      |     1
 spell     |     1
 item      |     1
 background|     1
```

## Common Issues

### Issue: Import fails on startup
**Solution:** Check logs for specific error. Ensure `backend/data/srd/` directory exists with JSON files.

### Issue: Tables not created
**Solution:** Check PostgreSQL connection. Ensure database exists and user has permissions.

### Issue: "Module not found" errors
**Solution:** Ensure all new files are in the correct locations and imports are correct.

## Next Steps

1. ✅ Verify auto-import works
2. ✅ Test API endpoints
3. ⏭️ Add more SRD content (expand the sample data)
4. ⏭️ Integrate with character creation
5. ⏭️ Build frontend compendium browser
