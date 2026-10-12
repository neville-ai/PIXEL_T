import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { AlertCircle, ArrowLeft, FileCheck2, Image as ImageIcon, UploadCloud, X } from 'lucide-react';
import { createAnalysis } from '@/services/analysis';

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_MIME_TYPES = new Set(['image/jpeg', 'image/png']);

function validateFile(file: File): string | null {
  if (!ALLOWED_MIME_TYPES.has(file.type)) {
    return 'Pilih citra JPEG atau PNG.';
  }
  if (file.size === 0) {
    return 'Berkas citra kosong. Pilih berkas lain.';
  }
  if (file.size > MAX_FILE_SIZE) {
    return 'Ukuran berkas melebihi batas 10 MB.';
  }
  if (
    file.name.includes('..') ||
    /[\\/]/.test(file.name) ||
    /[\u0000-\u001f\u007f]/.test(file.name)
  ) {
    return 'Nama berkas tidak valid.';
  }
  return null;
}

function formatFileSize(size: number): string {
  return size < 1024 * 1024
    ? `${(size / 1024).toFixed(1)} KB`
    : `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

export const NewAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const fileInput = useRef<HTMLInputElement>(null);
  const validationRun = useRef(0);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [validationError, setValidationError] = useState('');
  const [serverError, setServerError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreviewUrl('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const selectFile = async (selectedFile?: File) => {
    setServerError('');
    if (!selectedFile) return;
    const run = ++validationRun.current;
    setFile(null);
    setIsValidating(true);
    let error = validateFile(selectedFile);
    if (!error) {
      try {
        const decoded = await createImageBitmap(selectedFile);
        if (decoded.width <= 0 || decoded.height <= 0) {
          error = 'Dimensi citra tidak valid.';
        }
        decoded.close();
      } catch {
        error = 'Berkas tidak dapat dibaca sebagai citra JPEG atau PNG.';
      }
    }
    if (run !== validationRun.current) return;
    setValidationError(error || '');
    setFile(error ? null : selectedFile);
    setIsValidating(false);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file || isUploading) return;
    setServerError('');
    setIsUploading(true);
    try {
      const created = await createAnalysis(file);
      navigate(`/analysis/${encodeURIComponent(created.analysis_id)}`);
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Unggah citra gagal. Silakan coba lagi.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-7">
      <header className="space-y-3 border-b border-neutral-200 dark:border-dark-border pb-6">
        <Link to="/dashboard" className="inline-flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200">
          <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-dark-text">
            Pemeriksaan Citra Baru
          </h1>
          <Badge variant="accent">Unggah citra</Badge>
        </div>
        <p className="text-sm text-neutral-600 dark:text-dark-textMuted">
          File asli disimpan untuk sesi analisis. Inferensi belum dijalankan pada tahap ini.
        </p>
      </header>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <Card className={`overflow-hidden border-2 border-dashed transition-colors ${isDragging ? 'border-accent-600 bg-accent-50 dark:bg-dark-elevated' : 'border-neutral-300 dark:border-dark-border'}`}>
          <div
            className="p-7 sm:p-10 text-center space-y-4"
            onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setIsDragging(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              void selectFile(event.dataTransfer.files[0]);
            }}
          >
            <input
              ref={fileInput}
              className="sr-only"
              type="file"
              accept="image/jpeg,image/png"
              onChange={(event) => {
                void selectFile(event.currentTarget.files?.[0]);
                event.currentTarget.value = '';
              }}
            />
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary-50 text-primary-900 dark:bg-dark-elevated dark:text-accent-500">
              <UploadCloud className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-dark-text">
                {file ? 'Ganti citra' : 'Pilih citra endoskopi'}
              </h2>
              <p className="text-sm text-neutral-600 dark:text-dark-textMuted">
                Seret berkas ke area ini atau pilih dari perangkat.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              leftIcon={<ImageIcon className="h-4 w-4" />}
              onClick={() => fileInput.current?.click()}
            >
              Pilih berkas
            </Button>
            <p className="text-xs text-neutral-500 dark:text-dark-textMuted">
              JPEG atau PNG · Maksimal 10 MB
            </p>
          </div>

          {file && previewUrl && (
            <div className="grid gap-5 border-t border-neutral-200 bg-neutral-50 p-4 dark:border-dark-border dark:bg-dark-surface sm:grid-cols-[minmax(0,1fr)_220px] sm:p-5">
              <div className="min-w-0 self-center space-y-3">
                <div className="flex items-start gap-3">
                  <FileCheck2 className="mt-0.5 h-5 w-5 shrink-0 text-accent-700 dark:text-accent-500" />
                  <div className="min-w-0 flex-1">
                    <p className="break-all text-sm font-semibold text-neutral-900 dark:text-dark-text">{file.name}</p>
                    <p className="mt-1 text-xs text-neutral-600 dark:text-dark-textMuted">
                      {formatFileSize(file.size)} · {file.type}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label="Hapus citra terpilih"
                    onClick={() => {
                      validationRun.current += 1;
                      setFile(null);
                      setIsValidating(false);
                      setValidationError('');
                      setServerError('');
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <img
                src={previewUrl}
                alt={`Pratinjau ${file.name}`}
                className="max-h-56 w-full rounded-sm border border-neutral-200 bg-black object-contain dark:border-dark-border"
              />
            </div>
          )}
        </Card>

        {validationError && (
          <p role="alert" className="flex items-start gap-2 text-sm text-semantic-error">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {validationError}
          </p>
        )}
        {serverError && (
          <p role="alert" className="flex items-start gap-2 rounded-md border border-semantic-error/30 bg-semantic-error/5 p-3 text-sm text-semantic-error">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {serverError}
          </p>
        )}

        <div className="flex justify-end">
          <Button type="submit" size="md" isLoading={isUploading || isValidating} disabled={!file || isUploading || isValidating}>
            {isUploading ? 'Mengunggah citra...' : isValidating ? 'Memeriksa citra...' : 'Mulai analisis'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default NewAnalysis;
