// Barcode scanner using device camera
let scannerStream = null;
let scannerAnimationFrame = null;

async function openScanner() {
    const modal = document.getElementById('scannerModal');
    const video = document.getElementById('scanner');
    const canvas = document.getElementById('scannerCanvas');
    const resultDiv = document.getElementById('scannerResult');
    
    modal.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        // Request camera access
        scannerStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' } // Use back camera on mobile
        });
        
        video.srcObject = scannerStream;
        
        // Start scanning for barcodes
        video.addEventListener('loadedmetadata', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            scanBarcode(video, canvas, resultDiv);
        });
        
    } catch (error) {
        console.error('Camera access error:', error);
        resultDiv.innerHTML = '<div style="color: var(--danger);">Camera access denied. Please enable camera permissions.</div>';
    }
}

function scanBarcode(video, canvas, resultDiv) {
    const ctx = canvas.getContext('2d');
    
    function scan() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Try to detect barcode using BarcodeDetector API (Chrome/Edge only)
            if ('BarcodeDetector' in window) {
                const barcodeDetector = new BarcodeDetector({ formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e'] });
                
                barcodeDetector.detect(canvas)
                    .then(barcodes => {
                        if (barcodes.length > 0) {
                            const barcode = barcodes[0].rawValue;
                            onBarcodeDetected(barcode, resultDiv);
                            return;
                        }
                    })
                    .catch(err => console.error('Barcode detection error:', err));
            } else {
                // Fallback: show manual input
                resultDiv.innerHTML = `
                    <div>Barcode scanner not supported on this device.</div>
                    <input type="text" id="manualBarcode" placeholder="Enter barcode manually" class="search-input" style="margin-top: 1rem;">
                    <button onclick="lookupManualBarcode()" style="width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-md); font-weight: 600; margin-top: 0.5rem;">Look Up</button>
                `;
                stopScanner();
                return;
            }
        }
        
        scannerAnimationFrame = requestAnimationFrame(scan);
    }
    
    scan();
}

async function onBarcodeDetected(barcode, resultDiv) {
    stopScanner();
    
    resultDiv.innerHTML = `<div>Barcode detected: ${barcode}<br>Looking up...</div>`;
    
    try {
        const response = await fetch(`${API_BASE_URL}/foods/barcode/${barcode}`);
        
        if (!response.ok) {
            resultDiv.innerHTML = `<div style="color: var(--danger);">Product not found in database.</div>`;
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
            </div>
        `;
        
    } catch (error) {
        console.error('Error looking up barcode:', error);
        resultDiv.innerHTML = `<div style="color: var(--danger);">Failed to look up product.</div>`;
    }
}

async function lookupManualBarcode() {
    const barcode = document.getElementById('manualBarcode').value;
    if (!barcode) return;
    
    const resultDiv = document.getElementById('scannerResult');
    await onBarcodeDetected(barcode, resultDiv);
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
    stopScanner();
    document.getElementById('scannerModal').classList.remove('active');
}

function stopScanner() {
    if (scannerStream) {
        scannerStream.getTracks().forEach(track => track.stop());
        scannerStream = null;
    }
    
    if (scannerAnimationFrame) {
        cancelAnimationFrame(scannerAnimationFrame);
        scannerAnimationFrame = null;
    }
}

// Make functions globally available
window.openScanner = openScanner;
window.closeScanner = closeScanner;
window.lookupManualBarcode = lookupManualBarcode;
window.addScannedFood = addScannedFood;