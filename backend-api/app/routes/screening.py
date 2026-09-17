"""
SafeSkin AI – Screening Routes
POST /analyze-image       – run full AI pipeline
GET  /screening-history   – paginated history
GET  /screening/{id}      – single screening detail
DELETE /screening/{id}    – delete screening + storage
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response

from app.auth.middleware import get_current_user
from app.config import get_settings
from app.schemas.screening import (
    ScreeningHistoryItem,
    ScreeningHistoryResponse,
    ScreeningResponse,
)
from app.services.ai_pipeline import run_full_pipeline
from app.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Screening"])
settings = get_settings()


# ======================================================================
# Helper – fetch image bytes from Supabase Storage
# ======================================================================

def _download_image(service, storage_path: str) -> bytes:
    """Download image from Supabase Storage; raise 404 if not found."""
    img_bytes = service.download_file(
        bucket=settings.skin_images_bucket,
        storage_path=storage_path,
    )
    if img_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found in storage: {storage_path}",
        )
    return img_bytes


# ======================================================================
# Helper – upload Grad-CAM to storage and return signed URL
# ======================================================================

def _make_gradcam_uploader(service, user_id: str):
    """Return a callback that uploads Grad-CAM bytes and returns a signed URL."""

    def upload_gradcam(gradcam_bytes: bytes, gradcam_id: str, uid: Optional[str] = None) -> str:
        gcam_path = f"{uid or user_id}/gradcam/{gradcam_id}.png"
        service.upload_file(
            bucket=settings.skin_images_bucket,
            storage_path=gcam_path,
            file_bytes=gradcam_bytes,
            content_type="image/png",
        )
        return service.get_signed_url(
            bucket=settings.skin_images_bucket,
            storage_path=gcam_path,
        ) or ""

    return upload_gradcam


# ======================================================================
# POST /analyze-image
# ======================================================================

class AnalyzeRequest:
    """Query/body parameters for analyze-image."""
    pass


from pydantic import BaseModel


class AnalyzeImageRequest(BaseModel):
    image_path: str  # Storage path returned by /upload


@router.post(
    "/analyze-image",
    response_model=ScreeningResponse,
    summary="Analyse a skin image using the full AI pipeline",
)
async def analyze_image(
    body: AnalyzeImageRequest,
    user: dict = Depends(get_current_user),
) -> ScreeningResponse:
    """
    Run the full AI analysis pipeline on an already-uploaded image.

    Steps:
    1. Download image from Supabase Storage.
    2. Quality check → screener → classifier → Grad-CAM → severity.
    3. Persist result to `screening_history` table.
    4. Return ScreeningResponse.
    """
    user_id = user["id"]
    service = get_supabase_service()

    # ── Download image ────────────────────────────────────────────────
    image_bytes = _download_image(service, body.image_path)

    # ── Build Grad-CAM upload callback ────────────────────────────────
    gradcam_callback = _make_gradcam_uploader(service, user_id)

    # ── Run pipeline ──────────────────────────────────────────────────
    result: ScreeningResponse = run_full_pipeline(
        image_bytes=image_bytes,
        user_id=user_id,
        upload_gradcam_callback=gradcam_callback,
    )

    # ── Persist to DB ─────────────────────────────────────────────────
    record = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "image_path": body.image_path,
        "screening_result": result.screening_result,
        "possible_condition": result.possible_condition,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,
        "severity_estimate": result.severity_estimate,
        "quality_score": result.image_quality.overall_score,
        "quality_status": result.image_quality.status,
        "gradcam_path": None,  # Could store path separately
        "model_version": result.model_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    saved = service.insert("screening_history", record)
    screening_id = saved["id"] if saved else record["id"]

    result.image_path = body.image_path
    result.screening_id = screening_id

    logger.info(
        "Screening %s completed for user %s: %s (confidence=%.2f)",
        screening_id,
        user_id,
        result.screening_result,
        result.confidence or 0,
    )

    return result


# ======================================================================
# GET /screening-history
# ======================================================================

@router.get(
    "/screening-history",
    response_model=ScreeningHistoryResponse,
    summary="Get paginated screening history for the current user",
)
async def get_screening_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Items per page"),
    user: dict = Depends(get_current_user),
) -> ScreeningHistoryResponse:
    """Return a paginated list of the user's past screenings, newest first."""
    user_id = user["id"]
    service = get_supabase_service()
    offset = (page - 1) * page_size

    rows = service.select(
        table="screening_history",
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=False,
        limit=page_size,
        offset=offset,
    )
    total = service.count("screening_history", filters={"user_id": user_id})

    # Enrich with signed image URLs
    items = []
    for row in rows:
        signed_url = service.get_signed_url(
            bucket=settings.skin_images_bucket,
            storage_path=row.get("image_path", ""),
        )
        items.append(
            ScreeningHistoryItem(
                id=row["id"],
                user_id=row["user_id"],
                image_path=row.get("image_path", ""),
                image_url=signed_url,
                screening_result=row.get("screening_result", ""),
                possible_condition=row.get("possible_condition"),
                confidence=row.get("confidence"),
                confidence_level=row.get("confidence_level"),
                severity_estimate=row.get("severity_estimate"),
                quality_score=row.get("quality_score"),
                model_version=row.get("model_version"),
                created_at=row.get("created_at", datetime.now(timezone.utc)),
            )
        )

    return ScreeningHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


# ======================================================================
# GET /screening/{id}
# ======================================================================

@router.get(
    "/screening/{screening_id}",
    response_model=Dict[str, Any],
    summary="Get a single screening record by ID",
)
async def get_screening(
    screening_id: str,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return the full detail of one screening record."""
    service = get_supabase_service()
    row = service.select_one(
        "screening_history",
        filters={"id": screening_id, "user_id": user["id"]},
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening record not found.",
        )

    # Add signed URL
    row["image_url"] = service.get_signed_url(
        bucket=settings.skin_images_bucket,
        storage_path=row.get("image_path", ""),
    )

    return row


# ======================================================================
# DELETE /screening/{id}
# ======================================================================

@router.delete(
    "/screening/{screening_id}",
    summary="Delete a screening record and its associated images",
    status_code=status.HTTP_204_NO_CONTENT, response_class=Response,
)
async def delete_screening(
    screening_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a screening record + the image from Supabase Storage."""
    service = get_supabase_service()

    # Verify ownership
    row = service.select_one(
        "screening_history",
        filters={"id": screening_id, "user_id": user["id"]},
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening record not found.",
        )

    # Delete image from storage
    image_path = row.get("image_path", "")
    if image_path:
        service.delete_file(bucket=settings.skin_images_bucket, storage_path=image_path)

    # Delete DB record
    service.delete("screening_history", filters={"id": screening_id})
    logger.info("Deleted screening %s for user %s", screening_id, user["id"])
