import { supabase } from '@/lib/supabase';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'
).replace(/\/$/, '');

interface ApiError {
  code: string;
  message: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

export interface CreatedAnalysis {
  analysis_id: string;
  status: AnalysisStatus;
}

export type AnalysisStatus = 'processing' | 'completed' | 'failed';

export interface AnalysisDetail {
  analysis: {
    id: string;
    status: AnalysisStatus;
    created_at: string | null;
    completed_at?: string | null;
    original_filename: string | null;
    error_code?: string | null;
    error_message?: string | null;
  };
  input: {
    original_image_url?: string | null;
    width: number | null;
    height: number | null;
    mime_type: string | null;
  };
  segmentation?: {
    binary_mask_url?: string | null;
    overlay_url?: string | null;
  };
  gradcam?: {
    heatmap_url?: string | null;
    overlay_url?: string | null;
  };
  model_analysis?: {
    segmentation_status?: 'detected' | 'not_detected' | null;
    area_pixels?: number | null;
    area_ratio?: number | null;
    bounding_width_pixels?: number | null;
    bounding_height_pixels?: number | null;
  };
  model?: {
    architecture?: string | null;
    version?: string | null;
  };
  summary?: {
    text?: string | null;
  };
}

async function authenticatedRequest<T>(
  path: string,
  init?: RequestInit,
  options?: { expectData?: boolean },
): Promise<T> {
  const { data, error } = await supabase.auth.getSession();
  const accessToken = data.session?.access_token;
  if (error || !accessToken) {
    throw new Error('Sesi Anda telah berakhir. Silakan masuk kembali.');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
      Authorization: `Bearer ${accessToken}`,
    },
  });

  let payload: ApiResponse<T>;
  try {
    payload = await response.json() as ApiResponse<T>;
  } catch {
    throw new Error('Server mengembalikan respons yang tidak dapat dibaca.');
  }

  const expectData = options?.expectData ?? true;
  if (!response.ok || !payload.success || (expectData && payload.data === undefined)) {
    throw new Error(payload.error?.message || 'Permintaan analisis gagal. Silakan coba lagi.');
  }

  return payload.data as T;
}

export function createAnalysis(file: File): Promise<CreatedAnalysis> {
  const formData = new FormData();
  formData.append('image', file);
  return authenticatedRequest<CreatedAnalysis>('/analysis', {
    method: 'POST',
    body: formData,
  });
}

export function getAnalysis(id: string): Promise<AnalysisDetail> {
  return authenticatedRequest<AnalysisDetail>(`/analysis/${encodeURIComponent(id)}`);
}

export interface HistoryItem {
  id: string;
  created_at: string | null;
  completed_at?: string | null;
  status: AnalysisStatus;
  original_filename: string | null;
  thumbnail_url?: string | null;
  segmentation_status?: 'detected' | 'not_detected' | null;
}

export interface HistoryList {
  items: HistoryItem[];
}

export function listHistory(): Promise<HistoryList> {
  return authenticatedRequest<HistoryList>('/history', {
    method: 'GET',
  });
}

export function deleteAnalysis(id: string): Promise<void> {
  // DELETE /api/history/<id> returns { success, message } with no `data`
  // field (APIContract §21), so `expectData` is disabled for this call.
  return authenticatedRequest<void>(`/history/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  }, { expectData: false });
}
