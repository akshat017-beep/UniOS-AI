import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    university: str | None = None
    department: str | None = None
    degree: str | None = None
    branch: str | None = None
    semester: int | None = None
    enrollment_number: str | None = None
    interests: str | None = None


class ProfileUpdate(BaseModel):
    university: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    degree: str | None = Field(default=None, max_length=255)
    branch: str | None = Field(default=None, max_length=255)
    semester: int | None = Field(default=None, ge=1, le=16)
    enrollment_number: str | None = Field(default=None, max_length=64)
    interests: str | None = Field(default=None, max_length=2000)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: ProfileOut | None = None
