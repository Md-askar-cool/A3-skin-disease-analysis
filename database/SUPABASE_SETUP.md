# SafeSkin AI – Supabase Setup Guide

> Complete step-by-step instructions to provision and configure the Supabase
> backend for SafeSkin AI. Follow each section in order.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| A web browser | Any modern | Supabase dashboard |
| `psql` or the Supabase SQL editor | — | Running migrations |
| Node.js (optional) | ≥ 18 | Running the Supabase CLI |
| Supabase CLI (optional) | latest | Automated migrations |

---

## Step 1 – Create a Supabase Project

1. Go to **[https://supabase.com](https://supabase.com)** and sign in (or create a free account).
2. Click **New Project**.
3. Fill in the form:
   - **Organization**: select or create one.
   - **Name**: `safeskin-ai` (or your preferred name).
   - **Database Password**: generate a strong password and **save it** – you'll need it for direct DB connections.
   - **Region**: choose the region closest to your users.
4. Click **Create new project** and wait ~2 minutes for provisioning.

---

## Step 2 – Run Migration Files (in order)

Navigate to **SQL Editor** in the left sidebar of your Supabase project dashboard.

### 2a. Run `001_initial_schema.sql`

1. Open a **New query** tab.
2. Copy-paste the entire contents of `database/migrations/001_initial_schema.sql`.
3. Click **Run** (or press `Ctrl+Enter` / `Cmd+Enter`).
4. Confirm the output shows no errors. You should see tables listed under
   **Table Editor → public schema**.

> [!IMPORTANT]
> This migration must succeed before the others. It creates all tables that the
> subsequent migrations reference.

### 2b. Run `002_storage.sql`

1. Open another **New query** tab.
2. Copy-paste `database/migrations/002_storage.sql`.
3. Click **Run**.
4. Verify in **Storage** → you should now see two buckets: `skin-images` and
   `gradcam-results`, both with the **Private** badge.

### 2c. Run `003_functions.sql`

1. Open another **New query** tab.
2. Copy-paste `database/migrations/003_functions.sql`.
3. Click **Run**.
4. Verify in **Database → Functions** → you should see `handle_new_user`,
   `get_user_progress`, `delete_user_data`, `compute_day_number`, and
   `get_screening_stats`.

### 2d. (Optional) Run `seed_data.sql` for development/testing

> [!WARNING]
> **Never run seed data on a production project.** Seed data contains test
> users and fake medical results intended for development only.

1. Open a **New query** tab.
2. Copy-paste `database/seed_data.sql`.
3. Click **Run** only on a **development** project.

---

## Step 3 – Enable Email Authentication

1. In the Supabase dashboard sidebar click **Authentication → Providers**.
2. Find **Email** and confirm it is **Enabled** (it is on by default).
3. Configure the following settings (recommended):
   - **Confirm email**: ✅ Enabled (users must verify email before logging in).
   - **Secure email change**: ✅ Enabled.
   - **Minimum password length**: `8` (adjust to your security policy).
4. Under **Authentication → URL Configuration**, set:
   - **Site URL**: `http://localhost:5173` (for development) or your production URL.
   - **Redirect URLs**: add `http://localhost:5173/**` and your production domain.
5. Click **Save**.

> [!TIP]
> For Google OAuth (Phase 2), come back to **Providers → Google** and add your
> OAuth client ID/secret from the Google Cloud Console.

---

## Step 4 – Configure Storage Buckets

The migration `002_storage.sql` already creates the buckets. Verify them here:

1. Navigate to **Storage** in the sidebar.
2. Confirm both buckets exist:

   | Bucket | Access | Max file size | Allowed types |
   |--------|--------|---------------|---------------|
   | `skin-images` | Private | 10 MB | JPEG, PNG, WEBP, HEIC, HEIF |
   | `gradcam-results` | Private | 5 MB | JPEG, PNG, WEBP |

3. For each bucket, click the **⋮** menu → **Edit bucket** and double-check the
   settings match the table above.
4. Under **Storage → Policies**, confirm the RLS policies were created:
   - `skin_images_select_own`, `skin_images_insert_own`, `skin_images_update_own`, `skin_images_delete_own`
   - `gradcam_select_own`, `gradcam_insert_own`, `gradcam_delete_own`

> [!NOTE]
> The AI FastAPI backend writes GradCAM files using the **service role key**,
> which bypasses RLS. The RLS policies on `gradcam-results` restrict read/delete
> access for regular users only.

---

## Step 5 – Retrieve API Keys

1. Go to **Project Settings** → **API** (in the left sidebar under the gear icon).
2. Note down the following values:

   | Key | Where used | Notes |
   |-----|-----------|-------|
   | **Project URL** | `SUPABASE_URL` | e.g. `https://xyzabc.supabase.co` |
   | **anon / public** | `SUPABASE_ANON_KEY` | Safe to expose in frontend |
   | **service_role / secret** | `SUPABASE_SERVICE_ROLE_KEY` | **Keep secret – backend only** |

> [!CAUTION]
> **Never expose the `service_role` key in client-side code or public repos.**
> It bypasses Row Level Security and has full database access.

### 5a – Create Environment Files

**Web app** (`web/.env.local` – created in Phase 2):
```env
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

**FastAPI backend** (`backend/.env` – created in Phase 3):
```env
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

**Flutter mobile** (`mobile/lib/config/supabase_config.dart` – created in Phase 4):
```dart
const supabaseUrl = 'https://YOUR_PROJECT_REF.supabase.co';
const supabaseAnonKey = 'your_anon_key_here';
```

---

## Step 6 – Verify Row Level Security

Run this query in the SQL Editor to confirm RLS is active on all tables:

```sql
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Expected output (all `rowsecurity` values should be `true`):

| schemaname | tablename | rowsecurity |
|------------|-----------|-------------|
| public | ai_model_results | true |
| public | progress_images | true |
| public | screening_history | true |
| public | users | true |

> [!IMPORTANT]
> If any row shows `false`, run `ALTER TABLE public.<table_name> ENABLE ROW LEVEL SECURITY;`
> for the offending table.

---

## Step 7 – Verify Trigger

Test that new user sign-ups automatically create a profile row:

```sql
-- Check if the trigger exists
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';
```

Expected: one row returned with `event_object_table = 'users'` (in `auth` schema).

---

## Step 8 – (Optional) Supabase CLI for Automated Migrations

If you prefer a code-first approach with version control:

```bash
# Install the CLI
npm install -g supabase

# Login
supabase login

# Link to your project (get project ref from Project Settings -> General)
supabase link --project-ref YOUR_PROJECT_REF

# Push all migrations
supabase db push
```

Place migration files in `supabase/migrations/` (CLI convention) or run them
manually in order through the dashboard SQL editor.

---

## Architecture Overview

```
User Device (Web / Mobile)
        │
        │  HTTPS (JWT in Authorization header)
        ▼
┌─────────────────────────┐
│     Supabase Auth       │  ← Issues JWT on sign-in
│   (GoTrue service)      │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│  Supabase PostgREST API │  ← Auto-generated REST from schema
│  (RLS enforced per JWT) │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│   PostgreSQL Database   │
│  • public.users          │
│  • public.screening_history │
│  • public.progress_images   │
│  • public.ai_model_results  │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│   Supabase Storage      │
│  • skin-images (private) │
│  • gradcam-results (private) │
└─────────────────────────┘
             ▲
             │  service_role key (bypasses RLS)
┌────────────┴────────────┐
│   FastAPI AI Backend    │
│  • /analyze endpoint    │
│  • TensorFlow models    │
│  • OpenCV processing    │
└─────────────────────────┘
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `relation "public.users" does not exist` | Run `001_initial_schema.sql` first |
| `new row violates row-level security policy` | Make sure you are authenticated before calling the API |
| `storage/object: not found` when fetching image | Image path must start with `<user_uuid>/` to match RLS policy |
| `function auth.uid() does not exist` | You are running the SQL in a context outside Supabase (e.g. direct psql). This function only exists inside Supabase's managed Postgres. |
| Trigger `on_auth_user_created` not firing | Check `003_functions.sql` ran successfully; verify in Database → Triggers |
| `ERROR: duplicate key value violates unique constraint "users_pkey"` | The trigger fired but a user already exists – this is handled by `ON CONFLICT DO NOTHING` |
