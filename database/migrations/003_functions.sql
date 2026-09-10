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

COMMENT ON FUNCTION public.handle_new_user() IS
    'Trigger function: mirrors new auth.users rows into public.users automatically.';

-- Drop the trigger first so this migration is re-runnable without error
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create the trigger on Supabase internal auth schema
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

COMMENT ON TRIGGER on_auth_user_created ON auth.users IS
    'Fires after every new sign-up to create the matching public.users profile row.';

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

COMMENT ON FUNCTION public.get_user_progress(uuid) IS
    'Returns all progress images for a user joined with any linked screening data, ordered chronologically.';

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
      AND storage.foldername(name)[1] = p_user_id::text;
    GET DIAGNOSTICS v_deleted_storage_objs = ROW_COUNT;

    -- -----------------------------------------------------------------------
    -- Step 2: Delete storage objects from gradcam-results bucket
    -- -----------------------------------------------------------------------
    DELETE FROM storage.objects
    WHERE bucket_id = 'gradcam-results'
      AND storage.foldername(name)[1] = p_user_id::text;
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

COMMENT ON FUNCTION public.delete_user_data(uuid) IS
    'GDPR erasure: removes all rows and storage objects for a user across every table/bucket. Must be called with the service role key.';

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

COMMENT ON FUNCTION public.compute_day_number() IS
    'Trigger: automatically sets day_number on progress_images inserts based on the user earliest image date.';

-- Attach the trigger (BEFORE INSERT so we can mutate NEW before it is written)
DROP TRIGGER IF EXISTS trg_compute_day_number ON public.progress_images;

CREATE TRIGGER trg_compute_day_number
    BEFORE INSERT ON public.progress_images
    FOR EACH ROW
    WHEN (NEW.day_number IS NULL)  -- Only compute if the caller did not supply a value
    EXECUTE FUNCTION public.compute_day_number();

COMMENT ON TRIGGER trg_compute_day_number ON public.progress_images IS
    'Automatically computes day_number relative to the user first progress image.';

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

COMMENT ON FUNCTION public.get_screening_stats(uuid) IS
    'Returns a JSON summary of screening statistics for the given user. Used by the dashboard widget.';

-- =============================================================================
-- END OF MIGRATION 003
-- =============================================================================
