from fastapi import APIRouter

from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(_: RegisterRequest) -> AuthResponse:
    return AuthResponse(access_token="scaffold-token")


@router.post("/login", response_model=AuthResponse)
async def login(_: LoginRequest) -> AuthResponse:
    return AuthResponse(access_token="scaffold-token")
