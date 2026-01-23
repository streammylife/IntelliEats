// Configuration
const API_BASE_URL = 'https://192.168.68.67:8000';
const USER_ID = 1; // For now, hardcode user 1. We'll add auth later.

let currentMealType = '';
let dailyData = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadDailySummary();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('foodSearch');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchFoods(e.target.value);
            }, 300);
        });
    }

    // Analyze button
    document.getElementById('analyzeBtn')?.addEventListener('click', analyzeNutrition);
    
    // Scan barcode button
    document.getElementById('scanBarcodeBtn')?.addEventListener('click', openScanner);
}

// Load daily summary
async function loadDailySummary(date = null) {
    try {
        const dateParam = date ? `?date_str=${date}` : '';
        const response = await fetch(`${API_BASE_URL}/entries/daily/${USER_ID}${dateParam}`);
        
        if (!response.ok) throw new Error('Failed to load daily summary');
        
        dailyData = await response.json();
        
        // Update UI
        updateDailySummary(dailyData);
        updateMealEntries(dailyData.entries);
        
    } catch (error) {
        console.error('Error loading daily summary:', error);
        showError('Failed to load data. Make sure the API server is running.');
    }
}

// Update daily summary display
function updateDailySummary(data) {
    // Update values
    document.getElementById('caloriesValue').textContent = Math.round(data.total_calories);
    document.getElementById('caloriesGoal').textContent = data.calorie_goal;
    document.getElementById('proteinValue').textContent = Math.round(data.total_protein);
    document.getElementById('proteinGoal').textContent = data.protein_goal;
    document.getElementById('carbsValue').textContent = Math.round(data.total_carbs);
    document.getElementById('carbsGoal').textContent = data.carb_goal;
    document.getElementById('fatValue').textContent = Math.round(data.total_fat);
    document.getElementById('fatGoal').textContent = data.fat_goal;
    
    // Update progress bars
    updateProgressBar('caloriesProgress', data.total_calories, data.calorie_goal);
    updateProgressBar('proteinProgress', data.total_protein, data.protein_goal);
    updateProgressBar('carbsProgress', data.total_carbs, data.carb_goal);
    updateProgressBar('fatProgress', data.total_fat, data.fat_goal);
    
    // Update date display
    const dateDisplay = document.getElementById('dateDisplay');
    const today = new Date().toISOString().split('T')[0];
    if (data.date === today) {
        dateDisplay.textContent = 'Today';
    } else {
        dateDisplay.textContent = new Date(data.date).toLocaleDateString();
    }
}

function updateProgressBar(elementId, value, goal) {
    const percentage = Math.min((value / goal) * 100, 100);
    const element = document.getElementById(elementId);
    element.style.width = `${percentage}%`;
    
    // Change color if over goal
    if (percentage > 100) {
        element.style.background = 'var(--warning)';
    } else {
        element.style.background = 'var(--primary)';
    }
}

// Update meal entries
function updateMealEntries(entries) {
    // Clear all meal sections
    ['breakfast', 'lunch', 'dinner', 'snack'].forEach(meal => {
        document.getElementById(`${meal}Entries`).innerHTML = '';
    });
    
    // Group entries by meal type
    entries.forEach(entry => {
        const mealContainer = document.getElementById(`${entry.meal_type}Entries`);
        if (mealContainer) {
            mealContainer.appendChild(createMealEntryElement(entry));
        }
    });
}

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

// Delete entry
async function deleteEntry(entryId) {
    if (!confirm('Delete this food entry?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/entries/${entryId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete entry');
        
        // Reload daily summary
        await loadDailySummary();
        
    } catch (error) {
        console.error('Error deleting entry:', error);
        showError('Failed to delete entry');
    }
}

// Add food modal
function addFood(mealType) {
    currentMealType = mealType;
    document.getElementById('foodSearch').value = '';
    document.getElementById('searchResults').innerHTML = '';
    openModal('addFoodModal');
}

// Search foods
async function searchFoods(query) {
    if (!query || query.length < 2) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/foods/search?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) throw new Error('Search failed');
        
        const results = await response.json();
        displaySearchResults(results);
        
    } catch (error) {
        console.error('Error searching foods:', error);
        showError('Search failed');
    }
}

function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    
    if (results.length === 0) {
        container.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-secondary);">No results found</div>';
        return;
    }
    
    container.innerHTML = results.map(food => `
        <div class="search-result-item" onclick="selectFood(${JSON.stringify(food).replace(/"/g, '&quot;')})">
            <div class="search-result-name">${food.name}</div>
            ${food.brand ? `<div class="search-result-brand">${food.brand}</div>` : ''}
            <div class="search-result-macros">
                ${Math.round(food.calories)} cal • 
                ${Math.round(food.protein)}g P • 
                ${Math.round(food.carbohydrates)}g C • 
                ${Math.round(food.fat)}g F
            </div>
        </div>
    `).join('');
}

// Select food and log it
async function selectFood(food) {
    // Ask for servings
    const servings = prompt('How many servings?', '1');
    if (!servings) return;
    
    const servingsNum = parseFloat(servings);
    if (isNaN(servingsNum) || servingsNum <= 0) {
        alert('Please enter a valid number');
        return;
    }
    
    try {
        // If food doesn't have an ID, we need to create it first
        let foodId = food.id;
        
        if (!foodId) {
            // Create food in database
            const createResponse = await fetch(`${API_BASE_URL}/foods`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: food.name,
                    brand: food.brand || null,
                    barcode: food.barcode || null,
                    serving_size: food.serving_size || '100g',
                    serving_size_grams: food.serving_size_grams || 100,
                    calories: food.calories,
                    protein: food.protein,
                    carbohydrates: food.carbohydrates,
                    fat: food.fat,
                    fiber: food.fiber || 0,
                    sugar: food.sugar || 0,
                    sodium: food.sodium || 0,
                    source: food.source
                })
            });
            
            if (!createResponse.ok) throw new Error('Failed to create food');
            
            const createdFood = await createResponse.json();
            foodId = createdFood.id;
        }
        
        // Log the entry
        const response = await fetch(`${API_BASE_URL}/entries?user_id=${USER_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                food_id: foodId,
                servings: servingsNum,
                meal_type: currentMealType
            })
        });
        
        if (!response.ok) throw new Error('Failed to log food');
        
        const result = await response.json();
        console.log('Entry created:', result);  // ADD THIS LINE
        console.log('Food object:', result.food);  // ADD THIS LINE

        // Close modal and reload
        closeModal();
        await loadDailySummary();
        
    } catch (error) {
        console.error('Error logging food:', error);
        showError('Failed to log food');
    }
}

// Analyze nutrition with Claude
async function analyzeNutrition() {
    openModal('analysisModal');
    document.getElementById('analysisContent').innerHTML = '<div class="loading">Analyzing your nutrition with AI...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze/daily/${USER_ID}`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const result = await response.json();
        document.getElementById('analysisContent').innerHTML = `<div style="white-space: pre-wrap;">${result.analysis}</div>`;
        
    } catch (error) {
        console.error('Error analyzing nutrition:', error);
        document.getElementById('analysisContent').innerHTML = '<div style="color: var(--danger);">Analysis failed. Make sure the API server is running and your Claude API key is configured.</div>';
    }
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

function closeAnalysis() {
    closeModal();
}

// Error handling
function showError(message) {
    alert(message); // Simple for now, can make this prettier later
}

// Make functions globally available
window.addFood = addFood;
window.deleteEntry = deleteEntry;
window.selectFood = selectFood;
window.closeModal = closeModal;
window.closeAnalysis = closeAnalysis;
