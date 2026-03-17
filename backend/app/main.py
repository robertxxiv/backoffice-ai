from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import get_settings
from app.core.logging import configure_logging, install_request_logging
from app.db.migrations import ensure_database_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().run_migrations_on_startup:
        ensure_database_schema()
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_logging(application)
    application.include_router(router)
    return application


app = create_app()
