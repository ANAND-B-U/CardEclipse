const API_BASE_URL = 'http://localhost:5000';
let files = [];
let isProcessing = false;
let allResults = [];
let stats = {
    totalCards: 0,
    successfulCards: 0,
    tokensUsed: 0
};

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const processBtn = document.getElementById('processBtn');
const clearBtn = document.getElementById('clearBtn');
const filesSection = document.getElementById('filesSection');
const filesList = document.getElementById('filesList');
const fileCount = document.getElementById('fileCount');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const downloadSection = document.getElementById('downloadSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const apiStatus = document.getElementById('apiStatus');

// Event Listeners
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

processBtn.addEventListener('click', processFiles);
clearBtn.addEventListener('click', clearAll);

function handleFiles(newFiles) {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    const maxSize = 50 * 1024 * 1024; // 50MB

    const validFiles = [];
    const skippedFiles = [];

    Array.from(newFiles).forEach(file => {
        const isValidType = validTypes.includes(file.type);
        const isValidSize = file.size <= maxSize;

        if (isValidType && isValidSize) {
            validFiles.push(file);
        } else {
            skippedFiles.push({
                name: file.name,
                reason: !isValidType ? 'Invalid file type' : 'File too large (>50MB)'
            });
        }
    });

    // Show detailed feedback for skipped files
    if (skippedFiles.length > 0) {
        const skippedMessage = skippedFiles.map(f => `${f.name} (${f.reason})`).join(', ');
        showToast(`${skippedFiles.length} file(s) skipped: ${skippedMessage}`, 'error');
    }

    // Check for duplicates
    const duplicateFiles = [];
    const newValidFiles = [];

    validFiles.forEach(file => {
        const isDuplicate = files.some(existingFile =>
            existingFile.name === file.name && existingFile.size === file.size
        );

        if (isDuplicate) {
            duplicateFiles.push(file.name);
        } else {
            newValidFiles.push(file);
        }
    });

    if (duplicateFiles.length > 0) {
        showToast(`${duplicateFiles.length} duplicate file(s) skipped`, 'error');
    }

    // Add valid files
    if (newValidFiles.length > 0) {
        files = [...files, ...newValidFiles];
        updateFilesList();
        updateProcessButton();
        showToast(`${newValidFiles.length} file(s) added successfully`, 'success');
    }

    // Clear file input to allow re-selecting same files
    fileInput.value = '';
}

function removeFile(index) {
    files = files.filter((_, i) => i !== index);
    updateFilesList();
    updateProcessButton();
}

function updateFilesList() {
    if (files.length === 0) {
        filesSection.style.display = 'none';
        return;
    }

    filesSection.style.display = 'block';
    fileCount.textContent = files.length;

    filesList.innerHTML = files.map((file, index) => `
        <div class="file-item fade-in">
            <div class="file-info">
                <div class="file-preview">
                    <i class="fas fa-image"></i>
                </div>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <p>${(file.size / 1024 / 1024).toFixed(2)} MB • ${file.type}</p>
                </div>
            </div>
            <div class="file-actions">
                <button class="icon-btn" onclick="removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function updateProcessButton() {
    processBtn.disabled = files.length === 0 || isProcessing;
}

function clearAll() {
    files = [];
    allResults = [];
    updateFilesList();
    updateProcessButton();
    resultsSection.style.display = 'none';
    downloadSection.style.display = 'none';
    showToast('All files cleared', 'success');
}

async function processFiles() {
    if (files.length === 0) return;

    isProcessing = true;
    updateProcessButton();
    showLoading();

    try {
        const formData = new FormData();

        if (files.length === 1) {
            formData.append('image', files[0]);
        } else {
            files.forEach(file => {
                formData.append('images', file);
            });
        }

        formData.append('model', document.getElementById('model').value);

        const endpoint = files.length === 1 ? '/api/single' : '/api/batch';

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        displayResults(data);
        updateStats(data);

    } catch (error) {
        showToast(`Processing failed: ${error.message}`, 'error');
    } finally {
        isProcessing = false;
        updateProcessButton();
        hideLoading();
    }
}

function displayResults(data) {
    if (!data.success) {
        showToast(`Processing failed: ${data.error}`, 'error');
        return;
    }

    resultsSection.style.display = 'block';
    const resultsArray = data.results || [data];

    allResults = allResults.concat(resultsArray);

    resultsGrid.innerHTML = resultsArray.map((result, index) => `
        <div class="result-card fade-in">
            <div class="result-header">
                <div class="result-title">
                    <i class="fas fa-id-card"></i> ${result.filename || `Card ${index + 1}`}
                </div>
                <div class="result-badge">${result.model_used}</div>
            </div>
            
            ${result.success ? `
                <div class="result-content">
                    ${result.data.name ? `
                        <div class="result-field">
                            <label>Name</label>
                            <div class="value"><i class="fas fa-user"></i> ${result.data.name}</div>
                        </div>
                    ` : ''}
                    ${result.data.title ? `
                        <div class="result-field">
                            <label>Title</label>
                            <div class="value"><i class="fas fa-briefcase"></i> ${result.data.title}</div>
                        </div>
                    ` : ''}
                    ${result.data.company ? `
                        <div class="result-field">
                            <label>Company</label>
                            <div class="value"><i class="fas fa-building"></i> ${result.data.company}</div>
                        </div>
                    ` : ''}
                    ${result.data.email ? `
                        <div class="result-field">
                            <label>Email</label>
                            <div class="value"><i class="fas fa-envelope"></i> ${result.data.email}</div>
                        </div>
                    ` : ''}
                    ${result.data.phoneNumbers && result.data.phoneNumbers.length > 0 ? `
                        <div class="result-field">
                            <label>Phone</label>
                            <div class="value">
                                <i class="fas fa-phone"></i> 
                                ${result.data.phoneNumbers.join(', ')}
                            </div>
                        </div>
                    ` : ''}
                    ${result.data.website ? `
                        <div class="result-field">
                            <label>Website</label>
                            <div class="value"><i class="fas fa-globe"></i> ${result.data.website}</div>
                        </div>
                    ` : ''}
                    ${result.data.address ? `
                        <div class="result-field">
                            <label>Address</label>
                            <div class="value"><i class="fas fa-map-marker-alt"></i> ${result.data.address}</div>
                        </div>
                    ` : ''}
                    ${result.data.tokens ? `
                        <div class="result-field">
                            <label>Tokens Used</label>
                            <div class="value"><i class="fas fa-microchip"></i> ${result.data.tokens}</div>
                        </div>
                    ` : ''}
                </div>
            ` : `
                <div class="message error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${result.error || 'Failed to process this card'}</span>
                </div>
            `}
        </div>
    `).join('');

    const successfulResults = resultsArray.filter(r => r.success);
    if (successfulResults.length > 0) {
        downloadSection.style.display = 'block';
    }

    showToast(`Successfully processed ${successfulResults.length} card(s)`, 'success');
}

function updateStats(data) {
    const resultsArray = data.results || [data];
    stats.totalCards += resultsArray.length;
    stats.successfulCards += resultsArray.filter(r => r.success).length;

    resultsArray.forEach(result => {
        if (result.success && result.data.tokens) {
            stats.tokensUsed += result.data.tokens;
        }
    });

    document.getElementById('totalCards').textContent = stats.totalCards;
    document.getElementById('successRate').textContent =
        stats.totalCards > 0 ? Math.round((stats.successfulCards / stats.totalCards) * 100) + '%' : '0%';
    document.getElementById('tokensUsed').textContent = stats.tokensUsed;
}

function downloadCSV() {
    const successfulResults = allResults.filter(r => r.success);
    if (successfulResults.length === 0) {
        showToast('No data to export', 'error');
        return;
    }

    fetch(`${API_BASE_URL}/api/download/csv`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            results: successfulResults
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `business_cards_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            showToast('CSV file downloaded successfully', 'success');
        })
        .catch(error => {
            showToast(`Download failed: ${error.message}`, 'error');
        });
}

function downloadExcel() {
    const successfulResults = allResults.filter(r => r.success);
    if (successfulResults.length === 0) {
        showToast('No data to export', 'error');
        return;
    }

    fetch(`${API_BASE_URL}/api/download/excel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            results: successfulResults
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `business_cards_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
            showToast('Excel file downloaded successfully', 'success');
        })
        .catch(error => {
            showToast(`Download failed: ${error.message}`, 'error');
        });
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast message ${type}-message fade-in`;

    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    const iconColor = type === 'success' ? 'var(--accent-gold)' : 'var(--accent-purple)';

    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon" style="color: ${iconColor}">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="toast-message">
                <span>${message}</span>
                <div class="toast-progress"></div>
            </div>
        </div>
    `;

    // Add enhanced styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 350px;
        max-width: 500px;
        background: rgba(26, 26, 26, 0.95);
        backdrop-filter: blur(20px);
        border: 2px solid ${type === 'success' ? 'var(--accent-gold)' : 'var(--accent-purple)'};
        border-radius: 15px;
        padding: 0;
        box-shadow: 0 0 30px ${type === 'success' ? 'rgba(212, 175, 55, 0.5)' : 'rgba(107, 70, 193, 0.5)'};
        animation: slideIn 0.5s ease, ${type === 'success' ? 'gold-glow' : 'hover-purple'} 2s infinite;
        transform-origin: right center;
    `;

    // Add internal styles
    const style = document.createElement('style');
    style.textContent = `
        .toast-content {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            gap: 1rem;
        }
        
        .toast-icon {
            font-size: 1.5rem;
            animation: ${type === 'success' ? 'gold-pulse' : 'hover-purple'} 1s infinite;
        }
        
        .toast-message {
            flex: 1;
            color: var(--text-primary);
            font-weight: 500;
            position: relative;
        }
        
        .toast-progress {
            position: absolute;
            bottom: -5px;
            left: 0;
            height: 3px;
            background: ${type === 'success' ? 'var(--accent-gold)' : 'var(--accent-purple)'};
            border-radius: 2px;
            animation: progress 5s linear;
        }
        
        @keyframes progress {
            from { width: 100%; }
            to { width: 0%; }
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;

    if (!document.querySelector('#toast-styles')) {
        style.id = 'toast-styles';
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds with slideOut animation
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 5000);

    // Add hover effect to pause auto-remove
    toast.addEventListener('mouseenter', () => {
        toast.style.animationPlayState = 'paused';
        const progress = toast.querySelector('.toast-progress');
        if (progress) progress.style.animationPlayState = 'paused';
    });

    toast.addEventListener('mouseleave', () => {
        toast.style.animationPlayState = 'running';
        const progress = toast.querySelector('.toast-progress');
        if (progress) progress.style.animationPlayState = 'running';
    });
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        document.querySelector('.fullscreen-btn i').className = 'fas fa-compress';
    } else {
        document.exitFullscreen();
        document.querySelector('.fullscreen-btn i').className = 'fas fa-expand';
    }
}

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            apiStatus.innerHTML = `
                <div class="message success-message">
                    <i class="fas fa-check-circle"></i>
                    <span>API Connected • Models: ${data.models.join(', ')}</span>
                </div>
            `;
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        apiStatus.innerHTML = `
            <div class="message error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <span>API Connection Failed</span>
            </div>
        `;
    }
}

// Initialize
checkAPIHealth();
updateModelOptions();

async function updateModelOptions() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        const modelSelect = document.getElementById('model');
        modelSelect.innerHTML = '<option value="auto">Auto Select</option>';

        if (data.models && data.models.length > 0) {
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = getModelDisplayName(model);
                modelSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to fetch models:', error);
        // Fallback to basic options
        const modelSelect = document.getElementById('model');
        modelSelect.innerHTML = '<option value="auto">Auto Select</option><option value="nvidia">NVIDIA Phi-3.5 Vision</option>';
    }
}

function getModelDisplayName(model) {
    const modelNames = {
        'nvidia': 'NVIDIA Phi-3.5 Vision',
        'mistral': 'Mistral 14B Instruct',
        'microsoft': 'Microsoft Phi-4 Multimodal',
        'gemini': 'Google Gemini 2.5 Flash'
    };
    return modelNames[model] || model;
}
