import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Modal } from '@/components/ui/Modal';
import { ArrowLeft, ArrowRight, Trash2 } from 'lucide-react';
import { deleteAnalysis, getAnalysis, type AnalysisDetail } from '@/utils/analysis';

function segmentationLabel(detail: AnalysisDetail | null): string {
  if (!detail) return '-';
  if (detail.analysis.status === 'failed') return 'Failed';
  if (detail.analysis.status === 'processing') return 'Processing';
  if (detail.model_analysis?.segmentation_status === 'detected') return 'Detected';
  if (detail.model_analysis?.segmentation_status === 'not_detected') return 'Not Detected';
  return 'Completed';
}

export const HistoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    if (!id) {
      setLoadError('History identifier is not defined.');
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setLoadError(null);
    try {
      setDetail(await getAnalysis(id));
    } catch (err) {
      setDetail(null);
      setLoadError(err instanceof Error ? err.message : 'Failed to load history details.');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const confirmDelete = useCallback(async () => {
    if (!id || isDeleting) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAnalysis(id);
      navigate('/history');
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete history record.');
    } finally {
      setIsDeleting(false);
    }
  }, [id, isDeleting, navigate]);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 dark:border-dark-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/dashboard" className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 inline-flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <Link to="/history" className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200">
              History
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <Badge variant="accent">Detail Arsip</Badge>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
              Examination Archive Detail
            </h1>
            <Badge variant="default" className="font-mono text-xs">
              ID: {id || 'Not specified'}
            </Badge>
          </div>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted leading-relaxed">
            Examination history metadata and access links to segmentation and Grad-CAM visualizations.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link to="/history">
            <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to History
            </Button>
          </Link>
          <Link to={`/analysis/${id}`}>
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Open Analysis Result
            </Button>
          </Link>
          <Button
            variant="danger"
            size="sm"
            leftIcon={<Trash2 className="w-4 h-4" />}
            onClick={() => {
              setDeleteError(null);
              setIsConfirmOpen(true);
            }}
            disabled={isLoading || detail === null}
          >
            Delete
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingState
          title="Loading history details"
          description="Fetching analysis session metadata from the server."
        />
      ) : loadError || !detail ? (
        <ErrorState
          code="HISTORY_DETAIL_FAILED"
          message={loadError ?? 'History details are not available.'}
          onRetry={() => void loadDetail()}
        />
      ) : (
        <Card className="p-6 space-y-6">
          <CardHeader className="p-0">
            <CardTitle className="text-lg">Examination Metadata</CardTitle>
            <CardDescription>Clinical analysis session log details</CardDescription>
          </CardHeader>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">History Identifier</span>
              <p className="font-mono text-sm font-semibold text-neutral-900 dark:text-dark-text">{detail.analysis.id}</p>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Segmentation Status</span>
              <div>
                <Badge variant="default">{segmentationLabel(detail)}</Badge>
              </div>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">File Name</span>
              <p className="text-neutral-800 dark:text-dark-text font-semibold">{detail.analysis.original_filename ?? '-'}</p>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Model Framework</span>
              <p className="text-neutral-800 dark:text-dark-text font-semibold">
                {detail.model?.architecture ?? 'U-Net'} ({detail.model?.version ?? 'Scenario 1 Ver.22'})
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-neutral-100 dark:border-dark-border flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs text-neutral-500 dark:text-dark-textMuted">
              Direct access to segmentation visualization for this ID:
            </span>
            <Link to={`/analysis/${id}`}>
              <Button variant="accent" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Open /analysis/{id}
              </Button>
            </Link>
          </div>
        </Card>
      )}

      <Modal
        isOpen={isConfirmOpen}
        onClose={() => {
          if (!isDeleting) {
            setIsConfirmOpen(false);
            setDeleteError(null);
          }
        }}
        title="Delete history record?"
        description="This action will delete the analysis results and all associated images. This cannot be undone."
      >
        <div className="space-y-4">
          {deleteError && (
            <div role="alert" className="p-3 rounded-md border border-semantic-error/30 bg-semantic-error/5 text-xs text-neutral-700 dark:text-neutral-300">
              {deleteError}
            </div>
          )}
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsConfirmOpen(false);
                setDeleteError(null);
              }}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => void confirmDelete()}
              isLoading={isDeleting}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
            >
              Yes, Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default HistoryDetail;
