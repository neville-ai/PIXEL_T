-- ==============================================================================
-- PIXEL-T — Database Migration: 006_add_avatar_url_to_doctor_profiles.sql
-- Description: Adds the avatar_url column to public.doctor_profiles so that
--              profile photos uploaded to the 'profile-avatars' storage bucket
--              can be persisted in the database alongside the rest of the
--              clinician profile.
--
-- This column is referenced by:
--   Frontend/src/utils/profile.ts line 124  (read: row.avatar_url)
--   Frontend/src/utils/profile.ts line 360  (write: avatar_url in upsert payload)
--
-- The column is intentionally nullable because not every doctor uploads a photo.
-- ==============================================================================
ALTER TABLE public.doctor_profiles
  ADD COLUMN IF NOT EXISTS avatar_url TEXT;
