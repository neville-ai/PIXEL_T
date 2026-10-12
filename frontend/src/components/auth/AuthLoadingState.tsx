import React from 'react';
import { LoadingState } from '@/components/ui/LoadingState';

export const AuthLoadingState: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[50vh] px-4">
      <LoadingState
        title="Memulihkan Sesi Pengguna"
        description="Memverifikasi kredensial dan status autentikasi Supabase..."
      />
    </div>
  );
};

export default AuthLoadingState;
