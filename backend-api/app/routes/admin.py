"""
SafeSkin AI – Admin Routes
GET /admin/metrics – aggregated platform statistics (admin-only)
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_admin
from app.services.ai_pipeline import _model_version
from app.services.supabase_service import get_supabase_service
from app.schemas.screening import AdminMetrics, ConfidenceDistribution, ResultDistribution

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin"])


@router.get(
    "/admin/metrics",
    response_model=AdminMetrics,
    summary="Platform-wide AI screening metrics (admin only)",
)
async def get_admin_metrics(
    admin: dict = Depends(get_current_admin),
) -> AdminMetrics:
    """
    Aggregate statistics across all users:
    - Total screenings
    - Total users
    - Breakdown by result type
    - Breakdown by confidence level
    - Top detected conditions
    - Average image quality score
    """
    service = get_supabase_service()

    # ── Fetch all screening records ────────────────────────────────────
    all_screenings = service.select(
        table="screening_history",
        columns="screening_result,confidence_level,possible_condition,quality_score",
        order_by="created_at",
        ascending=False,
        limit=10000,  # Practical cap; use aggregation queries in production
    )

    total_screenings = len(all_screenings)

    # ── Total unique users ─────────────────────────────────────────────
    total_users = service.count("user_profiles")

    # ── Result distribution ────────────────────────────────────────────
    result_counts: Counter = Counter(row.get("screening_result", "") for row in all_screenings)
    result_dist = ResultDistribution(
        healthy=result_counts.get("healthy", 0),
        potentially_affected=result_counts.get("potentially_affected", 0),
        uncertain=result_counts.get("uncertain", 0),
        quality_failed=result_counts.get("quality_failed", 0),
    )

    # ── Confidence distribution ────────────────────────────────────────
    conf_counts: Counter = Counter(row.get("confidence_level", "") for row in all_screenings)
    conf_dist = ConfidenceDistribution(
        high=conf_counts.get("high", 0),
        moderate=conf_counts.get("moderate", 0),
        low=conf_counts.get("low", 0),
    )

    # ── Top conditions ─────────────────────────────────────────────────
    condition_counts: Counter = Counter(
        row.get("possible_condition")
        for row in all_screenings
        if row.get("possible_condition")
    )
    top_conditions: List[Dict[str, Any]] = [
        {"condition": cond, "count": cnt}
        for cond, cnt in condition_counts.most_common(10)
    ]

    # ── Average quality score ──────────────────────────────────────────
    quality_scores = [
        row["quality_score"]
        for row in all_screenings
        if row.get("quality_score") is not None
    ]
    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None

    logger.info(
        "Admin metrics fetched: %d screenings, %d users", total_screenings, total_users
    )

    return AdminMetrics(
        total_screenings=total_screenings,
        total_users=total_users,
        result_distribution=result_dist,
        confidence_distribution=conf_dist,
        top_conditions=top_conditions,
        model_version=_model_version,
        avg_quality_score=avg_quality,
    )
