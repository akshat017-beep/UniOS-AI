"""Multimodal input: images (vision) and voice (speech-to-text)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.ai.multimodal import (
    describe_image,
    transcribe_audio,
    transcription_is_configured,
    vision_is_configured,
)
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.tools import TranscriptionResponse
from app.security.uploads import UnsafeUploadError, screen_upload

router = APIRouter()

_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
_AUDIO_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/x-wav",
    "audio/mp3",
    "video/webm",
}


class MultimodalStatus(BaseModel):
    vision_configured: bool
    vision_model: str | None
    transcription_configured: bool
    transcription_model: str | None
    detail: str


class ImageAnswer(BaseModel):
    answer: str
    model: str


@router.get("/status", response_model=MultimodalStatus)
def multimodal_status(user: User = Depends(get_current_user)) -> MultimodalStatus:
    vision = vision_is_configured()
    speech = transcription_is_configured()
    parts = []
    if not vision:
        parts.append("Set AI_VISION_MODEL for image questions.")
    if not speech:
        parts.append("Set AI_TRANSCRIPTION_MODEL for voice input.")
    return MultimodalStatus(
        vision_configured=vision,
        vision_model=settings.ai_vision_model or None,
        transcription_configured=speech,
        transcription_model=settings.ai_transcription_model or None,
        detail=" ".join(parts) or "Image and voice input are ready.",
    )


def _screen(file_bytes: bytes, upload: UploadFile, allowed: set[str]) -> str:
    try:
        return screen_upload(
            file_bytes,
            filename=upload.filename or "upload",
            content_type=upload.content_type or "",
            allowed_types=allowed,
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        )
    except UnsafeUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _provider_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProviderNotConfiguredError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/image", response_model=ImageAnswer)
async def ask_about_image(
    question: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> ImageAnswer:
    data = await file.read()
    content_type = _screen(data, file, _IMAGE_TYPES)
    try:
        answer, model = await describe_image(
            data=data, content_type=content_type, question=question
        )
    except (ProviderNotConfiguredError, ProviderRequestError) as exc:
        raise _provider_error(exc) from exc
    return ImageAnswer(answer=answer, model=model)


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> TranscriptionResponse:
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is too large."
        )
    declared = (file.content_type or "").split(";")[0].strip().lower()
    if declared and declared not in _AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio type '{declared}'.",
        )
    try:
        text, model = await transcribe_audio(
            data=data, filename=file.filename or "audio.webm", content_type=declared
        )
    except (ProviderNotConfiguredError, ProviderRequestError) as exc:
        raise _provider_error(exc) from exc
    return TranscriptionResponse(text=text, model=model)
