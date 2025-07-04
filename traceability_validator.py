#!/usr/bin/env python3
"""
Aviation Traceability Validation System

This system validates aviation parts traceability against ASA-100 requirements
and regulated source standards based on aviation industry best practices.
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from openai import OpenAI
import logging
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegulatedSourceType(Enum):
    """Regulated source types based on aviation standards"""
    OEM = "OEM"  # Original Equipment Manufacturer
    FAR_121 = "121"  # Domestic US airlines
    FAR_129 = "129"  # Foreign airlines operating in USA
    FAR_135 = "135"  # Charter and cargo operators
    FAR_145 = "145"  # FAA regulated repair stations
    FOREIGN_OPERATOR = "FOREIGN_OPERATOR"  # Foreign airlines not operating in USA
    UNKNOWN = "UNKNOWN"

class PartClass(Enum):
    """Part classes from ASA-100 Appendix A"""
    CONSUMABLE = "CONSUMABLE"
    RAW_MATERIAL = "RAW_MATERIAL"
    STANDARD_PARTS = "STANDARD_PARTS"
    NEW_TC_HOLDER = "NEW_TC_HOLDER"
    NEW_PAH_WITH_APPROVAL = "NEW_PAH_WITH_APPROVAL"
    NEW_PAH_WITHOUT_APPROVAL = "NEW_PAH_WITHOUT_APPROVAL"
    NEW_NON_US_PAH_WITH_APPROVAL = "NEW_NON_US_PAH_WITH_APPROVAL"
    NEW_NON_US_PAH_WITHOUT_APPROVAL = "NEW_NON_US_PAH_WITHOUT_APPROVAL"
    USED_14CFR_PART43 = "USED_14CFR_PART43"
    USED_FOREIGN_MAINTENANCE = "USED_FOREIGN_MAINTENANCE"
    USED_WITHOUT_APPROVAL = "USED_WITHOUT_APPROVAL"
    UNKNOWN = "UNKNOWN"

@dataclass
class ValidationResult:
    """Result of traceability validation"""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    regulated_source: RegulatedSourceType
    traceability_chain: List[str]
    missing_documentation: List[str]
    compliance_notes: List[str]
    asa100_compliance: bool
    validation_issues: List[str]

@dataclass
class TraceabilityChain:
    """Represents a complete traceability chain"""
    certificates: List[Dict[str, Any]]
    source_to_buyer_flow: List[Tuple[str, str]]
    regulated_source: RegulatedSourceType
    is_complete: bool
    missing_links: List[str]

class TraceabilityValidator:
    """Main class for validating aviation parts traceability"""
    
    def __init__(self, api_key: str = ""):
        """Initialize the validator with OpenAI API key"""
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            self.client = OpenAI()
        
        # Known regulated sources from transcripts
        self.regulated_sources = {
            RegulatedSourceType.OEM: [
                "boeing", "airbus", "honeywell", "collins aerospace", "safran", "ge aviation",
                "pratt & whitney", "rolls-royce", "textron", "ateliers", "moeller", "anillo industries",
                "applied avionics", "mueller manufacturing", "ahg ateliers"
            ],
            RegulatedSourceType.FAR_121: [
                "delta", "american airlines", "united airlines", "southwest", "jetblue", "alaska airlines",
                "us airways", "usairways", "endeavor air", "expressjet"
            ],
            RegulatedSourceType.FAR_129: [
                "japan airlines", "china airlines", "lufthansa", "air france", "klm", "british airways",
                "cathay pacific", "singapore airlines", "emirates", "qatar airways"
            ],
            RegulatedSourceType.FAR_135: [
                "fedex", "ups", "dhl", "atlas air", "kalitta air", "netjets", "flexjet"
            ],
            RegulatedSourceType.FAR_145: [
                "jja", "ultima", "delta skytech", "aai", "b & w aviation", "logistica aeroespacial"
            ]
        }
        
        # ASA-100 requirements mapping
        self.asa100_requirements = {
            PartClass.CONSUMABLE: {
                "on_receipt": ["Statement from seller as to identity"],
                "for_shipment": ["Statement as to identity and that original seller's statement is on file"]
            },
            PartClass.RAW_MATERIAL: {
                "on_receipt": ["Physical and chemical properties reports traceable to heat code or lot number"],
                "for_shipment": ["Certified true copy of the physical and chemical properties reports"]
            },
            PartClass.STANDARD_PARTS: {
                "on_receipt": ["Certificate of Conformity (C of C) from producer or seller"],
                "for_shipment": ["Certified true copy of the received C of C"]
            },
            PartClass.NEW_PAH_WITH_APPROVAL: {
                "on_receipt": ["FAA Form 8130-3 or part marking required by 14 CFR part 45"],
                "for_shipment": ["Certified true copy of regulatory airworthiness approval document"]
            },
            PartClass.USED_14CFR_PART43: {
                "on_receipt": ["Approval for return to service meeting provisions of 14 CFR §§ 43.9, 43.11, or 43.17"],
                "for_shipment": ["Approval for return to service"]
            }
        }

    def identify_regulated_source(self, certificate: Dict[str, Any]) -> RegulatedSourceType:
        """Identify the regulated source type from certificate data"""
        
        # Check seller name and manufacturer
        seller = (certificate.get('seller_name', '') or '').lower()
        manufacturer = (certificate.get('manufacturer', '') or '').lower()
        traceability_source = (certificate.get('traceability_source', '') or '').lower()
        
        # Check all relevant fields
        all_sources = f"{seller} {manufacturer} {traceability_source}".lower()
        
        # Check against known regulated sources
        for source_type, companies in self.regulated_sources.items():
            for company in companies:
                if company.lower() in all_sources:
                    return source_type
        
        # Check for specific patterns
        if any(pattern in all_sources for pattern in ['boeing', 'airbus', 'manufacturer', 'oem']):
            return RegulatedSourceType.OEM
        elif any(pattern in all_sources for pattern in ['airlines', 'air ', 'airways']):
            return RegulatedSourceType.FAR_121
        elif any(pattern in all_sources for pattern in ['fedex', 'ups', 'dhl']):
            return RegulatedSourceType.FAR_135
        elif any(pattern in all_sources for pattern in ['repair', 'mro', 'maintenance']):
            return RegulatedSourceType.FAR_145
        
        return RegulatedSourceType.UNKNOWN

    def classify_part(self, certificate: Dict[str, Any]) -> PartClass:
        """Classify part based on certificate information"""
        
        cert_type = certificate.get('certificate_type', '').lower()
        condition = (certificate.get('condition_code', '') or '').lower()
        description = (certificate.get('description', '') or '').lower()
        
        # Basic classification logic
        if 'consumable' in description or 'tape' in description or 'grease' in description:
            return PartClass.CONSUMABLE
        elif 'raw material' in description or 'material' in cert_type:
            return PartClass.RAW_MATERIAL
        elif 'standard' in description or 'nas' in certificate.get('part_number', ''):
            return PartClass.STANDARD_PARTS
        elif 'faa form 8130-3' in cert_type:
            return PartClass.NEW_PAH_WITH_APPROVAL
        elif condition in ['oh', 'overhauled', 'used', 'sv']:
            return PartClass.USED_14CFR_PART43
        elif condition in ['ns', 'new surplus', 'ne', 'new']:
            return PartClass.NEW_TC_HOLDER
        
        return PartClass.UNKNOWN

    def build_traceability_chain(self, certificates: List[Dict[str, Any]]) -> TraceabilityChain:
        """Build traceability chain from certificates"""
        
        # Group certificates by part number
        part_chains = {}
        for cert in certificates:
            part_num = cert.get('part_number', 'unknown')
            if part_num not in part_chains:
                part_chains[part_num] = []
            part_chains[part_num].append(cert)
        
        # For now, take the first part's chain
        if part_chains:
            first_part = list(part_chains.keys())[0]
            chain_certs = part_chains[first_part]
            
            # Build seller-to-buyer flow
            flow = []
            for cert in chain_certs:
                seller = cert.get('seller_name', 'Unknown')
                buyer = cert.get('buyer_name', 'Unknown')
                if seller != 'Unknown' and buyer != 'Unknown':
                    flow.append((seller, buyer))
            
            # Find regulated source
            regulated_source = RegulatedSourceType.UNKNOWN
            for cert in chain_certs:
                source = self.identify_regulated_source(cert)
                if source != RegulatedSourceType.UNKNOWN:
                    regulated_source = source
                    break
            
            return TraceabilityChain(
                certificates=chain_certs,
                source_to_buyer_flow=flow,
                regulated_source=regulated_source,
                is_complete=len(flow) > 0 and regulated_source != RegulatedSourceType.UNKNOWN,
                missing_links=[]
            )
        
        return TraceabilityChain(
            certificates=[],
            source_to_buyer_flow=[],
            regulated_source=RegulatedSourceType.UNKNOWN,
            is_complete=False,
            missing_links=["No certificates found"]
        )

    def validate_asa100_compliance(self, certificates: List[Dict[str, Any]], part_class: PartClass) -> Tuple[bool, List[str]]:
        """Validate ASA-100 compliance for given certificates and part class"""
        
        issues = []
        
        if part_class not in self.asa100_requirements:
            issues.append(f"Unknown part class: {part_class}")
            return False, issues
        
        requirements = self.asa100_requirements[part_class]
        
        # Check for required documentation
        cert_types = [cert.get('certificate_type', '').lower() for cert in certificates]
        
        # Basic validation - check if we have required certificate types
        if part_class == PartClass.STANDARD_PARTS:
            if not any('conformity' in ct or 'conformance' in ct for ct in cert_types):
                issues.append("Missing Certificate of Conformity for standard parts")
        
        elif part_class == PartClass.NEW_PAH_WITH_APPROVAL:
            if not any('8130-3' in ct for ct in cert_types):
                issues.append("Missing FAA Form 8130-3 for new parts with approval")
        
        elif part_class == PartClass.USED_14CFR_PART43:
            if not any('return to service' in ct for ct in cert_types):
                issues.append("Missing return to service approval for used parts")
        
        # Check for packing slip
        if not any('packing' in ct for ct in cert_types):
            issues.append("Missing packing slip documentation")
        
        # Check for material certification
        if not any('material' in ct or 'certification' in ct for ct in cert_types):
            issues.append("Missing material certification")
        
        return len(issues) == 0, issues

    def create_validation_prompt(self, certificates: List[Dict[str, Any]]) -> str:
        """Create a detailed prompt for AI-assisted validation"""
        
        prompt = f"""
You are an expert aviation traceability validator. Analyze the following certificate chain for compliance with aviation regulations.

CERTIFICATES:
{json.dumps(certificates, indent=2)}

VALIDATION REQUIREMENTS FROM TRANSCRIPTS:
1. Complete traceability to regulated source (OEM, 121, 129, 135, 145)
2. Proper documentation (packing slip + material cert/C of C)
3. Linkage between each step in the chain
4. ASA-100 compliance based on part class

KEY VALIDATION CRITERIA:
- OEM trace is the best (manufacturer certification)
- 121 trace = domestic US airlines (Delta, American, etc.)
- 129 trace = foreign airlines operating in USA
- 135 trace = charter/cargo (FedEx, UPS, DHL)
- 145 trace = FAA repair stations
- Must have packing slip AND material cert for each link
- Look for linkage between sources (lot numbers, PO numbers)

ANALYZE AND RETURN JSON:
{{
    "is_valid": true/false,
    "confidence_score": 0.0-1.0,
    "regulated_source_found": "OEM/121/129/135/145/UNKNOWN",
    "traceability_chain": ["seller1 -> buyer1", "seller2 -> buyer2"],
    "has_packing_slip": true/false,
    "has_material_cert": true/false,
    "chain_linkage_complete": true/false,
    "validation_issues": ["issue1", "issue2"],
    "compliance_notes": ["note1", "note2"],
    "missing_documentation": ["doc1", "doc2"],
    "asa100_compliance": true/false,
    "traceability_analysis": "detailed analysis of the chain"
}}

Focus on:
- Chain completeness back to regulated source
- Document authenticity and proper types
- Regulatory compliance
- Missing links or documentation
"""
        return prompt

    def validate_traceability(self, certificates: List[Dict[str, Any]]) -> ValidationResult:
        """Main validation method"""
        
        try:
            # Basic validation
            if not certificates:
                return ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    regulated_source=RegulatedSourceType.UNKNOWN,
                    traceability_chain=[],
                    missing_documentation=["No certificates found"],
                    compliance_notes=[],
                    asa100_compliance=False,
                    validation_issues=["No certificates extracted from document"]
                )
            
            # Identify regulated source from certificates
            regulated_source = RegulatedSourceType.UNKNOWN
            for cert in certificates:
                source = self.identify_regulated_source(cert)
                if source != RegulatedSourceType.UNKNOWN:
                    regulated_source = source
                    break
            
            # Use AI for detailed validation
            prompt = self.create_validation_prompt(certificates)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert aviation traceability validator. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse AI response
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            ai_result = json.loads(result_text)
            
            # Map AI result to our structure
            return ValidationResult(
                is_valid=ai_result.get('is_valid', False),
                confidence_score=ai_result.get('confidence_score', 0.0),
                regulated_source=regulated_source,
                traceability_chain=ai_result.get('traceability_chain', []),
                missing_documentation=ai_result.get('missing_documentation', []),
                compliance_notes=ai_result.get('compliance_notes', []),
                asa100_compliance=ai_result.get('asa100_compliance', False),
                validation_issues=ai_result.get('validation_issues', [])
            )
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                regulated_source=RegulatedSourceType.UNKNOWN,
                traceability_chain=[],
                missing_documentation=["Validation failed"],
                compliance_notes=[],
                asa100_compliance=False,
                validation_issues=[f"Validation error: {str(e)}"]
            )

    def validate_all_documents(self, extraction_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ValidationResult]:
        """Validate all documents from extraction results"""
        
        results = {}
        
        for document_name, certificates in extraction_results.items():
            logger.info(f"Validating {document_name}...")
            validation_result = self.validate_traceability(certificates)
            results[document_name] = validation_result
        
        return results

    def generate_validation_report(self, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        total_documents = len(validation_results)
        valid_documents = sum(1 for result in validation_results.values() if result.is_valid)
        
        # Count by regulated source
        source_counts = {}
        for result in validation_results.values():
            source = result.regulated_source.value
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Compliance statistics
        asa100_compliant = sum(1 for result in validation_results.values() if result.asa100_compliance)
        
        # Common issues
        all_issues = []
        for result in validation_results.values():
            all_issues.extend(result.validation_issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return {
            "validation_summary": {
                "total_documents": total_documents,
                "valid_documents": valid_documents,
                "validation_rate": valid_documents / total_documents if total_documents > 0 else 0,
                "asa100_compliant": asa100_compliant,
                "compliance_rate": asa100_compliant / total_documents if total_documents > 0 else 0
            },
            "regulated_source_distribution": source_counts,
            "common_issues": dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "validation_timestamp": datetime.now().isoformat()
        }

    def save_validation_results(self, validation_results: Dict[str, ValidationResult], 
                              output_file: str = "traceability_validation_results.json"):
        """Save validation results to JSON file"""
        
        # Convert ValidationResult objects to dictionaries with enum serialization
        serializable_results = {}
        for doc_name, result in validation_results.items():
            result_dict = asdict(result)
            # Convert enum to string value
            result_dict['regulated_source'] = result.regulated_source.value
            serializable_results[doc_name] = result_dict
        
        # Generate report
        report = self.generate_validation_report(validation_results)
        
        # Combine results and report
        output_data = {
            "validation_results": serializable_results,
            "validation_report": report
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Validation results saved to {output_file}")
        return output_data

def main():
    """Main function to run traceability validation"""
    
    # Initialize validator
    validator = TraceabilityValidator()
    
    # Load extraction results
    results_file = "certificate_extraction_results.json"
    
    if not os.path.exists(results_file):
        logger.error(f"Results file {results_file} not found!")
        return
    
    logger.info("Loading extraction results...")
    with open(results_file, 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    extraction_results = extraction_data.get('extraction_results', {})
    
    # Validate all documents
    logger.info("Starting traceability validation...")
    validation_results = validator.validate_all_documents(extraction_results)
    
    # Save results
    output_data = validator.save_validation_results(validation_results)
    
    # Print summary
    report = output_data["validation_report"]
    summary = report["validation_summary"]

    print("\n" + "="*70)
    print("TRACEABILITY VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Documents: {summary['total_documents']}")
    print(f"Valid Documents: {summary['valid_documents']}")
    print(f"Validation Rate: {summary['validation_rate']:.1%}")
    print(f"ASA-100 Compliant: {summary['asa100_compliant']}")
    print(f"Compliance Rate: {summary['compliance_rate']:.1%}")
    
    print("\nRegulated Source Distribution:")
    for source, count in report['regulated_source_distribution'].items():
        print(f"  {source}: {count}")
    
    print("\nCommon Issues:")
    for issue, count in list(report['common_issues'].items())[:5]:
        print(f"  {issue}: {count}")
    
    print(f"\nDetailed results saved to: traceability_validation_results.json")

if __name__ == "__main__":
    main() 