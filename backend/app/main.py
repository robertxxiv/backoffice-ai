from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, install_request_logging
from app.db.migrations import ensure_database_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().run_migrations_on_startup:
        ensure_database_schema()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        lifespan=lifespan,
        docs_url="/docs" if resolved_settings.enable_api_docs else None,
        redoc_url="/redoc" if resolved_settings.enable_api_docs else None,
        openapi_url="/openapi.json" if resolved_settings.enable_api_docs else None,
    )
    if settings is not None:
        application.dependency_overrides[get_settings] = lambda: resolved_settings
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=resolved_settings.trusted_hosts)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_origin_regex=resolved_settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_logging(application)
    application.include_router(router)
    return application


app = create_app()
