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

# Configuration for directories
TEMP_DIR = "temp_uploads"
OUTPUT_DIR = "processed_reports"
PUBLIC_DIR = "public"

def setup_directories():
    """Create and setup all required directories"""
    directories = [
        TEMP_DIR,
        OUTPUT_DIR,
        PUBLIC_DIR,
        os.path.join(PUBLIC_DIR, "css"),
        os.path.join(PUBLIC_DIR, "js"),
        os.path.join(PUBLIC_DIR, "assets"),
        os.path.join(PUBLIC_DIR, "assets", "images"),
        os.path.join(PUBLIC_DIR, "assets", "documents"),
        os.path.join(PUBLIC_DIR, "assets", "fonts"),
        os.path.join(PUBLIC_DIR, "assets", "data")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")

# Setup directories on startup
setup_directories()

def check_public_files():
    """Check if public files exist and log status"""
    public_files = [
        ("main.html", "Main application page"),
        ("index.html", "Public demo page"),
        ("css/styles.css", "Main stylesheet"),
        ("js/app.js", "Main JavaScript file")
    ]
    
    logger.info("Checking public files availability:")
    for file_path, description in public_files:
        full_path = os.path.join(PUBLIC_DIR, file_path)
        status = "✅ Available" if os.path.exists(full_path) else "❌ Missing"
        logger.info(f"  {description}: {status}")

# Check public files on startup
check_public_files()

# Mount static files for serving generated HTML reports and public assets
app.mount("/reports", StaticFiles(directory=OUTPUT_DIR), name="reports")
app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

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
    """Root endpoint with upload form - now serves from public folder if available"""
    try:
        # Try to serve the main page from public folder
        main_page_path = os.path.join(PUBLIC_DIR, "main.html")
        if os.path.exists(main_page_path):
            with open(main_page_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.warning(f"Could not serve from public folder: {e}")
    
    # Fallback to embedded HTML with enhanced styling
    return """
        404 Page not found.
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
        
        # print("="*100)
        # print(certificates)
        # print("="*100)

        logger.info(f"Target cert: {certificates}")

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
    
    print("="*100)
    print(results)
    print("="*100)
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

@app.get("/public-demo", response_class=HTMLResponse)
async def public_demo():
    """Serve the public demo page"""
    try:
        with open(os.path.join(PUBLIC_DIR, "index.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Public demo page not found</h1><p>Please ensure the public/index.html file exists.</p>",
            status_code=404
        )

@app.get("/public/{file_path:path}", response_class=HTMLResponse)
async def serve_public_file(file_path: str):
    """Serve custom HTML files from public directory"""
    try:
        # Security check - prevent directory traversal
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Only serve HTML files through this endpoint
        if not file_path.endswith('.html'):
            raise HTTPException(status_code=400, detail="Only HTML files can be served through this endpoint")
        
        full_path = os.path.join(PUBLIC_DIR, file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving public file {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
            "GET /": "Main application interface",
            "POST /process-pdf": "Upload and process single PDF document",
            "POST /process-pdf-batch": "Upload and process multiple PDF documents",
            "GET /public-demo": "Public demo page",
            "GET /public/{file_path}": "Serve custom HTML files from public directory",
            "GET /public/": "Static files (CSS, JS, assets) from public directory",
            "GET /reports/{filename}": "Access generated HTML reports",
            "GET /health": "Health check endpoint",
            "GET /api/docs": "This API documentation"
        },
        "public_folder": {
            "description": "Static files served from public/ directory",
            "structure": {
                "public/": "Root public directory",
                "public/css/": "Stylesheets",
                "public/js/": "JavaScript files",
                "public/assets/": "Static assets (images, documents, fonts, data)"
            },
            "access_examples": {
                "HTML files": "GET /public/custom-page.html",
                "CSS files": "GET /public/css/styles.css",
                "JS files": "GET /public/js/app.js",
                "Assets": "GET /public/assets/images/logo.png"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 