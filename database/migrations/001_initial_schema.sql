-- =============================================================================
-- SafeSkin AI – Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Description: Creates all core tables with RLS policies for the SafeSkin AI
--              application. Every table is user-scoped via Row Level Security
--              so that Supabase's built-in auth.uid() is the only gatekeeper.
-- Run Order: 1st (must be run before any other migration)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Extensions
-- ---------------------------------------------------------------------------

-- Enable UUID generation helpers (gen_random_uuid, etc.)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pgcrypto is required for gen_random_uuid() in older Postgres versions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- 1. TABLE: public.users
--    Mirrors Supabase's auth.users so the rest of the schema can reference it
--    with a plain FK. Populated automatically via the handle_new_user trigger
--    defined in migration 003_functions.sql.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    -- Primary key is the same UUID as auth.users.id – keeps them in sync
    id          uuid        PRIMARY KEY DEFAULT auth.uid(),
    name        text,                          -- display name (can be null initially)
    email       text        UNIQUE NOT NULL,   -- copied from auth.users at sign-up
    avatar_url  text,                          -- optional profile picture URL
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.users               IS 'User profile data that mirrors auth.users.';
COMMENT ON COLUMN public.users.id            IS 'Same UUID as auth.users.id.';
COMMENT ON COLUMN public.users.email         IS 'Kept in sync with auth.users.email.';
COMMENT ON COLUMN public.users.avatar_url    IS 'Public URL to the user profile avatar (Supabase Storage or external).';

-- ---------------------------------------------------------------------------
-- 2. TABLE: public.screening_history
--    Every AI screening session for a user. Stores the uploaded image, the
--    AI model verdict, confidence metrics, GradCAM visualisation URL, and
--    optional free-text notes entered by the user or clinician.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.screening_history (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              uuid        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Storage references ---------------------------------------------------
    image_url            text,       -- Signed / public URL to original image
    image_path           text,       -- Storage object path  e.g. "<uid>/screenings/<uuid>.jpg"

    -- Top-level AI verdict ------------------------------------------------
    screening_result     text        CHECK (
                                         screening_result IN (
                                             'no_clear_abnormality',
                                             'potentially_affected',
                                             'uncertain'
                                         )
                                     ),
    possible_condition   text,       -- Human-readable condition name e.g. "Eczema"
    confidence_score     float       CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    confidence_level     text        CHECK (
                                         confidence_level IN (
                                             'high',       -- >= 0.85
                                             'moderate',   -- >= 0.65
                                             'low',        -- >= 0.40
                                             'uncertain'   -- < 0.40
                                         )
                                     ),
    severity_estimate    text        CHECK (
                                         severity_estimate IN (
                                             'mild',
                                             'moderate',
                                             'severe',
                                             'unable_to_assess'
                                         )
                                     ),

    -- Image quality metrics -----------------------------------------------
    image_quality_score  int         CHECK (image_quality_score BETWEEN 0 AND 100),
    quality_checks       jsonb,      -- Detailed quality sub-scores, e.g. {"blur": 92, "lighting": 88}

    -- Explainability -------------------------------------------------------
    gradcam_url          text,       -- URL to GradCAM heat-map overlay image

    -- Versioning -----------------------------------------------------------
    model_version        text,       -- e.g. "v1.2.0"
    notes                text,       -- Optional clinician / user notes

    created_at           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.screening_history                  IS 'Records every AI skin screening result for a user.';
COMMENT ON COLUMN public.screening_history.image_path       IS 'Object path inside Supabase Storage bucket "skin-images".';
COMMENT ON COLUMN public.screening_history.screening_result IS 'Top-level 3-class verdict from the AI pipeline.';
COMMENT ON COLUMN public.screening_history.quality_checks   IS 'JSONB map of individual image-quality sub-checks (blur, lighting, skin-visible, etc.).';
COMMENT ON COLUMN public.screening_history.gradcam_url      IS 'Signed URL to GradCAM heat-map stored in the "gradcam-results" bucket.';

-- Index to speed up per-user history listing (most recent first)
CREATE INDEX IF NOT EXISTS idx_screening_history_user_id
    ON public.screening_history(user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 3. TABLE: public.progress_images
--    Tracks a user's longitudinal / follow-up images so they can visually
--    compare skin condition over time. Optionally linked to a screening result.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.progress_images (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              uuid        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Storage references ---------------------------------------------------
    image_url            text,       -- Signed / public URL
    image_path           text,       -- Storage object path  e.g. "<uid>/progress/<uuid>.jpg"

    -- Link to an optional AI screening of this image ----------------------
    screening_history_id uuid        REFERENCES public.screening_history(id) ON DELETE SET NULL,

    -- Timeline metadata ---------------------------------------------------
    upload_date          date        NOT NULL DEFAULT CURRENT_DATE,
    comparison_notes     text,       -- User own observations for this date
    day_number           int,        -- Day offset from first image (computed or user-supplied)

    created_at           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.progress_images                        IS 'Longitudinal progress photos for visual comparison over time.';
COMMENT ON COLUMN public.progress_images.screening_history_id   IS 'If this image was also sent through the AI screener, link it here.';
COMMENT ON COLUMN public.progress_images.day_number             IS 'Day-offset relative to the user first progress image (day 0). Used for timeline display.';

-- Index for per-user chronological progress gallery
CREATE INDEX IF NOT EXISTS idx_progress_images_user_id
    ON public.progress_images(user_id, upload_date ASC);

-- ---------------------------------------------------------------------------
-- 4. TABLE: public.ai_model_results
--    Stores the raw per-model outputs for each screening so we can audit /
--    retrain later. The pipeline has 3 sequential stages; each stage writes
--    one row here.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ai_model_results (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_id        uuid        NOT NULL REFERENCES public.screening_history(id) ON DELETE CASCADE,

    -- Which model / stage produced this row --------------------------------
    model_version       text,       -- e.g. "v1.2.0"
    model_stage         text        CHECK (
                                        model_stage IN (
                                            'quality_check',        -- Stage 1: image usability
                                            'healthy_screener',     -- Stage 2: healthy vs abnormal
                                            'condition_classifier'  -- Stage 3: specific condition
                                        )
                                    ),

    -- Model outputs --------------------------------------------------------
    prediction          text,       -- Top-1 class label for this stage
    confidence          float       CHECK (confidence BETWEEN 0.0 AND 1.0),
    raw_probabilities   jsonb,      -- Full softmax vector, e.g. {"eczema": 0.72, "psoriasis": 0.18}

    created_at          timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.ai_model_results                   IS 'Per-stage raw output from the AI pipeline for audit and retraining.';
COMMENT ON COLUMN public.ai_model_results.model_stage       IS 'One of three pipeline stages: quality_check then healthy_screener then condition_classifier.';
COMMENT ON COLUMN public.ai_model_results.raw_probabilities IS 'Full JSONB probability map from the model final softmax layer.';

-- Index for fast look-up of all stages for a given screening
CREATE INDEX IF NOT EXISTS idx_ai_model_results_screening_id
    ON public.ai_model_results(screening_id);

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================
-- RLS is enabled on every table. All policies use auth.uid() so that even
-- service-level queries that bypass JWT validation must explicitly use the
-- service role key - regular users can never access another user rows.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Table: public.users
-- ---------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "users_select_own"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Users can insert their own profile row (also called by the trigger)
CREATE POLICY "users_insert_own"
    ON public.users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Users can update their own profile (name, avatar_url, etc.)
CREATE POLICY "users_update_own"
    ON public.users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Users can delete their own profile (cascades to all child tables)
CREATE POLICY "users_delete_own"
    ON public.users FOR DELETE
    USING (auth.uid() = id);

-- ---------------------------------------------------------------------------
-- Table: public.screening_history
-- ---------------------------------------------------------------------------
ALTER TABLE public.screening_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "screening_select_own"
    ON public.screening_history FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "screening_insert_own"
    ON public.screening_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "screening_update_own"
    ON public.screening_history FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "screening_delete_own"
    ON public.screening_history FOR DELETE
    USING (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Table: public.progress_images
-- ---------------------------------------------------------------------------
ALTER TABLE public.progress_images ENABLE ROW LEVEL SECURITY;

CREATE POLICY "progress_select_own"
    ON public.progress_images FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "progress_insert_own"
    ON public.progress_images FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "progress_update_own"
    ON public.progress_images FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "progress_delete_own"
    ON public.progress_images FOR DELETE
    USING (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Table: public.ai_model_results
-- ---------------------------------------------------------------------------
-- This table does not have a direct user_id column; access is gated via the
-- parent screening_history row using a sub-select.
-- ---------------------------------------------------------------------------
ALTER TABLE public.ai_model_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ai_results_select_own"
    ON public.ai_model_results FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.screening_history sh
            WHERE sh.id = screening_id
              AND sh.user_id = auth.uid()
        )
    );

CREATE POLICY "ai_results_insert_own"
    ON public.ai_model_results FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.screening_history sh
            WHERE sh.id = screening_id
              AND sh.user_id = auth.uid()
        )
    );

CREATE POLICY "ai_results_delete_own"
    ON public.ai_model_results FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.screening_history sh
            WHERE sh.id = screening_id
              AND sh.user_id = auth.uid()
        )
    );

-- =============================================================================
-- END OF MIGRATION 001
-- =============================================================================
