import json
import os
from datetime import datetime
from pathlib import Path
from html_generator import HTMLTraceabilityGenerator
from summary import main as run_summary
from dataclasses import asdict
from certificate_extractor import CertificateExtractor
from traceability_source_validator import TraceabilitySourceValidator

class BatchHTMLGenerator:
    """Generate HTML reports for multiple aviation traceability documents"""
    
    def __init__(self):
        self.html_generator = HTMLTraceabilityGenerator()
        self.extractor = CertificateExtractor()
        self.validator = TraceabilitySourceValidator()
    
    def process_document(self, file_path):
        """Process a single document and return summary data"""
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                document_content = file.read()
            
            # Extract certificates
            results = self.extractor.extract_certificates_from_text(document_content, os.path.basename(file_path))
            
            if not results:
                return None
            
            # Find certificate for SKYLINK
            cert_info = None
            for result in results:
                if result.buyer_name and "skylink" in result.buyer_name.lower():
                    cert_info = result
                    break
            
            if not cert_info:
                cert_info = results[0]  # Fallback to first certificate
            
            # Validate traceability
            results_dict = [asdict(cert) for cert in results]
            traceability_source = self.validator.validate_source_traceability(results_dict, os.path.basename(file_path))
            
            # Create summary data
            summary_data = {
                "cert_type": cert_info.certificate_type,
                "part_number": cert_info.part_number,
                "serial_number": cert_info.serial_number,
                "description": cert_info.description,
                "condition_code": cert_info.condition_code,
                "quantity": cert_info.quantity,
                "traceability_type": traceability_source.final_source.source_type,
                "traceability_name": traceability_source.final_source.source_name,
                "document_name": os.path.basename(file_path)
            }
            
            return summary_data
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")
            return None
    
    def generate_dashboard_html(self, documents_data):
        """Generate a dashboard HTML showing multiple documents"""
        
        total_docs = len(documents_data)
        compliant_docs = sum(1 for doc in documents_data if doc['traceability_type'] in ['OEM', '121', '129', '135', '145'])
        compliance_rate = (compliant_docs / total_docs * 100) if total_docs > 0 else 0
        
        # Sort documents by compliance status
        documents_data.sort(key=lambda x: (
            x['document_name'],
            0 if x['traceability_type'] in ['OEM', '121', '129', '135', '145'] else 1
        ))
        
        dashboard_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aviation Traceability Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 10px;
                }}
                
                .dashboard-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                
                .dashboard-header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 25px;
                    text-align: center;
                }}
                
                .dashboard-header h1 {{
                    font-size: 2.2em;
                    margin-bottom: 10px;
                    font-weight: 300;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border-left: 4px solid #007bff;
                }}
                
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #007bff;
                    margin-bottom: 5px;
                }}
                
                .stat-label {{
                    color: #6c757d;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .documents-grid {{
                    display: grid;
                    gap: 15px;
                    padding: 20px;
                }}
                
                .document-card {{
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 10px;
                    padding: 20px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    position: relative;
                }}
                
                .document-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                
                .document-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                    gap: 10px;
                }}
                
                .document-title {{
                    font-weight: 600;
                    color: #343a40;
                    font-size: 1.1em;
                    flex: 1;
                    min-width: 200px;
                }}
                
                .status-badge {{
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.8em;
                    font-weight: bold;
                    white-space: nowrap;
                }}
                
                .status-compliant {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                
                .status-non-compliant {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                
                .document-info {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }}
                
                .info-item {{
                    display: flex;
                    flex-direction: column;
                }}
                
                .info-label {{
                    font-size: 0.75em;
                    color: #6c757d;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 3px;
                }}
                
                .info-value {{
                    color: #212529;
                    font-weight: 500;
                    word-break: break-word;
                }}
                
                .part-number {{
                    font-family: monospace;
                    background: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                
                .source-type {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-size: 0.75em;
                    font-weight: bold;
                    margin-top: 5px;
                }}
                
                .oem {{ background: #e8f5e8; color: #2e7d32; }}
                .airline-121 {{ background: #e3f2fd; color: #1565c0; }}
                .repair-145 {{ background: #fff3e0; color: #ef6c00; }}
                .unregulated {{ background: #ffebee; color: #c62828; }}
                
                .timestamp {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 0.8em;
                    padding: 20px;
                    border-top: 1px solid #dee2e6;
                }}
                
                @media (max-width: 768px) {{
                    .dashboard-container {{
                        margin: 5px;
                        border-radius: 10px;
                    }}
                    
                    .dashboard-header {{
                        padding: 20px;
                    }}
                    
                    .dashboard-header h1 {{
                        font-size: 1.8em;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: 1fr 1fr;
                        gap: 15px;
                        padding: 15px;
                    }}
                    
                    .documents-grid {{
                        padding: 15px;
                    }}
                    
                    .document-info {{
                        grid-template-columns: 1fr;
                        gap: 10px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <h1>✈️ Aviation Traceability Dashboard</h1>
                    <p>ASA-100 Compliance Analysis Summary</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_docs}</div>
                        <div class="stat-label">Total Documents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{compliant_docs}</div>
                        <div class="stat-label">Compliant</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_docs - compliant_docs}</div>
                        <div class="stat-label">Non-Compliant</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{compliance_rate:.1f}%</div>
                        <div class="stat-label">Compliance Rate</div>
                    </div>
                </div>
                
                <div class="documents-grid">
        """
        
        for doc in documents_data:
            is_compliant = doc['traceability_type'] in ['OEM', '121', '129', '135', '145']
            status_class = 'status-compliant' if is_compliant else 'status-non-compliant'
            status_text = '✅ COMPLIANT' if is_compliant else '❌ NON-COMPLIANT'
            
            source_class = self.html_generator.get_source_type_class(doc['traceability_type'])
            
            dashboard_html += f"""
                    <div class="document-card" onclick="window.open('individual_reports/{doc['document_name'].replace('.md', '.html')}', '_blank')">
                        <div class="document-header">
                            <div class="document-title">{doc['document_name']}</div>
                            <div class="status-badge {status_class}">{status_text}</div>
                        </div>
                        
                        <div class="document-info">
                            <div class="info-item">
                                <div class="info-label">Part Number</div>
                                <div class="info-value">
                                    <span class="part-number">{doc.get('part_number', 'N/A')}</span>
                                </div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Description</div>
                                <div class="info-value">{doc.get('description', 'N/A')}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Quantity</div>
                                <div class="info-value">{doc.get('quantity', 'N/A')}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Source</div>
                                <div class="info-value">
                                    {doc.get('traceability_name', 'N/A')[:50]}{'...' if len(doc.get('traceability_name', '')) > 50 else ''}
                                    <div class="source-type {source_class}">{doc['traceability_type']}</div>
                                </div>
                            </div>
                        </div>
                    </div>
            """
        
        dashboard_html += f"""
                </div>
                
                <div class="timestamp">
                    Dashboard generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </div>
            </div>
        </body>
        </html>
        """
        
        return dashboard_html
    
    def process_all_documents(self, markdowns_dir="markdowns", output_dir="html_reports"):
        """Process all markdown documents and generate HTML reports"""
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/individual_reports", exist_ok=True)
        
        documents_data = []
        
        # Process each markdown file
        for filename in os.listdir(markdowns_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(markdowns_dir, filename)
                print(f"🔄 Processing {filename}...")
                
                summary_data = self.process_document(file_path)
                if summary_data:
                    documents_data.append(summary_data)
                    
                    # Generate individual HTML report
                    html_content = self.html_generator.generate_html(summary_data, filename)
                    html_filename = filename.replace('.md', '.html')
                    html_path = os.path.join(f"{output_dir}/individual_reports", html_filename)
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"✅ Generated {html_filename}")
        
        # Generate dashboard
        if documents_data:
            dashboard_html = self.generate_dashboard_html(documents_data)
            dashboard_path = os.path.join(output_dir, "dashboard.html")
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            
            print(f"\n🎯 Dashboard generated: {dashboard_path}")
            print(f"📊 Processed {len(documents_data)} documents")
            print(f"✅ Compliant: {sum(1 for doc in documents_data if doc['traceability_type'] in ['OEM', '121', '129', '135', '145'])}")
            print(f"❌ Non-Compliant: {sum(1 for doc in documents_data if doc['traceability_type'] not in ['OEM', '121', '129', '135', '145'])}")
        
        return documents_data

if __name__ == "__main__":
    generator = BatchHTMLGenerator()
    generator.process_all_documents() 