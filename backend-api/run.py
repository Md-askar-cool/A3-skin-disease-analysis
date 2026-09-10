"""
SafeSkin AI – Local Development Runner
Run with: python run.py
"""

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,       # Hot-reload in development
        log_level="debug" if not settings.is_production else "info",
        access_log=True,
    )
