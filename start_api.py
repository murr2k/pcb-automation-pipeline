#!/usr/bin/env python3
"""Startup script for the PCB Pipeline API - handles module path setup"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import and run
from pcb_pipeline.web_api import create_app
import uvicorn

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        log_level="info"
    )