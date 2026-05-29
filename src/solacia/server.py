"""
Solacia - FastAPI Server Entry Point
"""

import logging

from fastapi import FastAPI

from solacia.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Solacia",
    description="An agentic AI companion that reads the room, not just the prompt",
    version="0.1.0",
)

# Register routes
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    from solacia.config import settings

    uvicorn.run(
        "solacia.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
    )
