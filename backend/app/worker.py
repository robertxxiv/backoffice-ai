from __future__ import annotations

import logging
import time

from sqlalchemy.exc import SQLAlchemyError

from app.chunking.service import ChunkingService
from app.core.config import get_settings
from app.db.migrations import ensure_database_schema
from app.db.session import SessionLocal
from app.embeddings.service import build_embedding_service
from app.indexing.service import IndexingService


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s worker %(message)s")
    settings = get_settings()
    if settings.run_migrations_on_startup:
        ensure_database_schema()
    service = IndexingService(
        settings=settings,
        chunking_service=ChunkingService(),
        embedding_service=build_embedding_service(settings),
    )
    while True:
        try:
            with SessionLocal() as session:
                processed = service.process_pending_jobs(session)
                if processed:
                    logging.info("processed_jobs=%s", processed)
        except SQLAlchemyError as exc:
            logging.warning("worker_loop_db_error=%s", exc)
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
