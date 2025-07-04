import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from openai import OpenAI
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CertificateInfo:
    """Data class for certificate information"""
    certificate_type: str
    document_source: str
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    condition_code: Optional[str] = None
    quantity: Optional[str] = None
    batch_lot: Optional[str] = None
    manufacturer: Optional[str] = None
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
    purchase_order: Optional[str] = None
    invoice_number: Optional[str] = None
    certification_date: Optional[str] = None
    authorized_signature: Optional[str] = None
    approval_number: Optional[str] = None
    traceability_source: Optional[str] = None
    last_operator: Optional[str] = None
    work_performed: Optional[str] = None
    airworthiness_authority: Optional[str] = None
    non_incident_statement: Optional[str] = None
    additional_notes: Optional[str] = None

class CertificateExtractor:
    """Main class for extracting certificate information from aviation documents"""
    
    def __init__(self, api_key: str = ""):
        """Initialize the extractor with OpenAI API key"""
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            self.client = OpenAI()
        
        # Define certificate types based on our analysis
        self.certificate_types = {
            "ATA_106": "Part or Material Certification Form (ATA Specification 106)",
            "FAA_8130-3": "FAA Form 8130-3 (Authorized Release Certificate)",
            "COC": "Certificate of Conformance/Conformity",
            "MATERIAL_CERT": "Material Certification",
            "WORK_ORDER": "Work Order Documentation",
            "TEARDOWN": "Teardown Report",
            "PACKING_SLIP": "Packing Slip with Certification",
            "BILL_OF_SALE": "Bill of Sale",
            "CONSIGNMENT": "Consignment Documentation",
            "OEM_CERT": "OEM Manufacturer Certification",
            "EUROPEAN_COC": "European Certificate of Conformity (EN10204)"
        }
    
    def create_extraction_prompt(self, document_content: str) -> str:
        """Create a detailed prompt for certificate extraction"""
        
        prompt = f"""
You are an expert aviation document analyzer. Extract ALL certificate information from this aviation document.

DOCUMENT CONTENT:
{document_content}

EXTRACT THE FOLLOWING INFORMATION FOR EACH CERTIFICATE FOUND:

1. **Certificate Type** - Identify from these types:
   - Part or Material Certification Form (ATA Specification 106)
   - FAA Form 8130-3 (Authorized Release Certificate)
   - Certificate of Conformance/Conformity
   - Material Certification
   - Work Order Documentation
   - Teardown Report
   - Packing Slip with Certification
   - Bill of Sale
   - Consignment Documentation
   - OEM Manufacturer Certification
   - European Certificate of Conformity (EN10204)

2. **Part Information:**
   - Part Number
   - Serial Number
   - Description
   - Condition Code (NS, OH, NE, SV, etc.)
   - Quantity
   - Batch/Lot Number
   - Manufacturer

3. **Transaction Details:**
   - Seller Name
   - Buyer Name
   - Purchase Order Number
   - Invoice Number
   - Certification Date

4. **Certification Details:**
   - Authorized Signature (person name)
   - Approval Number
   - Airworthiness Authority (FAA, EASA, etc.)
   - Work Performed (if applicable)

5. **Traceability:**
   - Traceability Source
   - Last Operator/Airline
   - Non-incident Statement

6. **Additional Notes:**
   - Any special remarks or conditions

RETURN RESULTS AS JSON ARRAY:
[
  {{
    "certificate_type": "...",
    "document_source": "...",
    "part_number": "...",
    "serial_number": "...",
    "description": "...",
    "condition_code": "...",
    "quantity": "...",
    "batch_lot": "...",
    "manufacturer": "...",
    "seller_name": "...",
    "buyer_name": "...",
    "purchase_order": "...",
    "invoice_number": "...",
    "certification_date": "...",
    "authorized_signature": "...",
    "approval_number": "...",
    "traceability_source": "...",
    "last_operator": "...",
    "work_performed": "...",
    "airworthiness_authority": "...",
    "non_incident_statement": "...",
    "additional_notes": "..."
  }}
]

IMPORTANT: 
- Extract ALL certificates found in the document
- Use null for missing information
- Be precise with part numbers and technical details
- Include complete traceability information
- Identify specific certificate types accurately
"""
        return prompt

    def extract_certificates_from_text(self, document_content: str, document_name: str) -> List[CertificateInfo]:
        """Extract certificates from document text using OpenAI"""
        
        try:
            prompt = self.create_extraction_prompt(document_content)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 for better accuracy
                messages=[
                    {"role": "system", "content": "You are an expert aviation document analyzer specializing in certificate extraction. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=4000
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            
            # Clean the response to extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            certificates_data = json.loads(result_text)
            
            # Convert to CertificateInfo objects
            certificates = []
            for cert_data in certificates_data:
                cert_data['document_source'] = document_name
                cert_info = CertificateInfo(**cert_data)
                certificates.append(cert_info)
            
            logger.info(f"Extracted {len(certificates)} certificates from {document_name}")
            return certificates
            
        except Exception as e:
            logger.error(f"Error extracting certificates from {document_name}: {str(e)}")
            return []

    def process_markdown_file(self, file_path: str) -> List[CertificateInfo]:
        """Process a single markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            document_name = Path(file_path).name
            return self.extract_certificates_from_text(content, document_name)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return []

    def process_directory(self, directory_path: str) -> Dict[str, List[CertificateInfo]]:
        """Process all markdown files in a directory"""
        results = {}
        
        directory = Path(directory_path)
        markdown_files = list(directory.glob("*.md"))
        
        logger.info(f"Processing {len(markdown_files)} markdown files...")
        
        for file_path in markdown_files:
            logger.info(f"Processing: {file_path.name}")
            certificates = self.process_markdown_file(str(file_path))
            results[file_path.name] = certificates
        
        return results

    def generate_summary_report(self, results: Dict[str, List[CertificateInfo]]) -> Dict[str, Any]:
        """Generate a summary report of extracted certificates"""
        
        total_certificates = sum(len(certs) for certs in results.values())
        
        # Count by certificate type
        cert_type_counts = {}
        all_certificates = []
        
        for file_name, certificates in results.items():
            all_certificates.extend(certificates)
            for cert in certificates:
                cert_type = cert.certificate_type
                cert_type_counts[cert_type] = cert_type_counts.get(cert_type, 0) + 1
        
        # Count by manufacturer
        manufacturer_counts = {}
        for cert in all_certificates:
            if cert.manufacturer:
                manufacturer_counts[cert.manufacturer] = manufacturer_counts.get(cert.manufacturer, 0) + 1
        
        # Count by condition code
        condition_counts = {}
        for cert in all_certificates:
            if cert.condition_code:
                condition_counts[cert.condition_code] = condition_counts.get(cert.condition_code, 0) + 1
        
        summary = {
            "total_documents_processed": len(results),
            "total_certificates_extracted": total_certificates,
            "certificates_by_type": cert_type_counts,
            "certificates_by_manufacturer": manufacturer_counts,
            "certificates_by_condition": condition_counts,
            "files_processed": list(results.keys()),
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        return summary

    def save_results(self, results: Dict[str, List[CertificateInfo]], output_file: str = "certificate_extraction_results.json"):
        """Save extraction results to JSON file"""
        
        # Convert CertificateInfo objects to dictionaries
        serializable_results = {}
        for file_name, certificates in results.items():
            serializable_results[file_name] = [asdict(cert) for cert in certificates]
        
        # Generate summary
        summary = self.generate_summary_report(results)
        
        # Combine results and summary
        output_data = {
            "extraction_results": serializable_results,
            "summary": summary
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_file}")
        return output_data

def main():
    """Main function to run the certificate extraction"""
    
    # Initialize extractor
    extractor = CertificateExtractor()
    
    # Process the markdowns directory
    markdowns_dir = "markdowns"
    
    if not os.path.exists(markdowns_dir):
        logger.error(f"Directory {markdowns_dir} not found!")
        return
    
    # Extract certificates from all files
    logger.info("Starting certificate extraction...")
    results = extractor.process_directory(markdowns_dir)
    
    # Save results
    output_data = extractor.save_results(results)
    
    # Print summary
    summary = output_data["summary"]
    print("\n" + "="*60)
    print("CERTIFICATE EXTRACTION SUMMARY")
    print("="*60)
    print(f"Documents Processed: {summary['total_documents_processed']}")
    print(f"Total Certificates: {summary['total_certificates_extracted']}")
    print("\nCertificates by Type:")
    for cert_type, count in summary['certificates_by_type'].items():
        print(f"  {cert_type}: {count}")
    
    print("\nCertificates by Condition:")
    for condition, count in summary['certificates_by_condition'].items():
        print(f"  {condition}: {count}")
    
    print(f"\nDetailed results saved to: certificate_extraction_results.json")

if __name__ == "__main__":
    main() 