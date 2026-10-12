import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[50vh] px-4">
      <Card className="max-w-md w-full text-center p-8 space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-neutral-100 dark:bg-dark-elevated flex items-center justify-center text-primary-900 dark:text-accent-500">
          <FileQuestion className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-accent-600 dark:text-accent-500">
            Error 404
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Halaman Tidak Ditemukan
          </h1>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted leading-relaxed">
            Halaman yang Anda tuju tidak tersedia atau tautan yang dimasukkan salah. Silakan kembali ke menu utama.
          </p>
        </div>

        <div className="pt-2">
          <Link to="/dashboard">
            <Button variant="primary" size="md" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Kembali ke Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default NotFound;
