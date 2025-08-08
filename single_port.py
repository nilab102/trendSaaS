#!/usr/bin/env python3
"""
Single-port development server for TrendSaaS

Serves:
- Backend API and WebSocket under /api/v1 (using existing routers)
- Frontend static files from /frontend at the root path /

Usage:
  python single_port.py  # defaults to HOST=0.0.0.0, PORT=8000

Environment variables (optional):
- HOST (default: 0.0.0.0)
- PORT (default: 8000)
- RELOAD (default: true)
"""

import os
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("single_port")

# Import existing routers (no changes to current code)
from services.trends_router import router as trends_router
from services.analyzer_router import router as analyzer_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrendSaaS (Single Port)",
        description="Frontend + API served on the same port for development",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS (safe to keep open in dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include existing API routers under /api/v1
    app.include_router(trends_router, prefix="/api/v1")
    app.include_router(analyzer_router, prefix="/api/v1")

    # Static frontend paths
    project_root = Path(__file__).resolve().parent
    frontend_dir = project_root / "frontend"
    index_file = frontend_dir / "index.html"

    if not index_file.exists():
        logger.warning("Frontend index.html not found at %s", index_file)

    # Serve directories exactly as referenced by index.html
    # e.g., href="styles/main.css" → /styles/*
    styles_dir = frontend_dir / "styles"
    scripts_dir = frontend_dir / "scripts"
    assets_dir = frontend_dir / "assets"

    if styles_dir.exists():
        app.mount("/styles", StaticFiles(directory=str(styles_dir)), name="styles")
    if scripts_dir.exists():
        app.mount("/scripts", StaticFiles(directory=str(scripts_dir)), name="scripts")
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def serve_index():
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Frontend not found",
                "detail": "Expected frontend/index.html to exist",
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Optional: serve favicon if present
    @app.get("/favicon.ico")
    def favicon():
        ico = frontend_dir / "favicon.ico"
        if ico.exists():
            return FileResponse(str(ico))
        return JSONResponse(status_code=404, content={"detail": "favicon not found"})

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info("Serving TrendSaaS frontend and API on http://%s:%s", host, port)
    uvicorn.run(
        "single_port:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


