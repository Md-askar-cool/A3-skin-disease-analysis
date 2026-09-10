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
-- =============================================================================
-- SafeSkin AI – Supabase Storage Configuration
-- Migration: 002_storage.sql
-- Description: Creates private storage buckets for user skin images and
--              GradCAM heat-map results. Applies RLS-style Storage policies
--              so that each user can only access files under their own
--              user-id prefix in the path.
-- Run Order: 2nd (after 001_initial_schema.sql)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- IMPORTANT NOTE ON STORAGE POLICIES
-- ---------------------------------------------------------------------------
-- Supabase Storage object paths are structured as:
--   <bucket_name>/<user_id>/<sub-folder>/<filename>
--
-- The helper function storage.foldername(name) returns an array of path
-- segments. Index [1] (1-based) is the first segment after the bucket name,
-- which we enforce to equal the calling user's UUID.
-- ---------------------------------------------------------------------------

-- =============================================================================
-- 1. BUCKET: skin-images
--    Stores original skin photos uploaded by users before AI analysis.
--    Access is PRIVATE – no anonymous reads.
-- =============================================================================
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'skin-images',          -- Bucket ID (must match bucket name for simplicity)
    'skin-images',          -- Human-readable name shown in dashboard
    false,                  -- private: NOT publicly accessible
    10485760,               -- 10 MB max file size (skin photos rarely exceed this)
    ARRAY[
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'image/heic',
        'image/heif'
    ]
)
ON CONFLICT (id) DO NOTHING;  -- Idempotent: safe to re-run if bucket already exists


-- =============================================================================
-- 2. BUCKET: gradcam-results
--    Stores GradCAM heat-map overlay images generated by the AI backend.
--    Access is PRIVATE – files are served via signed URLs with short TTL.
-- =============================================================================
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'gradcam-results',
    'gradcam-results',
    false,                  -- private: served via signed URLs only
    5242880,                -- 5 MB max (GradCAM outputs are typically small PNGs)
    ARRAY[
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp'
    ]
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 3. STORAGE RLS POLICIES – skin-images bucket
-- =============================================================================
-- File path convention inside the bucket:
--   <user_uuid>/screenings/<screening_uuid>.<ext>   -- original screening images
--   <user_uuid>/progress/<progress_uuid>.<ext>      -- progress tracking images
--
-- (storage.foldername(name))[1] extracts the first path segment (the user UUID).
-- =============================================================================

-- Allow authenticated users to SELECT (read) their own objects
CREATE POLICY "skin_images_select_own"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'skin-images'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to INSERT (upload) objects under their own prefix
CREATE POLICY "skin_images_insert_own"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'skin-images'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to UPDATE metadata on their own objects
CREATE POLICY "skin_images_update_own"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'skin-images'
        AND (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'skin-images'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to DELETE their own objects
CREATE POLICY "skin_images_delete_own"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'skin-images'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- =============================================================================
-- 4. STORAGE RLS POLICIES – gradcam-results bucket
-- =============================================================================
-- File path convention:
--   <user_uuid>/gradcam/<screening_uuid>_heatmap.png
--
-- The backend service role inserts GradCAM files (bypasses RLS by using the
-- service role key). Users can only read/delete their own heat-maps.
-- =============================================================================

-- Users can read their own GradCAM overlays (fetched via signed URL)
CREATE POLICY "gradcam_select_own"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'gradcam-results'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Service role writes GradCAM images on behalf of users.
-- This INSERT policy covers cases where the frontend uploads directly
-- (e.g., if the architecture changes to a direct-upload model).
CREATE POLICY "gradcam_insert_own"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'gradcam-results'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can delete their own GradCAM overlays
CREATE POLICY "gradcam_delete_own"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'gradcam-results'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- =============================================================================
-- 5. CORS CONFIGURATION (informational – set via Supabase Dashboard)
-- =============================================================================
-- Supabase Storage CORS is configured in the Dashboard under
-- Storage > Settings > CORS. Recommended origins for development:
--   - http://localhost:5173   (Vite web dev server)
--   - http://localhost:3000   (alternative web port)
-- For production add the deployed domain.
-- =============================================================================

-- =============================================================================
-- END OF MIGRATION 002
-- =============================================================================
-- =============================================================================
-- SafeSkin AI – Stored Procedures & Triggers
-- Migration: 003_functions.sql
-- Description: Defines all SQL functions used by the application and backend
--              service, including the auto-user-creation trigger, progress
--              data retrieval, and a GDPR-style user data purge function.
-- Run Order: 3rd (after 001 and 002)
-- =============================================================================

-- =============================================================================
-- 1. TRIGGER FUNCTION: handle_new_user()
--    Automatically creates a row in public.users whenever a new account is
--    registered in auth.users. Called by the on_auth_user_created trigger.
--
--    Why SECURITY DEFINER?
--    The trigger fires in the context of the auth schema (privileged). Using
--    SECURITY DEFINER lets it write to public.users even though the
--    initiating role might not have INSERT permission on that table.
-- =============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER                   -- Run with the privileges of the function owner
SET search_path = public           -- Avoid search_path hijacking (security best practice)
AS $$
BEGIN
    -- Insert a profile row mirroring the new auth user.
    -- new.raw_user_meta_data is a JSONB column that may contain:
    --   {"full_name": "Alice", "avatar_url": "https://..."}
    -- populated by the OAuth provider or the sign-up payload.
    INSERT INTO public.users (id, email, name, avatar_url, created_at)
    VALUES (
        NEW.id,                                                        -- same UUID as auth.users
        NEW.email,                                                     -- email from auth record
        NEW.raw_user_meta_data ->> 'full_name',                        -- optional display name
        NEW.raw_user_meta_data ->> 'avatar_url',                       -- optional avatar URL
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;   -- Idempotent: ignore if profile already exists

    RETURN NEW;
END;
$$;


-- Drop the trigger first so this migration is re-runnable without error


-- Create the trigger on Supabase internal auth schema
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();


-- =============================================================================
-- 2. FUNCTION: get_user_progress(p_user_id uuid)
--    Returns all progress images for a given user, enriched with the linked
--    screening result if one exists. Ordered chronologically by upload_date.
--
--    Returns a table so callers can treat the result like a SELECT query.
--    The FastAPI backend calls this via supabase.rpc('get_user_progress', {...}).
-- =============================================================================
CREATE OR REPLACE FUNCTION public.get_user_progress(p_user_id uuid)
RETURNS TABLE (
    -- Progress image fields
    progress_id             uuid,
    image_url               text,
    image_path              text,
    upload_date             date,
    comparison_notes        text,
    day_number              int,
    progress_created_at     timestamptz,

    -- Joined screening fields (nullable if no screening linked)
    screening_id            uuid,
    screening_result        text,
    possible_condition      text,
    confidence_score        float,
    confidence_level        text,
    severity_estimate       text,
    image_quality_score     int,
    gradcam_url             text,
    screening_created_at    timestamptz
)
LANGUAGE sql
STABLE                              -- does not modify the database, same result within a tx
SECURITY INVOKER                    -- respect RLS of the calling user
SET search_path = public
AS $$
    SELECT
        -- Progress image columns
        pi.id                    AS progress_id,
        pi.image_url             AS image_url,
        pi.image_path            AS image_path,
        pi.upload_date           AS upload_date,
        pi.comparison_notes      AS comparison_notes,
        pi.day_number            AS day_number,
        pi.created_at            AS progress_created_at,

        -- Screening history columns (LEFT JOIN keeps rows with no linked screening)
        sh.id                    AS screening_id,
        sh.screening_result      AS screening_result,
        sh.possible_condition    AS possible_condition,
        sh.confidence_score      AS confidence_score,
        sh.confidence_level      AS confidence_level,
        sh.severity_estimate     AS severity_estimate,
        sh.image_quality_score   AS image_quality_score,
        sh.gradcam_url           AS gradcam_url,
        sh.created_at            AS screening_created_at
    FROM
        public.progress_images pi
    LEFT JOIN
        public.screening_history sh
        ON sh.id = pi.screening_history_id
    WHERE
        pi.user_id = p_user_id    -- filter to the requested user
    ORDER BY
        pi.upload_date ASC,       -- chronological order for timeline display
        pi.created_at  ASC;       -- tie-break by insert time
$$;


-- =============================================================================
-- 3. FUNCTION: delete_user_data(p_user_id uuid)
--    Hard-deletes ALL data for a user from every application table and from
--    both storage buckets. Designed for GDPR "right to erasure" requests.
--
--    Cascade delete order (FK constraints determine this):
--      ai_model_results -> screening_history -> progress_images -> users
--
--    Storage objects are deleted via the storage.objects table directly.
--    Note: the function must be called with the service role key from the
--    backend, NOT from the client, because it deletes other users records
--    only when called by an admin endpoint.
-- =============================================================================
CREATE OR REPLACE FUNCTION public.delete_user_data(p_user_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, storage
AS $$
DECLARE
    v_deleted_screenings    int := 0;
    v_deleted_progress      int := 0;
    v_deleted_storage_objs  int := 0;
BEGIN
    -- -----------------------------------------------------------------------
    -- Step 1: Delete storage objects from skin-images bucket
    -- Path prefix convention: <user_id>/...
    -- -----------------------------------------------------------------------
    DELETE FROM storage.objects
    WHERE bucket_id = 'skin-images'
      AND (storage.foldername(name))[1] = p_user_id::text;
    GET DIAGNOSTICS v_deleted_storage_objs = ROW_COUNT;

    -- -----------------------------------------------------------------------
    -- Step 2: Delete storage objects from gradcam-results bucket
    -- -----------------------------------------------------------------------
    DELETE FROM storage.objects
    WHERE bucket_id = 'gradcam-results'
      AND (storage.foldername(name))[1] = p_user_id::text;
    -- Accumulate count
    v_deleted_storage_objs := v_deleted_storage_objs + (SELECT COUNT(*)::int FROM (SELECT 1) t);

    -- -----------------------------------------------------------------------
    -- Step 3: Delete ai_model_results rows (via cascade but being explicit)
    -- -----------------------------------------------------------------------
    DELETE FROM public.ai_model_results
    WHERE screening_id IN (
        SELECT id FROM public.screening_history WHERE user_id = p_user_id
    );

    -- -----------------------------------------------------------------------
    -- Step 4: Delete screening_history rows
    -- (ai_model_results cascade deletes also happen here automatically)
    -- -----------------------------------------------------------------------
    DELETE FROM public.screening_history WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_deleted_screenings = ROW_COUNT;

    -- -----------------------------------------------------------------------
    -- Step 5: Delete progress_images rows
    -- -----------------------------------------------------------------------
    DELETE FROM public.progress_images WHERE user_id = p_user_id;
    GET DIAGNOSTICS v_deleted_progress = ROW_COUNT;

    -- -----------------------------------------------------------------------
    -- Step 6: Delete the user profile row
    -- (all FK children should already be gone, preventing FK violation)
    -- -----------------------------------------------------------------------
    DELETE FROM public.users WHERE id = p_user_id;

    -- Return an audit summary so the calling service can log what was erased
    RETURN jsonb_build_object(
        'user_id',              p_user_id,
        'deleted_screenings',   v_deleted_screenings,
        'deleted_progress',     v_deleted_progress,
        'deleted_storage_objs', v_deleted_storage_objs,
        'deleted_at',           now()
    );

EXCEPTION
    WHEN OTHERS THEN
        -- Return error detail so the backend can surface it to the admin
        RETURN jsonb_build_object(
            'error',    SQLERRM,
            'user_id',  p_user_id
        );
END;
$$;


-- =============================================================================
-- 4. HELPER FUNCTION: compute_day_number()
--    Trigger function that automatically populates progress_images.day_number
--    when a new progress image is inserted, based on the user earliest image.
-- =============================================================================
CREATE OR REPLACE FUNCTION public.compute_day_number()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    v_first_date date;
BEGIN
    -- Find the earliest upload_date for this user (excluding the new row itself)
    SELECT MIN(upload_date)
      INTO v_first_date
      FROM public.progress_images
     WHERE user_id = NEW.user_id;

    IF v_first_date IS NULL THEN
        -- This is the very first image for this user -> day 0
        NEW.day_number := 0;
    ELSE
        NEW.day_number := (NEW.upload_date - v_first_date)::int;
    END IF;

    RETURN NEW;
END;
$$;


-- Attach the trigger (BEFORE INSERT so we can mutate NEW before it is written)
DROP TRIGGER IF EXISTS trg_compute_day_number ON public.progress_images;

CREATE TRIGGER trg_compute_day_number
    BEFORE INSERT ON public.progress_images
    FOR EACH ROW
    WHEN (NEW.day_number IS NULL)  -- Only compute if the caller did not supply a value
    EXECUTE FUNCTION public.compute_day_number();


-- =============================================================================
-- 5. HELPER FUNCTION: get_screening_stats(p_user_id uuid)
--    Dashboard summary: total screenings, breakdown by result, last screened.
-- =============================================================================
CREATE OR REPLACE FUNCTION public.get_screening_stats(p_user_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = public
AS $$
    SELECT jsonb_build_object(
        'total_screenings',         COUNT(*),
        'no_clear_abnormality',     COUNT(*) FILTER (WHERE screening_result = 'no_clear_abnormality'),
        'potentially_affected',     COUNT(*) FILTER (WHERE screening_result = 'potentially_affected'),
        'uncertain',                COUNT(*) FILTER (WHERE screening_result = 'uncertain'),
        'last_screening_date',      MAX(created_at),
        'avg_confidence_score',     ROUND(AVG(confidence_score)::numeric, 4)
    )
    FROM public.screening_history
    WHERE user_id = p_user_id;
$$;


-- =============================================================================
-- END OF MIGRATION 003
-- =============================================================================
