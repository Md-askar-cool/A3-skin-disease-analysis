"""
SafeSkin AI – Pydantic Schemas for Screening
All request/response models used across the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ======================================================================
# Image Quality
# ======================================================================

class QualityCheckDetail(BaseModel):
    passed: bool
    score: float
    message: Optional[str] = None

class ImageQualityResult(BaseModel):
    """Result returned by the image quality analysis step."""
    overall_score: int = Field(..., ge=0, le=100, description="Composite quality score 0-100")
    status: str = Field(..., description="ok | too_blurry | too_dark | too_bright | low_resolution | no_skin")
    can_proceed: bool = Field(True, description="Whether the pipeline should continue")
    checks: Dict[str, QualityCheckDetail]
    message: str = Field(..., description="Human-readable quality feedback")


# ======================================================================
# Screening (main analysis response)
# ======================================================================

class ScreeningResponse(BaseModel):
    """
    Full AI pipeline response returned to the client after image analysis.
    """
    # Quality gate
    image_quality: ImageQualityResult

    # Core result
    screening_result: str = Field(
        ...,
        description="healthy | potentially_affected | uncertain | quality_failed"
    )
    possible_condition: Optional[str] = Field(
        None,
        description="Predicted condition label, e.g. 'Acne Vulgaris'"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Classifier confidence (0.0–1.0)"
    )
    confidence_level: Optional[str] = Field(
        None,
        description="high | moderate | low"
    )
    severity_estimate: Optional[str] = Field(
        None,
        description="mild | moderate | severe | N/A"
    )

    # Explainability
    gradcam_url: Optional[str] = Field(
        None,
        description="Signed URL to Grad-CAM heatmap image"
    )

    # Metadata
    model_version: str = Field(..., description="Version tag of the models used")
    recommendation: str = Field(..., description="Actionable advice for the user")
    disclaimer: str = Field(..., description="Medical / legal disclaimer")

    # Storage
    image_path: Optional[str] = Field(None, description="Supabase storage path of the analysed image")
    screening_id: Optional[str] = Field(None, description="Database ID of this screening record")


# ======================================================================
# Screening History
# ======================================================================

class ScreeningHistoryItem(BaseModel):
    """Summary row used in paginated history list."""
    id: str
    user_id: str
    image_path: str
    image_url: Optional[str] = None  # Signed URL
    screening_result: str
    possible_condition: Optional[str] = None
    confidence: Optional[float] = None
    confidence_level: Optional[str] = None
    severity_estimate: Optional[str] = None
    quality_score: Optional[int] = None
    model_version: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScreeningHistoryResponse(BaseModel):
    """Paginated screening history."""
    items: List[ScreeningHistoryItem]
    total: int
    page: int
    page_size: int
    has_more: bool


# ======================================================================
# Progress Tracker
# ======================================================================

class ProgressImage(BaseModel):
    """A single progress-tracking image entry."""
    id: str
    user_id: str
    image_path: str
    image_url: Optional[str] = None
    screening_id: Optional[str] = None
    notes: Optional[str] = None
    upload_date: datetime
    condition_at_time: Optional[str] = None
    severity_at_time: Optional[str] = None

    model_config = {"from_attributes": True}


class AddProgressImageRequest(BaseModel):
    """Body for POST /progress."""
    image_path: str = Field(..., description="Supabase storage path of the image")
    screening_id: Optional[str] = Field(None, description="Link to an existing screening record")
    notes: Optional[str] = Field(None, max_length=1000)
    condition_at_time: Optional[str] = None
    severity_at_time: Optional[str] = None


class CompareImagesRequest(BaseModel):
    """Body for POST /compare-images."""
    screening_id_1: str = Field(..., description="ID of the first (earlier) screening")
    screening_id_2: str = Field(..., description="ID of the second (later) screening")


class CompareImagesResponse(BaseModel):
    """Result of comparing two screenings."""
    screening_id_1: str
    screening_id_2: str
    condition_change: str = Field(..., description="improved | worsened | stable | inconclusive")
    confidence_delta: Optional[float] = None
    severity_change: Optional[str] = None
    notes: List[str] = Field(default_factory=list, description="Bullet-point observations")
    recommendation: str
    disclaimer: str


# ======================================================================
# User Profile
# ======================================================================

class UserProfile(BaseModel):
    """Public user profile data."""
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    skin_type: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: Optional[datetime] = None
    total_screenings: int = 0
    last_screening_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """Body for PUT /user/profile."""
    full_name: Optional[str] = Field(None, max_length=120)
    avatar_url: Optional[str] = None
    skin_type: Optional[str] = Field(
        None,
        description="oily | dry | combination | normal | sensitive"
    )
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")


# ======================================================================
# Upload
# ======================================================================

class UploadResponse(BaseModel):
    """Returned by POST /upload."""
    storage_path: str = Field(..., description="Supabase storage path, e.g. skin-images/uid/uuid.jpg")
    signed_url: str = Field(..., description="Temporary signed URL for reading the image")
    expires_in: int = Field(..., description="Seconds until signed URL expires")
    file_name: str
    content_type: str
    size_bytes: int


# ======================================================================
# Admin Metrics
# ======================================================================

class ResultDistribution(BaseModel):
    healthy: int = 0
    potentially_affected: int = 0
    uncertain: int = 0
    quality_failed: int = 0


class ConfidenceDistribution(BaseModel):
    high: int = 0
    moderate: int = 0
    low: int = 0


class AdminMetrics(BaseModel):
    total_screenings: int
    total_users: int
    result_distribution: ResultDistribution
    confidence_distribution: ConfidenceDistribution
    top_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    model_version: str
    avg_quality_score: Optional[float] = None
