from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from db import get_db
from jsonmap import Token, UserPostLogin, UserPostRegister
from models import User
from myjwt import (
    REFRESH_COOKIE_NAME,
    authenticate_user,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    get_user,
    set_auth_cookies,

)


router = APIRouter(tags=["auth"])


def _issue_tokens(response: Response, email: str) -> Token:
    access_token = create_access_token(data={"sub": email})
    refresh_token = create_refresh_token(data={"sub": email})
    set_auth_cookies(response, access_token, refresh_token)
    return Token(access_token=access_token, token_type="bearer")




@router.post("/token", response_model=Token)
def login_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return _issue_tokens(response, user.email)


@router.post("/login", response_model=Token)
def login_user(
    user: UserPostLogin,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return _issue_tokens(response, db_user.email)


@router.post("/register", response_model=Token)
def register_user(
    user: UserPostRegister,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    existing_user = db.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        fullname=user.fullname,
        email=user.email,
        password=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _issue_tokens(response, new_user.email)


@router.post("/refresh_access_token", response_model=Token)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_token(refresh_token, "refresh")
    user = get_user(db, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return _issue_tokens(response, user.email)


@router.post("/logout")
def logout_user(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out"}
