-- PIXEL-T TASK 12: reproducibility metadata for completed AI analyses.
ALTER TABLE public.analyses
    ADD COLUMN IF NOT EXISTS model_checkpoint_sha256 VARCHAR(64),
    ADD COLUMN IF NOT EXISTS tta_scales JSONB,
    ADD COLUMN IF NOT EXISTS tta_orientations JSONB,
    ADD COLUMN IF NOT EXISTS gradcam_status VARCHAR(20);

ALTER TABLE public.analyses
    ADD CONSTRAINT analyses_gradcam_status_check
    CHECK (gradcam_status IS NULL OR gradcam_status IN ('completed', 'failed'));
