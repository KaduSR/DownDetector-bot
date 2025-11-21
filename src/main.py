"""Main application entry point for DownDetector Notification Bot."""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from src import __version__
from src.api import api_router, health_router
from src.api.routes import set_current_state, add_changes
from src.middleware.security import configure_security
from src.scheduler import OutageMonitorScheduler
from src.scraper.config import ScraperConfig
from src.detector.config import DetectorConfig
from src.notifier.config import EmailConfig
from src.ai.config import AIConfig
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(
    "main",
    os.getenv("LOG_FILE", "logs/outage_monitor.log"),
)

# Global scheduler instance
scheduler: OutageMonitorScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global scheduler

    logger.info(f"Starting DownDetector Notification Bot v{__version__}")

    # Initialize configurations
    scraper_config = ScraperConfig()
    detector_config = DetectorConfig()
    email_config = EmailConfig()
    ai_config = AIConfig()

    # Check if AI is enabled
    enable_ai = bool(ai_config.api_key)

    # Initialize scheduler
    scheduler = OutageMonitorScheduler(
        scraper_config=scraper_config,
        detector_config=detector_config,
        email_config=email_config,
        ai_config=ai_config,
        enable_ai=enable_ai,
    )

    # Start scheduler
    scheduler.start()

    # Setup state update callback
    async def update_state():
        """Periodically update API state from scheduler."""
        while True:
            try:
                state = scheduler.get_current_state()
                set_current_state(state)
            except Exception as e:
                logger.error(f"Error updating state: {e}")
            await asyncio.sleep(60)  # Update every minute

    # Start state update task
    state_task = asyncio.create_task(update_state())

    yield

    # Cleanup
    logger.info("Shutting down...")
    state_task.cancel()
    scheduler.stop()
    await scheduler.scraper.close()


# Create FastAPI application
app = FastAPI(
    title="DownDetector Notification Bot",
    description="Real-time service outage monitoring and notification system",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure security middleware
configure_security(app, enable_cors=os.getenv("API_ENABLE_CORS", "true").lower() == "true")

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DownDetector Notification Bot",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# Mount WebSocket app (if scheduler is available)
@app.on_event("startup")
async def mount_websocket():
    """Mount WebSocket application after startup."""
    global scheduler
    if scheduler:
        ws_app = scheduler.get_websocket_app()
        app.mount("/ws", ws_app)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
