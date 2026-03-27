"""Auth routes — Supabase Auth integration."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _get_anon_client():
    from app.services.supabase_service import get_supabase_anon_client
    client = get_supabase_anon_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return client


@router.post("/register")
async def register(body: AuthRequest):
    """Register a new user via Supabase Auth."""
    client = _get_anon_client()
    try:
        result = client.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        user = result.user
        session = result.session

        if not user:
            raise HTTPException(status_code=400, detail="Registration failed")

        return {
            "user": {"id": str(user.id), "email": user.email},
            "session": {
                "access_token": session.access_token if session else None,
                "refresh_token": session.refresh_token if session else None,
            } if session else None,
            "message": "Registration successful" + (
                ". Check your email for confirmation." if not session else ""
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(body: AuthRequest):
    """Authenticate user and return JWT tokens."""
    client = _get_anon_client()
    try:
        result = client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        user = result.user
        session = result.session

        if not session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "user": {"id": str(user.id), "email": user.email},
            "session": {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.get("/me")
async def me(user: Optional[dict] = Depends(get_current_user)):
    """Get current authenticated user."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    """Refresh access token using a refresh token."""
    client = _get_anon_client()
    try:
        result = client.auth.refresh_session(body.refresh_token)
        session = result.session
        if not session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        raise HTTPException(status_code=401, detail="Failed to refresh token")


@router.get("/google/url")
async def google_oauth_url():
    """Get Google OAuth redirect URL from Supabase."""
    client = _get_anon_client()
    from app.core.config import settings
    try:
        # Redirect back to frontend callback page
        redirect_to = "http://localhost:8501/auth/callback"
        result = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_to},
        })
        return {"url": result.url}
    except Exception as e:
        logger.error("Google OAuth URL generation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate Google sign-in URL")


class CodeExchangeRequest(BaseModel):
    code: str


@router.post("/google/callback")
async def google_oauth_callback(body: CodeExchangeRequest):
    """Exchange an OAuth authorization code for a session (PKCE flow)."""
    client = _get_anon_client()
    try:
        result = client.auth.exchange_code_for_session({"auth_code": body.code})
        session = result.session
        user = result.user
        if not session or not user:
            raise HTTPException(status_code=401, detail="Code exchange failed")
        return {
            "user": {"id": str(user.id), "email": user.email},
            "session": {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google OAuth code exchange failed: %s", e)
        raise HTTPException(status_code=401, detail="Failed to complete Google sign-in")


@router.post("/logout")
async def logout():
    """Logout — client should discard stored tokens."""
    return {"message": "Logged out"}
