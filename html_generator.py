import json
from datetime import datetime
from pathlib import Path

class HTMLTraceabilityGenerator:
    """Generate mobile-friendly HTML reports for aviation traceability validation"""
    
    def __init__(self):
        self.css_styles = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 10px;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                overflow: hidden;
                animation: slideIn 0.5s ease-out;
            }
            
            @keyframes slideIn {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .header::before {
                content: '✈️';
                position: absolute;
                top: 10px;
                right: 20px;
                font-size: 2em;
                opacity: 0.3;
            }
            
            .header h1 {
                font-size: 1.8em;
                margin-bottom: 5px;
                font-weight: 300;
            }
            
            .header .subtitle {
                font-size: 0.9em;
                opacity: 0.8;
                font-weight: 300;
            }
            
            .compliance-badge {
                display: inline-block;
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 0.9em;
                margin: 15px 0 5px 0;
                animation: pulse 2s infinite;
            }
            
            .compliant {
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }
            
            .non-compliant {
                background: linear-gradient(135deg, #f44336, #da190b);
                color: white;
                box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
            }
            
            .unregulated {
                background: linear-gradient(135deg, #ff9800, #f57c00);
                color: white;
                box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            .content {
                padding: 25px;
            }
            
            .info-grid {
                display: grid;
                gap: 15px;
                margin-bottom: 25px;
            }
            
            .info-card {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 15px;
                transition: all 0.3s ease;
                border-left: 4px solid #007bff;
            }
            
            .info-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .info-label {
                font-weight: 600;
                color: #495057;
                font-size: 0.85em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
                display: block;
            }
            
            .info-value {
                font-size: 1.1em;
                color: #212529;
                word-break: break-word;
            }
            
            .traceability-section {
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
                border: 2px solid #dee2e6;
            }
            
            .section-title {
                font-size: 1.3em;
                font-weight: 600;
                color: #343a40;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .source-info {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .source-type {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .oem { background: #e8f5e8; color: #2e7d32; }
            .airline-121 { background: #e3f2fd; color: #1565c0; }
            .airline-129 { background: #f3e5f5; color: #7b1fa2; }
            .repair-145 { background: #fff3e0; color: #ef6c00; }
            .unregulated { background: #ffebee; color: #c62828; }
            .fraudulent { background: #ffcdd2; color: #b71c1c; border: 1px solid #f44336; }
            
            .timestamp {
                text-align: center;
                color: #6c757d;
                font-size: 0.8em;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #dee2e6;
            }
            
            .warning-icon {
                color: #ff9800;
                margin-right: 5px;
            }
            
            .success-icon {
                color: #4CAF50;
                margin-right: 5px;
            }
            
            .error-icon {
                color: #f44336;
                margin-right: 5px;
            }
            
            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                body {
                    padding: 5px;
                }
                
                .container {
                    border-radius: 10px;
                    margin: 5px;
                }
                
                .header {
                    padding: 15px;
                }
                
                .header h1 {
                    font-size: 1.5em;
                }
                
                .content {
                    padding: 15px;
                }
                
                .info-card {
                    padding: 12px;
                }
                
                .traceability-section {
                    padding: 15px;
                }
            }
            
            @media (max-width: 480px) {
                .header h1 {
                    font-size: 1.3em;
                }
                
                .compliance-badge {
                    font-size: 0.8em;
                    padding: 6px 15px;
                }
                
                .info-value {
                    font-size: 1em;
                }
                
                .section-title {
                    font-size: 1.1em;
                }
            }
        </style>
        """
    
    def get_compliance_info(self, traceability_type):
        """Get compliance badge class and icon based on traceability type"""
        if traceability_type in ['OEM', '121', '129', '135', '145']:
            return 'compliant', '✅', 'success-icon'
        elif traceability_type == 'UNREGULATED':
            return 'unregulated', '⚠️', 'warning-icon'
        else:
            return 'non-compliant', '❌', 'error-icon'
    
    def get_source_type_class(self, traceability_type):
        """Get CSS class for source type badge"""
        type_map = {
            'OEM': 'oem',
            '121': 'airline-121',
            '129': 'airline-129',
            '135': 'airline-121',  # Same styling as 121
            '145': 'repair-145',
            'UNREGULATED': 'unregulated',
            'FRAUDULENT': 'fraudulent'
        }
        return type_map.get(traceability_type, 'unregulated')
    
    def get_source_type_description(self, traceability_type):
        """Get human-readable description of source type"""
        descriptions = {
            'OEM': 'Original Equipment Manufacturer',
            '121': 'US Domestic Airline',
            '129': 'Foreign Airline (Operating in USA)',
            '135': 'Charter/Cargo Operator',
            '145': 'FAA-Approved Repair Station',
            'UNREGULATED': 'Unregulated Source',
            'FRAUDULENT': 'Fraudulent Entity'
        }
        return descriptions.get(traceability_type, 'Unknown Source Type')
    
    def generate_html(self, summary_data, document_name="Aviation Part"):
        """Generate complete HTML report from summary data"""
        
        # Get compliance information
        compliance_class, compliance_icon, icon_class = self.get_compliance_info(summary_data['traceability_type'])
        source_class = self.get_source_type_class(summary_data['traceability_type'])
        source_description = self.get_source_type_description(summary_data['traceability_type'])
        
        # Determine compliance status text
        if summary_data['traceability_type'] in ['OEM', '121', '129', '135', '145']:
            compliance_text = "COMPLIANT"
            compliance_description = "✅ This part has valid traceability to a regulated source"
        elif summary_data['traceability_type'] == 'UNREGULATED':
            compliance_text = "NON-COMPLIANT"
            compliance_description = "⚠️ This part does not trace back to a regulated source"
        else:
            compliance_text = "NON-COMPLIANT"
            compliance_description = "❌ This part has traceability issues"
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aviation Traceability Report - {summary_data.get('part_number', 'Unknown')}</title>
            {self.css_styles}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Aviation Traceability Report</h1>
                    <div class="subtitle">ASA-100 Compliance Validation</div>
                    <div class="compliance-badge {compliance_class}">
                        {compliance_icon} {compliance_text}
                    </div>
                    <div style="font-size: 0.85em; margin-top: 5px; opacity: 0.9;">
                        {compliance_description}
                    </div>
                </div>
                
                <div class="content">
                    <div class="info-grid">
                        <div class="info-card">
                            <span class="info-label">Certificate Type</span>
                            <div class="info-value">{summary_data.get('cert_type', 'N/A')}</div>
                        </div>
                        
                        <div class="info-card">
                            <span class="info-label">Part Number</span>
                            <div class="info-value" style="font-family: monospace; font-weight: bold; color: #0066cc;">
                                {summary_data.get('part_number', 'N/A')}
                            </div>
                        </div>
                        
                        <div class="info-card">
                            <span class="info-label">Serial Number</span>
                            <div class="info-value" style="font-family: monospace;">
                                {summary_data.get('serial_number') or 'N/A'}
                            </div>
                        </div>
                        
                        <div class="info-card">
                            <span class="info-label">Description</span>
                            <div class="info-value">{summary_data.get('description', 'N/A')}</div>
                        </div>
                        
                        <div class="info-card">
                            <span class="info-label">Condition Code</span>
                            <div class="info-value">
                                <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                    {summary_data.get('condition_code', 'N/A')}
                                </span>
                            </div>
                        </div>
                        
                        <div class="info-card">
                            <span class="info-label">Quantity</span>
                            <div class="info-value">{summary_data.get('quantity', 'N/A')}</div>
                        </div>
                    </div>
                    
                    <div class="traceability-section">
                        <div class="section-title">
                            <span class="{icon_class}">{compliance_icon}</span>
                            Traceability Source Analysis
                        </div>
                        
                        <div class="source-info">
                            <div class="source-type {source_class}">
                                {summary_data.get('traceability_type', 'UNKNOWN')}
                            </div>
                            <div style="font-weight: 600; margin-bottom: 8px; color: #343a40;">
                                {source_description}
                            </div>
                            <div style="font-size: 1.1em; color: #212529;">
                                <strong>Source Entity:</strong> {summary_data.get('traceability_name', 'N/A')}
                            </div>
                            
                            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #007bff;">
                                <div style="font-size: 0.9em; color: #495057;">
                                    <strong>Regulatory Compliance:</strong><br>
                                    {self.get_compliance_explanation(summary_data['traceability_type'])}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="timestamp">
                        Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def get_compliance_explanation(self, traceability_type):
        """Get detailed explanation of compliance status"""
        explanations = {
            'OEM': 'This part traces back to the Original Equipment Manufacturer, providing the highest level of traceability assurance. The manufacturer certifies this part is suitable for aircraft use.',
            '121': 'This part traces back to a US domestic airline operating under Part 121 regulations. These are legitimate regulated sources for aircraft parts.',
            '129': 'This part traces back to a foreign airline operating in the USA under Part 129 regulations. These are legitimate regulated sources.',
            '135': 'This part traces back to a charter/cargo operator under Part 135 regulations. These are legitimate regulated sources.',
            '145': 'This part traces back to an FAA-approved repair station under Part 145 regulations. These are legitimate regulated sources.',
            'UNREGULATED': 'This part does not trace back to a regulated source as required by ASA-100 standards. Additional verification may be required.',
            'FRAUDULENT': 'This part traces back to an entity that falsely claims to be regulated. This creates serious compliance concerns.'
        }
        return explanations.get(traceability_type, 'Unknown compliance status.')
    
    def save_html(self, html_content, filename="traceability_report.html"):
        """Save HTML content to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename

def generate_traceability_report(summary_json_path="summary.json", output_html_path="traceability_report.html"):
    """Main function to generate HTML report from summary JSON"""
    
    try:
        # Load summary data
        with open(summary_json_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Generate HTML
        generator = HTMLTraceabilityGenerator()
        html_content = generator.generate_html(summary_data)
        
        # Save HTML file
        generator.save_html(html_content, output_html_path)
        
        print(f"✅ HTML report generated successfully: {output_html_path}")
        print(f"📊 Part Number: {summary_data.get('part_number', 'N/A')}")
        print(f"🔍 Traceability Type: {summary_data.get('traceability_type', 'N/A')}")
        print(f"🏭 Source: {summary_data.get('traceability_name', 'N/A')}")
        
        return output_html_path
        
    except FileNotFoundError:
        print(f"❌ Error: {summary_json_path} not found. Run summary.py first to generate the JSON data.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in {summary_json_path}")
        return None
    except Exception as e:
        print(f"❌ Error generating HTML report: {str(e)}")
        return None

if __name__ == "__main__":
    # Generate report from summary.json
    generate_traceability_report() 