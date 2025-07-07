import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from openai import OpenAI
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CertificateInfo:
    """Data class for certificate information"""
    certificate_type: str
    # document_source: str
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    condition_code: Optional[str] = None
    quantity: Optional[str] = None
    # batch_lot: Optional[str] = None
    manufacturer: Optional[str] = None
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
    # purchase_order: Optional[str] = None
    # invoice_number: Optional[str] = None
    certification_date: Optional[str] = None
    authorized_signature: Optional[str] = None
    # approval_number: Optional[str] = None
    traceability_source: Optional[str] = None
    # last_operator: Optional[str] = None
    # work_performed: Optional[str] = None
    # airworthiness_authority: Optional[str] = None
    # non_incident_statement: Optional[str] = None
    # additional_notes: Optional[str] = None

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
            # "WORK_ORDER": "Work Order Documentation",
            # "TEARDOWN": "Teardown Report",
            # "PACKING_SLIP": "Packing Slip with Certification",
            # "BILL_OF_SALE": "Bill of Sale",
            # "CONSIGNMENT": "Consignment Documentation",
            "OEM_CERT": "OEM Manufacturer Certification",
            "EUROPEAN_COC": "European Certificate of Conformity (EN10204)"
        }
    
    def create_extraction_prompt(self, document_content: str) -> str:
        """Create a detailed prompt for certificate extraction with high accuracy"""
        
        prompt = f"""
You are an expert aviation document auditor. Your task is to analyze a package of traceability documents and extract ONLY the official certificates for the part(s) sold to "SKYLINK".

DOCUMENT CONTENT:
---
{document_content}
---

CRITICAL EXTRACTION PROCESS & RULES:

1.  **Identify Primary Part Numbers**:
    *   First, perform a complete scan of the document to find the invoice or packing slip where the **BUYER is "SKYLINK", "SKYLINK INC", or "SKYLINK, INC."**.
    *   From that specific document, create a list of the primary `part_number`(s) being purchased by Skylink.

2.  **Extract All Matching Official Certificates**:
    *   Now, review the **entire document text again** from top to bottom.
    *   You MUST extract every document that is an **Official Certificate** AND is associated with one of the primary `part_number`(s) you identified in Step 1.
    *   A document is an "Official Certificate" if it is one of the following types. Use these exact names for `certificate_type`:
        *   `"Part or Material Certification Form (ATA Specification 106)"`
        *   `"FAA Form 8130-3 (Authorized Release Certificate)"`
        *   `"Certificate of Conformance/Conformity"`
        *   `"Material Certification"`
        *   `"OEM Manufacturer Certification"`
        *   `"European Certificate of Conformity (EN10204)"`
    *   **CRITICAL RULE**: Any document that is NOT on this list (e.g., a "Packing Slip", "Work Order") MUST be ignored and NOT included in the output, even if it was used to find the part numbers.

3.  **Extraction Fields**:
    *   For the official certificates you extract, populate all fields precisely.
    *   `traceability_source`: Look for explicit origin statements, PO numbers, or prior air carriers. If none is explicitly mentioned, set this to `null`.

4.  **Output Format**:
    *   Return a single JSON array containing ONLY the official certificate objects for the parts sold to Skylink.

RETURN RESULTS AS A JSON ARRAY:
[
  {{
    "certificate_type": "...",
    "part_number": "...",
    "serial_number": "...",
    "description": "...",
    "condition_code": "...",
    "quantity": "...",
    "manufacturer": "...",
    "seller_name": "...",
    "buyer_name": "...",
    "certification_date": "...",
    "authorized_signature": "...",
    "traceability_source": "..."
  }}
]

CRITICAL: Your entire output must be ONLY the JSON array. Do not include any document that isn't a formal certificate from the approved list.
"""
        return prompt

    def extract_certificates_from_text(self, document_content: str, document_name: str = "Unknown") -> List[CertificateInfo]:
        """Extract certificates from document text using OpenAI with enhanced accuracy"""
        
        try:
            prompt = self.create_extraction_prompt(document_content)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 for better accuracy
                messages=[
                    {"role": "system", "content": "You are an expert aviation document analyzer specializing in precise certificate extraction. Your accuracy is critical for aviation safety. Always return valid JSON with exact information from the documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature for maximum consistency
                max_tokens=6000   # Increased for complex documents
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            
            # Clean the response to extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            # Remove any leading/trailing whitespace
            result_text = result_text.strip()
            
            try:
                certificates_data = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {document_name}: {str(e)}")
                logger.error(f"Raw response: {result_text[:500]}...")
                return []
            
            # Validate and convert to CertificateInfo objects
            certificates = []
            for i, cert_data in enumerate(certificates_data):
                try:
                    # Validate part number format (basic check)
                    part_number = cert_data.get('part_number')
                    if part_number and not self._validate_part_number(part_number):
                        logger.warning(f"Suspicious part number format in {document_name}: {part_number}")
                    
                    # Validate certificate type
                    cert_type = cert_data.get('certificate_type')
                    if cert_type and not self._validate_certificate_type(cert_type):
                        logger.warning(f"Unknown certificate type in {document_name}: {cert_type}")
                    
                    cert_info = CertificateInfo(**cert_data)
                    certificates.append(cert_info)
                    
                except Exception as e:
                    logger.error(f"Error creating certificate {i+1} from {document_name}: {str(e)}")
                    logger.error(f"Certificate data: {cert_data}")
                    continue
            
            logger.info(f"Extracted {len(certificates)} certificates from {document_name}")
            
            # Additional validation
            if len(certificates) == 0:
                logger.warning(f"No certificates extracted from {document_name} - may need manual review")
            
            return certificates
            
        except Exception as e:
            logger.error(f"Error extracting certificates from {document_name}: {str(e)}")
            return []

    def _validate_part_number(self, part_number: str) -> bool:
        """Validate part number format"""
        if not part_number or part_number.lower() in ['null', 'none', '']:
            return True
        
        # Common aviation part number patterns
        import re
        patterns = [
            r'^[A-Z0-9]+-[A-Z0-9]+',        # 2606672-4, NAS1474-C06
            r'^[A-Z]{2,3}[0-9]+-[A-Z0-9]+', # MS20470AD4-5.5
            r'^[A-Z]{2}[0-9]+-[0-9]+-[0-9]+', # AN502-10-6
            r'^[0-9]+-[0-9]+',              # Simple numeric
            r'^[A-Z0-9]+$',                 # No hyphen parts
            r'LOT PURCHASE',                # Special cases
            r'See [Aa]ttached'
        ]
        
        for pattern in patterns:
            if re.match(pattern, part_number):
                return True
        
        # If it contains reasonable alphanumeric characters, accept it
        if re.match(r'^[A-Z0-9\-\.]+$', part_number):
            return True
            
        return False

    def _validate_certificate_type(self, cert_type: str) -> bool:
        """Validate certificate type against known types"""
        if not cert_type:
            return False
            
        valid_types = [
            "Part or Material Certification Form (ATA Specification 106)",
            "FAA Form 8130-3 (Authorized Release Certificate)",
            "Certificate of Conformance/Conformity",
            "Material Certification",
            "Work Order Documentation",
            "Teardown Report",
            "Packing Slip with Certification",
            "Bill of Sale",
            "Consignment Documentation",
            "OEM Manufacturer Certification",
            "European Certificate of Conformity (EN10204)"
        ]
        
        return cert_type in valid_types

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
            # "summary": summary
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

    print("Certificate extraction complete")
    
    # Print summary
    # summary = output_data["summary"]
    # print("\n" + "="*60)
    # print("CERTIFICATE EXTRACTION SUMMARY")
    # print("="*60)
    # print(f"Documents Processed: {summary['total_documents_processed']}")
    # print(f"Total Certificates: {summary['total_certificates_extracted']}")
    # print("\nCertificates by Type:")
    # for cert_type, count in summary['certificates_by_type'].items():
    #     print(f"  {cert_type}: {count}")
    
    # print("\nCertificates by Condition:")
    # for condition, count in summary['certificates_by_condition'].items():
    #     print(f"  {condition}: {count}")
    
    # print(f"\nDetailed results saved to: certificate_extraction_results.json")

if __name__ == "__main__":
    main() 