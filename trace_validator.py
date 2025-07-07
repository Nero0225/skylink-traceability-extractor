import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# --- Configuration and Setup ---

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file and add your key (e.g., OPENAI_API_KEY=sk-...).")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}")
    raise

# --- File Loading ---

def load_text_file(filepath):
    """Loads content from a text file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Context file not found at {filepath}. Please ensure it exists.")
        return ""

def load_json_file(filepath):
    """Loads content from a JSON file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load or parse JSON from {filepath}: {e}")
        return None

# --- Core Logic ---

def build_prompt(document_package_name, certificate_list, rules, docs):
    """Builds the detailed prompt for the OpenAI API call."""
    certificates_json_string = json.dumps(certificate_list, indent=2)
    final_owner = "Skylink, Inc."

    system_prompt = """
You are an expert AI assistant specializing in aviation supply chain auditing. Your task is to analyze a list of official certificates for aircraft parts and determine if a valid traceability chain back to a regulated source can be constructed from them.
"""

    user_prompt = f"""
**Part 1: Regulatory Context**

You must adhere to the following rules for your analysis.

*Definitions of Regulated Traceability Sources:*
---
{rules}
---

*General Documentation Requirements (ASA-100):*
---
{docs}
---

**Part 2: Certificate Data to Analyze**

The following JSON array contains the **official certificates** that were extracted from a full document package. The full package may have contained other documents (like Packing Slips or Work Orders) that are not present here. Your task is to build the traceability chain using only these provided certificates.

```json
{certificates_json_string}
```

**Part 3: Your Task & Output Format**

1.  **Group by Part Number:** Group the certificates by their `part_number`.
2.  **Construct Traceability Chains:** For each part, construct the chain of custody.
    *   Start with the certificate where the buyer is "Skylink" (or similar).
    *   Trace backwards by linking the certificates. A direct link is when the `seller_name` on one certificate matches the `buyer_name` on the next.
    *   **Crucially, use the `traceability_source` field to bridge gaps.** If a certificate lists a `traceability_source` (e.g., "From US Airways" or "PO from BizJet"), you must use that as the next link in the chain, even if a corresponding certificate from that source is not in this list. The `traceability_source` is a sworn statement of origin.
    *   Your goal is to determine the ultimate source at the beginning of the chain.
3.  **Classify Source & Validate:**
    *   Identify the ultimate source for each part (e.g., "US Airways", "Applied Avionics, Inc.").
    *   **Pay close attention to the `manufacturer` field.** If the trace chain leads back to the company listed as the `manufacturer`, you MUST classify the `source_type` as "OEM".
    *   Classify this source using the rules in Part 1 (OEM, 121 Airline, etc.).
    *   Determine if the traceability is valid. A valid trace must end at a regulated source. An incomplete chain or one ending at an unknown/unregulated entity is invalid.
4.  **Format Output:** Your entire response MUST be a single JSON object. The keys of this object should be the document package titles. The value for each key should be another JSON object where keys are the distinct part numbers found. If a part number is not available, use the description or a placeholder. Each part number's value should be a final JSON object with the following structure:
    {{
      "is_valid": boolean,
      "trace_chain": "Skylink, Inc. <- Company A <- Company B <- ... <- Original Source",
      "original_source": "Name of the Original Source Company",
      "source_type": "OEM | 121 Airline | 145 Repair Station | Unregulated | Unknown | etc.",
      "reasoning": "A concise explanation for your decision, detailing why the trace is valid or invalid. Mention any gaps or issues found."
    }}
"""
    return system_prompt, user_prompt

def analyze_traceability(package_name, cert_list, rules, docs):
    """Sends the prompt to OpenAI and gets the analysis."""
    logging.info(f"Analyzing package: {package_name}...")
    system_prompt, user_prompt = build_prompt(package_name, cert_list, rules, docs)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"An error occurred during OpenAI API call for '{package_name}': {e}")
        return {
            package_name: {
                "error": {
                    "is_valid": False,
                    "trace_chain": "Analysis failed",
                    "original_source": "N/A",
                    "source_type": "Error",
                    "reasoning": f"An exception occurred during analysis: {e}"
                }
            }
        }

# --- Main Execution ---

def save_results_to_json(results, filepath):
    """Saves the results dictionary to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        logging.info(f"Successfully saved validation results to {filepath}")
    except IOError as e:
        logging.error(f"Failed to write results to {filepath}: {e}")

def main():
    """Main function to run the traceability validation script."""
    # 1. Load all necessary context and data files
    logging.info("Loading context files and certificate data...")
    asa_docs = load_text_file("ASA-100.md")
    trace_rules = load_text_file("traceability_rules.md")
    cert_data = load_json_file("certificate_extraction_results.json")

    if not all([asa_docs, trace_rules, cert_data]):
        logging.error("One or more essential files could not be loaded. Exiting.")
        return

    # 2. Create output directory for split results
    output_dir = "validation_results"
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Validation results will be saved in the '{output_dir}' directory.")

    # 3. Iterate, validate, and save each package to a separate file
    extraction_results = cert_data.get("extraction_results", {})
    saved_files = []
    
    for package_name, cert_list in extraction_results.items():
        if not cert_list:
            logging.warning(f"Skipping empty certificate list for {package_name}")
            continue
        
        analysis_result = analyze_traceability(package_name, cert_list, trace_rules, asa_docs)

        # Generate a clean filename from the markdown document title
        base_name = Path(package_name).stem
        output_filename = f"{base_name}_validation.json"
        output_filepath = os.path.join(output_dir, output_filename)
        
        save_results_to_json(analysis_result, output_filepath)
        saved_files.append(output_filepath)

    # 4. Print a summary to the console listing the generated files
    print("\n" + "="*80)
    print(" " * 25 + "TRACEABILITY VALIDATION COMPLETE")
    print("="*80 + "\n")
    print(f"Validation results for each document package have been saved to the '{output_dir}' directory:")
    for file_path in saved_files:
        print(f"  - {file_path}")
    print("")

if __name__ == "__main__":
    main() 