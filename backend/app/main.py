"""FastAPI application entry point.

On startup the database tables are created if missing; nothing is dropped.
Exposes a health probe and the versioned notes API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.database import init_db
from app.routers import auth, notes
from app.services.files import FileValidationError

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Public academic notes library API.",
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        # Cookie-based auth requires explicit origins with credentials; never
        # use a wildcard origin together with credentials.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def csrf_origin_check(request: Request, call_next) -> Response:
    """Reject unsafe cross-origin requests from unknown origins.

    Browsers always attach an ``Origin`` header to cross-origin POST requests.
    If a signed-in user visits a malicious site, that site cannot include the
    HttpOnly cookie, and this check blocks it from replaying state-changing
    requests with a spoofed-but-known origin. SameSite=Lax cookie policy is the
    primary CSRF defense; this is a second layer.
    """

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origins:
            return JSONResponse(
                status_code=403, content={"detail": "Origin not allowed"}
            )
    return await call_next(request)

app.include_router(notes.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)


@app.exception_handler(FileValidationError)
async def _file_validation_handler(_request, exc: FileValidationError) -> JSONResponse:
    """Translate file-validation failures into clean JSON errors."""

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe used by tests and deployment checks."""

    return {"status": "ok", "service": settings.app_name, "version": app.version}
