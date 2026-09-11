// ============================================================
// SafeSkin AI – Axios API Client
// Typed API functions for all backend endpoints
// ============================================================
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type {
  AdminMetrics,
  PaginatedHistory,
  ProgressComparison,
  ProgressImage,
  QualityResult,
  ScreeningResult,
  UploadResponse,
} from '@/types';
import { supabase } from './supabase';

// ── Axios instance ────────────────────────────────────────────
export const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000',
  timeout: 60_000, // 60 s – AI inference can be slow
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Request interceptor: attach Supabase JWT ─────────────────
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
      }
    } catch {
      // No session – public endpoint or user not logged in
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor: normalize errors ───────────────────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;

    // Token expired – refresh and retry once
    if (status === 401) {
      try {
        const { data } = await supabase.auth.refreshSession();
        if (data.session && error.config) {
          error.config.headers.Authorization = `Bearer ${data.session.access_token}`;
          return api.request(error.config);
        }
      } catch {
        // Refresh failed – sign out
        await supabase.auth.signOut();
        window.location.href = '/login';
      }
    }

    // Build a clean error object
    const message =
      (error.response?.data as Record<string, string>)?.detail ??
      (error.response?.data as Record<string, string>)?.message ??
      error.message ??
      'An unexpected error occurred';

    return Promise.reject({
      status,
      message,
      detail: error.response?.data,
    });
  },
);

// ============================================================
// API Functions
// ============================================================

// ── Upload image ──────────────────────────────────────────────
/**
 * Uploads an image file to the backend and returns a storage path.
 * Uses multipart/form-data.
 */
export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);

  const { data } = await api.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      // Caller can track progress via axios config if needed
      console.debug(`[upload] ${Math.round((e.loaded / (e.total ?? 1)) * 100)}%`);
    },
  });
  return data;
}

// ── Analyze image ──────────────────────────────────────────────
/**
 * Runs the full AI pipeline on an already-uploaded image.
 */
export async function analyzeImage(storagePath: string): Promise<ScreeningResult> {
  const { data } = await api.post<ScreeningResult>('/analyze-image', {
    image_path: storagePath,
  });
  return data;
}

// ── Full pipeline: upload + analyze ──────────────────────────
/**
 * Convenience function: upload + analyze in sequence.
 * Callers can pass callbacks for each stage.
 */
export async function runFullScreening(
  file: File,
  onStage?: (stage: 'uploading' | 'analyzing') => void,
): Promise<{ screening: ScreeningResult }> {
  onStage?.('uploading');
  const uploaded = await uploadImage(file);
  onStage?.('analyzing');
  const screening = await analyzeImage(uploaded.storage_path);
  return { screening };
}

// ── Screening history ─────────────────────────────────────────
export async function getScreeningHistory(
  page = 1,
  perPage = 10,
): Promise<PaginatedHistory> {
  const { data } = await api.get<PaginatedHistory>('/screenings', {
    params: { page, per_page: perPage },
  });
  return data;
}

export async function getScreening(id: string): Promise<ScreeningResult> {
  const { data } = await api.get<ScreeningResult>(`/screenings/${id}`);
  return data;
}

export async function deleteScreening(id: string): Promise<void> {
  await api.delete(`/screenings/${id}`);
}

// ── Progress tracking ─────────────────────────────────────────
export async function getProgress(): Promise<ProgressImage[]> {
  const { data } = await api.get<ProgressImage[]>('/progress');
  return data;
}

export interface AddProgressPayload {
  file: File;
  notes?: string;
  body_location?: string;
  screening_id?: string;
}

export async function addProgress(payload: AddProgressPayload): Promise<ProgressImage> {
  const form = new FormData();
  form.append('file', payload.file);
  if (payload.notes) form.append('notes', payload.notes);
  if (payload.body_location) form.append('body_location', payload.body_location);
  if (payload.screening_id) form.append('screening_id', payload.screening_id);

  const { data } = await api.post<ProgressImage>('/progress', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function deleteProgressEntry(id: string): Promise<void> {
  await api.delete(`/progress/${id}`);
}

// ── Image comparison ──────────────────────────────────────────
export async function compareImages(
  imageAId: string,
  imageBId: string,
): Promise<ProgressComparison> {
  const { data } = await api.post<ProgressComparison>('/progress/compare', {
    image_a_id: imageAId,
    image_b_id: imageBId,
  });
  return data;
}

// ── Admin metrics ─────────────────────────────────────────────
export async function getAdminMetrics(): Promise<AdminMetrics> {
  const { data } = await api.get<AdminMetrics>('/admin/metrics');
  return data;
}

export default api;
