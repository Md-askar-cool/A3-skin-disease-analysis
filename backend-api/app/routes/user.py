"""
SafeSkin AI – User Profile Routes
GET    /user/profile         – fetch profile
PUT    /user/profile         – update profile fields
DELETE /user                 – delete account + all data
DELETE /user/image/{path}    – delete a specific image from storage
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Path, status, Response

from app.auth.middleware import get_current_user
from app.config import get_settings
from app.schemas.screening import UpdateProfileRequest, UserProfile
from app.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User"])
settings = get_settings()


# ======================================================================
# GET /user/profile
# ======================================================================

@router.get(
    "/user/profile",
    response_model=UserProfile,
    summary="Get the authenticated user's profile",
)
async def get_profile(
    user: dict = Depends(get_current_user),
) -> UserProfile:
    """Return profile data merged from Supabase auth metadata and user_profiles table."""
    service = get_supabase_service()
    user_id = user["id"]

    # Fetch extended profile from user_profiles table
    profile_row = service.select_one("user_profiles", filters={"id": user_id})

    # Count total screenings
    total_screenings = service.count("screening_history", filters={"user_id": user_id})

    # Get last screening date
    last_screenings = service.select(
        "screening_history",
        filters={"user_id": user_id},
        columns="created_at",
        order_by="created_at",
        ascending=False,
        limit=1,
    )
    last_date = last_screenings[0]["created_at"] if last_screenings else None

    # Merge auth metadata + DB profile
    user_meta = user.get("user_metadata", {})
    return UserProfile(
        id=user_id,
        email=user.get("email"),
        full_name=(profile_row or {}).get("full_name") or user_meta.get("full_name"),
        avatar_url=(profile_row or {}).get("avatar_url") or user_meta.get("avatar_url"),
        skin_type=(profile_row or {}).get("skin_type"),
        date_of_birth=(profile_row or {}).get("date_of_birth"),
        created_at=(profile_row or {}).get("created_at"),
        total_screenings=total_screenings,
        last_screening_date=last_date,
    )


# ======================================================================
# PUT /user/profile
# ======================================================================

@router.put(
    "/user/profile",
    response_model=UserProfile,
    summary="Update the authenticated user's profile",
)
async def update_profile(
    body: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
) -> UserProfile:
    """
    Upsert the user_profiles row with the provided fields.
    Only non-None fields in the request body are updated.
    """
    service = get_supabase_service()
    user_id = user["id"]

    update_data: Dict[str, Any] = {"id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.full_name is not None:
        update_data["full_name"] = body.full_name
    if body.avatar_url is not None:
        update_data["avatar_url"] = body.avatar_url
    if body.skin_type is not None:
        update_data["skin_type"] = body.skin_type
    if body.date_of_birth is not None:
        update_data["date_of_birth"] = body.date_of_birth

    # Check if profile exists
    existing = service.select_one("user_profiles", filters={"id": user_id})
    if existing:
        service.update("user_profiles", filters={"id": user_id}, data=update_data)
    else:
        service.insert("user_profiles", update_data)

    # Return fresh profile
    return await get_profile(user=user)


# ======================================================================
# DELETE /user
# ======================================================================

@router.delete(
    "/user",
    status_code=status.HTTP_204_NO_CONTENT, response_class=Response,
    summary="Delete the user's account and all associated data",
)
async def delete_account(
    user: dict = Depends(get_current_user),
):
    """
    Permanently delete all user data:
    - All screening_history rows
    - All progress_images rows
    - All images from Supabase Storage
    - user_profiles row

    Note: The Supabase auth user record deletion requires admin privileges
    and is handled server-side via Supabase's admin API (or RPC).
    """
    service = get_supabase_service()
    user_id = user["id"]

    # ── Collect all storage paths ──────────────────────────────────────
    screenings = service.select(
        "screening_history",
        filters={"user_id": user_id},
        columns="image_path",
    )
    progress = service.select(
        "progress_images",
        filters={"user_id": user_id},
        columns="image_path",
    )

    storage_paths = list(
        {row["image_path"] for row in screenings + progress if row.get("image_path")}
    )

    # ── Delete images from storage ─────────────────────────────────────
    if storage_paths:
        service.delete_files(bucket=settings.skin_images_bucket, paths=storage_paths)

    # ── Delete DB records ──────────────────────────────────────────────
    service.delete("screening_history", filters={"user_id": user_id})
    service.delete("progress_images", filters={"user_id": user_id})
    service.delete("user_profiles", filters={"id": user_id})

    logger.warning("Account deleted for user %s – all data wiped.", user_id)


# ======================================================================
# DELETE /user/image/{path}
# ======================================================================

@router.delete(
    "/user/image/{image_path:path}",
    status_code=status.HTTP_204_NO_CONTENT, response_class=Response,
    summary="Delete a specific image from Supabase Storage",
)
async def delete_user_image(
    image_path: str = Path(..., description="URL-encoded storage path"),
    user: dict = Depends(get_current_user),
):
    """
    Delete a single image from Supabase Storage.
    The path must start with the authenticated user's ID to prevent
    unauthorised deletion of other users' images.
    """
    decoded_path = unquote(image_path)
    user_id = user["id"]

    # Security: ensure the path belongs to this user
    if not decoded_path.startswith(f"{user_id}/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to delete this image.",
        )

    service = get_supabase_service()
    deleted = service.delete_file(
        bucket=settings.skin_images_bucket,
        storage_path=decoded_path,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete image from storage.",
        )

    logger.info("User %s deleted image: %s", user_id, decoded_path)
