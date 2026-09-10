"""
SafeSkin AI – Auth Middleware
Provides a FastAPI dependency that verifies Supabase JWTs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)

# HTTPBearer extracts the token from the Authorization: Bearer <token> header.
_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """
    FastAPI dependency – verifies the Bearer JWT against Supabase.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            ...

    Returns:
        dict with keys: id, email, role, app_metadata, user_metadata
    Raises:
        HTTPException 401 if token is missing, expired, or invalid.
    """
    token = credentials.credentials

    service = get_supabase_service()
    user = service.verify_token(token)

    if user is None:
        logger.warning("JWT verification failed – invalid or expired token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("Authenticated user: %s", user.get("id"))
    return user


async def get_current_admin(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    FastAPI dependency – requires the user to have admin role.
    Extends get_current_user; raises 403 if the user is not an admin.

    Admin status is stored in Supabase app_metadata.role = 'admin'.
    """
    app_metadata = user.get("app_metadata", {})
    role = app_metadata.get("role", "")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )

    return user
