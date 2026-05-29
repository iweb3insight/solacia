"""Entry point for `python -m solacia` and `solacia` CLI."""

import uvicorn

from solacia.config import settings


def main():
    """Start the Solacia server."""
    uvicorn.run(
        "solacia.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
    )


if __name__ == "__main__":
    main()
