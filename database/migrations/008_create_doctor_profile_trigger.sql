-- ==============================================================================
-- PIXEL-T — Database Migration: 008_create_doctor_profile_trigger.sql
-- Description: Ensures every new doctor signup automatically creates a
--              corresponding row in public.doctor_profiles.
--
-- DEPENDENCY: Migration 007 MUST be applied first. This trigger writes the
--             `role` and `account_status` columns that 007 introduces.
--
-- Mechanism: AFTER INSERT trigger on auth.users.
--   - Fires only for rows where raw_user_meta_data contains `full_name`
--     (doctor signups). Admin accounts (raw_app_meta_data.role = 'admin')
--     are explicitly skipped so they never appear as doctor registrations.
--   - Reads full_name, hospital, and primary_specialty from raw_user_meta_data.
--   - Sets role = 'doctor' and account_status = 'pending'.
--   - Idempotent: skips if a profile for the same user_id already exists.
--   - Uses SECURITY DEFINER so the trigger function can write to doctor_profiles
--     even though RLS is enabled on that table.
--   - Never blocks account creation: provisioning failures are logged as a
--     Postgres WARNING (Supabase > Logs > Postgres) instead of aborting signup.
--
-- Backfill: Any auth.users row that has full_name metadata (doctor) but no
--           doctor_profiles row (e.g. users registered before this migration)
--           receives a profile row with status = 'pending'. Admins are skipped.
--           Existing profiles are never modified or deleted.
-- ==============================================================================

-- 1. TRIGGER FUNCTION
CREATE OR REPLACE FUNCTION public.handle_new_doctor_signup()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only act on doctor signups: raw_user_meta_data must contain full_name,
    -- and the account must not already be marked as an admin.
    IF (NEW.raw_user_meta_data ? 'full_name')
       AND COALESCE(NEW.raw_app_meta_data->>'role', '') <> 'admin'
    THEN
        -- Skip if a profile already exists for this user (idempotent).
        IF NOT EXISTS (
            SELECT 1 FROM public.doctor_profiles dp WHERE dp.user_id = NEW.id
        ) THEN
            INSERT INTO public.doctor_profiles (
                user_id,
                full_name,
                hospital,
                primary_specialty,
                role,
                account_status,
                is_verified
            ) VALUES (
                NEW.id,
                COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
                COALESCE(NEW.raw_user_meta_data->>'hospital', ''),
                COALESCE(NEW.raw_user_meta_data->>'primary_specialty', ''),
                'doctor',
                'pending',
                false
            );
        END IF;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- Do not abort the Sign Up transaction. Log loudly so the failure is
        -- visible in Postgres logs; the backfill below can repair missing rows.
        RAISE WARNING
            'handle_new_doctor_signup: failed to create doctor_profiles for user %: %',
            NEW.id, SQLERRM;
END;
$$;

-- 2. DROP EXISTING TRIGGER (if any) AND CREATE FRESH
-- Uses a unique name so it can never collide with an unrelated trigger.
DROP TRIGGER IF EXISTS on_auth_user_created_doctor_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_doctor_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_doctor_signup();

-- 3. BACKFILL — create profiles for doctor accounts that predate this migration.
--    Only inserts when the metadata indicates a doctor and no profile exists.
--    Admins (raw_app_meta_data.role = 'admin') are excluded.
INSERT INTO public.doctor_profiles (
    user_id,
    full_name,
    hospital,
    primary_specialty,
    role,
    account_status,
    is_verified
)
SELECT
    u.id,
    COALESCE(u.raw_user_meta_data->>'full_name', ''),
    COALESCE(u.raw_user_meta_data->>'hospital', ''),
    COALESCE(u.raw_user_meta_data->>'primary_specialty', ''),
    'doctor',
    'pending',
    false
FROM auth.users u
WHERE u.raw_user_meta_data ? 'full_name'
  AND COALESCE(u.raw_app_meta_data->>'role', '') <> 'admin'
  AND NOT EXISTS (
      SELECT 1 FROM public.doctor_profiles dp WHERE dp.user_id = u.id
  );
