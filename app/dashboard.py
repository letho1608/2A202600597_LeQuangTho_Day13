from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

_DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"


def mount_dashboard(app: FastAPI) -> None:
    @app.get("/dashboard", include_in_schema=False)
    async def dashboard() -> HTMLResponse:
        if not _DASHBOARD_PATH.exists():
            return HTMLResponse("<h1>dashboard.html missing</h1>", status_code=500)
        return FileResponse(_DASHBOARD_PATH, media_type="text/html")
