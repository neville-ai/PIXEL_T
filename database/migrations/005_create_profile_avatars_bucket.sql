-- ==============================================================================
-- PIXEL-T — Database Migration: 005_create_profile_avatars_bucket.sql
-- Description: Creates the 'profile-avatars' storage bucket (public) and RLS
--              policies so authenticated users can only manage their own avatar.
--
-- Path convention: {user_id}/profile.{ext}
--   foldername(name)[1] = user_id  (ownership check)
--   foldername(name)[2] = profile.ext
--
-- NOTE: PostgreSQL does NOT support "CREATE POLICY IF NOT EXISTS".
-- Each policy is guarded with a DO $$ ... $$ block that checks pg_policies
-- first, making the migration safe to re-run without errors.
-- ==============================================================================

-- 1. CREATE BUCKET (idempotent — skipped if already exists)
INSERT INTO storage.buckets (id, name, public)
VALUES ('profile-avatars', 'profile-avatars', true)
ON CONFLICT (id) DO NOTHING;

-- 2. POLICY: SELECT — authenticated users can read any avatar in this bucket
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'objects' AND schemaname = 'storage'
      AND policyname = 'Avatar read all authenticated'
  ) THEN
    CREATE POLICY "Avatar read all authenticated"
      ON storage.objects
      FOR SELECT
      TO authenticated
      USING (bucket_id = 'profile-avatars');
  END IF;
END $$;

-- 3. POLICY: INSERT — authenticated users can upload only to their own folder
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'objects' AND schemaname = 'storage'
      AND policyname = 'Avatar upload own only'
  ) THEN
    CREATE POLICY "Avatar upload own only"
      ON storage.objects
      FOR INSERT
      TO authenticated
      WITH CHECK (
          bucket_id = 'profile-avatars'
          AND (storage.foldername(name))[1] = auth.uid()::text
      );
  END IF;
END $$;

-- 4. POLICY: UPDATE — authenticated users can replace (upsert) only their own file
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'objects' AND schemaname = 'storage'
      AND policyname = 'Avatar update own only'
  ) THEN
    CREATE POLICY "Avatar update own only"
      ON storage.objects
      FOR UPDATE
      TO authenticated
      USING (
          bucket_id = 'profile-avatars'
          AND (storage.foldername(name))[1] = auth.uid()::text
      )
      WITH CHECK (
          bucket_id = 'profile-avatars'
          AND (storage.foldername(name))[1] = auth.uid()::text
      );
  END IF;
END $$;

-- 5. POLICY: DELETE — authenticated users can delete only their own files
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'objects' AND schemaname = 'storage'
      AND policyname = 'Avatar delete own only'
  ) THEN
    CREATE POLICY "Avatar delete own only"
      ON storage.objects
      FOR DELETE
      TO authenticated
      USING (
          bucket_id = 'profile-avatars'
          AND (storage.foldername(name))[1] = auth.uid()::text
      );
  END IF;
END $$;
