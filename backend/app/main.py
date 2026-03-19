from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import router
from app.auth.service import ensure_initial_admin
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, install_request_logging
from app.db.migrations import ensure_database_schema
from app.db.session import SessionLocal


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if resolved_settings.run_migrations_on_startup:
            ensure_database_schema()
        with SessionLocal() as session:
            ensure_initial_admin(session, resolved_settings)
        yield

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
        allow_origin_regex=resolved_settings.cors_origin_regex or None,
        allow_credentials=resolved_settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_logging(application)
    application.include_router(router)
    return application


app = create_app()
