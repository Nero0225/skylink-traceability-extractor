from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging
from dataclasses import asdict
import asyncio

# Import our existing components
from pdfparser import parse_document
from certificate_extractor import CertificateExtractor
from traceability_source_validator import TraceabilitySourceValidator
from html_generator import HTMLTraceabilityGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Aviation Traceability PDF Processor",
    description="Upload PDF documents to extract certificates and validate traceability compliance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
extractor = CertificateExtractor()
validator = TraceabilitySourceValidator()
html_generator = HTMLTraceabilityGenerator()

# Create directories for storing processed files
TEMP_DIR = "temp_uploads"
OUTPUT_DIR = "processed_reports"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files for serving generated HTML reports
app.mount("/reports", StaticFiles(directory=OUTPUT_DIR), name="reports")

# Data models
class ProcessingResult(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    cert_type: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    condition_code: Optional[str] = None
    quantity: Optional[str] = None
    traceability_type: Optional[str] = None
    traceability_name: Optional[str] = None
    compliance_status: Optional[str] = None
    html_report_url: Optional[str] = None
    processing_time: Optional[float] = None
    filename: Optional[str] = None

class BatchProcessingResult(BaseModel):
    success: bool
    message: str
    batch_id: str
    total_files: int
    successful_files: int
    failed_files: int
    processing_results: List[ProcessingResult]
    total_processing_time: float
    dashboard_url: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aviation Traceability PDF Processor</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
                padding: 20px;
            }
            
            .container { 
                max-width: 900px; 
                margin: 0 auto; 
                background: white;
                padding: 0;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            
            .header h1 { 
                font-size: 2.5em;
                font-weight: 600;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }
            
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .content {
                padding: 40px;
            }
            
            .upload-section {
                background: #f8f9fa;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
            }
            
            .upload-options {
                display: flex;
                gap: 15px;
                margin-bottom: 30px;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .upload-option {
                flex: 1;
                min-width: 150px;
                position: relative;
            }
            
            .upload-option input[type="radio"] {
                position: absolute;
                opacity: 0;
            }
            
            .upload-option label {
                display: block;
                padding: 15px 20px;
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            
            .upload-option input[type="radio"]:checked + label {
                background: #007bff;
                color: white;
                border-color: #007bff;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,123,255,0.3);
            }
            
            .upload-option label:hover {
                border-color: #007bff;
                transform: translateY(-1px);
            }
            
            .upload-option .icon {
                font-size: 1.5em;
                margin-bottom: 5px;
                display: block;
            }
            
            .drop-zone {
                border: 3px dashed #007bff;
                border-radius: 15px;
                padding: 60px 40px;
                text-align: center;
                background: white;
                position: relative;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .drop-zone.drag-over {
                background: #e7f3ff;
                border-color: #0056b3;
                transform: scale(1.02);
            }
            
            .drop-zone-icon {
                font-size: 4em;
                color: #007bff;
                margin-bottom: 20px;
            }
            
            .drop-zone-text {
                font-size: 1.2em;
                color: #495057;
                margin-bottom: 10px;
            }
            
            .drop-zone-hint {
                font-size: 0.9em;
                color: #6c757d;
            }
            
            .file-input-wrapper {
                position: relative;
                overflow: hidden;
                display: inline-block;
                margin-top: 20px;
            }
            
            .file-input-wrapper input[type="file"] {
                position: absolute;
                left: -9999px;
            }
            
            .file-input-label {
                display: inline-block;
                padding: 12px 30px;
                background: #007bff;
                color: white;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            
            .file-input-label:hover {
                background: #0056b3;
                transform: translateY(-1px);
                box-shadow: 0 5px 15px rgba(0,123,255,0.3);
            }
            
            .selected-files {
                margin-top: 20px;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .selected-file {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 15px;
                background: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            
            .selected-file-name {
                flex: 1;
                font-size: 0.9em;
                color: #495057;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .selected-file-size {
                font-size: 0.8em;
                color: #6c757d;
                margin-left: 10px;
            }
            
            .remove-file {
                background: none;
                border: none;
                color: #dc3545;
                cursor: pointer;
                font-size: 1.2em;
                padding: 0 5px;
                transition: all 0.2s ease;
            }
            
            .remove-file:hover {
                transform: scale(1.2);
            }
            
            .process-button {
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                color: white;
                padding: 15px 50px;
                border: none;
                border-radius: 50px;
                font-size: 1.1em;
                font-weight: 600;
                cursor: pointer;
                margin: 30px auto 0;
                display: block;
                transition: all 0.3s ease;
                box-shadow: 0 5px 20px rgba(0,123,255,0.3);
            }
            
            .process-button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0,123,255,0.4);
            }
            
            .process-button:disabled {
                background: #6c757d;
                cursor: not-allowed;
                box-shadow: none;
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }
            
            .feature {
                padding: 25px;
                background: white;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
            }
            
            .feature:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            }
            
            .feature-icon {
                font-size: 2.5em;
                margin-bottom: 15px;
                display: block;
            }
            
            .feature h3 {
                color: #1e3c72;
                margin-bottom: 10px;
                font-size: 1.2em;
            }
            
            .feature p {
                color: #6c757d;
                font-size: 0.95em;
                line-height: 1.6;
            }
            
            #status {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
                animation: slideIn 0.3s ease;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .success { 
                background: #d4edda; 
                color: #155724; 
                border: 1px solid #c3e6cb;
            }
            
            .error { 
                background: #f8d7da; 
                color: #721c24; 
                border: 1px solid #f5c6cb;
            }
            
            .processing { 
                background: #fff3cd; 
                color: #856404; 
                border: 1px solid #ffeaa7;
            }
            
            .progress-bar {
                width: 100%;
                height: 4px;
                background: #e9ecef;
                border-radius: 2px;
                overflow: hidden;
                margin-top: 15px;
            }
            
            .progress-bar-fill {
                height: 100%;
                background: #007bff;
                width: 0%;
                animation: progress 2s ease-in-out infinite;
            }
            
            @keyframes progress {
                0% { width: 0%; }
                50% { width: 70%; }
                100% { width: 100%; }
            }
            
            @media (max-width: 768px) {
                .container {
                    margin: 10px;
                }
                
                .header {
                    padding: 30px 20px;
                }
                
                .header h1 {
                    font-size: 2em;
                }
                
                .content {
                    padding: 20px;
                }
                
                .upload-options {
                    flex-direction: column;
                }
                
                .drop-zone {
                    padding: 40px 20px;
                }
                
                .features {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✈️ Aviation Traceability PDF Processor</h1>
                <p>Extract certificates and validate compliance according to ASA-100 standards</p>
            </div>
            
            <div class="content">
                <div class="upload-section">
                    <h2 style="text-align: center; margin-bottom: 30px; color: #1e3c72;">Upload Your Documents</h2>
                    
                    <div class="upload-options">
                        <div class="upload-option">
                            <input type="radio" name="uploadType" id="single" value="single" checked>
                            <label for="single">
                                <span class="icon">📄</span>
                                Single File
                            </label>
                        </div>
                        <div class="upload-option">
                            <input type="radio" name="uploadType" id="multiple" value="multiple">
                            <label for="multiple">
                                <span class="icon">📚</span>
                                Multiple Files
                            </label>
                        </div>
                        <div class="upload-option">
                            <input type="radio" name="uploadType" id="folder" value="folder">
                            <label for="folder">
                                <span class="icon">📁</span>
                                Entire Folder
                            </label>
                        </div>
                    </div>
                    
                    <form id="uploadForm" enctype="multipart/form-data">
                        <div class="drop-zone" id="dropZone">
                            <div class="drop-zone-icon">📤</div>
                            <div class="drop-zone-text">Drag & drop your PDF files here</div>
                            <div class="drop-zone-hint">or click to browse</div>
                            
                            <div class="file-input-wrapper">
                                <input type="file" id="fileInput" name="files" accept=".pdf" required>
                                <label for="fileInput" class="file-input-label">Choose Files</label>
                            </div>
                        </div>
                        
                        <div id="selectedFiles" class="selected-files" style="display: none;"></div>
                        
                        <button type="submit" class="process-button" id="processButton" disabled>
                            🚀 Process Documents
                        </button>
                    </form>
                </div>
                
                <div id="status"></div>
                
                <div class="features">
                    <div class="feature">
                        <span class="feature-icon">📄</span>
                        <h3>PDF Parsing</h3>
                        <p>Advanced parsing with table extraction and structure preservation</p>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔬</span>
                        <h3>Certificate Extraction</h3>
                        <p>AI-powered extraction of aviation certificates and traceability info</p>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <h3>Compliance Validation</h3>
                        <p>Automatic validation against ASA-100 requirements</p>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <h3>HTML Reports</h3>
                        <p>Professional, mobile-friendly reports with detailed analysis</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let selectedFiles = [];
            
            // Initialize
            document.addEventListener('DOMContentLoaded', function() {
                const dropZone = document.getElementById('dropZone');
                const fileInput = document.getElementById('fileInput');
                const processButton = document.getElementById('processButton');
                const selectedFilesDiv = document.getElementById('selectedFiles');
                
                // Handle upload type changes
                document.querySelectorAll('input[name="uploadType"]').forEach(radio => {
                    radio.addEventListener('change', function() {
                        updateFileInput();
                        clearSelectedFiles();
                    });
                });
                
                // Handle drag and drop
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
                    handleFileSelection(files);
                });
                
                // Handle file input change
                fileInput.addEventListener('change', (e) => {
                    const files = Array.from(e.target.files);
                    handleFileSelection(files);
                });
                
                // Handle click on drop zone
                dropZone.addEventListener('click', (e) => {
                    if (e.target === dropZone || e.target.parentElement === dropZone) {
                        fileInput.click();
                    }
                });
            });
            
            function updateFileInput() {
                const fileInput = document.getElementById('fileInput');
                const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
                const fileLabel = document.querySelector('.file-input-label');
                
                if (uploadType === 'single') {
                    fileInput.multiple = false;
                    fileInput.removeAttribute('webkitdirectory');
                    fileInput.setAttribute('accept', '.pdf');
                    fileLabel.textContent = 'Choose File';
                } else if (uploadType === 'multiple') {
                    fileInput.multiple = true;
                    fileInput.removeAttribute('webkitdirectory');
                    fileInput.setAttribute('accept', '.pdf');
                    fileLabel.textContent = 'Choose Files';
                } else if (uploadType === 'folder') {
                    fileInput.multiple = true;
                    fileInput.setAttribute('webkitdirectory', '');
                    fileInput.setAttribute('accept', '.pdf');
                    fileLabel.textContent = 'Choose Folder';
                }
            }
            
            function handleFileSelection(files) {
                const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
                
                // Filter for PDF files only
                const pdfFiles = files.filter(file => file.name.toLowerCase().endsWith('.pdf'));
                
                if (uploadType === 'single' && pdfFiles.length > 0) {
                    selectedFiles = [pdfFiles[0]];
                } else {
                    selectedFiles = pdfFiles;
                }
                
                updateSelectedFilesDisplay();
                updateProcessButton();
            }
            
            function updateSelectedFilesDisplay() {
                const selectedFilesDiv = document.getElementById('selectedFiles');
                const dropZoneText = document.querySelector('.drop-zone-text');
                const dropZoneHint = document.querySelector('.drop-zone-hint');
                
                if (selectedFiles.length === 0) {
                    selectedFilesDiv.style.display = 'none';
                    dropZoneText.textContent = 'Drag & drop your PDF files here';
                    dropZoneHint.textContent = 'or click to browse';
                    return;
                }
                
                selectedFilesDiv.style.display = 'block';
                selectedFilesDiv.innerHTML = '';
                
                dropZoneText.textContent = `${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected`;
                dropZoneHint.textContent = 'Click to change selection';
                
                selectedFiles.forEach((file, index) => {
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'selected-file';
                    
                    const fileName = document.createElement('div');
                    fileName.className = 'selected-file-name';
                    fileName.textContent = file.name;
                    
                    const fileSize = document.createElement('div');
                    fileSize.className = 'selected-file-size';
                    fileSize.textContent = formatFileSize(file.size);
                    
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-file';
                    removeBtn.innerHTML = '×';
                    removeBtn.onclick = () => removeFile(index);
                    
                    fileDiv.appendChild(fileName);
                    fileDiv.appendChild(fileSize);
                    fileDiv.appendChild(removeBtn);
                    
                    selectedFilesDiv.appendChild(fileDiv);
                });
            }
            
            function removeFile(index) {
                selectedFiles.splice(index, 1);
                updateSelectedFilesDisplay();
                updateProcessButton();
            }
            
            function clearSelectedFiles() {
                selectedFiles = [];
                updateSelectedFilesDisplay();
                updateProcessButton();
                document.getElementById('fileInput').value = '';
            }
            
            function updateProcessButton() {
                const processButton = document.getElementById('processButton');
                processButton.disabled = selectedFiles.length === 0;
            }
            
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
            }

            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                if (selectedFiles.length === 0) {
                    alert('Please select PDF file(s)');
                    return;
                }
                
                const formData = new FormData();
                
                // Append all selected files
                for (const file of selectedFiles) {
                    formData.append('files', file);
                }
                
                const statusDiv = document.getElementById('status');
                const processButton = document.getElementById('processButton');
                
                // Disable button and update UI
                processButton.disabled = true;
                processButton.textContent = '⏳ Processing...';
                
                statusDiv.style.display = 'block';
                statusDiv.className = 'processing';
                
                if (selectedFiles.length === 1) {
                    statusDiv.innerHTML = `
                        <h3>🔄 Processing Document</h3>
                        <p>Analyzing ${selectedFiles[0].name}...</p>
                        <div class="progress-bar">
                            <div class="progress-bar-fill"></div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <h3>🔄 Processing ${selectedFiles.length} Documents</h3>
                        <p>This may take several minutes. Processing files in parallel...</p>
                        <div class="progress-bar">
                            <div class="progress-bar-fill"></div>
                        </div>
                    `;
                }
                
                try {
                    const endpoint = selectedFiles.length === 1 ? '/process-pdf' : '/process-pdf-batch';
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.className = 'success';
                        
                        if (selectedFiles.length === 1) {
                            // Single file result
                            statusDiv.innerHTML = `
                                <h3>✅ Processing Complete!</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                                    <div>
                                        <strong style="color: #6c757d; font-size: 0.9em;">Document ID</strong>
                                        <p style="margin: 5px 0;">${result.document_id}</p>
                                    </div>
                                    <div>
                                        <strong style="color: #6c757d; font-size: 0.9em;">Part Number</strong>
                                        <p style="margin: 5px 0;">${result.part_number || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <strong style="color: #6c757d; font-size: 0.9em;">Traceability Type</strong>
                                        <p style="margin: 5px 0;">${result.traceability_type || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <strong style="color: #6c757d; font-size: 0.9em;">Compliance Status</strong>
                                        <p style="margin: 5px 0;">${result.compliance_status || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <strong style="color: #6c757d; font-size: 0.9em;">Processing Time</strong>
                                        <p style="margin: 5px 0;">${result.processing_time}s</p>
                                    </div>
                                </div>
                                <a href="${result.html_report_url}" target="_blank" 
                                   style="display: inline-block; margin-top: 20px; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 50px; font-weight: 600;">
                                    📊 View Detailed Report
                                </a>
                            `;
                        } else {
                            // Batch processing result
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
                    } else {
                        statusDiv.className = 'error';
                        statusDiv.innerHTML = `
                            <h3>❌ Processing Failed</h3>
                            <p>${result.message}</p>
                            <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                Try Again
                            </button>
                        `;
                    }
                    
                    // Reset button
                    processButton.textContent = '🚀 Process Documents';
                    processButton.disabled = selectedFiles.length === 0;
                    
                    // Clear files after successful processing
                    if (result.success) {
                        clearSelectedFiles();
                    }
                    
                } catch (error) {
                    statusDiv.className = 'error';
                    statusDiv.innerHTML = `
                        <h3>❌ Connection Error</h3>
                        <p>Failed to connect to the server: ${error.message}</p>
                        <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            Try Again
                        </button>
                    `;
                    
                    // Reset button
                    processButton.textContent = '🚀 Process Documents';
                    processButton.disabled = selectedFiles.length === 0;
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/process-pdf", response_model=ProcessingResult)
async def process_pdf(files: List[UploadFile] = File(...)):
    """Process uploaded PDF document(s) - if multiple files, processes first one only"""
    # Handle backward compatibility - if multiple files sent, process first one
    file = files[0] if isinstance(files, list) else files
    start_time = datetime.now()
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique document ID
    document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename.replace('.pdf', '')}"
    
    try:
        # Save uploaded file temporarily
        temp_file_path = os.path.join(TEMP_DIR, f"{document_id}.pdf")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Step 1: Parse PDF to markdown
        logger.info("Step 1: Parsing PDF...")
        markdown_content = parse_document(temp_file_path)
        
        if not markdown_content or not markdown_content.strip():
            raise Exception("Failed to extract content from PDF")
        
        # Step 2: Extract certificates from markdown
        logger.info("Step 2: Extracting certificates...")
        certificates = extractor.extract_certificates_from_text(markdown_content, file.filename)
        # print(certificates)
        if not certificates:
            raise Exception("No certificates found in document")
        
        # Step 3: Find certificate for analysis (prefer SKYLINK, fallback to first)
        target_cert = None
        for cert in certificates:
            if cert.buyer_name and "skylink" in cert.buyer_name.lower():
                target_cert = cert
                break
        
        if not target_cert:
            target_cert = certificates[0]
        
        # with open("results/target_cert.json", "w") as f:
        #     import json
        #     json.dump(target_cert, f, indent=4)

        # Step 4: Validate traceability
        logger.info("Step 3: Validating traceability...")
        certificates_dict = [asdict(cert) for cert in certificates]
        traceability_result = validator.validate_source_traceability(certificates_dict, file.filename)
        
        # Step 5: Generate HTML report
        logger.info("Step 4: Generating HTML report...")
        summary_data = {
            "cert_type": target_cert.certificate_type,
            "part_number": target_cert.part_number,
            "serial_number": target_cert.serial_number,
            "description": target_cert.description,
            "condition_code": target_cert.condition_code,
            "quantity": target_cert.quantity,
            "traceability_type": traceability_result.final_source.source_type,
            "traceability_name": traceability_result.final_source.source_name,
            "validation_notes": traceability_result.validation_notes,
            "document_name": file.filename
        }
        
        html_content = html_generator.generate_html(summary_data, file.filename)
        
        # Save HTML report
        html_filename = f"{document_id}_report.html"
        html_path = os.path.join(OUTPUT_DIR, html_filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Determine compliance status
        is_compliant = traceability_result.final_source.source_type in ['OEM', '121', '129', '135', '145']
        compliance_status = "✅ COMPLIANT" if is_compliant else "❌ NON-COMPLIANT"
        
        return ProcessingResult(
            success=True,
            message="Document processed successfully",
            document_id=document_id,
            cert_type=target_cert.certificate_type,
            part_number=target_cert.part_number,
            serial_number=target_cert.serial_number,
            description=target_cert.description,
            condition_code=target_cert.condition_code,
            quantity=target_cert.quantity,
            traceability_type=traceability_result.final_source.source_type,
            traceability_name=traceability_result.final_source.source_name,
            compliance_status=compliance_status,
            html_report_url=f"/reports/{html_filename}",
            processing_time=round(processing_time, 2),
            filename=file.filename
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        
        # Clean up temporary file if it exists
        temp_file_path = os.path.join(TEMP_DIR, f"{document_id}.pdf")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return ProcessingResult(
            success=False,
            message=f"Processing failed: {str(e)}",
            document_id=document_id,
            processing_time=round((datetime.now() - start_time).total_seconds(), 2),
            filename=file.filename
        )

async def process_single_file_async(file: UploadFile) -> ProcessingResult:
    """Process a single PDF file asynchronously"""
    start_time = datetime.now()
    
    # Generate unique document ID
    document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{file.filename.replace('.pdf', '')}"
    
    try:
        # Save uploaded file temporarily
        temp_file_path = os.path.join(TEMP_DIR, f"{document_id}.pdf")
        
        # Read file content
        content = await file.read()
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Step 1: Parse PDF to markdown
        markdown_content = parse_document(temp_file_path)
        
        if not markdown_content or not markdown_content.strip():
            raise Exception("Failed to extract content from PDF")
        
        # Step 2: Extract certificates from markdown
        certificates = extractor.extract_certificates_from_text(markdown_content, file.filename)
        
        if not certificates:
            raise Exception("No certificates found in document")
        
        # Step 3: Find certificate for analysis (prefer SKYLINK, fallback to first)
        target_cert = None
        for cert in certificates:
            if cert.buyer_name and "skylink" in cert.buyer_name.lower():
                target_cert = cert
                break
        
        if not target_cert:
            target_cert = certificates[0]
        
        # Step 4: Validate traceability
        certificates_dict = [asdict(cert) for cert in certificates]
        traceability_result = validator.validate_source_traceability(certificates_dict, file.filename)
        
        # Step 5: Generate HTML report
        summary_data = {
            "cert_type": target_cert.certificate_type,
            "part_number": target_cert.part_number,
            "serial_number": target_cert.serial_number,
            "description": target_cert.description,
            "condition_code": target_cert.condition_code,
            "quantity": target_cert.quantity,
            "traceability_type": traceability_result.final_source.source_type,
            "traceability_name": traceability_result.final_source.source_name,
            "validation_notes": traceability_result.validation_notes,
            "document_name": file.filename
        }
        
        html_content = html_generator.generate_html(summary_data, file.filename)
        
        # Save HTML report
        html_filename = f"{document_id}_report.html"
        html_path = os.path.join(OUTPUT_DIR, html_filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Determine compliance status
        is_compliant = traceability_result.final_source.source_type in ['OEM', '121', '129', '135', '145']
        compliance_status = "✅ COMPLIANT" if is_compliant else "❌ NON-COMPLIANT"
        
        return ProcessingResult(
            success=True,
            message="Document processed successfully",
            document_id=document_id,
            cert_type=target_cert.certificate_type,
            part_number=target_cert.part_number,
            serial_number=target_cert.serial_number,
            description=target_cert.description,
            condition_code=target_cert.condition_code,
            quantity=target_cert.quantity,
            traceability_type=traceability_result.final_source.source_type,
            traceability_name=traceability_result.final_source.source_name,
            compliance_status=compliance_status,
            html_report_url=f"/reports/{html_filename}",
            processing_time=round(processing_time, 2),
            filename=file.filename
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {str(e)}")
        
        # Clean up temporary file if it exists
        temp_file_path = os.path.join(TEMP_DIR, f"{document_id}.pdf")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return ProcessingResult(
            success=False,
            message=f"Processing failed: {str(e)}",
            document_id=document_id,
            processing_time=round((datetime.now() - start_time).total_seconds(), 2),
            filename=file.filename
        )

@app.post("/process-pdf-batch", response_model=BatchProcessingResult)
async def process_pdf_batch(files: List[UploadFile] = File(...)):
    """Process multiple PDF documents in batch"""
    start_time = datetime.now()
    
    # Generate unique batch ID
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Filter for PDF files only
    pdf_files = [file for file in files if file.filename.lower().endswith('.pdf')]
    
    if not pdf_files:
        raise HTTPException(status_code=400, detail="No PDF files found")
    
    logger.info(f"Processing batch of {len(pdf_files)} PDF files")
    
    # Process files in parallel with a reasonable concurrency limit
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent processes
    
    async def process_with_semaphore(file):
        async with semaphore:
            return await process_single_file_async(file)
    
    # Process all files
    tasks = [process_with_semaphore(file) for file in pdf_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to ProcessingResult objects
    processing_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processing_results.append(ProcessingResult(
                success=False,
                message=f"Processing failed: {str(result)}",
                document_id=f"failed_{i}",
                processing_time=0,
                filename=pdf_files[i].filename
            ))
        else:
            processing_results.append(result)
    
    # Generate batch dashboard
    successful_results = [r for r in processing_results if r.success]
    failed_results = [r for r in processing_results if not r.success]
    
    # Create batch dashboard HTML
    dashboard_html = generate_batch_dashboard(batch_id, processing_results)
    dashboard_filename = f"{batch_id}_dashboard.html"
    dashboard_path = os.path.join(OUTPUT_DIR, dashboard_filename)
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    # Calculate total processing time
    total_processing_time = (datetime.now() - start_time).total_seconds()
    
    return BatchProcessingResult(
        success=True,
        message=f"Batch processing completed. {len(successful_results)} successful, {len(failed_results)} failed.",
        batch_id=batch_id,
        total_files=len(pdf_files),
        successful_files=len(successful_results),
        failed_files=len(failed_results),
        processing_results=processing_results,
        total_processing_time=round(total_processing_time, 2),
        dashboard_url=f"/reports/{dashboard_filename}"
    )

def generate_batch_dashboard(batch_id: str, results: List[ProcessingResult]) -> str:
    """Generate HTML dashboard for batch processing results"""
    
    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]
    compliance_count = sum(1 for r in successful_results if r.traceability_type in ['OEM', '121', '129', '135', '145'])
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Batch Processing Results - {batch_id}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 10px;
            }}
            
            .dashboard-container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            
            .dashboard-header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 25px;
                text-align: center;
            }}
            
            .dashboard-header h1 {{
                font-size: 2.2em;
                margin-bottom: 10px;
                font-weight: 300;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 20px;
                background: #f8f9fa;
            }}
            
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-left: 4px solid #007bff;
            }}
            
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 5px;
            }}
            
            .stat-label {{
                color: #6c757d;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .results-section {{
                padding: 20px;
            }}
            
            .section-title {{
                font-size: 1.5em;
                margin-bottom: 20px;
                color: #1e3c72;
            }}
            
            .results-grid {{
                display: grid;
                gap: 15px;
            }}
            
            .result-card {{
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            .result-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                flex-wrap: wrap;
                gap: 10px;
            }}
            
            .result-filename {{
                font-weight: 600;
                color: #343a40;
                font-size: 1.1em;
            }}
            
            .status-badge {{
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                white-space: nowrap;
            }}
            
            .status-success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            
            .status-error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            
            .result-details {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}
            
            .detail-item {{
                display: flex;
                flex-direction: column;
            }}
            
            .detail-label {{
                font-size: 0.8em;
                color: #6c757d;
                text-transform: uppercase;
                margin-bottom: 3px;
            }}
            
            .detail-value {{
                color: #212529;
                font-weight: 500;
            }}
            
            .report-link {{
                color: #007bff;
                text-decoration: none;
                font-weight: bold;
            }}
            
            .report-link:hover {{
                text-decoration: underline;
            }}
            
            .timestamp {{
                text-align: center;
                color: #6c757d;
                font-size: 0.8em;
                padding: 20px;
                border-top: 1px solid #dee2e6;
            }}
            
            @media (max-width: 768px) {{
                .stats-grid {{
                    grid-template-columns: 1fr 1fr;
                }}
                
                .result-details {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="dashboard-header">
                <h1>📊 Batch Processing Results</h1>
                <p>Batch ID: {batch_id}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{len(results)}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(successful_results)}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(failed_results)}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{compliance_count}</div>
                    <div class="stat-label">Compliant</div>
                </div>
            </div>
            
            <div class="results-section">
                <h2 class="section-title">Processing Results</h2>
                <div class="results-grid">
    """
    
    # Sort results: successful first, then failed
    sorted_results = sorted(results, key=lambda x: (not x.success, x.filename))
    
    for result in sorted_results:
        status_class = "status-success" if result.success else "status-error"
        status_text = "✅ SUCCESS" if result.success else "❌ FAILED"
        
        dashboard_html += f"""
                    <div class="result-card">
                        <div class="result-header">
                            <div class="result-filename">{result.filename}</div>
                            <div class="status-badge {status_class}">{status_text}</div>
                        </div>
                        
                        <div class="result-details">
                            <div class="detail-item">
                                <div class="detail-label">Document ID</div>
                                <div class="detail-value">{result.document_id}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Processing Time</div>
                                <div class="detail-value">{result.processing_time}s</div>
                            </div>
        """
        
        if result.success:
            dashboard_html += f"""
                            <div class="detail-item">
                                <div class="detail-label">Part Number</div>
                                <div class="detail-value">{result.part_number or 'N/A'}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Traceability Type</div>
                                <div class="detail-value">{result.traceability_type or 'N/A'}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Compliance Status</div>
                                <div class="detail-value">{result.compliance_status or 'N/A'}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Report</div>
                                <div class="detail-value">
                                    <a href="{result.html_report_url}" target="_blank" class="report-link">
                                        View Report
                                    </a>
                                </div>
                            </div>
            """
        else:
            dashboard_html += f"""
                            <div class="detail-item">
                                <div class="detail-label">Error Message</div>
                                <div class="detail-value">{result.message}</div>
                            </div>
            """
        
        dashboard_html += """
                        </div>
                    </div>
        """
    
    dashboard_html += f"""
                </div>
            </div>
            
            <div class="timestamp">
                Dashboard generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/docs")
async def get_api_docs():
    """Get API documentation"""
    return {
        "title": "Aviation Traceability PDF Processor API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process-pdf": "Upload and process PDF document",
            "GET /health": "Health check",
            "GET /reports/{filename}": "Access generated HTML reports"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 