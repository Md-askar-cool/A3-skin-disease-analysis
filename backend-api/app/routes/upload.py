"""
SafeSkin AI – Upload Route
POST /upload  – authenticated multipart file upload to Supabase Storage.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.middleware import get_current_user
from app.config import get_settings
from app.schemas.screening import UploadResponse
from app.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Upload"])
settings = get_settings()


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a skin image to Supabase Storage",
)
async def upload_image(
    file: UploadFile = File(..., description="JPG or PNG image of the affected skin area"),
    user: dict = Depends(get_current_user),
) -> UploadResponse:
    """
    Upload a skin image to Supabase Storage.

    - Validates content-type and file extension.
    - Enforces maximum upload size.
    - Stores file at `skin-images/{user_id}/{uuid}.jpg`.
    - Returns a signed URL valid for 1 hour.
    """
    # ── Validate content type ─────────────────────────────────────────
    content_type = (file.content_type or "").lower()
    if content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{content_type}'. Allowed: {settings.allowed_image_types}",
        )

    # ── Validate extension ────────────────────────────────────────────
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_image_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension '{ext}'. Allowed: {settings.allowed_image_extensions}",
        )

    # ── Read file bytes ───────────────────────────────────────────────
    file_bytes = await file.read()
    size_bytes = len(file_bytes)

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if size_bytes > settings.max_image_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size ({size_bytes / 1_048_576:.1f} MB) exceeds "
                f"maximum allowed size ({settings.max_image_size_mb} MB)."
            ),
        )

    # ── Build storage path ────────────────────────────────────────────
    user_id = user["id"]
    file_uuid = uuid.uuid4().hex
    storage_path = f"{user_id}/{file_uuid}.jpg"

    # ── Upload to Supabase Storage ────────────────────────────────────
    service = get_supabase_service()
    uploaded = service.upload_file(
        bucket=settings.skin_images_bucket,
        storage_path=storage_path,
        file_bytes=file_bytes,
        content_type="image/jpeg",
    )

    if not uploaded:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload image to storage. Please try again.",
        )

    # ── Generate signed URL ───────────────────────────────────────────
    signed_url = service.get_signed_url(
        bucket=settings.skin_images_bucket,
        storage_path=storage_path,
        expires_in=settings.signed_url_expiry,
    )

    if not signed_url:
        # Upload succeeded but URL generation failed – not fatal
        logger.warning("Signed URL generation failed for %s", storage_path)
        signed_url = ""

    logger.info(
        "User %s uploaded image: %s (%d bytes)", user_id, storage_path, size_bytes
    )

    return UploadResponse(
        storage_path=storage_path,
        signed_url=signed_url,
        expires_in=settings.signed_url_expiry,
        file_name=filename,
        content_type=content_type,
        size_bytes=size_bytes,
    )
