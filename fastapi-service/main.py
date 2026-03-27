from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add shared module to path
sys.path.append('/app/shared')

from api.routes import router
from services.jdownloader import jdownloader_service
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/fastapi.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Video Downloader API",
    description="API wrapper for JDownloader and yt-dlp",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Execute on startup"""
    logger.info("FastAPI service starting...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Connect to JDownloader
    try:
        if jdownloader_service.connect():
            logger.info("Connected to JDownloader")
        else:
            logger.warning("JDownloader connection failed - using yt-dlp fallback")
    except Exception as e:
        logger.error(f"JDownloader connection error: {e}")

    # Create directories
    os.makedirs('/downloads', exist_ok=True)
    os.makedirs('/downloads/temp', exist_ok=True)
    os.makedirs('/logs', exist_ok=True)

    logger.info("FastAPI service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on shutdown"""
    logger.info("FastAPI service shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Video Downloader API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
