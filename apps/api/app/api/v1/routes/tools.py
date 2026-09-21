"""Workspace generation endpoints: study material, research help, resume drafting."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.rag.pipeline import Retrieval, retrieve
from app.schemas.document import CitationOut
from app.schemas.tools import (
    GenerationResponse,
    ResearchRequest,
    ResumeRequest,
    StudyMaterialRequest,
)
from app.services.generation import RESEARCH_FORMATS, STUDY_FORMATS, generate

router = APIRouter()


def _unavailable(exc: Exception) -> HTTPException:
    if isinstance(exc, ProviderNotConfiguredError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


async def _context(db: Session, user: User, query: str, document_ids) -> Retrieval | None:
    if not document_ids:
        return None
    try:
        return await retrieve(db, user_id=user.id, query=query, document_ids=document_ids)
    except ProviderNotConfiguredError as exc:
        raise _unavailable(exc) from exc


def _respond(text: str, model: str, agent: str, retrieval: Retrieval | None) -> GenerationResponse:
    return GenerationResponse(
        content=text,
        model=model,
        agent=agent,
        citations=[
            CitationOut(**asdict(citation))
            for citation in (retrieval.citations if retrieval else [])
        ],
        injection_warnings=retrieval.injection_warnings if retrieval else [],
    )


@router.post("/study-material", response_model=GenerationResponse)
async def study_material(
    payload: StudyMaterialRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationResponse:
    instruction = STUDY_FORMATS.get(payload.format)
    if instruction is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown format. Choose one of: {', '.join(STUDY_FORMATS)}.",
        )
    retrieval = await _context(db, user, payload.topic, payload.document_ids)
    try:
        text, model = await generate(
            agent_name="study",
            instruction=f"{instruction} Target level: {payload.level}.",
            content=payload.topic,
            context=retrieval.context if retrieval else "",
        )
    except (ProviderNotConfiguredError, ProviderRequestError) as exc:
        raise _unavailable(exc) from exc
    return _respond(text, model, "study", retrieval)


@router.post("/research", response_model=GenerationResponse)
async def research(
    payload: ResearchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationResponse:
    instruction = RESEARCH_FORMATS.get(payload.format)
    if instruction is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown format. Choose one of: {', '.join(RESEARCH_FORMATS)}.",
        )
    retrieval = await _context(db, user, payload.topic, payload.document_ids)
    try:
        text, model = await generate(
            agent_name="research",
            instruction=instruction,
            content=payload.topic,
            context=retrieval.context if retrieval else "",
        )
    except (ProviderNotConfiguredError, ProviderRequestError) as exc:
        raise _unavailable(exc) from exc
    return _respond(text, model, "research", retrieval)


@router.post("/resume", response_model=GenerationResponse)
async def resume(
    payload: ResumeRequest,
    user: User = Depends(get_current_user),
) -> GenerationResponse:
    sections = "\n\n".join(
        f"## {label}\n{value}"
        for label, value in (
            ("Target role", payload.target_role),
            ("Summary", payload.summary),
            ("Education", payload.education),
            ("Experience", payload.experience),
            ("Projects", payload.projects),
            ("Skills", payload.skills),
            ("Achievements", payload.achievements),
        )
        if value.strip()
    )
    instruction = (
        "Rewrite the supplied material into a one-page ATS-friendly resume in markdown. "
        "Use action + tool + measurable result bullets. Never invent experience, employers, "
        "dates or numbers that are not present — instead leave a clearly marked "
        "[ADD: …] placeholder. End with a short 'What to improve' list."
    )
    try:
        text, model = await generate(
            agent_name="career", instruction=instruction, content=sections or payload.target_role
        )
    except (ProviderNotConfiguredError, ProviderRequestError) as exc:
        raise _unavailable(exc) from exc
    return _respond(text, model, "career", None)
