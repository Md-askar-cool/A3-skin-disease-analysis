"""
SafeSkin AI – Progress Tracker Routes
GET    /progress            – list user's progress images
POST   /progress            – add image to progress tracker
POST   /compare-images      – compare two screenings
DELETE /progress/{id}       – remove progress entry
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.auth.middleware import get_current_user
from app.config import get_settings
from app.schemas.screening import (
    AddProgressImageRequest,
    CompareImagesRequest,
    CompareImagesResponse,
    ProgressImage,
)
from app.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Progress"])
settings = get_settings()


# ======================================================================
# GET /progress
# ======================================================================

@router.get(
    "/progress",
    response_model=List[ProgressImage],
    summary="Get user's progress images, oldest first",
)
async def get_progress(
    user: dict = Depends(get_current_user),
) -> List[ProgressImage]:
    """Return all progress-tracking images for the authenticated user."""
    service = get_supabase_service()
    rows = service.select(
        table="progress_images",
        filters={"user_id": user["id"]},
        order_by="upload_date",
        ascending=True,
    )

    images = []
    for row in rows:
        signed_url = service.get_signed_url(
            bucket=settings.skin_images_bucket,
            storage_path=row.get("image_path", ""),
        )
        images.append(
            ProgressImage(
                id=row["id"],
                user_id=row["user_id"],
                image_path=row.get("image_path", ""),
                image_url=signed_url,
                screening_id=row.get("screening_id"),
                notes=row.get("notes"),
                upload_date=row.get("upload_date", datetime.now(timezone.utc)),
                condition_at_time=row.get("condition_at_time"),
                severity_at_time=row.get("severity_at_time"),
            )
        )
    return images


# ======================================================================
# POST /progress
# ======================================================================

@router.post(
    "/progress",
    response_model=ProgressImage,
    status_code=status.HTTP_201_CREATED,
    summary="Add an image to the progress tracker",
)
async def add_progress_image(
    body: AddProgressImageRequest,
    user: dict = Depends(get_current_user),
) -> ProgressImage:
    """
    Add a previously-uploaded image to the progress timeline.
    Optionally links to an existing screening record.
    """
    service = get_supabase_service()
    user_id = user["id"]

    record = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "image_path": body.image_path,
        "screening_id": body.screening_id,
        "notes": body.notes,
        "condition_at_time": body.condition_at_time,
        "severity_at_time": body.severity_at_time,
        "upload_date": datetime.now(timezone.utc).isoformat(),
    }

    saved = service.insert("progress_images", record)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to save progress image. Please try again.",
        )

    signed_url = service.get_signed_url(
        bucket=settings.skin_images_bucket,
        storage_path=body.image_path,
    )

    return ProgressImage(
        id=saved["id"],
        user_id=saved["user_id"],
        image_path=saved["image_path"],
        image_url=signed_url,
        screening_id=saved.get("screening_id"),
        notes=saved.get("notes"),
        upload_date=saved.get("upload_date", datetime.now(timezone.utc)),
        condition_at_time=saved.get("condition_at_time"),
        severity_at_time=saved.get("severity_at_time"),
    )


# ======================================================================
# POST /compare-images
# ======================================================================

@router.post(
    "/compare-images",
    response_model=CompareImagesResponse,
    summary="Compare two screening records and describe changes",
)
async def compare_images(
    body: CompareImagesRequest,
    user: dict = Depends(get_current_user),
) -> CompareImagesResponse:
    """
    Compare two screening records owned by the current user.
    Returns qualitative observations about condition change over time.
    """
    service = get_supabase_service()
    user_id = user["id"]

    # ── Fetch both records ────────────────────────────────────────────
    s1 = service.select_one(
        "screening_history",
        filters={"id": body.screening_id_1, "user_id": user_id},
    )
    s2 = service.select_one(
        "screening_history",
        filters={"id": body.screening_id_2, "user_id": user_id},
    )

    if not s1:
        raise HTTPException(status_code=404, detail=f"Screening {body.screening_id_1} not found.")
    if not s2:
        raise HTTPException(status_code=404, detail=f"Screening {body.screening_id_2} not found.")

    # ── Comparison logic ──────────────────────────────────────────────
    notes: list = []
    confidence_delta = None

    c1 = s1.get("confidence") or 0.0
    c2 = s2.get("confidence") or 0.0
    cond1 = s1.get("possible_condition")
    cond2 = s2.get("possible_condition")
    sev1 = s1.get("severity_estimate", "N/A")
    sev2 = s2.get("severity_estimate", "N/A")
    res1 = s1.get("screening_result", "")
    res2 = s2.get("screening_result", "")

    # Condition comparison
    if cond1 and cond2:
        if cond1 == cond2:
            notes.append(f"Condition remains: {cond2}.")
        else:
            notes.append(f"Condition changed from '{cond1}' → '{cond2}'.")

    # Confidence delta
    if c1 and c2:
        confidence_delta = round(c2 - c1, 4)
        direction = "increased" if confidence_delta > 0 else "decreased"
        notes.append(
            f"Model confidence {direction} by {abs(confidence_delta):.1%} "
            f"({c1:.1%} → {c2:.1%})."
        )

    # Severity change
    severity_order = {"mild": 0, "moderate": 1, "severe": 2, "N/A": -1}
    sev1_idx = severity_order.get(str(sev1).lower(), -1)
    sev2_idx = severity_order.get(str(sev2).lower(), -1)
    severity_change = None

    if sev1_idx != -1 and sev2_idx != -1:
        if sev2_idx < sev1_idx:
            severity_change = "decreased"
            notes.append(f"Severity improved: {sev1} → {sev2}.")
        elif sev2_idx > sev1_idx:
            severity_change = "increased"
            notes.append(f"Severity worsened: {sev1} → {sev2}.")
        else:
            severity_change = "stable"
            notes.append(f"Severity unchanged: {sev2}.")

    # Overall change
    if res2 == "healthy" and res1 != "healthy":
        condition_change = "improved"
        recommendation = (
            "Great news – your skin appears to have cleared up! "
            "Continue your current skin care routine and consult a dermatologist for confirmation."
        )
    elif res1 == "healthy" and res2 != "healthy":
        condition_change = "worsened"
        recommendation = (
            "A new concern has appeared. Please consult a dermatologist promptly."
        )
    elif confidence_delta is not None and confidence_delta < -0.10:
        condition_change = "improved"
        recommendation = (
            "Model confidence in a skin condition has decreased, "
            "which may indicate improvement. Keep monitoring."
        )
    elif confidence_delta is not None and confidence_delta > 0.10:
        condition_change = "worsened"
        recommendation = (
            "Model confidence in a skin condition has increased. "
            "Consider scheduling an appointment with a dermatologist."
        )
    else:
        condition_change = "stable"
        recommendation = (
            "No significant change detected. Continue monitoring weekly."
        )

    if not notes:
        notes.append("Insufficient data for a detailed comparison.")

    return CompareImagesResponse(
        screening_id_1=body.screening_id_1,
        screening_id_2=body.screening_id_2,
        condition_change=condition_change,
        confidence_delta=confidence_delta,
        severity_change=severity_change,
        notes=notes,
        recommendation=recommendation,
        disclaimer=settings.disclaimer,
    )


# ======================================================================
# DELETE /progress/{id}
# ======================================================================

@router.delete(
    "/progress/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT, response_class=Response,
    summary="Delete a progress tracker entry",
)
async def delete_progress_entry(
    entry_id: str,
    user: dict = Depends(get_current_user),
):
    """Remove a progress entry. Does NOT delete the underlying image from storage."""
    service = get_supabase_service()

    row = service.select_one(
        "progress_images",
        filters={"id": entry_id, "user_id": user["id"]},
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress entry not found.",
        )

    service.delete("progress_images", filters={"id": entry_id})
    logger.info("Deleted progress entry %s for user %s", entry_id, user["id"])
