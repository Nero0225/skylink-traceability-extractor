#!/usr/bin/env python3
"""
FastAPI Aviation Traceability PDF Processor Startup Script
"""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env")

def main():
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(current_dir))
    
    # Check for required environment variables
    required_env_vars = [
        "LLAMA_CLOUD_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("temp_uploads", exist_ok=True)
    os.makedirs("processed_reports", exist_ok=True)
    
    print("🚀 Starting Aviation Traceability PDF Processor...")
    print("=" * 60)
    print("📡 Server will be available at: http://localhost:8000")
    print("📊 API documentation at: http://localhost:8000/docs")
    print("🔧 Health check at: http://localhost:8000/health")
    print("=" * 60)
    print("\n✨ Features:")
    print("   • Modern drag-and-drop interface")
    print("   • Multiple file upload support")
    print("   • Real-time file selection preview")
    print("   • Batch processing with parallel execution")
    print("   • Beautiful results dashboard")
    print("\nPress Ctrl+C to stop the server")
    
    # Run the FastAPI application
    try:
        uvicorn.run(
            "fastapi_pdf_processor:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 