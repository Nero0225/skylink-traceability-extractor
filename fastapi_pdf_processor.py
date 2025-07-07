from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from dataclasses import asdict

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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aviation Traceability PDF Processor</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            h1 { 
                color: #1e3c72;
                text-align: center;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 2px dashed #007bff;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                background: #f8f9fa;
            }
            .upload-area:hover {
                background: #e9ecef;
            }
            input[type="file"] {
                margin: 20px 0;
                padding: 10px;
                font-size: 16px;
            }
            button {
                background: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                margin: 10px 0;
            }
            button:hover {
                background: #0056b3;
            }
            .info {
                background: #e7f3ff;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-left: 4px solid #007bff;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                text-align: center;
            }
            .feature h3 {
                color: #1e3c72;
                margin-bottom: 10px;
            }
            #status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .processing { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✈️ Aviation Traceability PDF Processor</h1>
            
            <div class="info">
                <h3>🔍 What This Does</h3>
                <p>Upload aviation documentation PDFs to automatically extract certificate information and validate traceability compliance according to ASA-100 standards.</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>📄 PDF Parsing</h3>
                    <p>Advanced PDF parsing with table extraction and structure preservation</p>
                </div>
                <div class="feature">
                    <h3>🔬 Certificate Extraction</h3>
                    <p>AI-powered extraction of aviation certificates and traceability information</p>
                </div>
                <div class="feature">
                    <h3>✅ Compliance Validation</h3>
                    <p>Automatic validation against ASA-100 requirements and regulatory standards</p>
                </div>
                <div class="feature">
                    <h3>📊 HTML Reports</h3>
                    <p>Professional, mobile-friendly HTML reports with detailed analysis</p>
                </div>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area">
                    <h3>📁 Upload PDF Document</h3>
                    <input type="file" name="file" accept=".pdf" required>
                    <br>
                    <button type="submit">🚀 Process Document</button>
                </div>
            </form>
            
            <div id="status"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.querySelector('input[type="file"]');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a PDF file');
                    return;
                }
                
                formData.append('file', file);
                
                const statusDiv = document.getElementById('status');
                statusDiv.style.display = 'block';
                statusDiv.className = 'processing';
                statusDiv.innerHTML = '🔄 Processing document... This may take a few minutes.';
                
                try {
                    const response = await fetch('/process-pdf', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.className = 'success';
                        statusDiv.innerHTML = `
                            <h3>✅ Processing Complete!</h3>
                            <p><strong>Document ID:</strong> ${result.document_id}</p>
                            <p><strong>Part Number:</strong> ${result.part_number || 'N/A'}</p>
                            <p><strong>Traceability Type:</strong> ${result.traceability_type || 'N/A'}</p>
                            <p><strong>Compliance Status:</strong> ${result.compliance_status || 'N/A'}</p>
                            <p><strong>Processing Time:</strong> ${result.processing_time}s</p>
                            <br>
                            <a href="${result.html_report_url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">
                                📊 View Detailed HTML Report
                            </a>
                        `;
                    } else {
                        statusDiv.className = 'error';
                        statusDiv.innerHTML = `<h3>❌ Error</h3><p>${result.message}</p>`;
                    }
                } catch (error) {
                    statusDiv.className = 'error';
                    statusDiv.innerHTML = `<h3>❌ Error</h3><p>Failed to process document: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/process-pdf", response_model=ProcessingResult)
async def process_pdf(file: UploadFile = File(...)):
    """Process uploaded PDF document"""
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
            processing_time=round(processing_time, 2)
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
            processing_time=round((datetime.now() - start_time).total_seconds(), 2)
        )

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