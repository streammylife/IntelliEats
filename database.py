#!/usr/bin/env python3
"""
Database schema for nutrition tracker
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User accounts"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Nutritional goals
    calorie_goal = Column(Integer, default=2000)
    protein_goal = Column(Float, default=150)
    carb_goal = Column(Float, default=200)
    fat_goal = Column(Float, default=65)
    
    # Relationships
    entries = relationship("FoodEntry", back_populates="user")


class Food(Base):
    """Food items (cached from APIs or user-created)"""
    __tablename__ = 'foods'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    brand = Column(String(100))
    barcode = Column(String(50), unique=True, index=True)  # For barcode lookup
    
    # Nutrition per serving
    serving_size = Column(String(50))  # "1 cup", "100g", etc.
    serving_size_grams = Column(Float)  # Standardized to grams
    
    calories = Column(Float, nullable=False)
    protein = Column(Float, default=0)
    carbohydrates = Column(Float, default=0)
    fat = Column(Float, default=0)
    fiber = Column(Float, default=0)
    sugar = Column(Float, default=0)
    sodium = Column(Float, default=0)  # in mg
    
    # Metadata
    source = Column(String(50))  # 'openfoodfacts', 'usda', 'user', etc.
    source_id = Column(String(100))  # ID from the source API
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)  # User-created vs API
    
    # Relationships
    entries = relationship("FoodEntry", back_populates="food")


class FoodEntry(Base):
    """Individual food log entries"""
    __tablename__ = 'food_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    food_id = Column(Integer, ForeignKey('foods.id'), nullable=False)
    
    # When and how much
    eaten_at = Column(DateTime, default=datetime.utcnow, index=True)
    meal_type = Column(String(20))  # 'breakfast', 'lunch', 'dinner', 'snack'
    
    # Quantity
    servings = Column(Float, default=1.0)  # 1.5 servings, 2 servings, etc.
    
    # Calculated nutrition (servings * food nutrition)
    calories = Column(Float)
    protein = Column(Float)
    carbohydrates = Column(Float)
    fat = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="entries")
    food = relationship("Food", back_populates="entries")


class Analysis(Base):
    """Claude's daily/weekly nutrition analyses"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    analysis_type = Column(String(20))  # 'daily' or 'weekly'
    analysis_date = Column(DateTime, nullable=False)
    
    # The actual analysis from Claude
    analysis_text = Column(String(5000))
    
    # Summary stats for the period
    avg_calories = Column(Float)
    avg_protein = Column(Float)
    avg_carbs = Column(Float)
    avg_fat = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Database initialization
def init_db(db_path='nutrition_tracker.db'):
    """Initialize the database"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Test: create the database
    print("Creating database...")
    engine = init_db()
    print("✓ Database created successfully!")
    print("✓ Tables: users, foods, food_entries, analyses")