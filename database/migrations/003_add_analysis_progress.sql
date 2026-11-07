-- PIXEL-T Batch P-02: nullable progress-tracking columns for the analyses table.
-- Adds `current_step` and `progress_percent` WITHOUT touching the existing
-- lifecycle `status` CHECK constraint. Both columns are nullable so existing
-- rows (and rows created before instrumentation) remain valid.
ALTER TABLE public.analyses
    ADD COLUMN IF NOT EXISTS current_step VARCHAR(64),
    ADD COLUMN IF NOT EXISTS progress_percent SMALLINT;

ALTER TABLE public.analyses
    ADD CONSTRAINT analyses_progress_percent_check
    CHECK (progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100));
