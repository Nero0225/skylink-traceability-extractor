# Aviation Traceability PDF Processor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68%2B-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive **FastAPI-based web application** for processing aviation traceability documents and validating compliance against **ASA-100 standards** and **FAA regulations**. This system provides automated PDF parsing, certificate extraction, and traceability validation with a modern web interface.

## 🚀 Features

### 📄 **Advanced PDF Processing**
- **Multi-format Support**: Handles complex aviation PDFs with tables, forms, and certificates
- **Intelligent Parsing**: Uses LlamaCloud for high-accuracy document structure preservation
- **Batch Processing**: Process multiple documents simultaneously with parallel execution
- **Content Extraction**: Converts PDFs to structured markdown for analysis

### 🔍 **AI-Powered Certificate Extraction**
- **GPT-4 Integration**: Leverages OpenAI's most advanced model for precise certificate identification
- **Multi-Certificate Support**: Extracts multiple certificates from single documents
- **Structured Data**: Converts unstructured documents into structured certificate data
- **Validation Logic**: Validates part numbers, certificate types, and data integrity

### ✅ **Regulatory Compliance Validation**
- **ASA-100 Standards**: Validates against Aerospace Standard ASA-100 Appendix A requirements
- **FAA Regulations**: Ensures compliance with Federal Aviation Administration standards
- **Regulated Source Verification**: Validates traceability to approved sources (OEM, 121, 129, 135, 145)
- **Chain Integrity**: Ensures complete traceability chains without breaks

### 🌐 **Modern Web Interface**
- **Drag & Drop Upload**: Intuitive file upload with preview
- **Real-time Processing**: Live status updates during document processing
- **Responsive Design**: Mobile-friendly interface with modern UI/UX
- **Batch Dashboard**: Comprehensive results dashboard for multiple documents

### 📊 **Professional Reporting**
- **HTML Reports**: Generate detailed, professional compliance reports
- **Batch Analytics**: Statistical analysis of processing results
- **Compliance Metrics**: Success rates, compliance percentages, and detailed breakdowns
- **Export Options**: Downloadable reports for record-keeping

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   FastAPI Server    │    │   PDF Parser        │    │ Certificate         │
│   (Web Interface)   │───▶│   (LlamaCloud)      │───▶│ Extractor (GPT-4)   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                                                      │
           ▼                                                      ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   HTML Generator    │    │   Traceability      │    │   Validation        │
│   (Report Output)   │◀───│   Validator         │◀───│   Engine            │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **PDF Processing**: LlamaCloud API
- **AI Analysis**: OpenAI GPT-4
- **Frontend**: Modern HTML5/CSS3/JavaScript
- **Storage**: Local file system with organized directory structure
- **Deployment**: Uvicorn ASGI server

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for batch processing)
- **Storage**: 1GB free space for temporary files and reports
- **Network**: Internet connection for API calls

### API Keys Required
- **OpenAI API Key**: For GPT-4 certificate extraction and validation
- **LlamaCloud API Key**: For PDF parsing and content extraction

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-org/aviation-traceability-processor.git
cd aviation-traceability-processor
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
LLAMA_CLOUD_API_KEY=your_llamacloud_api_key_here

# Optional Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_PROCESSES=3
TEMP_DIR=temp_uploads
OUTPUT_DIR=processed_reports
```

### 5. Directory Setup
The application will automatically create necessary directories:
```
aviation-traceability-processor/
├── temp_uploads/           # Temporary PDF storage
├── processed_reports/      # Generated HTML reports
├── markdowns/             # Parsed document content (optional)
└── logs/                  # Application logs
```

## 🚀 Quick Start

### 1. Start the Application
```bash
python index.py
```

### 2. Access Web Interface
Open your browser and navigate to:
- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Upload Documents
1. Drag and drop PDF files onto the upload area
2. Click "Process Documents" to start analysis
3. Monitor real-time processing status
4. View results in the generated dashboard

## 📖 Usage Guide

### Single Document Processing

**Endpoint**: `POST /process-pdf`

```python
import requests

files = {'files': open('certificate.pdf', 'rb')}
response = requests.post('http://localhost:8000/process-pdf', files=files)
result = response.json()

print(f"Success: {result['success']}")
print(f"Compliance: {result['compliance_status']}")
print(f"Report URL: {result['html_report_url']}")
```

### Batch Processing

**Endpoint**: `POST /process-pdf-batch`

```python
import requests

files = [
    ('files', open('cert1.pdf', 'rb')),
    ('files', open('cert2.pdf', 'rb')),
    ('files', open('cert3.pdf', 'rb'))
]

response = requests.post('http://localhost:8000/process-pdf-batch', files=files)
result = response.json()

print(f"Total Files: {result['total_files']}")
print(f"Success Rate: {result['successful_files']}/{result['total_files']}")
print(f"Dashboard: {result['dashboard_url']}")
```

### Web Interface Workflow

1. **Upload Phase**
   - Select multiple PDF files
   - Preview selected files with size information
   - Remove unwanted files before processing

2. **Processing Phase**
   - Real-time progress indicators
   - Parallel processing for efficiency
   - Error handling for invalid files

3. **Results Phase**
   - Comprehensive dashboard with metrics
   - Individual document reports
   - Downloadable compliance documentation

## 🔍 Certificate Extraction

### Supported Certificate Types

The system recognizes and extracts the following aviation certificate types:

| Certificate Type | Description | Compliance Level |
|------------------|-------------|------------------|
| **ATA-106** | Part or Material Certification Form | High |
| **FAA 8130-3** | Authorized Release Certificate | High |
| **COC** | Certificate of Conformance/Conformity | Medium |
| **Material Cert** | Material Certification | Medium |
| **OEM Cert** | OEM Manufacturer Certification | Highest |
| **European COC** | European Certificate of Conformity (EN10204) | Medium |

### Extraction Process

1. **PDF Parsing**: Convert PDF to structured markdown
2. **Content Analysis**: Identify certificate sections and tables
3. **Data Extraction**: Extract key fields using AI analysis
4. **Validation**: Verify part numbers, dates, and signatures
5. **Structuring**: Convert to standardized data format

### Extracted Data Fields

```json
{
  "certificate_type": "FAA Form 8130-3",
  "part_number": "2606672-4",
  "serial_number": "ABC123",
  "description": "Valve Assembly",
  "condition_code": "NE",
  "quantity": "1",
  "manufacturer": "Honeywell",
  "seller_name": "Aircraft Parts Logistic",
  "buyer_name": "SKYLINK, INC.",
  "certification_date": "2023-10-15",
  "authorized_signature": "John Smith",
  "traceability_source": "US Airways"
}
```

## ✅ Traceability Validation

### Regulated Source Hierarchy

The system validates traceability against the following regulated sources (in order of preference):

#### 🏭 **OEM (Original Equipment Manufacturer)** - HIGHEST
- **Description**: The manufacturer who actually produced the part
- **Examples**: Boeing, Airbus, Honeywell, Collins Aerospace
- **Validation**: Direct manufacturer certification
- **Compliance**: Highest level of traceability

#### ✈️ **121 Domestic Airlines** - HIGH
- **Description**: US-based airlines operating domestically
- **Examples**: Delta Airlines, American Airlines, United Airlines
- **Validation**: Parts removed from active airline operations
- **Compliance**: High confidence in maintenance standards

#### 🌍 **129 Foreign Airlines** - HIGH
- **Description**: Foreign airlines operating in the USA
- **Examples**: Japan Airlines, China Airlines, Lufthansa
- **Validation**: FAA oversight for US operations
- **Compliance**: High confidence due to FAA regulation

#### 📦 **135 Charter/Cargo Operators** - HIGH
- **Description**: Charter and cargo operators
- **Examples**: FedEx, UPS, DHL
- **Validation**: FAA-regulated fleet operations
- **Compliance**: High confidence in part provenance

#### 🔧 **145 Repair Stations** - HIGH
- **Description**: FAA-approved repair stations
- **Examples**: AAR, Lufthansa Technik, Delta TechOps
- **Validation**: FAA certification verification
- **Compliance**: High confidence in repair/overhaul standards

#### 🌐 **Foreign Operators** - MEDIUM
- **Description**: Foreign operators not flying to USA
- **Validation**: Limited FAA oversight
- **Compliance**: Medium confidence level

### Validation Process

1. **Chain Construction**: Build complete seller-to-buyer chain
2. **Source Identification**: Identify all entities in the chain
3. **Regulation Verification**: Validate each entity against FAA databases
4. **Fraud Detection**: Identify entities falsely claiming regulation
5. **Compliance Assessment**: Determine overall chain compliance

### Compliance Determination

```python
# Example validation logic
def determine_compliance(chain):
    if has_fraudulent_entities(chain):
        return "NON-COMPLIANT - Fraudulent entity detected"
    
    if traces_to_regulated_source(chain):
        return "COMPLIANT - Valid regulated source"
    
    return "NON-COMPLIANT - No regulated source found"
```

## 📊 ASA-100 Compliance

### Standard Requirements

The system validates against **ASA-100 Appendix A** requirements for different part categories:

| Part Category | Receipt Requirements | Shipment Requirements |
|---------------|---------------------|----------------------|
| **Consumable Materials** | Statement of identity | Identity statement + original on file |
| **Raw Materials** | Physical/chemical properties reports | Certified true copy of reports |
| **Standard Parts** | Certificate of Conformity | Certified true copy of C of C |
| **New Parts (TC Holder)** | Certified statement of identity/condition | Statement of identity/condition |
| **New Parts (PAH)** | FAA Form 8130-3 or part marking | Certified copy of approval document |
| **Used Parts (Approved)** | Approval for return to service | Approval for return to service |
| **Used Parts (Unapproved)** | Certified statement of condition | Statement of condition |

### Compliance Validation

The system automatically:
- Identifies part categories based on part numbers and descriptions
- Validates required documentation is present
- Checks for proper certification and signatures
- Ensures traceability to approved sources
- Generates compliance reports with specific findings

## 📈 Reporting and Analytics

### Individual Document Reports

Each processed document generates a comprehensive HTML report containing:

- **Executive Summary**: Compliance status and key findings
- **Certificate Details**: Complete extracted certificate information
- **Traceability Chain**: Visual representation of the supply chain
- **Compliance Analysis**: ASA-100 requirement validation
- **Recommendations**: Specific actions for non-compliant items

### Batch Processing Dashboard

For multiple documents, the system provides:

- **Statistical Overview**: Success rates, compliance percentages
- **Source Distribution**: Breakdown by regulated source types
- **Compliance Metrics**: Detailed compliance analysis
- **Problem Areas**: Common issues and recommendations
- **Downloadable Reports**: Individual and summary reports

### Sample Report Metrics

```json
{
  "total_files": 25,
  "successful_files": 23,
  "failed_files": 2,
  "compliance_rate": "92%",
  "source_breakdown": {
    "OEM": 12,
    "121": 8,
    "145": 3
  },
  "common_issues": [
    "Missing material certification",
    "Incomplete traceability chain",
    "Invalid part number format"
  ]
}
```

## 🔧 Configuration

### Environment Variables

```env
# API Configuration
OPENAI_API_KEY=your_openai_key
LLAMA_CLOUD_API_KEY=your_llama_key

# Processing Configuration
MAX_CONCURRENT_PROCESSES=3
PROCESSING_TIMEOUT=300
BATCH_SIZE_LIMIT=50

# Storage Configuration
TEMP_DIR=temp_uploads
OUTPUT_DIR=processed_reports
CLEANUP_TEMP_FILES=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Advanced Configuration

```python
# config.py
class Config:
    # PDF Processing
    PDF_MAX_SIZE_MB = 50
    PDF_ALLOWED_EXTENSIONS = ['.pdf']
    
    # AI Processing
    OPENAI_MODEL = "gpt-4o"
    OPENAI_TEMPERATURE = 0.0
    OPENAI_MAX_TOKENS = 6000
    
    # Validation
    STRICT_VALIDATION = True
    REQUIRE_COMPLETE_CHAIN = True
    
    # Reporting
    GENERATE_DETAILED_REPORTS = True
    INCLUDE_SOURCE_DOCUMENTS = False
```

## 🚨 Error Handling

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **API Key Error** | Missing or invalid API keys | Check `.env` file configuration |
| **PDF Parse Error** | Corrupted or unsupported PDF | Verify PDF integrity and format |
| **Timeout Error** | Large document processing | Increase `PROCESSING_TIMEOUT` value |
| **Memory Error** | Insufficient system memory | Reduce `MAX_CONCURRENT_PROCESSES` |
| **Network Error** | API connectivity issues | Check internet connection and API status |

### Error Response Format

```json
{
  "success": false,
  "message": "Processing failed: Invalid PDF format",
  "error_code": "PDF_PARSE_ERROR",
  "document_id": "doc_20231015_143022_certificate",
  "timestamp": "2023-10-15T14:30:22Z"
}
```

## 🔒 Security Considerations

### Data Protection
- **Temporary Files**: Automatically cleaned up after processing
- **API Keys**: Stored securely in environment variables
- **Document Privacy**: No documents stored permanently on server
- **Access Control**: Local deployment for sensitive documents

### Best Practices
- Use environment variables for all sensitive configuration
- Regularly rotate API keys
- Monitor API usage and costs
- Implement proper logging for audit trails
- Use HTTPS in production deployments

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_extraction.py
python -m pytest tests/test_validation.py
python -m pytest tests/test_api.py
```

### Integration Tests
```bash
# Test complete processing pipeline
python -m pytest tests/integration/

# Test with sample documents
python -m pytest tests/integration/test_sample_docs.py
```

### Performance Tests
```bash
# Load testing
python -m pytest tests/performance/test_batch_processing.py

# Memory usage testing
python -m pytest tests/performance/test_memory_usage.py
```

## 📚 API Documentation

### Interactive Documentation
Access the automatically generated API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/process-pdf` | POST | Process single PDF |
| `/process-pdf-batch` | POST | Process multiple PDFs |
| `/health` | GET | Health check |
| `/reports/{filename}` | GET | Access generated reports |

### Response Models

```python
class ProcessingResult(BaseModel):
    success: bool
    message: str
    document_id: Optional[str]
    cert_type: Optional[str]
    part_number: Optional[str]
    compliance_status: Optional[str]
    html_report_url: Optional[str]
    processing_time: Optional[float]
```

## 🚀 Deployment

### Local Development
```bash
python index.py
```

### Production Deployment

#### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "fastapi_pdf_processor:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Using Systemd (Linux)
```ini
[Unit]
Description=Aviation Traceability Processor
After=network.target

[Service]
Type=simple
User=aviation
WorkingDirectory=/opt/aviation-processor
ExecStart=/opt/aviation-processor/venv/bin/python index.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment-Specific Configuration

```bash
# Development
export ENVIRONMENT=development
export DEBUG=true

# Production
export ENVIRONMENT=production
export DEBUG=false
export WORKERS=4
```

## 📊 Performance Metrics

### Processing Benchmarks
- **Single Document**: 15-30 seconds average
- **Batch Processing**: 3-5 documents per minute
- **Memory Usage**: 200-500MB per document
- **Accuracy Rate**: 95%+ for standard aviation certificates

### Optimization Tips
1. **Parallel Processing**: Enable for batch operations
2. **Memory Management**: Monitor for large document batches
3. **API Rate Limits**: Respect OpenAI and LlamaCloud limits
4. **Caching**: Implement for repeated document processing

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Make your changes
5. Run tests: `python -m pytest`
6. Submit a pull request

### Code Standards
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations
- **Documentation**: Document all functions and classes
- **Testing**: Write tests for new functionality

### Areas for Contribution
- Additional certificate type support
- Enhanced validation rules
- Performance optimizations
- UI/UX improvements
- Integration with external systems

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **API Docs**: http://localhost:8000/docs
- **User Guide**: See Usage section above
- **Examples**: Check `examples/` directory

### Getting Help
- **Issues**: Report bugs on GitHub Issues
- **Questions**: Use GitHub Discussions
- **Email**: support@aviation-traceability.com

### Troubleshooting
1. Check the logs in `logs/app.log`
2. Verify API key configuration
3. Ensure all dependencies are installed
4. Check system requirements

## 🎯 Roadmap

### Version 2.0 (Planned)
- [ ] Real-time document collaboration
- [ ] Advanced analytics dashboard
- [ ] Integration with ERP systems
- [ ] Mobile application
- [ ] Multi-language support

### Version 1.5 (In Progress)
- [ ] Enhanced fraud detection
- [ ] Automated compliance reporting
- [ ] Performance optimizations
- [ ] Extended certificate type support

### Version 1.0 (Current)
- [x] Core PDF processing
- [x] Certificate extraction
- [x] Traceability validation
- [x] Web interface
- [x] Batch processing

---

**Built with ❤️ for aviation safety and compliance**

*For more information, visit our [documentation site](https://aviation-traceability-docs.com) or contact our support team.* 