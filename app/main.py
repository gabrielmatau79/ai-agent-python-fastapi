from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers.admin import router as admin_router
from app.api.routers.agent import router as agent_router
from app.api.routers.config import router as config_router
from app.api.routers.health import router as health_router
from app.api.routers.memory import router as memory_router
from app.api.routers.rag import router as rag_router
from app.core.exceptions import ApplicationError, to_http_exception
from app.core.lifespan import lifespan
from app.core.settings import Settings

STATIC_DIR = Path(__file__).resolve().parent / "static"


def get_app_version() -> str:
    try:
        return package_version("ai-agent-python-fastapi")
    except PackageNotFoundError:
        return "0.0.0"


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title=settings.app_name,
        version=get_app_version(),
        openapi_url="/openapi.json",
        docs_url="/docs",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_request: Request, exc: ApplicationError) -> JSONResponse:
        error = to_http_exception(exc)
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(health_router)
    app.include_router(agent_router, prefix=settings.api_v1_prefix)
    app.include_router(memory_router, prefix=settings.api_v1_prefix)
    app.include_router(rag_router, prefix=settings.api_v1_prefix)
    app.include_router(config_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router)
    return app


app = create_app()
