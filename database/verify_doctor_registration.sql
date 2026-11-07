-- ==============================================================================
-- PIXEL-T — Read-Only Verification Queries
-- Description: Non-destructive checks for doctor registration provisioning.
--            Safe to run in the Supabase SQL Editor at any time.
-- ==============================================================================

-- 1. Is the signup trigger installed?
SELECT
    tgname AS trigger_name,
    pg_get_triggerdef(oid) AS definition
FROM pg_trigger
WHERE tgrelid = 'auth.users'::regclass
  AND NOT tgisinternal;

-- 2. Does the trigger function exist?
SELECT proname, prosecdef AS security_definer, proconfig AS settings
FROM pg_proc
WHERE proname = 'handle_new_doctor_signup';

-- 3. Doctor accounts in auth.users that have NO doctor_profiles row.
--    These are the accounts the backfill in migration 008 repairs.
SELECT
    u.id AS user_id,
    u.email,
    u.email_confirmed_at,
    u.raw_user_meta_data->>'full_name'          AS full_name,
    u.raw_user_meta_data->>'hospital'           AS hospital,
    u.raw_user_meta_data->>'primary_specialty'  AS primary_specialty,
    u.raw_app_meta_data->>'role'                AS app_role
FROM auth.users u
WHERE u.raw_user_meta_data ? 'full_name'
  AND COALESCE(u.raw_app_meta_data->>'role', '') <> 'admin'
  AND NOT EXISTS (
      SELECT 1 FROM public.doctor_profiles dp WHERE dp.user_id = u.id
  );

-- 4. Current doctor registration status counts (what the Admin Dashboard reads).
SELECT
    account_status,
    COUNT(*) AS count
FROM public.doctor_profiles
GROUP BY account_status
ORDER BY account_status;

-- 5. Detailed profile list.
SELECT
    dp.id,
    dp.user_id,
    dp.full_name,
    dp.hospital,
    dp.primary_specialty,
    dp.role,
    dp.account_status,
    dp.approved_at,
    dp.rejection_reason,
    dp.created_at
FROM public.doctor_profiles dp
ORDER BY dp.created_at DESC;
