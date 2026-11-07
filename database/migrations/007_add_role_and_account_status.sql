-- ==============================================================================
-- PIXEL-T — Database Migration: 007_add_role_and_account_status.sql
-- Description: Adds role and account_status columns to doctor_profiles for
--              the two-role user system (admin + doctor).
--
-- Role: 'doctor' — medical personnel who can use analysis features
--        (created via public sign-up)
--
-- Status values:
--   pending   — account created but awaiting admin approval
--   approved  — account verified, full access granted
--   rejected  — account denied by admin
--
-- Existing accounts are migrated automatically:
--   role = 'doctor', account_status = 'approved'
--
-- Admin accounts are stored in auth.users.raw_user_meta_data.role = 'admin'
-- (created manually, no public registration path).
--
-- RLS policies are updated to allow service-role backend access.
-- ==============================================================================

-- 1. ADD ROLE COLUMN
ALTER TABLE public.doctor_profiles
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'doctor';

-- 2. ADD ACCOUNT_STATUS COLUMN
ALTER TABLE public.doctor_profiles
  ADD COLUMN IF NOT EXISTS account_status TEXT NOT NULL DEFAULT 'pending';

-- 3. ADD APPROVAL_METADATA COLUMNS
ALTER TABLE public.doctor_profiles
  ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES auth.users(id),
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- 4. MIGRATE EXISTING ACCOUNTS
-- All existing doctor_profiles get role='doctor' and status='approved'
-- so existing users retain access without interruption.
UPDATE public.doctor_profiles
SET
  role = 'doctor',
  account_status = 'approved'
WHERE role = 'doctor' AND account_status = 'pending';

-- 5. ADD INDEX FOR COMMON QUERY PATTERN (list by status)
CREATE INDEX IF NOT EXISTS idx_doctor_profiles_account_status
  ON public.doctor_profiles(account_status);

-- ==============================================================================
-- ADMIN ACCOUNT CREATION (MANUAL — NO PUBLIC UI ENDPOINT)
-- ==============================================================================
-- Admin accounts are created by setting app_metadata.role = 'admin' via the
-- Supabase Admin API (service-role key). This CANNOT be done through the
-- frontend or the anon key, preventing privilege escalation.
--
-- To create an admin account, run the following in Supabase SQL Editor
-- using the service-role key (or the Supabase Dashboard > SQL Editor):
--
--   SELECT supabase_auth.admin.update_user_by_id(
--     'USER_UUID_GOES_HERE',
--     jsonb_build_object('app_metadata', jsonb_build_object('role', 'admin'))
--   );
--
-- Alternatively, via psql / direct service-role API call:
--   PUT /auth/v1/admin/users/{id}
--   Body: {"app_metadata": {"role": "admin"}}
--
-- NOTE: user_metadata.role MUST NOT be used for authorization — it is
-- user-writable and can be exploited for privilege escalation.

-- 6. UPDATE RLS POLICIES
-- Service-role policy: allows backend to read all doctor profiles (admin operations)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'doctor_profiles'
      AND policyname = 'Service role can read all doctor profiles'
  ) THEN
    CREATE POLICY "Service role can read all doctor profiles"
      ON public.doctor_profiles
      FOR SELECT
      TO service_role
      USING (true);
  END IF;
END
$$;

-- Service-role policy: allows backend to update doctor profiles (admin operations)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'doctor_profiles'
      AND policyname = 'Service role can update doctor profiles'
  ) THEN
    CREATE POLICY "Service role can update doctor profiles"
      ON public.doctor_profiles
      FOR UPDATE
      TO service_role
      USING (true)
      WITH CHECK (true);
  END IF;
END
$$;
