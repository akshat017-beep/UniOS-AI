from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.tools import CodingStatus, LanguageInfo, RunCodeRequest, RunCodeResponse
from app.services.sandbox import (
    LANGUAGES,
    ExecutionUnavailableError,
    run_code,
    runtime_available,
)

router = APIRouter()

ISOLATION_NOTE = (
    "Code runs in a temporary directory with a stripped environment, CPU, memory, "
    "file-size and wall-clock limits. Network isolation and syscall filtering come "
    "from the container runtime — run the API with `--network none` and a read-only "
    "root filesystem before accepting untrusted code."
)


@router.get("/status", response_model=CodingStatus)
def coding_status(user: User = Depends(get_current_user)) -> CodingStatus:
    return CodingStatus(
        execution_enabled=settings.code_execution_enabled,
        languages=[
            LanguageInfo(
                id=key, label=str(spec["label"]), available=runtime_available(key)
            )
            for key, spec in LANGUAGES.items()
        ],
        timeout_seconds=settings.code_execution_timeout_seconds,
        isolation_note=ISOLATION_NOTE,
    )


@router.post("/run", response_model=RunCodeResponse)
def run(payload: RunCodeRequest, user: User = Depends(get_current_user)) -> RunCodeResponse:
    try:
        result = run_code(payload.language, payload.source, payload.stdin)
    except ExecutionUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return RunCodeResponse(**asdict(result))
