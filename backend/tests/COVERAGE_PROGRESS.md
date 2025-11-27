# Test Coverage Progress

## Goal: 80% Coverage

### Current Status: 71.00%
- Need: +9% more coverage
- That's approximately 57 more lines covered

### Module Breakdown

#### ✅ Already at Goal
- Models: 100%
- Schemas: 100%
- Services: 100%
- Main: 85.19%
- Database: 80.00%

#### 🎯 Focus Areas (Need Improvement)
1. **api/campaigns.py** - 43.90% (69 lines missing)
   - Helper functions not tested
   - Error paths in member management
   
2. **api/messages.py** - 42.03% (40 lines missing)
   - Character ownership validation
   - Time limit checks
   
3. **api/characters.py** - 49.35% (39 lines missing)
   - Helper function check_can_modify_character
   - DM permission checks

4. **api/auth.py** - 69.23% (16 lines missing)
   - Token creation edge cases

### Strategy
Add tests that specifically exercise:
- All helper functions
- All error/exception paths
- All conditional branches (if/else)
- Edge cases in validation logic
