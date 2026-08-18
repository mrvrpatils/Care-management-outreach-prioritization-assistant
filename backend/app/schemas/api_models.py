
from typing import Any, Optional
from pydantic import BaseModel, Field

class OutreachStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending, In Progress, Contacted, Follow-up, or Completed")

class CallGuideRequest(BaseModel):
    include_questions: bool = True
    force_fallback: bool = False

class HealthResponse(BaseModel):
    status: str


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=4, max_length=100, description="Password")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name of the user")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    role: Optional[str] = Field("Care Manager", max_length=50, description="Role e.g. Care Manager, Administrator, Clinician")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "Care Manager"
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

