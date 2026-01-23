# IntelliEats Setup Guide

Complete setup instructions for development and deployment.

---

## Prerequisites

### Required Software

- **Python 3.12+**
- **Git**
- **Text editor** (VS Code recommended)

### Required API Keys

1. **Anthropic Claude API Key**
   - Sign up: https://console.anthropic.com/
   - Navigate to API Keys
   - Create new key
   - Cost: ~$1-2/month for daily analysis

2. **USDA FoodData Central API Key**
   - Sign up: https://fdc.nal.usda.gov/api-key-signup.html
   - Free, instant approval
   - 1000 requests/hour limit

3. **Open Food Facts** - No API key required (public API)

---

## Development Setup (Local)

### 1. Clone Repository
```bash
git clone git@github.com:yourusername/intellieats.git
cd intellieats
```

---

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

---

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**If requirements.txt doesn't exist:**
```bash
pip install fastapi uvicorn sqlalchemy anthropic requests python-dotenv
pip freeze > requirements.txt
```

---

### 4. Configure Environment Variables

Create `.env` file in project root:
```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api-your-key-here

# USDA Food Database API
USDA_API_KEY=your-usda-key-here

# Optional: MyFitnessPal (not currently used)
MFP_USERNAME=your_username
MFP_PASSWORD=your_password
```

**⚠️ IMPORTANT:** Never commit `.env` to git!

Verify `.gitignore` includes:
```
.env
*.db
venv/
__pycache__/
```

---

### 5. Initialize Database
```bash
python database.py
```

This creates `nutrition_tracker.db` with all tables.

---

### 6. Create Test User
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

Note the user ID from the response (usually `1`).

---

### 7. Start the API Server

**Option A: Basic**
```bash
python api.py
```

**Option B: With auto-reload (recommended for development)**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/
# Should return: {"status":"healthy","app":"IntelliEats API","version":"0.1.0"}
```

---

### 8. Start the Frontend Server

Open a **new terminal**:
```bash
cd frontend
python3 -m http.server 3000
```

**Access the app:** http://localhost:3000

---

## Testing

### Test API Endpoints

**Health check:**
```bash
curl http://localhost:8000/
```

**Food search:**
```bash
curl "http://localhost:8000/foods/search?q=chicken"
```

**Barcode lookup:**
```bash
curl "http://localhost:8000/foods/barcode/0049000042566"
```

**Daily summary:**
```bash
curl "http://localhost:8000/entries/daily/1"
```

**AI analysis:**
```bash
curl -X POST "http://localhost:8000/analyze/daily/1"
```

---

### Test Frontend Features

1. **Daily Summary**
   - Should show 0 calories (no entries yet)
   - Progress bars should be empty

2. **Add Food**
   - Click "+ Add Food" under any meal
   - Search for "apple"
   - Select a food
   - Enter servings (e.g., "1")
   - Entry should appear in the meal section

3. **Delete Entry**
   - Click × button on any entry
   - Confirm deletion
   - Entry should disappear

4. **Claude Analysis**
   - Click 🤖 button
   - Should show "Analyzing..." then Claude's feedback

5. **Barcode Scanner**
   - Click 📷 button
   - On desktop: should show manual entry fallback
   - Enter barcode: `0049000042566`
   - Should look up Coca-Cola Zero Sugar

---

## Mobile Testing

### Access from Phone (Same Network)

1. **Find your computer's IP address:**

   **Linux/WSL:**
```bash
   ip addr show | grep "inet "
```

   **Mac:**
```bash
   ifconfig | grep "inet "
```

   **Windows (PowerShell):**
```powershell
   ipconfig | findstr IPv4
```

   Example result: `192.168.1.100`

2. **Update frontend API URL:**

   Edit `frontend/js/app.js`:
```javascript
   const API_BASE_URL = 'http://192.168.1.100:8000';  // Use your IP
```

3. **On your phone, open:**
```
   http://192.168.1.100:3000
```

4. **Test barcode scanner:**
   - Should request camera permission
   - Point at product barcode
   - Should detect and look up product

5. **Install as PWA:**
   - **iOS:** Safari → Share → Add to Home Screen
   - **Android:** Chrome → Menu → Add to Home Screen

---

## Raspberry Pi Deployment

### Prerequisites

- Raspberry Pi 3B+ or newer
- Raspberry Pi OS (64-bit recommended)
- Static IP or hostname on local network

---

### 1. Prepare Raspberry Pi
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git -y
```

---

### 2. Clone and Setup
```bash
# Clone repo
cd ~
git clone https://github.com/yourusername/intellieats.git
cd intellieats

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env file (use scp or create manually)
nano .env
# Paste your API keys
```

---

### 3. Initialize Database
```bash
python database.py
```

---

### 4. Create Systemd Services

**API Service:**

Create `/etc/systemd/system/intellieats-api.service`:
```ini
[Unit]
Description=IntelliEats API Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/intellieats
Environment="PATH=/home/pi/intellieats/venv/bin"
ExecStart=/home/pi/intellieats/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service:**

Create `/etc/systemd/system/intellieats-frontend.service`:
```ini
[Unit]
Description=IntelliEats Frontend Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/intellieats/frontend
ExecStart=/usr/bin/python3 -m http.server 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### 5. Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable intellieats-api
sudo systemctl enable intellieats-frontend

# Start services
sudo systemctl start intellieats-api
sudo systemctl start intellieats-frontend

# Check status
sudo systemctl status intellieats-api
sudo systemctl status intellieats-frontend
```

---

### 6. Access the App

**On local network:**
```
http://raspberrypi.local:3000
```

Or use the Pi's IP address:
```
http://192.168.1.XXX:3000
```

---

### 7. Update Frontend API URL

Since the Pi is the server, update `frontend/js/app.js`:
```javascript
// Option 1: Use relative localhost (works when accessing from Pi)
const API_BASE_URL = 'http://localhost:8000';

// Option 2: Use Pi's hostname (works from any device on network)
const API_BASE_URL = 'http://raspberrypi.local:8000';

// Option 3: Use Pi's IP address
const API_BASE_URL = 'http://192.168.1.XXX:8000';
```

**Restart frontend service:**
```bash
sudo systemctl restart intellieats-frontend
```

---

### 8. (Optional) Setup Nginx Reverse Proxy

This allows single port access and HTTPS:

**Install Nginx:**
```bash
sudo apt install nginx -y
```

**Create config `/etc/nginx/sites-available/intellieats`:**
```nginx
server {
    listen 80;
    server_name raspberrypi.local;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/intellieats /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Update frontend API URL:**
```javascript
const API_BASE_URL = 'http://raspberrypi.local/api';
```

Now access everything at: `http://raspberrypi.local`

---

## Maintenance

### View Logs

**API logs:**
```bash
sudo journalctl -u intellieats-api -f
```

**Frontend logs:**
```bash
sudo journalctl -u intellieats-frontend -f
```

---

### Update Application
```bash
cd ~/intellieats
git pull origin master
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart intellieats-api
sudo systemctl restart intellieats-frontend
```

---

### Backup Database
```bash
# Create backup
cp nutrition_tracker.db nutrition_tracker.db.backup

# Or automated backup script
cd ~
cat > backup_intellieats.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/intellieats/nutrition_tracker.db ~/backups/nutrition_tracker_$DATE.db
# Keep only last 30 backups
ls -t ~/backups/nutrition_tracker_*.db | tail -n +31 | xargs rm -f
EOF

chmod +x backup_intellieats.sh

# Add to crontab (daily at 3am)
crontab -e
# Add: 0 3 * * * /home/pi/backup_intellieats.sh
```

---

### Reset Database

**⚠️ Warning: This deletes all data!**
```bash
cd ~/intellieats
rm nutrition_tracker.db
python database.py

# Restart API
sudo systemctl restart intellieats-api
```

---

## Troubleshooting

### API Won't Start

**Check logs:**
```bash
sudo journalctl -u intellieats-api -n 50
```

**Common issues:**
- Port 8000 already in use: `sudo lsof -i :8000`
- Missing .env file: Check API keys are set
- Database locked: Stop API, delete `.db-journal` file

---

### Frontend Won't Load

**Check if server is running:**
```bash
curl http://localhost:3000
```

**Common issues:**
- Port 3000 already in use: `sudo lsof -i :3000`
- Wrong directory: Check WorkingDirectory in service file
- Firewall: `sudo ufw allow 3000`

---

### CORS Errors

**Symptom:** Browser console shows "blocked by CORS policy"

**Fix:** Update `api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: allow all
    # allow_origins=["http://raspberrypi.local:3000"],  # Production: specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Database Errors

**"Database is locked":**
```bash
# Stop API
sudo systemctl stop intellieats-api

# Remove journal file
rm nutrition_tracker.db-journal

# Restart
sudo systemctl start intellieats-api
```

**"Table doesn't exist":**
```bash
# Recreate database
rm nutrition_tracker.db
python database.py
sudo systemctl restart intellieats-api
```

---

### Claude API Errors

**"Could not resolve authentication method":**
- Check `.env` has `ANTHROPIC_API_KEY`
- Check key is valid at console.anthropic.com
- Verify API is loading .env (check `load_dotenv()` in api.py)

**"Rate limit exceeded":**
- Wait 1 minute and try again
- Check usage at console.anthropic.com
- Consider upgrading plan

---

### Barcode Scanner Not Working

**Desktop:** Expected - shows manual entry fallback

**Mobile - Camera not starting:**
- Must use HTTPS or localhost
- Check camera permissions in browser settings
- Try different browser (Chrome works best)

**Barcode not detected:**
- Ensure good lighting
- Hold steady, scan slowly
- Try manual entry as fallback

---

## Environment Variables Reference
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api-xxxxx    # Claude AI analysis
USDA_API_KEY=xxxxx                     # Food search

# Optional
MFP_USERNAME=xxxxx                     # Not currently used
MFP_PASSWORD=xxxxx                     # Not currently used
```

---

## Port Reference

- **3000** - Frontend (PWA)
- **8000** - Backend API
- **80** - Nginx reverse proxy (optional)
- **443** - HTTPS (future)

---

## File Permissions

Ensure correct ownership on Raspberry Pi:
```bash
cd ~/intellieats
sudo chown -R pi:pi .
chmod +x *.py
```

---

## Security Checklist

**Development (Current):**
- [x] `.env` in `.gitignore`
- [x] Database not in git
- [x] API keys in environment variables
- [ ] Password hashing (TODO)
- [ ] User authentication (TODO)
- [ ] HTTPS (TODO)

**Production (Future):**
- [ ] Enable HTTPS/SSL
- [ ] Restrict CORS to specific domain
- [ ] Implement rate limiting
- [ ] Add authentication middleware
- [ ] Use password hashing (bcrypt)
- [ ] Set up firewall rules
- [ ] Regular security updates

---

## Performance Tips

1. **Database optimization:**
```sql
   -- Add indexes for frequently queried fields
   CREATE INDEX idx_food_entries_user_date ON food_entries(user_id, eaten_at);
   CREATE INDEX idx_foods_barcode ON foods(barcode);
```

2. **API caching:**
   - Foods from USDA/OpenFoodFacts are cached in SQLite
   - First search is slow, subsequent searches are instant

3. **Frontend optimization:**
   - Search debounced (300ms)
   - Minimal DOM updates
   - Progressive enhancement

---

## Getting Help

**Issues:**
- Check logs first: `sudo journalctl -u intellieats-api -n 100`
- Search GitHub issues
- Create new issue with logs and error messages

**Documentation:**
- API Reference: `docs/API.md`
- Frontend Guide: `docs/FRONTEND.md`
- Architecture: `docs/ARCHITECTURE.md`

**Testing:**
- API docs (auto-generated): http://localhost:8000/docs
- Try example cURL commands from API.md

---

## Next Steps

1. ✅ Setup complete
2. Test all features on desktop
3. Test on mobile device
4. Deploy to Raspberry Pi
5. Use daily for 1 week
6. Review Claude's feedback
7. Iterate and improve

**Ready to track your nutrition!** 🎉