import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { PlusCircle, History as HistoryIcon, Activity, ArrowRight } from 'lucide-react';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Top Greeting & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 dark:border-dark-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="accent">Dashboard Klinis</Badge>
            <Badge variant="default">Routing Foundation</Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Sistem Analisis Citra Polip Endoskopi
          </h1>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted max-w-2xl leading-relaxed">
            Platform berbasis web untuk segmentasi polip (U-Net + ResNet50) dan penjelasan visual Grad-CAM.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/analysis/new">
            <Button
              variant="primary"
              size="md"
              leftIcon={<PlusCircle className="w-4 h-4" />}
            >
              Analisis Baru
            </Button>
          </Link>
          <Link to="/history">
            <Button
              variant="outline"
              size="md"
              leftIcon={<HistoryIcon className="w-4 h-4" />}
            >
              Riwayat
            </Button>
          </Link>
        </div>
      </div>

      {/* Feature & Workflow Quick Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card className="p-5 space-y-3">
          <div className="w-10 h-10 rounded-md bg-primary-100 dark:bg-dark-elevated text-primary-900 dark:text-accent-500 flex items-center justify-center">
            <PlusCircle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900 dark:text-dark-text">
              Pemeriksaan Citra Baru
            </h2>
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted mt-1">
              Unggah citra kolonoskopi tunggal untuk inferensi segmentasi polip usus.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/analysis/new" className="inline-flex items-center text-xs font-medium text-accent-600 dark:text-accent-500 hover:underline gap-1">
              Buka New Analysis <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </Card>

        <Card className="p-5 space-y-3">
          <div className="w-10 h-10 rounded-md bg-accent-50 dark:bg-dark-elevated text-accent-600 dark:text-accent-500 flex items-center justify-center">
            <HistoryIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900 dark:text-dark-text">
              Riwayat Analisis
            </h2>
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted mt-1">
              Telusuri arsip pemeriksaan sebelumnya beserta visualisasi Grad-CAM.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/history" className="inline-flex items-center text-xs font-medium text-accent-600 dark:text-accent-500 hover:underline gap-1">
              Buka Riwayat <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </Card>

        <Card className="p-5 space-y-3">
          <div className="w-10 h-10 rounded-md bg-neutral-100 dark:bg-dark-elevated text-neutral-700 dark:text-neutral-300 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900 dark:text-dark-text">
              Integritas &amp; Prinsip Medis
            </h2>
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted mt-1">
              Explainability first: keluaran AI difokuskan sebagai second-opinion non-diagnostik.
            </p>
          </div>
          <div className="pt-2">
            <span className="text-xs text-neutral-500 dark:text-neutral-400">
              U-Net + ResNet50 &amp; Grad-CAM
            </span>
          </div>
        </Card>
      </div>

      {/* Recent Analyses Section (Routing Foundation State) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-neutral-900 dark:text-dark-text">
              Pemeriksaan Terkini
            </h2>
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
              Daftar sesi analisis citra kolonoskopi yang baru diproses
            </p>
          </div>
          <Link to="/history" className="text-xs font-medium text-accent-600 dark:text-accent-500 hover:underline">
            Lihat Semua
          </Link>
        </div>

        <Card className="p-8">
          <EmptyState
            title="Belum Ada Analisis Terkini"
            description="Mulai pemeriksaan baru dengan memilih citra endoskopi polip usus pada halaman New Analysis."
            action={
              <Link to="/analysis/new">
                <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-4 h-4" />}>
                  Mulai Analisis Baru
                </Button>
              </Link>
            }
          />
        </Card>
      </section>
    </div>
  );
};

export default Dashboard;
