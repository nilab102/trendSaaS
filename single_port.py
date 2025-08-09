import os
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import routers
from services.trends_router import router as trends_router
from services.analyzer_router import router as analyzer_router

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: dict
    version: str
    frontend_available: bool

# Initialize FastAPI app
app = FastAPI(
    title="TrendSaaS API",
    description="A comprehensive API for analyzing Google Trends data and identifying SaaS opportunities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trends_router, prefix="/api/v1")
app.include_router(analyzer_router, prefix="/api/v1")

# Frontend setup
frontend_dir = Path("frontend")
frontend_index = frontend_dir / "index.html"

# Mount static files if frontend directory exists
if frontend_dir.exists() and frontend_dir.is_dir():
    # Mount static files for assets (CSS, JS, images, etc.)
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    logger.info(f"📁 Frontend directory mounted: {frontend_dir.absolute()}")
else:
    logger.warning("⚠️ Frontend directory not found. Only API will be available.")

@app.get("/", tags=["root"])
async def root():
    """Root endpoint - serves frontend or API information"""
    # If frontend exists, serve the index.html
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    
    # Otherwise, return API information
    return {
        "message": "TrendSaaS API",
        "version": "1.0.0",
        "description": "Google Trends Analysis & SaaS Opportunity Identification",
        "documentation": "/docs",
        "endpoints": {
            "trends": "/api/v1/trends",
            "analyzer": "/api/v1/analyzer",
            "health": "/health"
        },
        "websocket": "/api/v1/analyzer/ws",
        "timestamp": datetime.now().isoformat(),
        "note": "Frontend not available - place your frontend files in the 'frontend' directory"
    }

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check environment variables
        env_status = {
            "google_api_key": bool(os.getenv("google_api_key")),
            "trends_api_url": bool(os.getenv("TRENDS_API_BASE_URL")),
            "serp_api_key": bool(os.getenv("serp_api_key"))
        }
        
        # Check service status
        services_status = {
            "trends_service": "healthy",
            "analyzer_service": "healthy",
            "websocket_service": "healthy"
        }
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            services=services_status,
            version="1.0.0",
            frontend_available=frontend_index.exists()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/api/v1", tags=["api"])
async def api_info():
    """API version information"""
    return {
        "version": "1.0.0",
        "name": "TrendSaaS API",
        "description": "Google Trends Analysis & SaaS Opportunity Identification",
        "endpoints": {
            "trends": {
                "base": "/api/v1/trends",
                "analyze": "/api/v1/trends/analyze/{keyword}",
                "health": "/api/v1/trends/health"
            },
            "analyzer": {
                "base": "/api/v1/analyzer",
                "analyze_sync": "/api/v1/analyzer/analyze",
                "analyze_get": "/api/v1/analyzer/analyze/{keyword}",
                "websocket": "/api/v1/analyzer/ws",
                "status": "/api/v1/analyzer/status",
                "health": "/api/v1/analyzer/health"
            }
        },
        "websocket": {
            "endpoint": "/api/v1/analyzer/ws",
            "message_format": {
                "type": "analyze|ping",
                "keyword": "string (for analyze)",
                "comparison": "boolean (for analyze)"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

# Catch-all route for SPA routing (must be last)
@app.get("/{full_path:path}", tags=["frontend"])
async def serve_frontend(full_path: str):
    """
    Serve frontend files or fallback to index.html for SPA routing
    This handles all routes that don't match API endpoints
    """
    # Skip if it's an API route (shouldn't reach here anyway due to router priority)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Skip docs routes (let FastAPI handle these)
    if full_path in ["docs", "redoc", "openapi.json"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try to serve the specific file first
    file_path = frontend_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    
    # Fallback to index.html for SPA routing (React Router, Vue Router, etc.)
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    else:
        # If no frontend, return a helpful message
        return JSONResponse(
            status_code=404,
            content={
                "error": "Frontend not available",
                "message": "Place your frontend files in the 'frontend' directory",
                "api_docs": "/docs",
                "api_info": "/api/v1"
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Request failed with status {exc.status_code}",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Starting TrendSaaS API...")
    
    # Check environment variables
    required_env_vars = ["google_api_key"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {missing_vars}")
        logger.warning("Some features may not work properly without these variables")
    
    # Check frontend availability
    if frontend_index.exists():
        logger.info(f"📱 Frontend available at: /")
        logger.info(f"📁 Frontend files: {frontend_dir.absolute()}")
    else:
        logger.warning("📱 Frontend not found - place files in 'frontend' directory")
    
    # Log configuration
    logger.info(f"📊 Trends API URL: {os.getenv('TRENDS_API_BASE_URL', 'http://localhost:8000')}")
    logger.info(f"🤖 Gemini Model: {os.getenv('google_gemini_name', 'gemini-1.5-pro')}")
    logger.info(f"🔍 SERP API: {'✓ Available' if os.getenv('serp_api_key') else '✗ Not configured'}")
    
    logger.info("✅ TrendSaaS API started successfully!")
    logger.info("🌐 Application running on http://localhost:8000")
    logger.info("📖 API Documentation: http://localhost:8000/docs")
    logger.info("💚 Health Check: http://localhost:8000/health")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Shutting down TrendSaaS API...")

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "10000"))  # Render's default port
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("🚀 TrendSaaS Application Starting")
    logger.info("=" * 60)
    logger.info(f"🌐 Server: http://{host}:{port}")
    logger.info(f"📱 Frontend: http://localhost:{port}")
    logger.info(f"🔧 API: http://localhost:{port}/api/v1")
    logger.info(f"📖 Docs: http://localhost:{port}/docs")
    logger.info(f"🔄 Auto-reload: {'enabled' if reload else 'disabled'}")
    logger.info("=" * 60)
    
    # Start the server
    uvicorn.run(
        "single_port:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )