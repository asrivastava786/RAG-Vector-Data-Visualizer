from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.healthcheck")
def healthcheck() -> str:
    return "ok"


@celery_app.task(name="app.workers.tasks.process_document")
def process_document_task(document_id: str) -> dict:
    from uuid import UUID

    from app.db.session import SessionLocal
    from app.services.document_service import process_document

    db = SessionLocal()
    try:
        result = process_document(db, document_id=UUID(document_id))
        return result.model_dump(mode="json")
    finally:
        db.close()
