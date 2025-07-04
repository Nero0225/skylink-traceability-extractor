#!/usr/bin/env python3
"""
Test script for the Aviation Traceability Validation System
This demonstrates the validation logic without requiring OpenAI API
"""

import json
from traceability_validator import TraceabilityValidator, RegulatedSourceType, ValidationResult

def test_validation_without_ai():
    """Test the basic validation logic without AI"""
    
    # Mock validator that doesn't use OpenAI
    class MockValidator(TraceabilityValidator):
        def __init__(self):
            # Initialize without OpenAI client
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
        
        def validate_traceability(self, certificates):
            """Mock validation without AI"""
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
            
            # Basic validation logic
            regulated_source = RegulatedSourceType.UNKNOWN
            traceability_chain = []
            validation_issues = []
            compliance_notes = []
            
            # Check for regulated source
            for cert in certificates:
                source = self.identify_regulated_source(cert)
                if source != RegulatedSourceType.UNKNOWN:
                    regulated_source = source
                    break
            
            # Build basic traceability chain
            for cert in certificates:
                seller = cert.get('seller_name', 'Unknown')
                buyer = cert.get('buyer_name', 'Unknown')
                if seller != 'Unknown' and buyer != 'Unknown':
                    traceability_chain.append(f"{seller} -> {buyer}")
            
            # Check for required documents
            cert_types = [cert.get('certificate_type', '').lower() for cert in certificates]
            has_packing_slip = any('packing' in ct for ct in cert_types)
            has_material_cert = any('material' in ct or 'conformity' in ct or 'conformance' in ct for ct in cert_types)
            
            if not has_packing_slip:
                validation_issues.append("Missing packing slip")
            if not has_material_cert:
                validation_issues.append("Missing material certification")
            
            # Determine validity
            is_valid = (regulated_source != RegulatedSourceType.UNKNOWN and 
                       len(traceability_chain) > 0 and 
                       has_packing_slip and 
                       has_material_cert)
            
            if regulated_source == RegulatedSourceType.OEM:
                compliance_notes.append("OEM trace found - best possible traceability")
            elif regulated_source == RegulatedSourceType.FAR_121:
                compliance_notes.append("121 trace found - domestic airline traceability")
            elif regulated_source == RegulatedSourceType.FAR_145:
                compliance_notes.append("145 trace found - repair station traceability")
            
            confidence_score = 0.9 if is_valid else 0.3
            
            return ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                regulated_source=regulated_source,
                traceability_chain=traceability_chain,
                missing_documentation=validation_issues,
                compliance_notes=compliance_notes,
                asa100_compliance=is_valid,
                validation_issues=validation_issues
            )
    
    # Load test data
    with open('my_results.json', 'r') as f:
        data = json.load(f)
    
    extraction_results = data['extraction_results']
    
    # Test with mock validator
    validator = MockValidator()
    
    print("="*70)
    print("TRACEABILITY VALIDATION TEST RESULTS")
    print("="*70)
    
    for doc_name, certificates in extraction_results.items():
        print(f"\n📄 Document: {doc_name}")
        print(f"   Certificates: {len(certificates)}")
        
        result = validator.validate_traceability(certificates)
        
        print(f"   ✅ Valid: {result.is_valid}")
        print(f"   📊 Confidence: {result.confidence_score:.1%}")
        print(f"   🏢 Regulated Source: {result.regulated_source.value}")
        print(f"   🔗 Chain Length: {len(result.traceability_chain)}")
        
        if result.traceability_chain:
            print(f"   📋 Chain: {result.traceability_chain[0]}")
        
        if result.compliance_notes:
            print(f"   📝 Notes: {result.compliance_notes[0]}")
        
        if result.validation_issues:
            print(f"   ⚠️  Issues: {', '.join(result.validation_issues[:2])}")
        
        print(f"   📜 ASA-100 Compliant: {result.asa100_compliance}")
    
    # Generate summary
    total_docs = len(extraction_results)
    results = [validator.validate_traceability(certs) for certs in extraction_results.values()]
    
    valid_count = sum(1 for r in results if r.is_valid)
    oem_count = sum(1 for r in results if r.regulated_source == RegulatedSourceType.OEM)
    far121_count = sum(1 for r in results if r.regulated_source == RegulatedSourceType.FAR_121)
    far145_count = sum(1 for r in results if r.regulated_source == RegulatedSourceType.FAR_145)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total Documents: {total_docs}")
    print(f"Valid Documents: {valid_count} ({valid_count/total_docs:.1%})")
    print(f"OEM Traced: {oem_count}")
    print(f"121 Traced: {far121_count}")
    print(f"145 Traced: {far145_count}")
    print(f"Average Confidence: {sum(r.confidence_score for r in results)/len(results):.1%}")

if __name__ == "__main__":
    test_validation_without_ai() 