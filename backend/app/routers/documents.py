import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentDetail, DocumentProcessResponse, DocumentRead
from app.services.auth_service import get_current_user
from app.services.document_service import (
    create_document_from_upload,
    delete_document,
    document_to_detail,
    get_document_for_user,
    list_project_documents,
    parse_json_list,
    parse_json_object,
    process_document,
)

router = APIRouter(tags=["documents"])


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/projects/{project_id}/documents/upload",
    response_model=DocumentRead,
    status_code=201,
)
async def upload_document(
    project_id: uuid.UUID,
    title: Annotated[str, Form()],
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    db: DbSession,
    allowed_roles: Annotated[str, Form()] = "[]",
    allowed_user_ids: Annotated[str, Form()] = "[]",
    tags: Annotated[str, Form()] = "[]",
    metadata: Annotated[str, Form()] = "{}",
) -> Document:
    return await create_document_from_upload(
        db,
        project_id=project_id,
        user=current_user,
        upload=file,
        title=title,
        allowed_roles=parse_json_list(allowed_roles, field_name="allowed_roles"),
        allowed_user_ids=parse_json_list(allowed_user_ids, field_name="allowed_user_ids"),
        tags=parse_json_list(tags, field_name="tags"),
        metadata=parse_json_object(metadata, field_name="metadata"),
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def get_project_documents(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[Document]:
    return list_project_documents(db, project_id=project_id, user=current_user)


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentDetail:
    document = get_document_for_user(db, document_id=document_id, user=current_user)
    return document_to_detail(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    delete_document(db, document_id=document_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
def post_process_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentProcessResponse:
    get_document_for_user(db, document_id=document_id, user=current_user)
    return process_document(db, document_id=document_id, user_id=current_user.id)
