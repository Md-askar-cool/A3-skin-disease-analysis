-- =============================================================================
-- SafeSkin AI – Seed Data for Development / Testing
-- File: database/seed_data.sql
-- Description: Inserts realistic synthetic test data into all application
--              tables. This file is safe to run multiple times (uses
--              ON CONFLICT DO NOTHING / idempotent inserts).
--
-- WARNING: NEVER run this in production. Seed UUIDs are hard-coded and
--          the auth rows below are synthetic – they do NOT create real
--          Supabase auth accounts. Use the Supabase dashboard or the
--          auth API to create real test accounts, then run only the
--          public.users INSERT section with the real UUIDs.
--
-- HOW TO USE IN DEVELOPMENT:
--   1. Create two test accounts via the Supabase dashboard or API:
--        - test1@safeskin.dev  (password: Test@1234)
--        - test2@safeskin.dev  (password: Test@5678)
--   2. Replace the UUIDs below with the actual UUIDs returned by Supabase.
--   3. Run this script in the Supabase SQL Editor.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- SECTION 0: Synthetic UUIDs
-- These are fixed development UUIDs. Replace with real auth.users UUIDs when
-- running against a live Supabase project that has real auth accounts.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    -- Just a note block – the UUIDs are defined inline below for clarity
    RAISE NOTICE 'SafeSkin AI seed data – development environment only';
END $$;

-- ===========================================================================
-- SECTION 1: Insert into auth.users (ONLY for local Supabase CLI dev)
-- ===========================================================================
-- When using the Supabase CLI locally (supabase start) you can insert directly
-- into auth.users. On a hosted Supabase project, create users via:
--   POST https://<ref>.supabase.co/auth/v1/signup
-- and replace the UUIDs with the ones returned.
--
-- bcrypt hashes below were generated for:
--   test1@safeskin.dev -> password "Test@1234"
--   test2@safeskin.dev -> password "Test@5678"
-- (These are dev-only throwaway credentials)
-- ===========================================================================

-- NOTE: The INSERT into auth.users is commented out because it requires
-- running on a local Supabase instance (supabase CLI) or with superuser
-- privileges. Uncomment if using supabase start locally.

/*
INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    role,
    aud,
    raw_user_meta_data,
    created_at,
    updated_at
)
VALUES
(
    '11111111-1111-1111-1111-111111111111',
    '00000000-0000-0000-0000-000000000000',
    'test1@safeskin.dev',
    -- bcrypt hash of 'Test@1234' (cost 10)
    '$2a$10$9Nd7wXj9N1rD5K0xzHEiTeVpqJQQ7q5iXdP.O1X9R3L5YiDq.Tnqu',
    now(),
    'authenticated',
    'authenticated',
    '{"full_name": "Alice Tester", "avatar_url": null}'::jsonb,
    now(),
    now()
),
(
    '22222222-2222-2222-2222-222222222222',
    '00000000-0000-0000-0000-000000000000',
    'test2@safeskin.dev',
    -- bcrypt hash of 'Test@5678' (cost 10)
    '$2a$10$QmS4vLpF3K9EwT2jXqB8oOY4nHdG1Cv8bkWvNPd6m5Za7Ie3UzK3G',
    now(),
    'authenticated',
    'authenticated',
    '{"full_name": "Bob Developer", "avatar_url": null}'::jsonb,
    now(),
    now()
)
ON CONFLICT (id) DO NOTHING;
*/

-- ===========================================================================
-- SECTION 2: public.users profiles
-- The handle_new_user trigger normally creates these automatically.
-- We insert them manually here since we may not have fired the trigger.
-- ===========================================================================
INSERT INTO public.users (id, name, email, avatar_url, created_at)
VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'Alice Tester',
    'test1@safeskin.dev',
    null,
    now() - INTERVAL '30 days'   -- Simulate account created 30 days ago
),
(
    '22222222-2222-2222-2222-222222222222',
    'Bob Developer',
    'test2@safeskin.dev',
    null,
    now() - INTERVAL '15 days'   -- Account created 15 days ago
)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- SECTION 3: screening_history – test screenings for Alice (user 1)
-- ===========================================================================
INSERT INTO public.screening_history (
    id,
    user_id,
    image_url,
    image_path,
    screening_result,
    possible_condition,
    confidence_score,
    confidence_level,
    severity_estimate,
    image_quality_score,
    quality_checks,
    gradcam_url,
    model_version,
    notes,
    created_at
)
VALUES
-- Screening 1: Eczema detected with high confidence
(
    'aaaa0001-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../seed_img_1.jpg',
    '11111111-1111-1111-1111-111111111111/screenings/seed_img_1.jpg',
    'potentially_affected',
    'Eczema (Atopic Dermatitis)',
    0.8921,
    'high',
    'mild',
    88,
    '{"blur": 91, "lighting": 87, "skin_visible": true, "resolution_ok": true, "multiple_lesions": false}'::jsonb,
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/gradcam-results/11111111.../seed_gradcam_1.png',
    'v1.0.0',
    'Patch of dry, itchy skin on inner elbow. No secondary infection visible.',
    now() - INTERVAL '25 days'
),
-- Screening 2: Follow-up, improved condition
(
    'aaaa0002-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../seed_img_2.jpg',
    '11111111-1111-1111-1111-111111111111/screenings/seed_img_2.jpg',
    'potentially_affected',
    'Eczema (Atopic Dermatitis)',
    0.7435,
    'moderate',
    'mild',
    92,
    '{"blur": 95, "lighting": 90, "skin_visible": true, "resolution_ok": true, "multiple_lesions": false}'::jsonb,
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/gradcam-results/11111111.../seed_gradcam_2.png',
    'v1.0.0',
    'Follow-up after 2 weeks of moisturiser. Redness reduced.',
    now() - INTERVAL '11 days'
),
-- Screening 3: No abnormality
(
    'aaaa0003-0000-0000-0000-000000000003',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../seed_img_3.jpg',
    '11111111-1111-1111-1111-111111111111/screenings/seed_img_3.jpg',
    'no_clear_abnormality',
    null,
    0.9312,
    'high',
    null,
    95,
    '{"blur": 97, "lighting": 94, "skin_visible": true, "resolution_ok": true, "multiple_lesions": false}'::jsonb,
    null,
    'v1.0.0',
    'Skin looks clear after full treatment course.',
    now() - INTERVAL '2 days'
)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- SECTION 4: screening_history – test screenings for Bob (user 2)
-- ===========================================================================
INSERT INTO public.screening_history (
    id,
    user_id,
    image_url,
    image_path,
    screening_result,
    possible_condition,
    confidence_score,
    confidence_level,
    severity_estimate,
    image_quality_score,
    quality_checks,
    gradcam_url,
    model_version,
    notes,
    created_at
)
VALUES
-- Screening 1: Low quality image, uncertain result
(
    'bbbb0001-0000-0000-0000-000000000001',
    '22222222-2222-2222-2222-222222222222',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/22222222.../seed_img_b1.jpg',
    '22222222-2222-2222-2222-222222222222/screenings/seed_img_b1.jpg',
    'uncertain',
    null,
    0.3845,
    'uncertain',
    'unable_to_assess',
    42,
    '{"blur": 38, "lighting": 50, "skin_visible": true, "resolution_ok": false, "multiple_lesions": false}'::jsonb,
    null,
    'v1.0.0',
    'Image too blurry for reliable assessment. User asked to retake photo.',
    now() - INTERVAL '10 days'
),
-- Screening 2: Psoriasis suspected
(
    'bbbb0002-0000-0000-0000-000000000002',
    '22222222-2222-2222-2222-222222222222',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/22222222.../seed_img_b2.jpg',
    '22222222-2222-2222-2222-222222222222/screenings/seed_img_b2.jpg',
    'potentially_affected',
    'Psoriasis',
    0.7812,
    'moderate',
    'moderate',
    79,
    '{"blur": 82, "lighting": 75, "skin_visible": true, "resolution_ok": true, "multiple_lesions": true}'::jsonb,
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/gradcam-results/22222222.../seed_gradcam_b2.png',
    'v1.0.0',
    'Scaly plaques on elbow. Referred to dermatologist.',
    now() - INTERVAL '5 days'
)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- SECTION 5: ai_model_results – per-stage raw outputs for Alice screening 1
-- ===========================================================================
INSERT INTO public.ai_model_results (
    id,
    screening_id,
    model_version,
    model_stage,
    prediction,
    confidence,
    raw_probabilities,
    created_at
)
VALUES
-- Stage 1: Quality check passed
(
    'cccc0001-0000-0000-0000-000000000001',
    'aaaa0001-0000-0000-0000-000000000001',
    'v1.0.0',
    'quality_check',
    'acceptable',
    0.9124,
    '{"acceptable": 0.9124, "blurry": 0.0512, "poor_lighting": 0.0364}'::jsonb,
    now() - INTERVAL '25 days'
),
-- Stage 2: Healthy screener – flagged as potentially abnormal
(
    'cccc0002-0000-0000-0000-000000000002',
    'aaaa0001-0000-0000-0000-000000000001',
    'v1.0.0',
    'healthy_screener',
    'potentially_affected',
    0.8763,
    '{"no_clear_abnormality": 0.1237, "potentially_affected": 0.8763}'::jsonb,
    now() - INTERVAL '25 days'
),
-- Stage 3: Condition classifier
(
    'cccc0003-0000-0000-0000-000000000003',
    'aaaa0001-0000-0000-0000-000000000001',
    'v1.0.0',
    'condition_classifier',
    'Eczema (Atopic Dermatitis)',
    0.8921,
    '{
        "Eczema (Atopic Dermatitis)": 0.8921,
        "Contact Dermatitis": 0.0612,
        "Psoriasis": 0.0287,
        "Seborrheic Dermatitis": 0.0098,
        "Tinea (Ringworm)": 0.0082
    }'::jsonb,
    now() - INTERVAL '25 days'
)
ON CONFLICT (id) DO NOTHING;

-- Stage outputs for Bob screening 2 (Psoriasis)
INSERT INTO public.ai_model_results (
    id, screening_id, model_version, model_stage, prediction, confidence, raw_probabilities, created_at
)
VALUES
(
    'dddd0001-0000-0000-0000-000000000001',
    'bbbb0002-0000-0000-0000-000000000002',
    'v1.0.0',
    'quality_check',
    'acceptable',
    0.8231,
    '{"acceptable": 0.8231, "blurry": 0.1012, "poor_lighting": 0.0757}'::jsonb,
    now() - INTERVAL '5 days'
),
(
    'dddd0002-0000-0000-0000-000000000002',
    'bbbb0002-0000-0000-0000-000000000002',
    'v1.0.0',
    'healthy_screener',
    'potentially_affected',
    0.8056,
    '{"no_clear_abnormality": 0.1944, "potentially_affected": 0.8056}'::jsonb,
    now() - INTERVAL '5 days'
),
(
    'dddd0003-0000-0000-0000-000000000003',
    'bbbb0002-0000-0000-0000-000000000002',
    'v1.0.0',
    'condition_classifier',
    'Psoriasis',
    0.7812,
    '{
        "Psoriasis": 0.7812,
        "Eczema (Atopic Dermatitis)": 0.1256,
        "Seborrheic Dermatitis": 0.0621,
        "Contact Dermatitis": 0.0311
    }'::jsonb,
    now() - INTERVAL '5 days'
)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- SECTION 6: progress_images – Alice progress timeline (30-day treatment)
-- ===========================================================================
INSERT INTO public.progress_images (
    id,
    user_id,
    image_url,
    image_path,
    screening_history_id,
    upload_date,
    comparison_notes,
    day_number,
    created_at
)
VALUES
-- Day 0 – baseline (linked to first screening)
(
    'eeee0001-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../progress_d0.jpg',
    '11111111-1111-1111-1111-111111111111/progress/progress_d0.jpg',
    'aaaa0001-0000-0000-0000-000000000001',   -- linked to first screening
    CURRENT_DATE - INTERVAL '25 days',
    'Day 0: Baseline photo. Significant redness and dry patches on inner elbow.',
    0,
    now() - INTERVAL '25 days'
),
-- Day 7 – one week in
(
    'eeee0002-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../progress_d7.jpg',
    '11111111-1111-1111-1111-111111111111/progress/progress_d7.jpg',
    null,
    CURRENT_DATE - INTERVAL '18 days',
    'Day 7: Some improvement, less scratching. Moisturiser applied twice daily.',
    7,
    now() - INTERVAL '18 days'
),
-- Day 14 – two weeks (linked to second screening)
(
    'eeee0003-0000-0000-0000-000000000003',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../progress_d14.jpg',
    '11111111-1111-1111-1111-111111111111/progress/progress_d14.jpg',
    'aaaa0002-0000-0000-0000-000000000002',   -- linked to follow-up screening
    CURRENT_DATE - INTERVAL '11 days',
    'Day 14: Redness reduced by ~60%. Skin texture still a bit rough.',
    14,
    now() - INTERVAL '11 days'
),
-- Day 23 – near clearance
(
    'eeee0004-0000-0000-0000-000000000004',
    '11111111-1111-1111-1111-111111111111',
    'https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/sign/skin-images/11111111.../progress_d23.jpg',
    '11111111-1111-1111-1111-111111111111/progress/progress_d23.jpg',
    'aaaa0003-0000-0000-0000-000000000003',   -- linked to clearance screening
    CURRENT_DATE - INTERVAL '2 days',
    'Day 23: Almost completely clear. Will continue maintenance moisturising.',
    23,
    now() - INTERVAL '2 days'
)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- SECTION 7: Verification queries (optional – run separately to check data)
-- ===========================================================================
/*
-- Count rows in each table
SELECT 'users'             AS tbl, COUNT(*) FROM public.users
UNION ALL
SELECT 'screening_history' AS tbl, COUNT(*) FROM public.screening_history
UNION ALL
SELECT 'ai_model_results'  AS tbl, COUNT(*) FROM public.ai_model_results
UNION ALL
SELECT 'progress_images'   AS tbl, COUNT(*) FROM public.progress_images;

-- Test get_user_progress function for Alice
SELECT * FROM public.get_user_progress('11111111-1111-1111-1111-111111111111');

-- Test get_screening_stats for Bob
SELECT public.get_screening_stats('22222222-2222-2222-2222-222222222222');
*/

-- =============================================================================
-- END OF SEED DATA
-- =============================================================================
