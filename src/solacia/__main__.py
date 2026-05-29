"""Entry point for `python -m solacia`."""

import uvicorn
from solacia.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "solacia.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
    )
