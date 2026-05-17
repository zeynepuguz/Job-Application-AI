import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth import create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    expected = os.getenv("APP_PASSWORD", "")
    if not expected:
        raise HTTPException(status_code=500, detail="APP_PASSWORD tanımlı değil.")
    if request.password != expected:
        raise HTTPException(status_code=401, detail="Hatalı şifre.")
    return {"token": create_token()}
