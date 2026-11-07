-- ==============================================================================
-- PIXEL-T — Database Migration: 004_create_doctor_profiles.sql
-- Description: Creates the 'doctor_profiles' table with user ownership,
--              professional clinical metadata, education, experience, and bio.
--              Sets up Row Level Security (RLS) so clinicians can only view and
--              update their own profile data.
-- ==============================================================================

-- 1. DOCTOR PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.doctor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Personal Information
    full_name TEXT NOT NULL,
    phone TEXT,
    birth_date DATE,
    city TEXT,

    -- Professional Information
    profession_category TEXT,
    academic_title TEXT,
    primary_specialty TEXT,
    subspecialty TEXT,
    clinical_focus TEXT,
    hospital TEXT,
    department TEXT,
    clinical_role TEXT,
    years_experience TEXT,
    practice_address TEXT,
    str_number TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT false,

    -- Biography
    bio TEXT,

    -- Structured Dynamic Lists (JSONB)
    education JSONB NOT NULL DEFAULT '[]'::jsonb,
    experience JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),

    -- Ensure one profile per authenticated user
    CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)
);

-- 2. INDEXES
CREATE INDEX IF NOT EXISTS idx_doctor_profiles_user_id ON public.doctor_profiles(user_id);

-- 3. ROW LEVEL SECURITY (RLS)
ALTER TABLE public.doctor_profiles ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to view only their own profile
CREATE POLICY "Users can view own doctor profile"
    ON public.doctor_profiles
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Allow authenticated users to insert their own profile
CREATE POLICY "Users can insert own doctor profile"
    ON public.doctor_profiles
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Allow authenticated users to update their own profile
CREATE POLICY "Users can update own doctor profile"
    ON public.doctor_profiles
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Allow authenticated users to delete their own profile
CREATE POLICY "Users can delete own doctor profile"
    ON public.doctor_profiles
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);
