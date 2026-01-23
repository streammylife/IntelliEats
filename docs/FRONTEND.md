# IntelliEats Frontend Guide

The IntelliEats frontend is a Progressive Web App (PWA) built with vanilla HTML, CSS, and JavaScript.

---

## Overview

**Type:** Progressive Web App (PWA)  
**Framework:** None - Vanilla JavaScript  
**Design:** Mobile-first, responsive  
**Installation:** Can be installed on iOS/Android home screen

---

## File Structure
```
frontend/
├── index.html          # Main app page
├── manifest.json       # PWA configuration
├── css/
│   └── style.css       # All styles (no preprocessor)
├── js/
│   ├── app.js          # Main application logic
│   └── scanner.js      # Barcode scanning
└── images/
    ├── icon-192.png    # PWA icon (small)
    └── icon-512.png    # PWA icon (large)
```

---

## Architecture

### Component Breakdown

**index.html**
- Semantic HTML structure
- Modal dialogs (add food, scan barcode, analysis)
- Progress bars and macro cards
- Meal sections (breakfast, lunch, dinner, snacks)

**style.css**
- CSS custom properties (variables) for theming
- Mobile-first responsive design
- Smooth animations and transitions
- iOS safe area support

**app.js**
- API communication
- State management
- Event handling
- UI updates

**scanner.js**
- Camera access
- Barcode detection
- Fallback for unsupported devices

---

## Key Features

### 1. Daily Summary

Displays today's nutrition with progress bars:
- Calories: current / goal
- Protein: current / goal
- Carbs: current / goal
- Fat: current / goal

Progress bars change color when over goal (warning orange).

**Implementation:**
```javascript
function updateDailySummary(data) {
    document.getElementById('caloriesValue').textContent = Math.round(data.total_calories);
    updateProgressBar('caloriesProgress', data.total_calories, data.calorie_goal);
}
```

---

### 2. Food Search

Real-time search with 300ms debounce:
```javascript
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchFoods(e.target.value);
    }, 300);
});
```

**Why debounce?**
- Prevents API spam while typing
- Waits for user to finish typing
- Better performance

---

### 3. Adding Food

**Flow:**
1. User clicks "+ Add Food" button
2. Modal opens with search input
3. User types food name
4. Results appear from local DB + USDA
5. User selects food
6. Prompt asks for servings
7. Entry logged via API
8. Page refreshes with new entry

**Key code:**
```javascript
async function selectFood(food) {
    const servings = prompt('How many servings?', '1');
    
    // If food not in DB, create it first
    if (!food.id) {
        const response = await fetch(`${API_BASE_URL}/foods`, {
            method: 'POST',
            body: JSON.stringify(food)
        });
        foodId = (await response.json()).id;
    }
    
    // Log the entry
    await fetch(`${API_BASE_URL}/entries?user_id=${USER_ID}`, {
        method: 'POST',
        body: JSON.stringify({
            food_id: foodId,
            servings: parseFloat(servings),
            meal_type: currentMealType
        })
    });
    
    // Refresh UI
    await loadDailySummary();
}
```

---

### 4. Barcode Scanning

Uses browser's BarcodeDetector API (Chrome/Edge only):
```javascript
if ('BarcodeDetector' in window) {
    const detector = new BarcodeDetector({
        formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e']
    });
    
    const barcodes = await detector.detect(canvas);
    if (barcodes.length > 0) {
        onBarcodeDetected(barcodes[0].rawValue);
    }
}
```

**Fallback:**
- If BarcodeDetector not supported (Safari, Firefox)
- Shows manual input field
- User enters barcode manually

**Supported formats:**
- EAN-13 (most common)
- EAN-8 (short version)
- UPC-A (US/Canada)
- UPC-E (compressed UPC)

---

### 5. Claude Analysis

**Flow:**
1. User clicks 🤖 button
2. Modal opens with "Analyzing..." message
3. API call to `/analyze/daily/{user_id}`
4. Claude analyzes today's nutrition
5. Analysis displayed in modal

**Implementation:**
```javascript
async function analyzeNutrition() {
    openModal('analysisModal');
    
    const response = await fetch(`${API_BASE_URL}/analyze/daily/${USER_ID}`, {
        method: 'POST'
    });
    
    const result = await response.json();
    document.getElementById('analysisContent').innerHTML = result.analysis;
}
```

---

## State Management

### Global State
```javascript
const API_BASE_URL = 'http://localhost:8000';
const USER_ID = 1;

let currentMealType = '';   // Which meal user is adding to
let dailyData = null;        // Cached daily summary
```

**Why simple state?**
- Small app, no complex state needed
- React/Vue would be overkill
- Easy to understand and debug

---

### Data Flow
```
Initial Load:
loadDailySummary()
  ↓
fetch('/entries/daily/1')
  ↓
dailyData = response
  ↓
updateDailySummary(dailyData)
updateMealEntries(dailyData.entries)

User Action (Add Food):
selectFood(food)
  ↓
POST /entries
  ↓
loadDailySummary()  // Refresh
```

---

## API Communication

All API calls use `fetch` with `async/await`:
```javascript
async function loadDailySummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/entries/daily/${USER_ID}`);
        
        if (!response.ok) throw new Error('Failed to load');
        
        dailyData = await response.json();
        updateUI(dailyData);
        
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load data');
    }
}
```

**Error handling:**
- Try/catch blocks on all async functions
- Check `response.ok` before parsing JSON
- Display user-friendly error messages

---

## UI Components

### Modal System

All modals use same HTML structure:
```html
<div id="modalName" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Title</h2>
            <button class="close-btn" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
            <!-- Content here -->
        </div>
    </div>
</div>
```

**Open/close:**
```javascript
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}
```

**Styling:**
```css
.modal {
    display: none;  /* Hidden by default */
}

.modal.active {
    display: flex;  /* Show when active */
}
```

---

### Progress Bars

Dynamic width based on percentage:
```javascript
function updateProgressBar(elementId, value, goal) {
    const percentage = Math.min((value / goal) * 100, 100);
    const element = document.getElementById(elementId);
    
    element.style.width = `${percentage}%`;
    
    // Change color if over goal
    if (percentage > 100) {
        element.style.background = 'var(--warning)';
    }
}
```

---

### Meal Entries

Dynamically created from data:
```javascript
function createMealEntryElement(entry) {
    const div = document.createElement('div');
    div.className = 'meal-entry';
    div.innerHTML = `
        <div class="meal-entry-info">
            <div class="meal-entry-name">${entry.food.name}</div>
            <div class="meal-entry-macros">
                ${Math.round(entry.calories)} cal • 
                ${Math.round(entry.protein)}g P • 
                ${Math.round(entry.carbohydrates)}g C • 
                ${Math.round(entry.fat)}g F
            </div>
        </div>
        <button class="meal-entry-delete" onclick="deleteEntry(${entry.id})">×</button>
    `;
    return div;
}
```

---

## Styling

### Design System

**CSS Custom Properties:**
```css
:root {
    /* Colors */
    --primary: #4F46E5;
    --secondary: #10B981;
    --danger: #EF4444;
    --background: #F9FAFB;
    --text: #111827;
    
    /* Spacing */
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    
    /* Border Radius */
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
}
```

**Usage:**
```css
.button {
    background: var(--primary);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
}
```

---

### Mobile-First Design

Start with mobile, add desktop features:
```css
/* Mobile (default) */
.macros-grid {
    grid-template-columns: 1fr;
}

/* Desktop (override) */
@media (min-width: 640px) {
    .macros-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
```

---

### iOS Support

**Safe areas for notch:**
```css
body {
    padding-bottom: env(safe-area-inset-bottom);
}
```

**Status bar:**
```html
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

---

## Progressive Web App (PWA)

### manifest.json
```json
{
  "name": "IntelliEats - Nutrition Tracker",
  "short_name": "IntelliEats",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#4F46E5",
  "theme_color": "#4F46E5",
  "icons": [
    {
      "src": "/images/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**What this does:**
- Makes app installable on home screen
- Defines app name and icon
- Sets theme colors
- Configures display mode (fullscreen, no browser chrome)

---

### Installing on iOS

1. Open in Safari
2. Tap Share button (📤)
3. Tap "Add to Home Screen"
4. App appears on home screen like native app

---

### Installing on Android

1. Open in Chrome
2. Tap menu (⋮)
3. Tap "Add to Home Screen"
4. Or browser shows install prompt automatically

---

## Performance Optimizations

### 1. Debounced Search

Prevents excessive API calls:
```javascript
let searchTimeout;
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchFoods(e.target.value);
    }, 300);  // Wait 300ms after user stops typing
});
```

---

### 2. Cached Responses

API caches food lookups in database:
- First search: hits USDA API
- Subsequent searches: instant from SQLite

---

### 3. Minimal Reflows

Update DOM in batches:
```javascript
// BAD: Multiple reflows
entries.forEach(entry => {
    container.appendChild(createEntry(entry));
});

// GOOD: Single reflow
const fragment = document.createDocumentFragment();
entries.forEach(entry => {
    fragment.appendChild(createEntry(entry));
});
container.appendChild(fragment);
```

---

## Browser Support

**Required features:**
- Fetch API (all modern browsers)
- ES6+ JavaScript (arrow functions, async/await)
- CSS Grid and Flexbox
- CSS Custom Properties

**Optional features:**
- BarcodeDetector API (Chrome/Edge only)
- getUserMedia (camera access)
- Service Workers (for offline support - future)

**Tested on:**
- ✅ Chrome 90+
- ✅ Edge 90+
- ✅ Safari 14+ (iOS)
- ✅ Firefox 88+

---

## Development

### Running Locally
```bash
# Terminal 1: API server
cd ~/intellieats
source venv/bin/activate
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend server
cd ~/intellieats/frontend
python3 -m http.server 3000
```

**Access:** http://localhost:3000

---

### Making Changes

1. Edit files in `frontend/`
2. Refresh browser (no build step!)
3. Check console for errors

---

### Debugging

**Browser DevTools (F12):**
- **Console:** JavaScript errors and logs
- **Network:** API calls and responses
- **Application:** Storage, cache, manifest
- **Elements:** Inspect DOM and CSS

**Common issues:**
- CORS errors → Check API CORS settings
- 404 on API calls → Check API_BASE_URL
- Modal not opening → Check console for JS errors
- Entries not showing → Check food relationship in API

---

## Testing on Mobile

### Local Network Access

1. Find your computer's IP:
```bash
   ip addr show  # Linux/WSL
   ipconfig      # Windows
   ifconfig      # Mac
```

2. Note IP (e.g., `192.168.1.100`)

3. On phone, open browser to:
   - Frontend: `http://192.168.1.100:3000`
   - API: `http://192.168.1.100:8000`

4. **Update app.js:**
```javascript
   const API_BASE_URL = 'http://192.168.1.100:8000';
```

---

### Testing Barcode Scanner

1. Open on phone (needs real device, not desktop)
2. Click camera button
3. Allow camera access
4. Point at barcode
5. Should detect and look up product

**Test barcodes:**
- Coca-Cola: `0049000042566`
- Any product with UPC/EAN barcode

---

## Future Enhancements

### Planned Features

- [ ] **Offline support** - Service Worker caching
- [ ] **Photo logging** - Take pictures of meals
- [ ] **Meal templates** - Save common meals
- [ ] **Dark mode** - Auto-detect or toggle
- [ ] **Graphs/charts** - Visualize trends
- [ ] **Export data** - Download as CSV/PDF
- [ ] **Sharing** - Share meals with friends

### Technical Improvements

- [ ] **TypeScript** - Type safety
- [ ] **Build process** - Minification, bundling
- [ ] **Testing** - Unit and integration tests
- [ ] **Accessibility** - Screen reader support, keyboard nav
- [ ] **i18n** - Multi-language support

---

## Common Patterns

### Making API Calls
```javascript
async function apiCall() {
    try {
        const response = await fetch(`${API_BASE_URL}/endpoint`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Request failed');
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('API Error:', error);
        showError('Something went wrong');
        return null;
    }
}
```

### Updating UI
```javascript
function updateUI(data) {
    // Update text
    document.getElementById('element').textContent = data.value;
    
    // Update HTML
    document.getElementById('element').innerHTML = `<div>${data.value}</div>`;
    
    // Update styles
    document.getElementById('element').style.width = `${data.percentage}%`;
    
    // Add/remove classes
    element.classList.add('active');
    element.classList.remove('hidden');
}
```

### Event Listeners
```javascript
// Button click
button.addEventListener('click', handleClick);

// Input with debounce
let timeout;
input.addEventListener('input', (e) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        handleInput(e.target.value);
    }, 300);
});

// Form submit (prevent default)
form.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSubmit();
});
```

---

## Troubleshooting

**Problem:** Modal doesn't open  
**Solution:** Check `openModal()` function, verify modal ID matches

**Problem:** Search returns no results  
**Solution:** Check API is running, check Network tab for errors

**Problem:** Can't delete entries  
**Solution:** Check DELETE endpoint exists in API

**Problem:** Barcode scanner doesn't work  
**Solution:** Must use HTTPS or localhost, test on real mobile device

**Problem:** Icons not loading  
**Solution:** Create icon files or remove from manifest.json

**Problem:** CORS error  
**Solution:** Check API CORS middleware allows your origin

---

## Resources

**MDN Web Docs:** https://developer.mozilla.org/  
**Can I Use:** https://caniuse.com/ (browser support)  
**CSS Tricks:** https://css-tricks.com/  
**PWA Guide:** https://web.dev/progressive-web-apps/