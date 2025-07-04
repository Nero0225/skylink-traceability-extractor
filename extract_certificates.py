#!/usr/bin/env python3
"""
Command-line utility for extracting certificates from aviation documents.

Usage:
    python extract_certificates.py --help
    python extract_certificates.py --directory markdowns
    python extract_certificates.py --file "markdowns/1. UNREGULATED SOURCE EXAMPLE.md"
    python extract_certificates.py --directory markdowns --output results.json
"""

import argparse
import sys
import os
from pathlib import Path
from certificate_extractor import CertificateExtractor
from dotenv import load_dotenv

def main():
    """Main command-line interface"""
    
    parser = argparse.ArgumentParser(
        description="Extract certificate information from aviation documents using OpenAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from all files in directory:
    python extract_certificates.py --directory markdowns

  Extract from single file:
    python extract_certificates.py --file "markdowns/1. UNREGULATED SOURCE EXAMPLE.md"

  Specify output file:
    python extract_certificates.py --directory markdowns --output my_results.json

  Use custom API key:
    python extract_certificates.py --directory markdowns --api-key your-key-here

  Enable verbose logging:
    python extract_certificates.py --directory markdowns --verbose
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--directory", "-d",
        help="Directory containing markdown files to process"
    )
    input_group.add_argument(
        "--file", "-f",
        help="Single markdown file to process"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        default="certificate_extraction_results.json",
        help="Output JSON file (default: certificate_extraction_results.json)"
    )
    
    # API configuration
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (overrides environment variable)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)"
    )
    
    # Processing options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show summary, don't save detailed results"
    )
    
    parser.add_argument(
        "--filter-type",
        help="Filter results by certificate type (e.g., 'ATA Specification 106')"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Check API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OpenAI API key not found!")
        print("Set it with:")
        print("  1. --api-key argument")
        print("  2. OPENAI_API_KEY environment variable")
        print("  3. .env file with OPENAI_API_KEY=your-key")
        sys.exit(1)
    
    # Initialize extractor
    try:
        extractor = CertificateExtractor(api_key=api_key)
        # Update model if specified
        if args.model != "gpt-4o":
            print(f"Using model: {args.model}")
    except Exception as e:
        print(f"❌ Error initializing extractor: {e}")
        sys.exit(1)
    
    # Process files
    results = {}
    
    if args.directory:
        # Process directory
        if not os.path.exists(args.directory):
            print(f"❌ Error: Directory '{args.directory}' not found!")
            sys.exit(1)
        
        print(f"📁 Processing directory: {args.directory}")
        results = extractor.process_directory(args.directory)
        
    elif args.file:
        # Process single file
        if not os.path.exists(args.file):
            print(f"❌ Error: File '{args.file}' not found!")
            sys.exit(1)
        
        print(f"📄 Processing file: {args.file}")
        certificates = extractor.process_markdown_file(args.file)
        results[Path(args.file).name] = certificates
    
    # Filter results if specified
    if args.filter_type:
        print(f"🔍 Filtering by certificate type: {args.filter_type}")
        filtered_results = {}
        for file_name, certificates in results.items():
            filtered_certs = [
                cert for cert in certificates 
                if args.filter_type.lower() in cert.certificate_type.lower()
            ]
            if filtered_certs:
                filtered_results[file_name] = filtered_certs
        results = filtered_results
    
    # Generate summary
    summary = extractor.generate_summary_report(results)
    
    # Display summary
    print("\n" + "="*60)
    print("📊 CERTIFICATE EXTRACTION SUMMARY")
    print("="*60)
    print(f"📋 Documents Processed: {summary['total_documents_processed']}")
    print(f"🏷️  Total Certificates: {summary['total_certificates_extracted']}")
    
    if summary['certificates_by_type']:
        print("\n📑 Certificates by Type:")
        for cert_type, count in summary['certificates_by_type'].items():
            print(f"  • {cert_type}: {count}")
    
    if summary['certificates_by_condition']:
        print("\n🔧 Certificates by Condition:")
        for condition, count in summary['certificates_by_condition'].items():
            print(f"  • {condition}: {count}")
    
    if summary['certificates_by_manufacturer']:
        print("\n🏭 Top Manufacturers:")
        sorted_manufacturers = sorted(
            summary['certificates_by_manufacturer'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for manufacturer, count in sorted_manufacturers[:5]:
            print(f"  • {manufacturer}: {count}")
    
    # Save results (unless summary-only)
    if not args.summary_only:
        try:
            output_data = extractor.save_results(results, args.output)
            print(f"\n💾 Results saved to: {args.output}")
            print(f"📊 Summary included in output file")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            sys.exit(1)
    
    print("\n✅ Processing complete!")
    
    # Show example of accessing results
    if results and not args.summary_only:
        print(f"\n💡 Access results in Python:")
        print(f"   import json")
        print(f"   with open('{args.output}', 'r') as f:")
        print(f"       data = json.load(f)")
        print(f"       certificates = data['extraction_results']")

if __name__ == "__main__":
    main() 