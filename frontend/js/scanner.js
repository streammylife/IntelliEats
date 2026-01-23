// Barcode scanner using html5-qrcode library (works on all browsers)
let html5QrcodeScanner = null;

async function openScanner() {
    const modal = document.getElementById('scannerModal');
    const resultDiv = document.getElementById('scannerResult');
    
    modal.classList.add('active');
    resultDiv.innerHTML = '';
    
    // Hide the video element, we'll use the library's built-in UI
    document.getElementById('scanner').style.display = 'none';
    
    // Create scanner div
    resultDiv.innerHTML = '<div id="qr-reader" style="width: 100%;"></div>';
    
    // Initialize scanner with html5-qrcode
    html5QrcodeScanner = new Html5QrcodeScanner(
        "qr-reader",
        { 
            fps: 10,
            qrbox: { width: 250, height: 100 },
            formatsToSupport: [
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.UPC_E
            ]
        }
    );
    
    html5QrcodeScanner.render(onBarcodeSuccess, onBarcodeError);
}

function onBarcodeSuccess(decodedText, decodedResult) {
    // Stop scanning
    html5QrcodeScanner.clear();
    
    // Show result and lookup
    const resultDiv = document.getElementById('scannerResult');
    resultDiv.innerHTML = `<div>Barcode detected: ${decodedText}<br>Looking up...</div>`;
    
    // Lookup the barcode
    lookupBarcode(decodedText, resultDiv);
}

function onBarcodeError(error) {
    // Ignore errors (happens constantly while scanning)
}

async function lookupBarcode(barcode, resultDiv) {
    try {
        const response = await fetch(`${API_BASE_URL}/foods/barcode/${barcode}`);
        
        if (!response.ok) {
            resultDiv.innerHTML = `
                <div style="color: var(--danger);">Product not found in database.</div>
                <button onclick="openScanner()" style="width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-md); font-weight: 600; margin-top: 1rem;">Scan Again</button>
            `;
            return;
        }
        
        const food = await response.json();
        
        resultDiv.innerHTML = `
            <div style="text-align: left;">
                <strong>${food.name}</strong><br>
                ${food.brand ? `<small>${food.brand}</small><br>` : ''}
                <div style="margin-top: 0.5rem; font-size: 0.875rem;">
                    ${Math.round(food.calories)} cal • 
                    ${Math.round(food.protein)}g P • 
                    ${Math.round(food.carbohydrates)}g C • 
                    ${Math.round(food.fat)}g F
                </div>
                <button onclick="addScannedFood(${JSON.stringify(food).replace(/"/g, '&quot;')})" 
                        style="width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-md); font-weight: 600; margin-top: 1rem;">
                    Add to Diary
                </button>
                <button onclick="openScanner()" 
                        style="width: 100%; padding: 1rem; background: var(--secondary); color: white; border: none; border-radius: var(--radius-md); font-weight: 600; margin-top: 0.5rem;">
                    Scan Another
                </button>
            </div>
        `;
        
    } catch (error) {
        console.error('Error looking up barcode:', error);
        resultDiv.innerHTML = `<div style="color: var(--danger);">Failed to look up product.</div>`;
    }
}

async function addScannedFood(food) {
    // Show meal selection
    const mealType = prompt('Which meal?\n1. Breakfast\n2. Lunch\n3. Dinner\n4. Snack', '3');
    const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];
    const selectedMeal = mealTypes[parseInt(mealType) - 1];
    
    if (!selectedMeal) return;
    
    currentMealType = selectedMeal;
    closeScanner();
    await selectFood(food);
}

function closeScanner() {
    if (html5QrcodeScanner) {
        html5QrcodeScanner.clear();
        html5QrcodeScanner = null;
    }
    document.getElementById('scannerModal').classList.remove('active');
}

// Make functions globally available
window.openScanner = openScanner;
window.closeScanner = closeScanner;
window.addScannedFood = addScannedFood;