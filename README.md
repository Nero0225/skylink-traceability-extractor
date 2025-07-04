# Aviation Traceability Validation System

A comprehensive system for validating aviation parts traceability against ASA-100 requirements and regulated source standards.

## Overview

This system implements traceability validation based on aviation industry best practices as outlined in video transcripts about aviation traceability essentials. It validates certificate chains against regulated sources and ASA-100 Appendix A requirements.

## Key Features

### 🔍 Regulated Source Validation
- **OEM Trace**: Original Equipment Manufacturer (Best possible trace)
- **121 Trace**: Domestic US airlines (Delta, American Airlines, etc.)
- **129 Trace**: Foreign airlines operating in USA
- **135 Trace**: Charter and cargo operators (FedEx, UPS, DHL)
- **145 Trace**: FAA regulated repair stations

### 📋 Document Requirements
- Packing slip/packing list validation
- Material certification/Certificate of Conformance (C of C)
- Traceability chain linkage verification
- ASA-100 compliance checking

### 🤖 AI-Powered Analysis
- Uses OpenAI GPT-4 for detailed certificate analysis
- Validates complete traceability chains
- Identifies missing documentation
- Provides confidence scoring

## Files

### Core System
- `traceability_validator.py`: Main validation system
- `certificate_extractor.py`: Certificate extraction from documents
- `test_validator.py`: Test script without OpenAI requirement

### Data Files
- `my_results.json`: Extracted certificate data from markdown documents
- `ASA-100.md`: ASA-100 Appendix A requirements reference
- `markdowns/`: Example aviation traceability documents

## Installation

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install openai python-dotenv
```

4. Set OpenAI API key:

**Option 1: Environment Variable**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Option 2: .env File (Recommended)**
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### With OpenAI API
```bash
python traceability_validator.py
```

### Test Mode (No API Required)
```bash
python test_validator.py
```

## Validation Results

Based on the test run of 9 aviation documents:

### Summary Statistics
- **Total Documents**: 9
- **Valid Documents**: 3 (33.3%)
- **ASA-100 Compliant**: 3 (33.3%)
- **Average Confidence**: 50.0%

### Regulated Source Distribution
- **OEM Traced**: 4 documents (Boeing, Applied Avionics, etc.)
- **121 Traced**: 3 documents (US Airways, Endeavor Air, ExpressJet)
- **145 Traced**: 1 document (B & W Aviation, Logistica Aeroespacial)
- **Unknown**: 1 document

### Common Issues Found
- Missing packing slip documentation
- Incomplete traceability chains
- Missing material certifications

## Validation Logic

### Document Analysis
1. **Certificate Extraction**: Extracts all certificates from document
2. **Source Identification**: Identifies regulated sources in chain
3. **Chain Building**: Builds seller-to-buyer traceability flow
4. **Compliance Check**: Validates against ASA-100 requirements
5. **AI Analysis**: Deep analysis using OpenAI GPT-4

### Validation Criteria
- ✅ Complete chain to regulated source
- ✅ Proper documentation (packing slip + material cert)
- ✅ Linkage between all chain steps
- ✅ ASA-100 compliance for part class
- ✅ Regulatory compliance

## Examples

### Valid Trace Example
```
📄 Document: 1. UNREGULATED SOURCE EXAMPLE.md
   ✅ Valid: True
   📊 Confidence: 90.0%
   🏢 Regulated Source: 145 (FAA Repair Station)
   🔗 Chain: Aircraft Parts Logistic -> Skylink, Inc.
   📝 Notes: 145 trace found - repair station traceability
   📜 ASA-100 Compliant: True
```

### Invalid Trace Example
```
📄 Document: 2. 121 FULL TRACE EXAMPLE.md
   ✅ Valid: False
   📊 Confidence: 30.0%
   🏢 Regulated Source: 121 (Domestic Airline)
   🔗 Chain: Avsource International Inc. -> SKYLINK INC
   ⚠️  Issues: Missing packing slip
   📜 ASA-100 Compliant: False
```

## Key Insights from Video Transcripts

### What is Traceability?
- Documentation ensuring history and location of all aviation parts
- Includes packing slips, material certs, ATAs, manufacturer CFCs
- Critical for safety - all parts must be traceable to regulated sources

### Why is Traceability Important?
- **Safety**: Lives depend on aircraft parts
- **Regulatory**: FAA compliance requirements
- **Quality**: Ensures parts are safe for aircraft installation
- **Chain of Custody**: Complete documentation from origin to installation

### Traceability Chain Requirements
- **Linkage**: Must connect each source to next buyer
- **Documentation**: Each link needs packing slip + material cert
- **Source Validation**: Must trace to regulated source
- **Completeness**: No missing links in chain

## ASA-100 Compliance

The system cross-references ASA-100 Appendix A requirements:

### Part Classes
- **Consumable Materials**: Statement of identity required
- **Raw Materials**: Physical/chemical properties reports
- **Standard Parts**: Certificate of Conformity required
- **New Parts (PAH)**: FAA Form 8130-3 or part marking
- **Used Parts**: Approval for return to service

### Documentation Requirements
- **On Receipt**: Specific documents based on part class
- **For Shipment**: Certified copies and statements
- **Traceability**: Complete chain to regulated source

## Future Enhancements

1. **Enhanced AI Analysis**: More sophisticated pattern recognition
2. **Automated Scoring**: Detailed compliance scoring system
3. **Batch Processing**: Process multiple document folders
4. **Report Generation**: Detailed PDF reports
5. **Integration**: API endpoints for external systems

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
- Review the test examples in `test_validator.py`
- Check the validation logic in `traceability_validator.py`
- Examine the certificate extraction in `certificate_extractor.py`
- Reference ASA-100 requirements in `ASA-100.md` 