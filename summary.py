import json
from dataclasses import asdict
from certificate_extractor import CertificateExtractor
from traceability_source_validator import TraceabilitySourceValidator

def main():
    file_path = "markdowns/3. OEM TRACE EXAMPLE.md"
    # Load the certificates
    extractor = CertificateExtractor()
    validator = TraceabilitySourceValidator()

    with open(file_path, "r") as file:
        document_content = file.read()

    print("Completed document loading...")

    results = extractor.extract_certificates_from_text(document_content)

    print("Completed certificate extraction...")

    cert_type = ""
    part_number = ""
    serial_number = ""
    description = ""
    condition_code = ""
    quantity = ""
    traceability_type = ""
    traceability_name = ""
    validation_notes = ""

    print(results)

    for result in results:
        if result.buyer_name and "skylink" in result.buyer_name.lower():
            cert_type = result.certificate_type
            part_number = result.part_number
            serial_number = result.serial_number
            description = result.description
            condition_code = result.condition_code
            quantity = result.quantity

    print("Completed certificate extraction, starting traceability validation...")

    # Convert CertificateInfo objects to dictionaries for the validator
    results_dict = [asdict(cert) for cert in results]
    
    traceability_source = validator.validate_source_traceability(results_dict, file_path.split("/")[-1])
    
    print(traceability_source)
    print("Completed traceability source validation...")

    traceability_type = traceability_source.final_source.source_type
    traceability_name = traceability_source.final_source.source_name
    validation_notes = traceability_source.validation_notes

    with open("summary.json", "w") as file:
        json.dump({
            "cert_type": cert_type,
            "part_number": part_number,
            "serial_number": serial_number,
            "description": description,
            "condition_code": condition_code,
            "quantity": quantity,
            "traceability_type": traceability_type,
            "traceability_name": traceability_name,
            "validation_notes": validation_notes
        }, file, indent=4)

if __name__ == "__main__":
    main()