from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.services.auth_service import login, refresh_token
from app.schemas.user import TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login_route(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    db = request.app.state.mongodb
    return await login(db, form_data.username, form_data.password)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_route(payload: RefreshRequest, request: Request = None):
    db = request.app.state.mongodb
    return await refresh_token(db, payload.refresh_token)
