# Aviation Certificate Extractor

A Python application that uses OpenAI's GPT-4 API to extract certificate information from aviation documents. This tool is designed to parse various types of aviation certificates, including ATA 106 forms, FAA 8130-3 tags, Certificates of Conformance, and more.

## Features

- **Multi-format Support**: Extracts certificates from various aviation document types
- **Structured Output**: Returns organized JSON data with all certificate details
- **Batch Processing**: Process multiple documents at once
- **Comprehensive Extraction**: Captures part numbers, traceability, certification details, and more
- **Summary Reports**: Generates detailed summaries of extracted data

## Supported Certificate Types

1. **Part or Material Certification Form (ATA Specification 106)**
2. **FAA Form 8130-3 (Authorized Release Certificate)**
3. **Certificate of Conformance/Conformity**
4. **Material Certification**
5. **Work Order Documentation**
6. **Teardown Report**
7. **Packing Slip with Certification**
8. **Bill of Sale**
9. **Consignment Documentation**
10. **OEM Manufacturer Certification**
11. **European Certificate of Conformity (EN10204)**

## Installation

1. Clone or download the repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### OpenAI API Key

You need an OpenAI API key to use this tool. Get one from [OpenAI's platform](https://platform.openai.com/api-keys).

Set your API key using one of these methods:

**Method 1: Environment Variable**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Method 2: .env file**
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

**Method 3: Direct in code**
```python
from certificate_extractor import CertificateExtractor
extractor = CertificateExtractor(api_key="your-api-key-here")
```

## Usage

### Basic Usage

```python
from certificate_extractor import CertificateExtractor

# Initialize extractor
extractor = CertificateExtractor()

# Process all files in markdowns directory
results = extractor.process_directory("markdowns")

# Save results to JSON file
extractor.save_results(results)
```

### Command Line

Run the main script to process all markdown files:
```bash
python certificate_extractor.py
```

### Example Scripts

Run the example script to see different usage patterns:
```bash
python example_usage.py
```

## Data Structure

Each extracted certificate contains the following information:

```python
@dataclass
class CertificateInfo:
    certificate_type: str           # Type of certificate
    document_source: str            # Source document filename
    part_number: str               # Part number
    serial_number: str             # Serial number
    description: str               # Part description
    condition_code: str            # Condition (NS, OH, NE, SV, etc.)
    quantity: str                  # Quantity
    batch_lot: str                 # Batch/lot number
    manufacturer: str              # Manufacturer name
    seller_name: str               # Seller company
    buyer_name: str                # Buyer company
    purchase_order: str            # PO number
    invoice_number: str            # Invoice number
    certification_date: str        # Date of certification
    authorized_signature: str      # Signatory name
    approval_number: str           # Approval/certificate number
    traceability_source: str       # Traceability information
    last_operator: str             # Last operator/airline
    work_performed: str            # Work performed (if applicable)
    airworthiness_authority: str   # FAA, EASA, etc.
    non_incident_statement: str    # Non-incident declaration
    additional_notes: str          # Additional remarks
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "extraction_results": {
    "document1.md": [
      {
        "certificate_type": "Part or Material Certification Form (ATA Specification 106)",
        "document_source": "document1.md",
        "part_number": "2606672-4",
        "serial_number": "B8093",
        "description": "BRAKE",
        "condition_code": "OH",
        "quantity": "1",
        "manufacturer": "B & W Aviation Corp",
        "seller_name": "Aircraft Parts Logistic",
        "buyer_name": "SKYLINK, INC.",
        "purchase_order": "156414",
        "invoice_number": "14142",
        "certification_date": "02/21/2025",
        "authorized_signature": "Giancarlo S Campodonico",
        "traceability_source": "PO 11421 - 145-Logistica Aeroespacial S.A. de C.V",
        "last_operator": "B & W Aviation Corp",
        "airworthiness_authority": "FAA",
        "non_incident_statement": "The Part(s) is / are not from a military or government source and has / have not been subjected to severe stress or heat"
      }
    ]
  },
  "summary": {
    "total_documents_processed": 9,
    "total_certificates_extracted": 25,
    "certificates_by_type": {
      "Part or Material Certification Form (ATA Specification 106)": 12,
      "FAA Form 8130-3 (Authorized Release Certificate)": 3,
      "Certificate of Conformance/Conformity": 8,
      "Material Certification": 2
    },
    "certificates_by_condition": {
      "NS": 15,
      "OH": 5,
      "NE": 3,
      "SV": 2
    },
    "extraction_timestamp": "2025-01-26T10:30:00"
  }
}
```

## Configuration

### Model Selection

The default model is `gpt-4o`. You can modify this in the `CertificateExtractor` class:

```python
response = self.client.chat.completions.create(
    model="gpt-4o",  # Change to your preferred model
    messages=[...],
    temperature=0.1,
    max_tokens=4000
)
```

### Processing Parameters

- **Temperature**: Set to 0.1 for consistent results
- **Max Tokens**: 4000 tokens per request
- **Model**: GPT-4o recommended for best accuracy

## Error Handling

The tool includes comprehensive error handling:

- **API Errors**: Logs OpenAI API errors and continues processing
- **File Errors**: Handles missing files gracefully
- **JSON Parsing**: Robust JSON extraction from API responses
- **Encoding Issues**: Handles various text encodings

## Performance Considerations

- **API Costs**: Each document processed uses OpenAI API tokens
- **Rate Limits**: The tool respects OpenAI's rate limits
- **Batch Size**: Process documents in batches to optimize API usage
- **Caching**: Consider implementing caching for repeated extractions

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure your OpenAI API key is properly set
   - Check environment variables or .env file

2. **Rate Limit Errors**
   - Reduce batch size or add delays between requests
   - Check your OpenAI plan limits

3. **JSON Parsing Errors**
   - The tool includes robust JSON cleaning
   - Check document format if issues persist

4. **Missing Certificates**
   - Ensure documents are in the correct format
   - Check if certificate types are properly defined

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

- `openai>=1.0.0` - OpenAI API client
- `python-dotenv>=0.19.0` - Environment variable management
- `pathlib2>=2.3.0` - Path handling utilities
- `typing-extensions>=4.0.0` - Type hints support

## License

This project is provided as-is for educational and commercial use. Please ensure compliance with OpenAI's usage policies when using their API.

## Contributing

Contributions are welcome! Please ensure:

1. Code follows Python best practices
2. New certificate types are properly documented
3. Tests are included for new features
4. Documentation is updated accordingly

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the example scripts
3. Ensure your OpenAI API key is valid
4. Verify document formats are supported

## Changelog

### Version 1.0.0
- Initial release
- Support for 11 certificate types
- Batch processing capability
- Comprehensive JSON output
- Error handling and logging
- Example scripts and documentation 