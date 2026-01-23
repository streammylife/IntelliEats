# IntelliEats API Reference

Base URL: `http://localhost:8000`

API documentation is auto-generated and available at: `http://localhost:8000/docs`

---

## Authentication

⚠️ **Currently no authentication** - This is a development version for single-user local use.

All endpoints currently use hardcoded `user_id=1` in the frontend.

**Future:** JWT-based authentication with login/logout endpoints.

---

## Endpoints

### Health Check

#### `GET /`

Check if API is running.

**Response:**
```json
{
  "status": "healthy",
  "app": "IntelliEats API",
  "version": "0.1.0"
}
```

---

## User Management

### Create User

#### `POST /users`

Create a new user account.

**Request Body:**
```json
{
  "username": "mjohnson",
  "email": "mj@example.com",
  "password": "testpass123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "mjohnson",
  "email": "mj@example.com",
  "calorie_goal": 2000,
  "protein_goal": 150.0,
  "carb_goal": 200.0,
  "fat_goal": 65.0
}
```

**Errors:**
- `400` - Invalid input
- `409` - Email already exists

---

### Get User

#### `GET /users/{user_id}`

Get user details and goals.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "mjohnson",
  "email": "mj@example.com",
  "calorie_goal": 2000,
  "protein_goal": 150.0,
  "carb_goal": 200.0,
  "fat_goal": 65.0
}
```

**Errors:**
- `404` - User not found

---

## Food Database

### Search Foods

#### `GET /foods/search?q={query}`

Search for foods by name in local database and USDA.

**Parameters:**
- `q` (required) - Search query (e.g., "chicken")

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Chicken Breast",
    "brand": "Generic",
    "calories": 165.0,
    "protein": 31.0,
    "carbohydrates": 0.0,
    "fat": 3.6,
    "source": "user",
    "in_database": true
  },
  {
    "id": null,
    "name": "Chicken, ground",
    "brand": "",
    "calories": 201,
    "protein": 27.14,
    "carbohydrates": 0,
    "fat": 2.893,
    "source": "usda",
    "in_database": false
  }
]
```

**Notes:**
- Results include both local database and USDA API
- `in_database: true` means it's cached locally
- `in_database: false` means it's from USDA (will be cached on first use)

---

### Lookup by Barcode

#### `GET /foods/barcode/{barcode}`

Look up food by barcode (UPC/EAN).

**Parameters:**
- `barcode` (required) - Barcode number (e.g., "0049000042566")

**Response:** `200 OK`
```json
{
  "id": 5,
  "name": "Coca-Cola Zero Sugar",
  "brand": "Coke Zero",
  "barcode": "0049000042566",
  "serving_size": "100g",
  "calories": 0.0,
  "protein": 0.0,
  "carbohydrates": 0.0,
  "fat": 0.0
}
```

**Errors:**
- `404` - Product not found in Open Food Facts database

**Notes:**
- First checks local database
- If not found, queries Open Food Facts API
- Automatically caches result in local database

---

### Create Food

#### `POST /foods`

Add a custom food to the database.

**Request Body:**
```json
{
  "name": "Homemade Protein Shake",
  "brand": null,
  "barcode": null,
  "serving_size": "1 shake",
  "serving_size_grams": 350,
  "calories": 250,
  "protein": 40,
  "carbohydrates": 15,
  "fat": 5,
  "fiber": 2,
  "sugar": 5,
  "sodium": 200,
  "source": "user"
}
```

**Response:** `201 Created`
```json
{
  "id": 10,
  "name": "Homemade Protein Shake",
  "brand": null,
  "barcode": null,
  "serving_size": "1 shake",
  "calories": 250,
  "protein": 40,
  "carbohydrates": 15,
  "fat": 5
}
```

---

## Food Entries (Logging)

### Log Food Entry

#### `POST /entries?user_id={user_id}`

Log a food entry for a meal.

**Parameters:**
- `user_id` (required) - User ID

**Request Body:**
```json
{
  "food_id": 1,
  "servings": 1.5,
  "meal_type": "lunch",
  "eaten_at": "2026-01-23T12:30:00"
}
```

**Fields:**
- `food_id` - ID of food from database
- `servings` - Number of servings (can be decimal)
- `meal_type` - One of: `breakfast`, `lunch`, `dinner`, `snack`
- `eaten_at` - (optional) Timestamp, defaults to now

**Response:** `201 Created`
```json
{
  "id": 15,
  "food": {
    "id": 1,
    "name": "Chicken Breast",
    "brand": "Generic",
    "calories": 165.0,
    "protein": 31.0,
    "carbohydrates": 0.0,
    "fat": 3.6
  },
  "servings": 1.5,
  "meal_type": "lunch",
  "eaten_at": "2026-01-23T12:30:00",
  "calories": 247.5,
  "protein": 46.5,
  "carbohydrates": 0.0,
  "fat": 5.4
}
```

**Notes:**
- Nutrition values are automatically calculated: `food_nutrition * servings`
- Entry includes full food object for display

**Errors:**
- `404` - Food not found

---

### Get Daily Summary

#### `GET /entries/daily/{user_id}?date_str={date}`

Get nutrition summary and all entries for a specific date.

**Parameters:**
- `user_id` (required) - User ID
- `date_str` (optional) - Date in format `YYYY-MM-DD`, defaults to today

**Response:** `200 OK`
```json
{
  "date": "2026-01-23",
  "total_calories": 1847,
  "total_protein": 95.3,
  "total_carbs": 198.2,
  "total_fat": 65.3,
  "calorie_goal": 2000,
  "protein_goal": 150.0,
  "carb_goal": 200.0,
  "fat_goal": 65.0,
  "entries": [
    {
      "id": 1,
      "food": {
        "id": 2,
        "name": "Oatmeal",
        "brand": null,
        "calories": 150,
        "protein": 5
      },
      "servings": 1,
      "meal_type": "breakfast",
      "eaten_at": "2026-01-23T08:00:00",
      "calories": 150,
      "protein": 5,
      "carbohydrates": 27,
      "fat": 3
    }
  ]
}
```

**Notes:**
- Returns all entries for the day grouped by meal type
- Includes total nutrition vs goals
- Entries include full food details

---

### Delete Entry

#### `DELETE /entries/{entry_id}`

Delete a food entry.

**Response:** `200 OK`
```json
{
  "status": "deleted",
  "id": 15
}
```

**Errors:**
- `404` - Entry not found

---

## AI Analysis

### Analyze Daily Nutrition

#### `POST /analyze/daily/{user_id}?date_str={date}`

Get AI-powered analysis of daily nutrition using Claude.

**Parameters:**
- `user_id` (required) - User ID
- `date_str` (optional) - Date in format `YYYY-MM-DD`, defaults to today

**Response:** `200 OK`
```json
{
  "analysis": "## Overall Assessment\n\nYou hit your calorie target well today (1,847/1,850), but protein intake is low at 95g vs your 150g goal...",
  "date": "2026-01-23",
  "totals": {
    "calories": 1847,
    "protein": 95.3,
    "carbs": 198.2,
    "fat": 65.3
  }
}
```

**Notes:**
- Analysis is generated by Claude AI based on the day's nutrition
- Includes assessment, recommendations, and specific suggestions
- Analysis is saved to database for history

**Errors:**
- `500` - Analysis failed (check Claude API key)

**Example Analysis Output:**
```
Overall Assessment:
You hit your calorie target well today (1,847 vs 1,850 goal), but protein 
intake is significantly low at 95g versus your 150g target.

What You Did Well:
- Excellent calorie accuracy
- Strong dinner with high-quality protein
- Good variety of whole foods

Areas for Improvement:
1. Protein deficiency (critical): Missing 55g of protein
2. High sodium: At 3,245mg, well above recommended 2,300mg
3. Unbalanced protein distribution

Specific Suggestions for Tomorrow:
- Add protein to breakfast (Greek yogurt or eggs)
- Double protein portion at lunch
- Consider a protein shake post-workout
```

---

## External API Integrations

### Open Food Facts

**Used for:** Barcode scanning  
**Rate Limit:** Unlimited (public API)  
**Endpoint:** `https://world.openfoodfacts.org/api/v0/product/{barcode}.json`

**Coverage:**
- 2+ million products worldwide
- Best for packaged foods
- Community-maintained

---

### USDA FoodData Central

**Used for:** Food search  
**Rate Limit:** 1000 requests/hour (with API key)  
**Setup:** Get free API key at https://fdc.nal.usda.gov/api-key-signup.html

**Coverage:**
- 600K+ foods
- Raw ingredients, restaurant chains
- Government-maintained

---

### Anthropic Claude

**Used for:** AI nutrition analysis  
**Rate Limit:** Based on your plan  
**Setup:** Get API key at https://console.anthropic.com/

**Model:** `claude-sonnet-4-20250514`  
**Max tokens:** 1000 per analysis

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `409` - Conflict (duplicate)
- `500` - Internal Server Error

---

## Rate Limiting

**Current:** No rate limiting (single-user development)

**Future:** Rate limiting will be added for production:
- 100 requests/minute per user
- 1000 requests/hour per user
- Caching will reduce API calls to external services

---

## CORS Configuration

**Current:** Allows all origins (`*`)

**Production:** Will be restricted to specific domain
```python
allow_origins=["https://yourdomain.com"]
```

---

## Testing the API

### Using cURL
```bash
# Health check
curl http://localhost:8000/

# Create user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123"}'

# Search foods
curl "http://localhost:8000/foods/search?q=chicken"

# Barcode lookup
curl http://localhost:8000/foods/barcode/0049000042566

# Get daily summary
curl http://localhost:8000/entries/daily/1

# Analyze nutrition
curl -X POST http://localhost:8000/analyze/daily/1
```

### Using the Interactive Docs

FastAPI provides automatic interactive documentation:

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

You can test all endpoints directly in the browser!

---

## Database Schema (Reference)

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME,
    calorie_goal INTEGER DEFAULT 2000,
    protein_goal FLOAT DEFAULT 150.0,
    carb_goal FLOAT DEFAULT 200.0,
    fat_goal FLOAT DEFAULT 65.0
);
```

### Foods Table
```sql
CREATE TABLE foods (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    brand VARCHAR(100),
    barcode VARCHAR(50) UNIQUE,
    serving_size VARCHAR(50),
    serving_size_grams FLOAT,
    calories FLOAT NOT NULL,
    protein FLOAT DEFAULT 0,
    carbohydrates FLOAT DEFAULT 0,
    fat FLOAT DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    sugar FLOAT DEFAULT 0,
    sodium FLOAT DEFAULT 0,
    source VARCHAR(50),
    source_id VARCHAR(100),
    created_at DATETIME,
    is_verified BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_foods_barcode ON foods(barcode);
```

### Food Entries Table
```sql
CREATE TABLE food_entries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    eaten_at DATETIME NOT NULL,
    meal_type VARCHAR(20),
    servings FLOAT DEFAULT 1.0,
    calories FLOAT,
    protein FLOAT,
    carbohydrates FLOAT,
    fat FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (food_id) REFERENCES foods(id)
);
CREATE INDEX idx_food_entries_user_date ON food_entries(user_id, eaten_at);
```

### Analyses Table
```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    analysis_type VARCHAR(20),
    analysis_date DATETIME NOT NULL,
    analysis_text VARCHAR(5000),
    avg_calories FLOAT,
    avg_protein FLOAT,
    avg_carbs FLOAT,
    avg_fat FLOAT,
    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```