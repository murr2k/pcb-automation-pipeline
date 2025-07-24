"""Simplified PCB Pipeline API for initial deployment"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data models
class HealthStatus(BaseModel):
    status: str
    service: str
    version: str
    deployment: str
    timestamp: str

class DesignSpec(BaseModel):
    name: str
    description: Optional[str] = ""
    board: Dict[str, Any]
    components: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]

def create_app() -> FastAPI:
    """Create the FastAPI application"""
    
    app = FastAPI(
        title="PCB Automation Pipeline API",
        description="REST API for automated PCB design and manufacturing",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    @app.get("/", response_class=HTMLResponse)
    async def home():
        """Landing page"""
        return """
        <html>
        <head>
            <title>PCB Automation Pipeline</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    text-align: center;
                    padding: 50px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    font-size: 3em;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }
                p {
                    font-size: 1.2em;
                    margin-bottom: 40px;
                    opacity: 0.9;
                }
                .buttons {
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                a {
                    display: inline-block;
                    padding: 15px 30px;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
                a:hover {
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                }
                .status {
                    margin-top: 40px;
                    padding: 20px;
                    background: rgba(46, 204, 113, 0.2);
                    border-radius: 10px;
                    border: 1px solid rgba(46, 204, 113, 0.5);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 PCB Automation Pipeline</h1>
                <p>Automated PCB design and manufacturing API</p>
                <div class="buttons">
                    <a href="/health">Health Status</a>
                    <a href="/api">API Info</a>
                    <a href="/docs">Documentation</a>
                    <a href="/redoc">ReDoc</a>
                </div>
                <div class="status">
                    <p><strong>Status:</strong> 🟢 API is running</p>
                    <p>Full pipeline functionality coming soon!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """Health check endpoint"""
        from datetime import datetime
        return HealthStatus(
            status="healthy",
            service="pcb-pipeline",
            version="1.0.0",
            deployment="fly.io",
            timestamp=datetime.utcnow().isoformat()
        )
    
    @app.get("/api")
    async def api_info():
        """API information endpoint"""
        return {
            "name": "PCB Automation Pipeline API",
            "version": "1.0.0",
            "status": "operational",
            "features": [
                "Automated PCB design generation",
                "Multi-manufacturer support (JLCPCB, MacroFab, PCBWay)",
                "AI-assisted component placement",
                "Design rule checking",
                "Auto-routing integration"
            ],
            "endpoints": {
                "health": "/health - Service health status",
                "api": "/api - API information",
                "docs": "/docs - Interactive API documentation",
                "designs": "/designs - PCB design operations (coming soon)",
                "quotes": "/quotes - Manufacturing quotes (coming soon)",
                "orders": "/orders - Order management (coming soon)"
            }
        }
    
    @app.post("/designs/validate")
    async def validate_design(design_spec: DesignSpec):
        """Validate a design specification"""
        # Simple validation for now
        try:
            component_count = len(design_spec.components)
            net_count = len(design_spec.connections)
            
            return {
                "valid": True,
                "message": "Design specification is valid",
                "stats": {
                    "name": design_spec.name,
                    "component_count": component_count,
                    "net_count": net_count,
                    "board_size": design_spec.board.get("size", "unknown")
                }
            }
        except Exception as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/manufacturers")
    async def list_manufacturers():
        """List supported manufacturers"""
        return {
            "manufacturers": [
                {
                    "id": "jlcpcb",
                    "name": "JLCPCB",
                    "description": "Fast and affordable PCB manufacturing",
                    "capabilities": ["2-6 layer boards", "SMT assembly", "Fast turnaround"],
                    "status": "supported"
                },
                {
                    "id": "macrofab",
                    "name": "MacroFab",
                    "description": "US-based PCB assembly and manufacturing",
                    "capabilities": ["Prototype to production", "Full assembly", "US manufacturing"],
                    "status": "supported"
                },
                {
                    "id": "pcbway",
                    "name": "PCBWay",
                    "description": "Professional PCB manufacturing",
                    "capabilities": ["Advanced PCBs", "Flexible PCBs", "Metal core PCBs"],
                    "status": "coming_soon"
                }
            ]
        }
    
    return app

# For direct execution
if __name__ == "__main__":
    import uvicorn
    app = create_app()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)