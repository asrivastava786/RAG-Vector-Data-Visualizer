import json
import re
import uuid
from typing import Any

from fastapi import UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import bad_request, not_found
from app.models.common import WorkspaceRole
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentDetail, DocumentProcessResponse
from app.services.audit_service import write_audit_log
from app.services.extraction_service import extract_text, validate_document_type
from app.services.object_storage_service import get_object_storage
from app.services.rbac_service import (
    ROLE_ORDER,
    get_accessible_project,
    get_workspace_membership,
    require_workspace_role,
)


def parse_json_list(value: str | None, *, field_name: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise bad_request(f"{field_name} must be a JSON array.") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise bad_request(f"{field_name} must be a JSON array of strings.")
    return parsed


def parse_json_object(value: str | None, *, field_name: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise bad_request(f"{field_name} must be a JSON object.") from exc
    if not isinstance(parsed, dict):
        raise bad_request(f"{field_name} must be a JSON object.")
    return parsed


async def create_document_from_upload(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    upload: UploadFile,
    title: str,
    allowed_roles: list[str],
    allowed_user_ids: list[str],
    tags: list[str],
    metadata: dict[str, Any],
) -> Document:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    require_workspace_role(
        db, workspace_id=project.workspace_id, user_id=user.id, minimum_role=WorkspaceRole.developer
    )
    if not title.strip():
        raise bad_request("Document title is required.")
    if not upload.filename:
        raise bad_request("Uploaded file must have a filename.")
    content_type = upload.content_type or "application/octet-stream"
    validate_document_type(upload.filename, content_type)
    normalized_roles = _validate_roles(allowed_roles)
    if not normalized_roles and not allowed_user_ids:
        raise bad_request("At least one allowed role or user is required.")

    payload = await upload.read()
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if not payload:
        raise bad_request("Uploaded file is empty.")
    if len(payload) > max_bytes:
        raise bad_request(f"Uploaded file exceeds the {get_settings().max_upload_mb} MB limit.")

    document_id = uuid.uuid4()
    storage_key = _storage_key(project.workspace_id, project.id, document_id, upload.filename)
    get_object_storage().put_bytes(storage_key, payload, content_type)

    document = Document(
        id=document_id,
        workspace_id=project.workspace_id,
        project_id=project.id,
        uploaded_by=user.id,
        title=title.strip(),
        filename=upload.filename,
        content_type=content_type,
        storage_key=storage_key,
        status="uploaded",
        metadata_json={
            **metadata,
            "original_size_bytes": len(payload),
            "structure": {},
            "warnings": [],
        },
        allowed_roles_json=normalized_roles,
        allowed_users_json=[str(user_id) for user_id in allowed_user_ids],
        tags_json=_normalize_tags(tags),
    )
    db.add(document)
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        action="document.upload",
        entity_type="document",
        entity_id=str(document.id),
        metadata={"filename": upload.filename, "content_type": content_type},
    )
    db.commit()
    db.refresh(document)
    _try_enqueue_processing(document.id)
    return document


def list_project_documents(db: Session, *, project_id: uuid.UUID, user: User) -> list[Document]:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    membership = get_workspace_membership(db, workspace_id=project.workspace_id, user_id=user.id)
    stmt = (
        select(Document)
        .where(Document.workspace_id == project.workspace_id, Document.project_id == project.id)
        .order_by(Document.created_at.desc())
    )
    if ROLE_ORDER[membership.role] < ROLE_ORDER[WorkspaceRole.admin]:
        stmt = stmt.where(_document_access_clause(membership.role, user.id))
    return list(db.scalars(stmt).all())


def get_document_for_user(db: Session, *, document_id: uuid.UUID, user: User) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise not_found("Document not found.")
    membership = get_workspace_membership(db, workspace_id=document.workspace_id, user_id=user.id)
    is_admin = ROLE_ORDER[membership.role] >= ROLE_ORDER[WorkspaceRole.admin]
    if not is_admin and not user_can_access_document(
        document,
        role=membership.role,
        user_id=user.id,
    ):
        raise not_found("Document not found.")
    return document


def document_to_detail(document: Document) -> DocumentDetail:
    text = document.extracted_text or ""
    preview_text = text[:6000]
    return DocumentDetail.model_validate(
        {
            **document.__dict__,
            "preview": {
                "text": preview_text,
                "truncated": len(text) > len(preview_text),
                "character_count": len(text),
                "structure": document.metadata_json.get("structure", {}),
                "warnings": document.metadata_json.get("warnings", []),
            },
        }
    )


def process_document(
    db: Session,
    *,
    document_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> DocumentProcessResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise not_found("Document not found.")
    if user_id:
        require_workspace_role(
            db,
            workspace_id=document.workspace_id,
            user_id=user_id,
            minimum_role=WorkspaceRole.developer,
        )

    document.status = "processing"
    db.commit()
    try:
        payload = get_object_storage().get_bytes(document.storage_key)
        extracted = extract_text(document.filename, document.content_type, payload)
        structure = extracted.structure
        document.extracted_text = extracted.text
        document.page_count = structure.get("page_count")
        document.status = "processed"
        document.metadata_json = {
            **document.metadata_json,
            "structure": structure,
            "warnings": extracted.warnings,
            "extracted_character_count": len(extracted.text),
        }
        write_audit_log(
            db,
            workspace_id=document.workspace_id,
            user_id=user_id,
            action="document.process",
            entity_type="document",
            entity_id=str(document.id),
            metadata={"characters": len(extracted.text), "page_count": document.page_count},
        )
        db.commit()
        db.refresh(document)
        return DocumentProcessResponse(
            id=document.id,
            status=document.status,
            extracted_characters=len(extracted.text),
            page_count=document.page_count,
            warnings=extracted.warnings,
        )
    except Exception as exc:
        document.status = "failed"
        document.metadata_json = {
            **document.metadata_json,
            "warnings": [*document.metadata_json.get("warnings", []), "Extraction failed."],
            "processing_error": str(exc),
        }
        db.commit()
        raise


def delete_document(db: Session, *, document_id: uuid.UUID, user: User) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise not_found("Document not found.")
    require_workspace_role(
        db, workspace_id=document.workspace_id, user_id=user.id, minimum_role=WorkspaceRole.admin
    )
    get_object_storage().delete(document.storage_key)
    write_audit_log(
        db,
        workspace_id=document.workspace_id,
        user_id=user.id,
        action="document.delete",
        entity_type="document",
        entity_id=str(document.id),
    )
    db.delete(document)
    db.commit()


def user_can_access_document(
    document: Document,
    *,
    role: WorkspaceRole,
    user_id: uuid.UUID,
) -> bool:
    return role.value in document.allowed_roles_json or str(user_id) in document.allowed_users_json


def _validate_roles(roles: list[str]) -> list[str]:
    valid = {role.value for role in WorkspaceRole}
    normalized = []
    for role in roles:
        role_value = role.lower().strip()
        if role_value not in valid:
            raise bad_request(f"Unsupported role '{role}'.")
        normalized.append(role_value)
    return sorted(set(normalized))


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned:
            normalized.append(cleaned[:60])
    return sorted(set(normalized))


def _storage_key(
    workspace_id: uuid.UUID, project_id: uuid.UUID, document_id: uuid.UUID, filename: str
) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or "document"
    return f"workspaces/{workspace_id}/projects/{project_id}/documents/{document_id}/{safe_name}"


def _document_access_clause(role: WorkspaceRole, user_id: uuid.UUID):
    return or_(
        Document.allowed_roles_json.contains([role.value]),
        Document.allowed_users_json.contains([str(user_id)]),
    )


def _try_enqueue_processing(document_id: uuid.UUID) -> None:
    try:
        from app.workers.tasks import process_document_task

        process_document_task.delay(str(document_id))
    except Exception:
        # Upload remains valid; users can trigger /process if the worker/broker is unavailable.
        return
