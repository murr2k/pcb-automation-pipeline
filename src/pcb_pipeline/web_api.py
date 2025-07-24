"""
FastAPI web interface for PCB automation pipeline.
Provides REST API endpoints for design submission, status tracking, and file downloads.
"""

import logging
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from .pipeline import PCBPipeline
from .config import PipelineConfig
from .fab_interface import FabricationManager

logger = logging.getLogger(__name__)

# Data models for API
class DesignSpec(BaseModel):
    name: str
    description: Optional[str] = ""
    board: Dict[str, Any]
    components: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    power: Optional[Dict[str, List[str]]] = None
    design_rules: Optional[Dict[str, Any]] = None
    manufacturing: Optional[Dict[str, Any]] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0-100
    message: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

class QuoteRequest(BaseModel):
    design_spec: DesignSpec
    manufacturers: Optional[List[str]] = None
    quantity: int = 10

class OrderRequest(BaseModel):
    design_spec: DesignSpec
    manufacturer: str
    quantity: int = 10
    shipping_address: Dict[str, str]
    special_instructions: Optional[str] = None


# Global job storage (in production, use Redis or database)
job_storage: Dict[str, JobStatus] = {}
pipeline_cache: Dict[str, PCBPipeline] = {}


def create_app(config: Optional[PipelineConfig] = None) -> FastAPI:
    """Create FastAPI application."""
    
    app = FastAPI(
        title="PCB Automation Pipeline API",
        description="REST API for automated PCB design and manufacturing",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configuration
    app_config = config or PipelineConfig()
    
    # Mount static files
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def home():
        """Serve the landing page."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return index_file.read_text()
        else:
            return """
            <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>PCB Automation Pipeline API</h1>
                <p>REST API for automated PCB design and manufacturing</p>
                <a href="/docs" style="display: inline-block; margin: 20px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">API Documentation</a>
            </body>
            </html>
            """
    
    @app.get("/api")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "PCB Automation Pipeline API",
            "version": "1.0.0",
            "status": "active",
            "endpoints": {
                "designs": "/designs",
                "quotes": "/quotes",
                "orders": "/orders",
                "jobs": "/jobs",
                "manufacturers": "/manufacturers"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": "2025-01-24T00:00:00Z"}
    
    @app.post("/designs/validate")
    async def validate_design(design_spec: DesignSpec):
        """Validate design specification without generating PCB."""
        try:
            # Create temporary pipeline
            pipeline = PCBPipeline(app_config)
            
            # Convert to dict and validate
            spec_dict = design_spec.dict()
            pipeline._validate_spec(spec_dict)
            
            return {
                "valid": True,
                "message": "Design specification is valid",
                "component_count": len(spec_dict.get('components', [])),
                "net_count": len(spec_dict.get('connections', []))
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": str(e),
                "errors": [str(e)]
            }
    
    @app.post("/designs/generate")
    async def generate_design(design_spec: DesignSpec, background_tasks: BackgroundTasks):
        """Generate PCB design from specification (async)."""
        job_id = str(uuid.uuid4())
        
        # Create job status
        job_status = JobStatus(
            job_id=job_id,
            status="queued",
            progress=0,
            message="Job queued for processing",
            created_at="2025-01-24T00:00:00Z"
        )
        
        job_storage[job_id] = job_status
        
        # Start background processing
        background_tasks.add_task(process_design_generation, job_id, design_spec, app_config)
        
        return {"job_id": job_id, "status": "queued"}
    
    @app.get("/jobs/{job_id}")
    async def get_job_status(job_id: str):
        """Get job status and results."""
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job_storage[job_id]
    
    @app.get("/jobs")
    async def list_jobs():
        """List all jobs."""
        return {"jobs": list(job_storage.values())}
    
    @app.post("/quotes")
    async def get_quotes(quote_request: QuoteRequest):
        """Get manufacturer quotes for design."""
        try:
            # Create temporary pipeline
            pipeline = PCBPipeline(app_config)
            fab_manager = FabricationManager(app_config)
            
            # Generate minimal layout for quoting
            spec_dict = quote_request.design_spec.dict()
            schematic = pipeline.generate_schematic(spec_dict)
            layout = pipeline.create_layout(schematic)
            
            # Get quotes
            if quote_request.manufacturers:
                quotes = {}
                for manufacturer in quote_request.manufacturers:
                    try:
                        interface = fab_manager.get_interface(manufacturer)
                        order_data = interface.prepare_order(layout, quantity=quote_request.quantity)
                        quote = interface.get_quote(order_data)
                        quotes[manufacturer] = quote
                    except Exception as e:
                        quotes[manufacturer] = {"error": str(e)}
            else:
                quotes = fab_manager.get_all_quotes(layout, quantity=quote_request.quantity)
            
            return {
                "design_name": spec_dict.get('name', 'Unknown'),
                "quantity": quote_request.quantity,
                "quotes": quotes
            }
            
        except Exception as e:
            logger.error(f"Quote generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/orders")
    async def submit_order(order_request: OrderRequest):
        """Submit order to manufacturer."""
        try:
            # Create pipeline and generate layout
            pipeline = PCBPipeline(app_config)
            spec_dict = order_request.design_spec.dict()
            schematic = pipeline.generate_schematic(spec_dict)
            layout = pipeline.create_layout(schematic)
            
            # Submit order
            fab_manager = FabricationManager(app_config)
            interface = fab_manager.get_interface(order_request.manufacturer)
            
            order_data = interface.prepare_order(
                layout, 
                quantity=order_request.quantity,
                shipping_address=order_request.shipping_address,
                special_instructions=order_request.special_instructions
            )
            
            order_id = interface.submit_order(order_data)
            
            return {
                "order_id": order_id,
                "manufacturer": order_request.manufacturer,
                "status": "submitted",
                "quantity": order_request.quantity
            }
            
        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/orders/{order_id}")
    async def get_order_status(order_id: str, manufacturer: str):
        """Get order status from manufacturer."""
        try:
            fab_manager = FabricationManager(app_config)
            interface = fab_manager.get_interface(manufacturer)
            status = interface.check_order_status(order_id)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/manufacturers")
    async def list_manufacturers():
        """List available manufacturers and their capabilities."""
        fab_manager = FabricationManager(app_config)
        manufacturers = {}
        
        for name in ['jlcpcb', 'pcbway', 'oshpark', 'seeedstudio']:
            try:
                interface = fab_manager.get_interface(name)
                capabilities = interface.get_capabilities()
                manufacturers[name] = capabilities
            except Exception as e:
                manufacturers[name] = {"error": str(e)}
        
        return {"manufacturers": manufacturers}
    
    @app.post("/designs/upload")
    async def upload_design_file(file: UploadFile = File(...)):
        """Upload design specification file."""
        if not file.filename.endswith(('.yaml', '.yml', '.json')):
            raise HTTPException(status_code=400, detail="Only YAML and JSON files are supported")
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            # Load and validate
            pipeline = PCBPipeline(app_config)
            design_spec = pipeline.load_specification(tmp_path)
            
            # Clean up
            Path(tmp_path).unlink()
            
            return {
                "filename": file.filename,
                "design_name": design_spec.get('name', 'Unknown'),
                "component_count": len(design_spec.get('components', [])),
                "valid": True
            }
            
        except Exception as e:
            # Clean up on error
            if 'tmp_path' in locals():
                Path(tmp_path).unlink(missing_ok=True)
            
            raise HTTPException(status_code=400, detail=f"Invalid design file: {e}")
    
    @app.get("/jobs/{job_id}/files/{filename}")
    async def download_file(job_id: str, filename: str):
        """Download generated files from completed job."""
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_storage[job_id]
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        # Find file in job results
        file_path = None
        if job.results and 'output_dir' in job.results:
            output_dir = Path(job.results['output_dir'])
            file_path = output_dir / filename
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    
    return app


async def process_design_generation(job_id: str, design_spec: DesignSpec, config: PipelineConfig):
    """Background task to process design generation."""
    try:
        # Update status
        job_storage[job_id].status = "processing"
        job_storage[job_id].progress = 10
        job_storage[job_id].message = "Initializing pipeline"
        
        # Create pipeline
        pipeline = PCBPipeline(config)
        spec_dict = design_spec.dict()
        
        # Generate schematic
        job_storage[job_id].progress = 30
        job_storage[job_id].message = "Generating schematic"
        schematic = pipeline.generate_schematic(spec_dict)
        
        # Create layout
        job_storage[job_id].progress = 50
        job_storage[job_id].message = "Creating PCB layout"
        layout = pipeline.create_layout(schematic)
        
        # Validate design
        job_storage[job_id].progress = 70
        job_storage[job_id].message = "Validating design"
        validation_passed = pipeline.validate_design(layout)
        
        # Export files
        job_storage[job_id].progress = 90
        job_storage[job_id].message = "Exporting manufacturing files"
        
        output_dir = config.output_dir / f"job_{job_id}"
        output_path = pipeline.export_gerbers(layout, str(output_dir))
        
        # Complete job
        job_storage[job_id].status = "completed"
        job_storage[job_id].progress = 100
        job_storage[job_id].message = "Design generation completed"
        job_storage[job_id].completed_at = "2025-01-24T00:00:00Z"
        job_storage[job_id].results = {
            "design_name": spec_dict.get('name'),
            "component_count": len(schematic.components),
            "net_count": len(schematic.nets),
            "validation_passed": validation_passed,
            "output_dir": str(output_path),
            "files_generated": [f.name for f in Path(output_path).rglob('*') if f.is_file()]
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_storage[job_id].status = "failed"
        job_storage[job_id].message = f"Error: {str(e)}"


def main():
    """Run the web API server."""
    config = PipelineConfig()
    app = create_app(config)
    
    # Get port from environment for Fly.io
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()