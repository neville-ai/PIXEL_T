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

/**
 * Error bawaan server yang membawa `code` kontrak (mis. `QUEUE_FULL` pada
 * HTTP 429 — APIContract §12). Tetap sebuah `Error` sehingga penanganan
 * `instanceof Error` yang sudah ada tetap berlaku; `code` bersifat opsional
 * bagi pemanggil yang ingin membedakan penyebab.
 */
export class ApiRequestError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
  }
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
    /**
     * Fase progres dari backend (APIContract §12 — vocabulary P-03:
     * `preprocessing`, `inference`, `postprocessing`, `gradcam`,
     * `artifact_composition`, `uploading_results`, `completed`). Hanya
     * disertakan ketika backend benar-benar mengisinya; tidak pernah dibuat.
     */
    current_step?: string;
    /**
     * Pekerjaan nyata yang selesai dalam persen (integer 0–100,
     * APIContract §12). Hanya disertakan ketika tersedia; 100 hanya ditulis
     * bersama status `completed`.
     */
    progress_percent?: number;
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
  // Get the current session. Supabase client with autoRefreshToken: true
  // will automatically refresh the access token if needed.
  const { data: { session }, error: sessionError } = await supabase.auth.getSession();
  if (sessionError || !session?.access_token) {
    // No valid session - user needs to log in again
    throw new Error('Sesi Anda telah berakhir. Silakan masuk kembali.');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
      Authorization: `Bearer ${session.access_token}`,
    },
  });

  // Handle 401 Unauthorized - token expired or invalid
  if (response.status === 401) {
    // Try to refresh the session one more time
    const { data: { session: refreshedSession }, error: refreshError } = await supabase.auth.refreshSession();
    if (refreshError || !refreshedSession?.access_token) {
      throw new Error('Sesi Anda telah berakhir. Silakan masuk kembali.');
    }

    // Retry the request with the refreshed token
    const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        ...init?.headers,
        Authorization: `Bearer ${refreshedSession.access_token}`,
      },
    });

    if (!retryResponse.ok) {
      // If retry also fails, session is truly invalid
      throw new Error('Sesi Anda telah berakhir. Silakan masuk kembali.');
    }

    let payload: ApiResponse<T>;
    try {
      payload = await retryResponse.json() as ApiResponse<T>;
    } catch {
      throw new Error('Server mengembalikan respons yang tidak dapat dibaca.');
    }

    const expectData = options?.expectData ?? true;
    if (!payload.success || (expectData && payload.data === undefined)) {
      throw new ApiRequestError(
        payload.error?.code ?? 'REQUEST_FAILED',
        payload.error?.message || 'Permintaan analisis gagal. Silakan coba lagi.',
      );
    }

    return payload.data as T;
  }

  let payload: ApiResponse<T>;
  try {
    payload = await response.json() as ApiResponse<T>;
  } catch {
    throw new Error('Server mengembalikan respons yang tidak dapat dibaca.');
  }

  const expectData = options?.expectData ?? true;
  if (!response.ok || !payload.success || (expectData && payload.data === undefined)) {
    // Kode error kontrak dibawa apa adanya (mis. QUEUE_FULL/429, §12) agar
    // pemanggil dapat menjelaskan penyebabnya kepada pengguna.
    throw new ApiRequestError(
      payload.error?.code ?? 'REQUEST_FAILED',
      payload.error?.message || 'Permintaan analisis gagal. Silakan coba lagi.',
    );
  }

  return payload.data as T;
}

/**
 * POST /api/analysis.
 *
 * Backend menjawab **HTTP 202 Accepted** berisi `analysis_id` stabil dan
 * `status: "processing"` SEBELUM pipeline AI selesai (APIContract §12).
 * Penerimaan bukan penyelesaian: pekerjaan hanya dinyatakan selesai ketika
 * polling `getAnalysis` mengembalikan status terminal `completed`.
 * HTTP 429 `QUEUE_FULL` dilempar sebagai `ApiRequestError` ber-code
 * `QUEUE_FULL` dengan pesan dari kontrak.
 */
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
