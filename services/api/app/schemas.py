from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole
    invite_code: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    display_name: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class MeResponse(UserResponse):
    safety_label: Literal[
        "Synthetic demonstration data only. Do not enter real patient data."
    ] = "Synthetic demonstration data only. Do not enter real patient data."


class DashboardResponse(BaseModel):
    role: UserRole
    data: dict[str, object]


class PatientSummaryResponse(BaseModel):
    patient_id: UUID
    display_name: str
    synthetic_identifier: str
    safety_label: Literal[
        "Synthetic demonstration data only. Do not enter real patient data."
    ] = "Synthetic demonstration data only. Do not enter real patient data."


class PatientListResponse(BaseModel):
    items: list[PatientSummaryResponse]
    next_cursor: None = None
