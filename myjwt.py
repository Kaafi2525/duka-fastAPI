from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import User


ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
security = HTTPBearer(auto_error=False)
password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def get_user(db: Session, email: str):
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.password):
        return False
    return user


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    if "sub" not in data:
        raise ValueError("Token data must include 'sub'")

    to_encode = data.copy()
    to_encode.update(
        {
            "scope": "user",
            "type": token_type,
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=settings.access_token_minutes),
        "access",
    )


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(days=settings.refresh_token_days),
        "refresh",
    )


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    email = payload.get("sub")
    token_type = payload.get("type")
    if not email or token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")


def _resolve_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    cookie_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
):
    token = _resolve_bearer_token(request, credentials)
    payload = decode_token(token, "access")
    user = get_user(db, payload["sub"])

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if getattr(current_user, "disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return current_user
