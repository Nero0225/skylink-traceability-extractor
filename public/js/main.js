// Main Application JavaScript
// File upload and processing functionality

class FileUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupDragAndDrop();
    }

    bindEvents() {
        const uploadForm = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const dropZone = document.getElementById('dropZone');

        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileInputChange(e));
        }

        if (dropZone) {
            dropZone.addEventListener('click', (e) => this.handleDropZoneClick(e));
        }
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            this.handleFileSelection(files);
        });
    }

    handleFileInputChange(e) {
        const files = Array.from(e.target.files);
        this.handleFileSelection(files);
    }

    handleDropZoneClick(e) {
        const fileInput = document.getElementById('fileInput');
        if (e.target === e.currentTarget || e.target.closest('.drop-zone-icon, .drop-zone-text, .drop-zone-hint')) {
            fileInput?.click();
        }
    }

    handleFileSelection(files) {
        const pdfFiles = files.filter(file => file.name.toLowerCase().endsWith('.pdf'));
        this.selectedFiles = pdfFiles;
        this.updateSelectedFilesDisplay();
        this.updateProcessButton();
    }

    updateSelectedFilesDisplay() {
        const selectedFilesDiv = document.getElementById('selectedFiles');
        const dropZoneText = document.querySelector('.drop-zone-text');
        const dropZoneHint = document.querySelector('.drop-zone-hint');

        if (!selectedFilesDiv || !dropZoneText || !dropZoneHint) return;

        if (this.selectedFiles.length === 0) {
            selectedFilesDiv.style.display = 'none';
            dropZoneText.textContent = 'Drag & drop your PDF files here';
            dropZoneHint.textContent = 'or click to browse for multiple files';
            return;
        }

        selectedFilesDiv.style.display = 'block';
        selectedFilesDiv.innerHTML = '';

        dropZoneText.textContent = `${this.selectedFiles.length} file${this.selectedFiles.length > 1 ? 's' : ''} selected`;
        dropZoneHint.textContent = 'Click to change selection';

        this.selectedFiles.forEach((file, index) => {
            const fileDiv = this.createFileElement(file, index);
            selectedFilesDiv.appendChild(fileDiv);
        });
    }

    createFileElement(file, index) {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'selected-file';

        const fileName = document.createElement('div');
        fileName.className = 'selected-file-name';
        fileName.textContent = file.name;

        const fileSize = document.createElement('div');
        fileSize.className = 'selected-file-size';
        fileSize.textContent = this.formatFileSize(file.size);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-file';
        removeBtn.innerHTML = '×';
        removeBtn.type = 'button';
        removeBtn.onclick = () => this.removeFile(index);

        fileDiv.appendChild(fileName);
        fileDiv.appendChild(fileSize);
        fileDiv.appendChild(removeBtn);

        return fileDiv;
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateSelectedFilesDisplay();
        this.updateProcessButton();
    }

    clearSelectedFiles() {
        this.selectedFiles = [];
        this.updateSelectedFilesDisplay();
        this.updateProcessButton();
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
    }

    updateProcessButton() {
        const processButton = document.getElementById('processButton');
        if (processButton) {
            processButton.disabled = this.selectedFiles.length === 0;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    async handleFormSubmit(e) {
        e.preventDefault();

        if (this.selectedFiles.length === 0) {
            alert('Please select PDF file(s)');
            return;
        }

        const formData = new FormData();
        this.selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const statusDiv = document.getElementById('status');
        const processButton = document.getElementById('processButton');

        if (!statusDiv || !processButton) return;

        // Update UI for processing state
        this.setProcessingState(processButton, statusDiv, true);

        try {
            const response = await fetch('/process-pdf-batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.displaySuccess(statusDiv, result);
                this.clearSelectedFiles();
            } else {
                this.displayError(statusDiv, result.message);
            }
        } catch (error) {
            this.displayError(statusDiv, `Connection Error: ${error.message}`);
        } finally {
            this.setProcessingState(processButton, statusDiv, false);
        }
    }

    setProcessingState(processButton, statusDiv, isProcessing) {
        if (isProcessing) {
            processButton.disabled = true;
            processButton.textContent = '⏳ Processing...';
            
            statusDiv.style.display = 'block';
            statusDiv.className = 'processing';
            statusDiv.innerHTML = `
                <h3>🔄 Processing ${this.selectedFiles.length} Document${this.selectedFiles.length > 1 ? 's' : ''}</h3>
                <p>${this.selectedFiles.length > 1 ? 'Processing files in parallel. This may take several minutes...' : `Analyzing ${this.selectedFiles[0].name}...`}</p>
                <div class="progress-bar">
                    <div class="progress-bar-fill"></div>
                </div>
            `;
        } else {
            processButton.textContent = '🚀 Process Documents';
            processButton.disabled = this.selectedFiles.length === 0;
        }
    }

    displaySuccess(statusDiv, result) {
        statusDiv.className = 'success';
        const successRate = Math.round((result.successful_files / result.total_files) * 100);
        
        statusDiv.innerHTML = `
            <h3>✅ Batch Processing Complete!</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #007bff;">${result.total_files}</div>
                    <div style="color: #6c757d; font-size: 0.9em;">Total Files</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #28a745;">${result.successful_files}</div>
                    <div style="color: #6c757d; font-size: 0.9em;">Successful</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #dc3545;">${result.failed_files}</div>
                    <div style="color: #6c757d; font-size: 0.9em;">Failed</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #17a2b8;">${successRate}%</div>
                    <div style="color: #6c757d; font-size: 0.9em;">Success Rate</div>
                </div>
            </div>
            <p style="text-align: center; color: #6c757d; margin: 10px 0;">
                Processing completed in ${result.total_processing_time} seconds
            </p>
            <a href="${result.dashboard_url}" target="_blank" 
               style="display: inline-block; margin-top: 20px; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 50px; font-weight: 600;">
                📊 View Batch Dashboard
            </a>
        `;
    }

    displayError(statusDiv, message) {
        statusDiv.className = 'error';
        statusDiv.innerHTML = `
            <h3>❌ Processing Failed</h3>
            <p>${message}</p>
            <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Try Again
            </button>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛩️ Aviation Traceability - Main Application Loaded');
    
    // Initialize file upload manager
    new FileUploadManager();
    
    // Initialize any additional functionality from app.js
    if (window.AviationTraceability) {
        window.AviationTraceability.checkSystemStatus();
    }
});

// Export for external use
window.FileUploadManager = FileUploadManager; 