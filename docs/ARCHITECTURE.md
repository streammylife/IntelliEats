# IntelliEats Architecture

## Overview

IntelliEats is a self-hosted nutrition tracking application with AI-powered analysis. It consists of three main components:
```
┌─────────────────┐
│   PWA Frontend  │  (HTML/CSS/JS)
│   Port 3000     │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   FastAPI       │  (Python)
│   Port 8000     │
└────────┬────────┘
         │
         ├──────────► SQLite Database
         │            (nutrition_tracker.db)
         │
         ├──────────► Open Food Facts API
         │            (Barcode lookup)
         │
         ├──────────► USDA FoodData Central
         │            (Food search)
         │
         └──────────► Anthropic Claude API
                      (Nutrition analysis)
```

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** SQLite with SQLAlchemy ORM
- **APIs:**
  - Anthropic Claude (AI analysis)
  - Open Food Facts (barcode scanning)
  - USDA FoodData Central (food database)

### Frontend
- **Type:** Progressive Web App (PWA)
- **Structure:** Vanilla HTML/CSS/JavaScript
- **Features:**
  - Responsive mobile-first design
  - Camera access for barcode scanning
  - Offline-capable (via PWA)
  - Installable on iOS/Android

### Deployment
- **Target:** Raspberry Pi (always-on server)
- **Frontend Server:** Python HTTP server (port 3000)
- **API Server:** Uvicorn (port 8000)

## Data Flow

### Adding a Food Entry
```
1. User searches "chicken" in PWA
   ↓
2. Frontend → GET /foods/search?q=chicken
   ↓
3. API queries:
   - Local SQLite database (cached foods)
   - USDA API (if not cached)
   ↓
4. API returns combined results
   ↓
5. User selects food + enters servings
   ↓
6. Frontend → POST /entries
   ↓
7. API:
   - Creates food in DB (if needed)
   - Logs entry with calculated nutrition
   - Returns entry with food details
   ↓
8. Frontend refreshes daily summary
```

### Barcode Scanning
```
1. User clicks camera button
   ↓
2. Browser requests camera access
   ↓
3. Camera feed starts (or fallback to manual)
   ↓
4. Barcode detected: "0049000042566"
   ↓
5. Frontend → GET /foods/barcode/0049000042566
   ↓
6. API checks:
   - SQLite database (cached?)
   - If not found → Open Food Facts API
   ↓
7. Food data returned and cached in DB
   ↓
8. User confirms and logs entry
```

### AI Analysis
```
1. User clicks 🤖 button
   ↓
2. Frontend → POST /analyze/daily/{user_id}
   ↓
3. API:
   - Queries all entries for today
   - Calculates totals vs goals
   - Formats data for Claude
   ↓
4. API → Claude API with prompt
   ↓
5. Claude analyzes nutrition and returns feedback
   ↓
6. API saves analysis to database
   ↓
7. Frontend displays analysis in modal
```

## Database Schema

### Core Tables

**users**
- User accounts and nutritional goals
- Fields: username, email, password_hash, calorie_goal, protein_goal, etc.

**foods**
- Food database (cached from APIs + user-created)
- Fields: name, brand, barcode, serving_size, calories, macros, source
- Indexed on: barcode (for fast lookup)

**food_entries**
- Daily food logs
- Fields: user_id, food_id, servings, meal_type, eaten_at, calculated_nutrition
- Indexed on: user_id, eaten_at (for daily queries)

**analyses**
- Stored AI analyses
- Fields: user_id, analysis_type, analysis_date, analysis_text, summary_stats

### Relationships
```
users (1) ──< (many) food_entries
foods (1) ──< (many) food_entries
users (1) ──< (many) analyses
```

## API Architecture

### Endpoint Organization
```
/                          # Health check
/users                     # User management
/foods                     # Food database
  /search                  # Search foods
  /barcode/{barcode}       # Barcode lookup
/entries                   # Food logging
  /daily/{user_id}         # Daily summary
  /{entry_id}              # Delete entry
/analyze                   # AI analysis
  /daily/{user_id}         # Analyze day
```

### Key Design Decisions

**1. Caching Strategy**
- All API food lookups are cached in local database
- Reduces external API calls
- Faster subsequent lookups
- Works offline for previously seen foods

**2. Eager Loading**
- Food relationships loaded with `.options(joinedload())`
- Prevents N+1 query problems
- Single query fetches entry + food data

**3. Calculated Nutrition**
- Nutrition values calculated on entry creation
- Stored in food_entries table (denormalized)
- Fast daily summary queries (no joins needed)

**4. CORS Configuration**
- Allow all origins during development
- Will restrict to specific domain in production

## Security Considerations

### Current State (Development)

⚠️ **Not production-ready**

- Passwords stored as plaintext (TODO: bcrypt hashing)
- No authentication/authorization
- Hardcoded USER_ID in frontend
- CORS allows all origins
- API keys in .env file (not in git)

### Production Roadmap

- [ ] Password hashing (bcrypt)
- [ ] JWT-based authentication
- [ ] User sessions
- [ ] HTTPS/SSL certificates
- [ ] Rate limiting
- [ ] Input validation/sanitization
- [ ] CORS restricted to domain

## Performance Considerations

### Current Optimizations

- SQLite with eager loading (joinedload)
- API response caching in local database
- Frontend debouncing on search (300ms)
- Progressive enhancement (works without JS)

### Future Optimizations

- Database indexes on frequently queried fields
- Redis caching layer for hot data
- Connection pooling for concurrent users
- CDN for static assets
- Image optimization for food photos

## Development Workflow
```
1. Create feature branch from master
2. Develop locally (WSL on Windows)
3. Test on desktop browser (localhost)
4. Test on mobile device (local network)
5. Merge to master when tested
6. Deploy to Raspberry Pi
```

## Deployment Architecture

### Raspberry Pi Setup (Future)
```
Raspberry Pi
├── IntelliEats/
│   ├── backend (Python/FastAPI)
│   ├── frontend (static files)
│   └── nutrition_tracker.db
├── systemd services
│   ├── intellieats-api.service
│   └── intellieats-frontend.service
└── nginx (reverse proxy)
    └── HTTPS termination
```

### Network Access

- Local network: `http://raspberrypi.local:8000`
- Port forwarding: Access from anywhere (with proper security)
- Or Tailscale/VPN for secure remote access

## File Structure
```
intellieats/
├── api.py                  # FastAPI server
├── database.py             # SQLAlchemy models
├── food_apis.py            # External API integrations
├── .env                    # API keys (not in git)
├── requirements.txt        # Python dependencies
├── nutrition_tracker.db    # SQLite database
├── frontend/
│   ├── index.html          # Main PWA page
│   ├── manifest.json       # PWA configuration
│   ├── css/
│   │   └── style.css       # All styles
│   ├── js/
│   │   ├── app.js          # Main app logic
│   │   └── scanner.js      # Barcode scanning
│   └── images/
│       ├── icon-192.png    # PWA icon
│       └── icon-512.png    # PWA icon
└── docs/
    ├── ARCHITECTURE.md     # This file
    ├── API.md              # API reference
    ├── FRONTEND.md         # Frontend guide
    └── SETUP.md            # Setup instructions
```

## Key Technologies Explained

### FastAPI
- Modern Python web framework
- Automatic API documentation (/docs)
- Type hints for validation
- Async support (future scalability)

### SQLAlchemy
- Python ORM (Object-Relational Mapping)
- Relationships defined in code
- Database-agnostic (easy to migrate from SQLite)

### Progressive Web App (PWA)
- Installable on mobile home screen
- Works offline (when configured)
- Native-like experience
- No app store required

### Anthropic Claude
- Large language model API
- Analyzes nutrition patterns
- Provides personalized feedback
- Contextual recommendations

## Future Enhancements

### Planned Features
- [ ] User authentication/login
- [ ] Multi-user support
- [ ] Weekly/monthly trends
- [ ] Weight tracking correlation
- [ ] Meal planning suggestions
- [ ] Recipe analysis
- [ ] Photo-based food logging
- [ ] Social features (optional sharing)
- [ ] Export data (CSV, PDF reports)
- [ ] Integration with fitness trackers

### Technical Improvements
- [ ] Move to PostgreSQL for multi-user
- [ ] Add Redis for caching
- [ ] Implement proper authentication
- [ ] Add comprehensive test suite
- [ ] CI/CD pipeline
- [ ] Docker containerization
- [ ] Kubernetes deployment (if scaling)