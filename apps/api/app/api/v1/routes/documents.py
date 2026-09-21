from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.ai.embeddings import embeddings_are_configured, get_embedding_model
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.rag.extract import SUPPORTED_TYPES, UnsupportedDocumentError
from app.rag.pipeline import ingest_document, retrieve
from app.schemas.document import (
    CitationOut,
    DocumentOut,
    DocumentSearchRequest,
    DocumentSearchResponse,
    RagStatus,
)
from app.security.uploads import UnsafeUploadError, screen_upload

router = APIRouter()

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/status", response_model=RagStatus)
def rag_status() -> RagStatus:
    configured = embeddings_are_configured()
    model = get_embedding_model().name if configured else None
    detail = (
        "Retrieval is ready."
        if configured
        else (
            "Embeddings are not configured. Set EMBEDDING_BASE_URL and EMBEDDING_MODEL "
            "(or EMBEDDING_PROVIDER=hashing for offline development)."
        )
    )
    if configured and settings.embedding_provider.strip().lower() == "hashing":
        detail = (
            "Running the offline hashing embedder: retrieval is lexical, not semantic. "
            "Configure a real embedding model for production quality."
        )
    return RagStatus(
        embeddings_configured=configured,
        provider=settings.embedding_provider,
        model=model,
        vector_backend=settings.vector_backend,
        detail=detail,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
            .limit(200)
        )
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    data = await file.read()
    try:
        screen_upload(
            data,
            filename=file.filename or "upload",
            content_type=file.content_type or "",
            allowed_types=SUPPORTED_TYPES,
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        )
    except UnsafeUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    document = Document(
        user_id=user.id,
        title=(file.filename or "Untitled").rsplit("/", 1)[-1][:255],
        filename=(file.filename or "upload")[:255],
        content_type=(file.content_type or "application/octet-stream")[:128],
        size_bytes=len(data),
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        return await ingest_document(db, document, data)
    except (UnsupportedDocumentError, ValueError) as exc:
        document.status = "failed"
        document.error = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProviderNotConfiguredError as exc:
        document.status = "failed"
        document.error = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ProviderRequestError as exc:
        document.status = "failed"
        document.error = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    document = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    if document is None:
        raise _NOT_FOUND
    db.delete(document)
    db.commit()


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    payload: DocumentSearchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentSearchResponse:
    try:
        result = await retrieve(
            db,
            user_id=user.id,
            query=payload.query,
            document_ids=payload.document_ids,
            limit=payload.limit,
        )
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return DocumentSearchResponse(
        citations=[CitationOut(**asdict(citation)) for citation in result.citations],
        injection_warnings=result.injection_warnings,
    )
