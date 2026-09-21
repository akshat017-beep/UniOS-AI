from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.document import CitationOut


class StudyMaterialRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=4000)
    format: str = Field(default="summary", max_length=32)
    level: str = Field(default="undergraduate", max_length=64)
    document_ids: list[UUID] | None = None


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=8000)
    format: str = Field(default="outline", max_length=32)
    document_ids: list[UUID] | None = None


class ResumeRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=200)
    summary: str = Field(default="", max_length=2000)
    education: str = Field(default="", max_length=4000)
    experience: str = Field(default="", max_length=6000)
    projects: str = Field(default="", max_length=6000)
    skills: str = Field(default="", max_length=2000)
    achievements: str = Field(default="", max_length=2000)


class GenerationResponse(BaseModel):
    content: str
    model: str
    agent: str
    citations: list[CitationOut] = []
    injection_warnings: list[str] = []


class RunCodeRequest(BaseModel):
    language: str = Field(default="python", max_length=32)
    source: str = Field(min_length=1, max_length=100_000)
    stdin: str = Field(default="", max_length=20_000)


class RunCodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    language: str


class LanguageInfo(BaseModel):
    id: str
    label: str
    available: bool


class CodingStatus(BaseModel):
    execution_enabled: bool
    languages: list[LanguageInfo]
    timeout_seconds: int
    isolation_note: str


class TranscriptionResponse(BaseModel):
    text: str
    model: str


class VisionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
