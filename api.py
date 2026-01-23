#!/usr/bin/env python3
"""
IntelliEats API Server
FastAPI backend for nutrition tracking
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
import database

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="IntelliEats API",
    description="AI-powered nutrition tracking API",
    version="0.1.0"
)

# CORS middleware (so your PWA can call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = database.init_db()

def get_db():
    """Dependency to get database session"""
    db = database.get_session(engine)
    try:
        yield db
    finally:
        db.close()


# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    calorie_goal: int
    protein_goal: float
    carb_goal: float
    fat_goal: float
    
    class Config:
        from_attributes = True


class FoodCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: str
    serving_size_grams: float
    calories: float
    protein: float = 0
    carbohydrates: float = 0
    fat: float = 0
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0
    source: str = "user"


class FoodResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    barcode: Optional[str]
    serving_size: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    
    class Config:
        from_attributes = True


class FoodEntryCreate(BaseModel):
    food_id: int
    servings: float
    meal_type: str  # breakfast, lunch, dinner, snack
    eaten_at: Optional[datetime] = None


class FoodEntryResponse(BaseModel):
    id: int
    food: FoodResponse
    servings: float
    meal_type: str
    eaten_at: datetime
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    
    class Config:
        from_attributes = True


class DailySummary(BaseModel):
    date: date
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    calorie_goal: int
    protein_goal: float
    carb_goal: float
    fat_goal: float
    entries: List[FoodEntryResponse]


# Routes
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "IntelliEats API",
        "version": "0.1.0"
    }


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # TODO: Add password hashing
    db_user = database.User(
        username=user.username,
        email=user.email,
        password_hash=user.password  # TODO: Hash this!
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/foods", response_model=FoodResponse)
def create_food(food: FoodCreate, db: Session = Depends(get_db)):
    """Add a new food to the database"""
    db_food = database.Food(**food.dict())
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


@app.get("/foods/search")
def search_foods(q: str, db: Session = Depends(get_db)):
    """Search foods by name (checks local DB first, then USDA)"""
    # First search our local database
    local_foods = db.query(database.Food).filter(
        database.Food.name.ilike(f"%{q}%")
    ).limit(10).all()
    
    # Also search USDA
    from food_apis import USDAFoodData
    usda_results = USDAFoodData.search(q, page_size=10)
    
    # Combine results (local first, then USDA)
    results = []
    
    # Add local foods
    for food in local_foods:
        results.append({
            'id': food.id,
            'name': food.name,
            'brand': food.brand,
            'calories': food.calories,
            'protein': food.protein,
            'carbohydrates': food.carbohydrates,
            'fat': food.fat,
            'source': food.source,
            'in_database': True
        })
    
    # Add USDA results (not yet in our DB)
    for food in usda_results:
        results.append({
            'id': None,  # Not in our DB yet
            'name': food['name'],
            'brand': food['brand'],
            'calories': food['calories'],
            'protein': food['protein'],
            'carbohydrates': food['carbohydrates'],
            'fat': food['fat'],
            'source': food['source'],
            'in_database': False
        })
    
    return results[:20]  # Limit to 20 total results


@app.get("/foods/barcode/{barcode}")
def get_food_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Look up food by barcode"""
    # First check our database
    food = db.query(database.Food).filter(
        database.Food.barcode == barcode
    ).first()
    
    if food:
        return food
    
    # Not in our DB, query Open Food Facts
    from food_apis import OpenFoodFacts
    
    result = OpenFoodFacts.get_by_barcode(barcode)
    
    if not result:
        raise HTTPException(status_code=404, detail="Food not found")
    
    # Save to our database for future lookups
    new_food = database.Food(
        name=result['name'],
        brand=result['brand'],
        barcode=result['barcode'],
        serving_size=result['serving_size'],
        serving_size_grams=result['serving_size_grams'],
        calories=result['calories'],
        protein=result['protein'],
        carbohydrates=result['carbohydrates'],
        fat=result['fat'],
        fiber=result['fiber'],
        sugar=result['sugar'],
        sodium=result['sodium'],
        source=result['source'],
        source_id=result['source_id'],
        is_verified=True
    )
    
    db.add(new_food)
    db.commit()
    db.refresh(new_food)
    
    return new_food


@app.post("/entries", response_model=FoodEntryResponse)
def log_food(entry: FoodEntryCreate, user_id: int, db: Session = Depends(get_db)):
    """Log a food entry"""
    # Get the food
    food = db.query(database.Food).filter(database.Food.id == entry.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    
    # Calculate nutrition based on servings
    db_entry = database.FoodEntry(
        user_id=user_id,
        food_id=entry.food_id,
        servings=entry.servings,
        meal_type=entry.meal_type,
        eaten_at=entry.eaten_at or datetime.now(),
        calories=food.calories * entry.servings,
        protein=food.protein * entry.servings,
        carbohydrates=food.carbohydrates * entry.servings,
        fat=food.fat * entry.servings
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # IMPORTANT: Manually attach the food object so it's included in response
    db_entry.food = food

    return db_entry

@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete a food entry"""
    entry = db.query(database.FoodEntry).filter(database.FoodEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    
    return {"status": "deleted", "id": entry_id}

@app.get("/entries/daily/{user_id}")
def get_daily_summary(
    user_id: int,
    date_str: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get daily nutrition summary"""
    # Parse date or use today
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        target_date = date.today()
    
    # Get user
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all entries for this date
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    entries = db.query(database.FoodEntry).options(
        joinedload(database.FoodEntry.food)  # ADD THIS LINE
    ).filter(
        database.FoodEntry.user_id == user_id,
        database.FoodEntry.eaten_at >= start_datetime,
        database.FoodEntry.eaten_at <= end_datetime
    ).all()
    
    # Calculate totals
    total_calories = sum(e.calories for e in entries)
    total_protein = sum(e.protein for e in entries)
    total_carbs = sum(e.carbohydrates for e in entries)
    total_fat = sum(e.fat for e in entries)
    
    return {
        "date": target_date,
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "calorie_goal": user.calorie_goal,
        "protein_goal": user.protein_goal,
        "carb_goal": user.carb_goal,
        "fat_goal": user.fat_goal,
        "entries": entries
    }

@app.post("/analyze/daily/{user_id}")
def analyze_daily_nutrition(user_id: int, date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """Get AI analysis of daily nutrition using Claude"""
    import os
    from anthropic import Anthropic
    from datetime import date as date_class
    
    # Get daily summary
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        target_date = date_class.today()
    
    # Get user
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all entries for this date
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    entries = db.query(database.FoodEntry).filter(
        database.FoodEntry.user_id == user_id,
        database.FoodEntry.eaten_at >= start_datetime,
        database.FoodEntry.eaten_at <= end_datetime
    ).all()
    
    # Calculate totals
    total_calories = sum(e.calories for e in entries)
    total_protein = sum(e.protein for e in entries)
    total_carbs = sum(e.carbohydrates for e in entries)
    total_fat = sum(e.fat for e in entries)
    
    # Format nutrition data for Claude
    nutrition_summary = f"""Date: {target_date.strftime('%Y-%m-%d')}

DAILY TOTALS:
  Calories: {total_calories:.0f} / {user.calorie_goal} (goal)
  Protein: {total_protein:.1f}g / {user.protein_goal}g (goal)
  Carbs: {total_carbs:.1f}g / {user.carb_goal}g (goal)
  Fat: {total_fat:.1f}g / {user.fat_goal}g (goal)

MEALS:
"""
    
    # Group by meal type
    meals_by_type = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
    for entry in entries:
        meals_by_type[entry.meal_type].append(entry)
    
    for meal_type, meal_entries in meals_by_type.items():
        if meal_entries:
            nutrition_summary += f"\n{meal_type.capitalize()}:\n"
            for entry in meal_entries:
                nutrition_summary += f"  - {entry.food.name}"
                if entry.servings != 1.0:
                    nutrition_summary += f" ({entry.servings} servings)"
                nutrition_summary += f"\n    Cal: {entry.calories:.0f}, P: {entry.protein:.1f}g, C: {entry.carbohydrates:.1f}g, F: {entry.fat:.1f}g\n"
    
    # Call Claude API
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze today's nutrition and provide feedback:

{nutrition_summary}

Please provide:
1. Overall assessment of the day's nutrition
2. What I did well
3. Areas for improvement (macros, food choices)
4. Specific suggestions for tomorrow
5. Any concerning patterns or deficiencies

Keep your response concise and actionable."""
                }
            ],
            system="You are an expert nutritionist and dietitian. Provide evidence-based, practical advice. Be encouraging but honest about areas to improve."
        )
        
        analysis_text = response.content[0].text
        
        # Save analysis to database
        analysis_record = database.Analysis(
            user_id=user_id,
            analysis_type='daily',
            analysis_date=target_date,
            analysis_text=analysis_text,
            avg_calories=total_calories,
            avg_protein=total_protein,
            avg_carbs=total_carbs,
            avg_fat=total_fat
        )
        db.add(analysis_record)
        db.commit()
        
        return {
            "analysis": analysis_text,
            "date": target_date.isoformat(),
            "totals": {
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )
