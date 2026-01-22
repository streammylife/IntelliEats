#!/usr/bin/env python3
"""
Integration with external food databases
- Open Food Facts (barcode scanning)
- USDA FoodData Central (whole foods)
"""

import requests
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

USDA_API_KEY = os.getenv('USDA_API_KEY', 'DEMO_KEY')


class OpenFoodFacts:
    """Interface to Open Food Facts API"""
    
    BASE_URL = "https://world.openfoodfacts.org/api/v0"
    
    @staticmethod
    def get_by_barcode(barcode: str) -> Optional[Dict]:
        """
        Look up product by barcode
        Returns standardized nutrition data or None
        """
        try:
            url = f"{OpenFoodFacts.BASE_URL}/product/{barcode}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get('status') != 1:  # Product not found
                return None
            
            product = data.get('product', {})
            nutriments = product.get('nutriments', {})
            
            # Standardize the data
            return {
                'name': product.get('product_name', 'Unknown Product'),
                'brand': product.get('brands', ''),
                'barcode': barcode,
                'serving_size': product.get('serving_size', '100g'),
                'serving_size_grams': float(product.get('serving_quantity', 100)),
                'calories': float(nutriments.get('energy-kcal_100g', 0)),
                'protein': float(nutriments.get('proteins_100g', 0)),
                'carbohydrates': float(nutriments.get('carbohydrates_100g', 0)),
                'fat': float(nutriments.get('fat_100g', 0)),
                'fiber': float(nutriments.get('fiber_100g', 0)),
                'sugar': float(nutriments.get('sugars_100g', 0)),
                'sodium': float(nutriments.get('sodium_100g', 0)) * 1000,  # Convert to mg
                'source': 'openfoodfacts',
                'source_id': barcode,
                'image_url': product.get('image_url', ''),
            }
            
        except Exception as e:
            print(f"Error fetching from Open Food Facts: {e}")
            return None


class USDAFoodData:
    """Interface to USDA FoodData Central API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    @staticmethod
    def search(query: str, page_size: int = 10) -> list:
        """
        Search for foods in USDA database
        Returns list of foods with basic info
        """
        try:
            url = f"{USDAFoodData.BASE_URL}/foods/search"
            params = {
                'api_key': USDA_API_KEY,
                'query': query,
                'pageSize': page_size,
                'dataType': ['Survey (FNDDS)', 'Foundation', 'SR Legacy']
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            foods = data.get('foods', [])
            
            results = []
            for food in foods:
                # Extract nutrition data
                nutrients = {}
                for nutrient in food.get('foodNutrients', []):
                    nutrient_name = nutrient.get('nutrientName', '').lower()
                    nutrient_value = nutrient.get('value', 0)
                    
                    if 'energy' in nutrient_name or 'calor' in nutrient_name:
                        nutrients['calories'] = nutrient_value
                    elif 'protein' in nutrient_name:
                        nutrients['protein'] = nutrient_value
                    elif 'carbohydrate' in nutrient_name:
                        nutrients['carbohydrates'] = nutrient_value
                    elif 'total lipid' in nutrient_name or 'fat' in nutrient_name:
                        nutrients['fat'] = nutrient_value
                    elif 'fiber' in nutrient_name:
                        nutrients['fiber'] = nutrient_value
                    elif 'sugars' in nutrient_name:
                        nutrients['sugar'] = nutrient_value
                    elif 'sodium' in nutrient_name:
                        nutrients['sodium'] = nutrient_value
                
                results.append({
                    'name': food.get('description', 'Unknown'),
                    'brand': food.get('brandOwner', ''),
                    'serving_size': '100g',
                    'serving_size_grams': 100.0,
                    'calories': nutrients.get('calories', 0),
                    'protein': nutrients.get('protein', 0),
                    'carbohydrates': nutrients.get('carbohydrates', 0),
                    'fat': nutrients.get('fat', 0),
                    'fiber': nutrients.get('fiber', 0),
                    'sugar': nutrients.get('sugar', 0),
                    'sodium': nutrients.get('sodium', 0),
                    'source': 'usda',
                    'source_id': str(food.get('fdcId', '')),
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching USDA: {e}")
            return []


# Testing functions
if __name__ == "__main__":
    print("Testing Open Food Facts API...")
    print("=" * 50)
    
    # Test barcode lookup (Coca-Cola can)
    barcode = "0049000042566"
    print(f"\nLooking up barcode: {barcode}")
    result = OpenFoodFacts.get_by_barcode(barcode)
    
    if result:
        print(f"✓ Found: {result['name']}")
        print(f"  Brand: {result['brand']}")
        print(f"  Calories: {result['calories']} kcal")
        print(f"  Protein: {result['protein']}g")
    else:
        print("✗ Product not found")
    
    print("\n" + "=" * 50)
    print("Testing USDA FoodData Central API...")
    print("=" * 50)
    
    # Test food search
    query = "chicken breast"
    print(f"\nSearching for: {query}")
    results = USDAFoodData.search(query, page_size=3)
    
    if results:
        print(f"✓ Found {len(results)} results:")
        for i, food in enumerate(results, 1):
            print(f"\n{i}. {food['name']}")
            print(f"   Calories: {food['calories']} kcal")
            print(f"   Protein: {food['protein']}g")
    else:
        print("✗ No results found")