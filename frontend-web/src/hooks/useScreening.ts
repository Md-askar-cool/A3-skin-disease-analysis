// ============================================================
// SafeSkin AI – useScreening Hook
// State machine for the full screening flow
// ============================================================
import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { uploadImage, checkQuality, analyzeImage } from '@/lib/api';
import type { QualityResult, ScreeningResult, ScreeningState } from '@/types';

interface ScreeningHookState {
  // Current file & preview
  file: File | null;
  preview: string | null;
  imageId: string | null;

  // State machine
  screeningState: ScreeningState;

  // Results
  qualityResult: QualityResult | null;
  screeningResult: ScreeningResult | null;

  // Error
  error: string | null;

  // Upload progress 0-100
  uploadProgress: number;
}

interface ScreeningHookActions {
  setFile: (file: File | null) => void;
  startScreening: () => Promise<void>;
  reset: () => void;
  retryFromQuality: () => Promise<void>;
  proceedDespiteUncertain: () => void;
}

export type UseScreeningReturn = ScreeningHookState & ScreeningHookActions;

const initialState: ScreeningHookState = {
  file: null,
  preview: null,
  imageId: null,
  screeningState: 'upload',
  qualityResult: null,
  screeningResult: null,
  error: null,
  uploadProgress: 0,
};

/**
 * Manages the full SafeSkin screening state machine:
 * upload → uploading → quality → analyzing → results | uncertain | poor_quality | error
 */
export function useScreening(): UseScreeningReturn {
  const [state, setState] = useState<ScreeningHookState>(initialState);

  // ── Set file & generate preview ──────────────────────────────
  const setFile = useCallback((file: File | null) => {
    if (!file) {
      setState((s) => ({ ...s, file: null, preview: null }));
      return;
    }

    // Validate type
    if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
      toast.error('Please upload a JPEG or PNG image.');
      return;
    }

    // Validate size (10 MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Image must be smaller than 10 MB.');
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    setState((s) => ({
      ...s,
      file,
      preview: objectUrl,
      screeningState: 'upload',
      qualityResult: null,
      screeningResult: null,
      error: null,
    }));
  }, []);

  // ── Main screening pipeline ──────────────────────────────────
  const startScreening = useCallback(async () => {
    const { file } = state;
    if (!file) {
      toast.error('Please select an image first.');
      return;
    }

    try {
      // ── Stage 1: Uploading ────────────────────────────────────
      setState((s) => ({ ...s, screeningState: 'uploading', error: null, uploadProgress: 0 }));

      let imageId: string;
      try {
        const uploaded = await uploadImage(file);
        imageId = uploaded.image_id;
        setState((s) => ({ ...s, imageId, uploadProgress: 100 }));
      } catch {
        setState((s) => ({
          ...s,
          screeningState: 'error',
          error: 'Failed to upload image. Please check your connection and try again.',
        }));
        toast.error('Upload failed');
        return;
      }

      // ── Stage 2: Quality check ────────────────────────────────
      setState((s) => ({ ...s, screeningState: 'quality' }));

      let quality: QualityResult;
      try {
        quality = await checkQuality(imageId);
        setState((s) => ({ ...s, qualityResult: quality }));
      } catch {
        setState((s) => ({
          ...s,
          screeningState: 'error',
          error: 'Quality check failed. Please try again.',
        }));
        toast.error('Quality check failed');
        return;
      }

      if (!quality.can_proceed) {
        setState((s) => ({ ...s, screeningState: 'poor_quality' }));
        return;
      }

      // ── Stage 3: AI analysis ──────────────────────────────────
      setState((s) => ({ ...s, screeningState: 'analyzing' }));

      let screening: ScreeningResult;
      try {
        screening = await analyzeImage(imageId);
        setState((s) => ({ ...s, screeningResult: screening }));
      } catch {
        setState((s) => ({
          ...s,
          screeningState: 'error',
          error: 'Analysis failed. Please try again later.',
        }));
        toast.error('Analysis failed');
        return;
      }

      // ── Determine outcome ─────────────────────────────────────
      if (screening.label === 'uncertain' || screening.confidence < 0.6) {
        setState((s) => ({ ...s, screeningState: 'uncertain' }));
      } else {
        setState((s) => ({ ...s, screeningState: 'results' }));
        toast.success('Analysis complete!');
      }
    } catch (err) {
      console.error('[screening] Unexpected error:', err);
      setState((s) => ({
        ...s,
        screeningState: 'error',
        error: 'An unexpected error occurred. Please try again.',
      }));
    }
  }, [state]);

  // ── Reset to initial state ───────────────────────────────────
  const reset = useCallback(() => {
    // Revoke object URL to prevent memory leaks
    if (state.preview) URL.revokeObjectURL(state.preview);
    setState(initialState);
  }, [state.preview]);

  // ── Retry after poor quality ─────────────────────────────────
  const retryFromQuality = useCallback(async () => {
    reset();
  }, [reset]);

  // ── Proceed despite uncertain result ─────────────────────────
  const proceedDespiteUncertain = useCallback(() => {
    setState((s) => ({ ...s, screeningState: 'results' }));
  }, []);

  return {
    ...state,
    setFile,
    startScreening,
    reset,
    retryFromQuality,
    proceedDespiteUncertain,
  };
}

export default useScreening;
