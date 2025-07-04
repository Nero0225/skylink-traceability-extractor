from llama_cloud_services import LlamaParse
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import logging

load_dotenv(dotenv_path=".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment variable
API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def parse_document(file_path: str) -> str:
    """Parse a document with retry logic on failure."""
    try:
        # Check if API key is available
        if not API_KEY:
            raise ValueError("LLAMA_CLOUD_API_KEY not found in environment variables")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Parse document
        logger.info(f"Starting to parse document: {file_path}")
        
        # Try different parsing strategies in order of preference
        strategies = [
            {
                "name": "Standard Markdown with Page Numbers and Exact Tables",
                "config": {
                    "api_key": API_KEY,
                    "result_type": "markdown",
                    "system_prompt": "Parse this document and extract all text content while preserving structure and formatting. Pay special attention to tables - preserve exact table structure, column alignment, merged cells, and all table data. Maintain precise spacing and formatting within tables.",
                    # "max_timeout": 180,
                    "verbose": True,
                    "language": "en",
                    "page_prefix": "START OF PAGE: {pageNumber}\n",
                    "page_suffix": "\n\nEND OF PAGE: {pageNumber}\n\n",
                    "split_by_page": True,
                    # Table-specific options for exact structure preservation
                    "output_tables_as_HTML": True,  # Output tables as HTML for better structure preservation
                    "outlined_table_extraction": True,  # Better extraction for tables with borders
                    "adaptive_long_table": True,  # Handle long tables that span multiple pages
                    "do_not_unroll_columns": True,  # Preserve original column structure
                    "premium_mode": True,  # Use best parsing quality
                    "extract_layout": True,  # Preserve layout information
                    "preserve_layout_alignment_across_pages": True,# Maintain alignment across pages
                }
            },
            {
                "name": "Text Only with Page Numbers and Exact Tables",
                "config": {
                    "api_key": API_KEY,
                    "result_type": "text",
                    "system_prompt": "Extract all text content from this document. For tables, preserve exact structure, spacing, and alignment. Maintain all rows, columns, and cell content exactly as they appear.",
                    # "max_timeout": 120,
                    "verbose": True,
                    "language": "en",
                    "page_prefix": "START OF PAGE: {pageNumber}\n",
                    "page_suffix": "\n\nEND OF PAGE: {pageNumber}\n\n",
                    "split_by_page": True,
                    # Table-specific options
                    "output_tables_as_HTML": True,
                    "outlined_table_extraction": True,
                    "adaptive_long_table": True,
                    "do_not_unroll_columns": True,
                    "premium_mode": True,
                    "extract_layout": True,
                    "preserve_layout_alignment_across_pages": True
                }
            },
            {
                "name": "Simple Parse with Page Numbers and Exact Tables",
                "config": {
                    "api_key": API_KEY,
                    # "max_timeout": 90,
                    "verbose": True,
                    "language": "en",
                    "page_prefix": "START OF PAGE: {pageNumber}\n",
                    "page_suffix": "\n\nEND OF PAGE: {pageNumber}\n\n",
                    "split_by_page": True,
                    # Table-specific options
                    "output_tables_as_HTML": True,
                    "outlined_table_extraction": True,
                    "adaptive_long_table": True,
                    "do_not_unroll_columns": True,
                    "premium_mode": True,
                    "extract_layout": True
                }
            }
        ]
        
        last_error = None
        
        for strategy in strategies:
            try:
                logger.info(f"Attempting parsing with strategy: {strategy['name']}")
                parser = LlamaParse(**strategy['config'])
                
                # Parse document
                documents = parser.load_data(file_path)
                
                if documents and len(documents) > 0:
                    # Extract text from parsed documents
                    result_text = ""
                    for doc in documents:
                        if doc.text and doc.text.strip():
                            result_text += doc.text
                            result_text += "\n\n"
                    
                    if result_text.strip():
                        logger.info(f"Successfully parsed document with strategy '{strategy['name']}': {file_path}")
                        return result_text
                    else:
                        logger.warning(f"Strategy '{strategy['name']}' returned empty content")
                        continue
                else:
                    logger.warning(f"Strategy '{strategy['name']}' returned no documents")
                    continue
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Strategy '{strategy['name']}' failed: {str(e)}")
                continue
        
        # If all strategies failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("All parsing strategies failed to extract content")
        
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {str(e)}")
        raise

def batch_parse_documents(directory_path: str, output_dir: str = "./markdowns"):
    """Parse all PDF files in a directory."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all PDF files in directory
        pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
        
        for pdf_file in pdf_files:
            file_path = os.path.join(directory_path, pdf_file)
            try:
                output = parse_document(file_path)
                
                # Write output to file
                output_filename = pdf_file.replace('.pdf', '.md')
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(output)
                    
                logger.info(f"Successfully wrote output to {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to process directory {directory_path}: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        os.listdir("./invoices")
        batch_parse_documents("./invoices", "./markdowns")
    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

# sync batch
# results = parser.parse(["./my_file1.pdf", "./my_file2.pdf"])

# # async
# result = await parser.aparse("./my_file.pdf")

# # async batch
# results = await parser.aparse(["./my_file1.pdf", "./my_file2.pdf"])