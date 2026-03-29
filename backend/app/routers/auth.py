"""
Authentication and session management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    AuthSessionResponse,
    AuthStatusResponse,
    CsrfTokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
)
from app.services.auth import (
    authenticate_user,
    clear_auth_cookies,
    decode_token,
    get_current_active_user,
    get_token_from_request,
    hash_password,
    set_csrf_cookie,
    set_auth_cookies,
)
from app.config import settings
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _session_response(response: Response, user: User, message: str) -> AuthSessionResponse:
    set_auth_cookies(response, user)
    set_csrf_cookie(response)
    return AuthSessionResponse(user=UserResponse.model_validate(user), message=message)


def _client_identifier(request: Request, email: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    return f"{client_ip}:{email.strip().lower()}"


@router.get("/csrf", response_model=CsrfTokenResponse)
def issue_csrf_token(response: Response):
    """Issue a CSRF token for the SPA before unsafe requests."""
    token = set_csrf_cookie(response)
    return CsrfTokenResponse(csrf_token=token)


@router.post("/signup", response_model=AuthSessionResponse, status_code=201)
def signup(
    data: UserSignup,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Create a new user account and start an authenticated session."""
    check_rate_limit(
        db,
        bucket="signup",
        key=_client_identifier(request, data.email),
        limit=settings.SIGNUP_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )

    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole.ENGINEER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _session_response(response, user, "Account created")


@router.post("/login", response_model=AuthSessionResponse)
def login(
    data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate an existing user and issue a fresh session."""
    check_rate_limit(
        db,
        bucket="login",
        key=_client_identifier(request, data.email),
        limit=settings.LOGIN_RATE_LIMIT_ATTEMPTS,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )

    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")

    return _session_response(response, user, "Login successful")


@router.post("/refresh", response_model=AuthSessionResponse)
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    """Renew the current session using a valid refresh token."""
    refresh_token = get_token_from_request(request, settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_token(refresh_token, expected_type="refresh")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Session refresh failed")

    return _session_response(response, user, "Session refreshed")


@router.post("/logout", response_model=AuthStatusResponse)
def logout(response: Response):
    """Clear the current browser session cookies."""
    clear_auth_cookies(response)
    return AuthStatusResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def current_user(current_user: User = Depends(get_current_active_user)):
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)