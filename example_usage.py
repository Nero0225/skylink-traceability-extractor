#!/usr/bin/env python3
"""
Example usage of the Certificate Extractor for Aviation Documents

This script demonstrates how to use the CertificateExtractor class to extract
certificate information from aviation documents using OpenAI's API.
"""

import os
from certificate_extractor import CertificateExtractor, CertificateInfo
from dotenv import load_dotenv

def example_single_file_extraction():
    """Example: Extract certificates from a single file"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize extractor
    extractor = CertificateExtractor()
    
    # Process a single file
    file_path = "markdowns/1. UNREGULATED SOURCE EXAMPLE.md"
    
    if os.path.exists(file_path):
        print(f"Processing single file: {file_path}")
        certificates = extractor.process_markdown_file(file_path)
        
        print(f"Found {len(certificates)} certificates:")
        for i, cert in enumerate(certificates, 1):
            print(f"\n--- Certificate {i} ---")
            print(f"Type: {cert.certificate_type}")
            print(f"Part Number: {cert.part_number}")
            print(f"Seller: {cert.seller_name}")
            print(f"Buyer: {cert.buyer_name}")
            print(f"Condition: {cert.condition_code}")
    else:
        print(f"File not found: {file_path}")

def example_directory_extraction():
    """Example: Extract certificates from all files in a directory"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize extractor
    extractor = CertificateExtractor()
    
    # Process all files in directory
    results = extractor.process_directory("markdowns")
    
    # Save results
    output_data = extractor.save_results(results, "example_results.json")
    
    # Print summary
    summary = output_data["summary"]
    print("\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    print(f"Documents: {summary['total_documents_processed']}")
    print(f"Certificates: {summary['total_certificates_extracted']}")
    
    print("\nBy Certificate Type:")
    for cert_type, count in summary['certificates_by_type'].items():
        print(f"  {cert_type}: {count}")

def example_filtered_extraction():
    """Example: Extract and filter certificates by specific criteria"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize extractor
    extractor = CertificateExtractor()
    
    # Process directory
    results = extractor.process_directory("markdowns")
    
    # Filter for specific certificate types
    ata_106_certificates = []
    faa_8130_certificates = []
    
    for file_name, certificates in results.items():
        for cert in certificates:
            if "ATA Specification 106" in cert.certificate_type:
                ata_106_certificates.append(cert)
            elif "FAA Form 8130-3" in cert.certificate_type:
                faa_8130_certificates.append(cert)
    
    print(f"\nFound {len(ata_106_certificates)} ATA 106 certificates")
    print(f"Found {len(faa_8130_certificates)} FAA 8130-3 certificates")
    
    # Show ATA 106 certificates
    print("\nATA 106 Certificates:")
    for cert in ata_106_certificates:
        print(f"  {cert.part_number} - {cert.seller_name} to {cert.buyer_name}")

def example_custom_api_key():
    """Example: Use custom OpenAI API key"""
    
    # You can pass API key directly
    api_key = "your-openai-api-key-here"
    extractor = CertificateExtractor(api_key=api_key)
    
    # Or set it in environment
    # os.environ["OPENAI_API_KEY"] = "your-api-key"
    # extractor = CertificateExtractor()
    
    print("Extractor initialized with custom API key")

def example_batch_processing():
    """Example: Process multiple specific files"""
    
    load_dotenv()
    extractor = CertificateExtractor()
    
    # List of specific files to process
    files_to_process = [
        "markdowns/1. UNREGULATED SOURCE EXAMPLE.md",
        "markdowns/2. 121 FULL TRACE EXAMPLE.md",
        "markdowns/3. OEM TRACE EXAMPLE.md"
    ]
    
    all_certificates = []
    
    for file_path in files_to_process:
        if os.path.exists(file_path):
            print(f"Processing: {file_path}")
            certificates = extractor.process_markdown_file(file_path)
            all_certificates.extend(certificates)
            print(f"  -> Found {len(certificates)} certificates")
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nTotal certificates extracted: {len(all_certificates)}")
    
    # Group by certificate type
    cert_types = {}
    for cert in all_certificates:
        cert_type = cert.certificate_type
        if cert_type not in cert_types:
            cert_types[cert_type] = []
        cert_types[cert_type].append(cert)
    
    print("\nCertificates by type:")
    for cert_type, certs in cert_types.items():
        print(f"  {cert_type}: {len(certs)} certificates")

def main():
    """Main function to run examples"""
    
    print("Certificate Extractor - Usage Examples")
    print("="*50)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not found!")
        print("Set your API key in:")
        print("  1. Environment variable: OPENAI_API_KEY")
        print("  2. Create a .env file with: OPENAI_API_KEY=your-key-here")
        print("  3. Pass it directly to CertificateExtractor(api_key='your-key')")
        return
    
    print("\nSelect an example to run:")
    print("1. Single file extraction")
    print("2. Directory extraction")
    print("3. Filtered extraction")
    print("4. Batch processing")
    print("5. Run all examples")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        example_single_file_extraction()
    elif choice == "2":
        example_directory_extraction()
    elif choice == "3":
        example_filtered_extraction()
    elif choice == "4":
        example_batch_processing()
    elif choice == "5":
        print("\nRunning all examples...")
        example_single_file_extraction()
        print("\n" + "-"*50)
        example_directory_extraction()
        print("\n" + "-"*50)
        example_filtered_extraction()
        print("\n" + "-"*50)
        example_batch_processing()
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main() 