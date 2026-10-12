-- ==============================================================================
-- PIXEL-T — Database Migration: 001_create_analyses_and_storage.sql
-- Product: PIXEL-T
-- Description: Creates the primary 'analyses' table with user ownership,
--              lifecycle constraints, model metadata, and asset path columns.
--              Sets up Row Level Security (RLS) and Supabase Storage bucket.
-- Conforms strictly to: docs/DataModelSpecification.md (MVP single-table architecture)
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. ANALYSES TABLE
CREATE TABLE IF NOT EXISTS public.analyses (
    -- Identity & User Ownership
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Lifecycle Status
    status VARCHAR(20) NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed')),

    -- Original Image Metadata
    original_image_path TEXT NOT NULL,
    original_filename TEXT,
    original_mime_type VARCHAR(50),
    original_width INTEGER,
    original_height INTEGER,

    -- Segmentation Output Data
    binary_mask_path TEXT,
    segmentation_overlay_path TEXT,
    segmentation_status VARCHAR(20)
        CHECK (segmentation_status IS NULL OR segmentation_status IN ('detected', 'not_detected')),
    area_pixels INTEGER,
    area_ratio NUMERIC(7, 4),
    bounding_width_pixels INTEGER,
    bounding_height_pixels INTEGER,

    -- Explainable AI (Grad-CAM) Data
    gradcam_heatmap_path TEXT,
    gradcam_overlay_path TEXT,
    gradcam_target_layer VARCHAR(100),
    gradcam_method VARCHAR(50),
    gradcam_config_version VARCHAR(50),

    -- Model Reproducibility Metadata
    model_architecture VARCHAR(100),
    model_version VARCHAR(50),
    model_config_version VARCHAR(50),
    model_input_size INTEGER,
    model_threshold NUMERIC(4, 3),
    tta_enabled BOOLEAN,
    postprocessing_enabled BOOLEAN,

    -- Summary & Safe Error Metadata
    summary_text TEXT,
    error_code VARCHAR(50),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. INDEXES FOR PERFORMANCE & QUERY ACCELERATION
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON public.analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON public.analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON public.analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON public.analyses(user_id, created_at DESC);

-- 4. ROW LEVEL SECURITY (RLS) FOR ANALYSES TABLE
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to view only their own analyses
CREATE POLICY "Users can view own analyses"
    ON public.analyses
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Allow authenticated users to insert analyses for themselves
CREATE POLICY "Users can insert own analyses"
    ON public.analyses
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Allow authenticated users to update their own analyses
CREATE POLICY "Users can update own analyses"
    ON public.analyses
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Allow authenticated users to delete their own analyses
CREATE POLICY "Users can delete own analyses"
    ON public.analyses
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- 5. SUPABASE STORAGE BUCKET CONFIGURATION
-- Note: 'analysis-assets' bucket is strictly private (public = false).
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'analysis-assets',
    'analysis-assets',
    false,
    10485760, -- 10 MB limit per file
    ARRAY['image/jpeg', 'image/png']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png'];

-- 6. STORAGE OBJECT POLICIES (OWNERSHIP ISOLATION)
-- storage.foldername() returns a PostgreSQL 1-based array: [1]=analysis, [2]=user_id.
-- Policy: authenticated users can upload assets to analysis/{user_id}/...
CREATE POLICY "Users can upload own analysis assets"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'analysis-assets' AND
        (storage.foldername(name))[1] = 'analysis' AND
        (storage.foldername(name))[2] = auth.uid()::text
    );

-- Policy: Authenticated users can read their own analysis assets: analysis/{user_id}/...
CREATE POLICY "Users can read own analysis assets"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'analysis-assets' AND
        (storage.foldername(name))[1] = 'analysis' AND
        (storage.foldername(name))[2] = auth.uid()::text
    );

-- Policy: Authenticated users can delete their own analysis assets: analysis/{user_id}/...
CREATE POLICY "Users can delete own analysis assets"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'analysis-assets' AND
        (storage.foldername(name))[1] = 'analysis' AND
        (storage.foldername(name))[2] = auth.uid()::text
    );
