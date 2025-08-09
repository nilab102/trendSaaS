import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Routers
from services.trends_router import router as trends_router
from services.analyzer_router import router as analyzer_router


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main_new")


FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting TrendSaaS unified app...")
    if not INDEX_FILE.exists():
        logger.warning("index.html not found at %s", INDEX_FILE)
    yield
    # Shutdown
    logger.info("🛑 Stopping TrendSaaS unified app")


app = FastAPI(
    title="TrendSaaS",
    description="Unified app serving API and static frontend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS (can be restricted if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(trends_router, prefix="/api/v1")
app.include_router(analyzer_router, prefix="/api/v1")


# Static files
if FRONTEND_DIR.exists():
    # Serve directories explicitly to keep asset URLs working
    static_mounts = {
        "/assets": FRONTEND_DIR / "assets",
        "/scripts": FRONTEND_DIR / "scripts",
        "/styles": FRONTEND_DIR / "styles",
    }
    for mount_point, dir_path in static_mounts.items():
        if dir_path.exists():
            app.mount(mount_point, StaticFiles(directory=str(dir_path)), name=mount_point.strip("/"))


@app.get("/", include_in_schema=False)
async def serve_index():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return JSONResponse(
        status_code=200,
        content={
            "message": "TrendSaaS",
            "docs": "/docs",
            "api_root": "/api/v1",
            "timestamp": datetime.now().isoformat(),
        },
    )


# SPA fallback: serve index.html for unknown non-API routes
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Do not intercept API routes
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    # Render provides PORT env var; default to 3000 for local single-port deployments
    port = int(os.getenv("PORT", "3000"))
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"

    logger.info("🌐 Starting unified server on %s:%s", host, port)
    logger.info("🔄 Auto-reload: %s", "enabled" if reload_enabled else "disabled")

    uvicorn.run(
        "main_new:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level="info",
    )


