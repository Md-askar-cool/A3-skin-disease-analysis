// ============================================================
// SafeSkin AI – TypeScript Types
// ============================================================

// ── User ─────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role: 'user' | 'admin' | 'researcher';
  created_at: string;
}

// ── Screening ─────────────────────────────────────────────────
export type ScreeningLabel = 'benign' | 'malignant' | 'uncertain';
export type SeverityLevel = 'low' | 'moderate' | 'high' | 'very_high';
export type ConditionType =
  | 'melanoma'
  | 'basal_cell_carcinoma'
  | 'squamous_cell_carcinoma'
  | 'actinic_keratosis'
  | 'benign_keratosis'
  | 'dermatofibroma'
  | 'nevus'
  | 'vascular_lesion'
  | 'unknown';

export interface ScreeningResult {
  id: string;
  user_id: string;
  image_url: string;
  gradcam_url?: string;
  label: ScreeningLabel;
  condition: ConditionType;
  confidence: number;           // 0–1
  severity: SeverityLevel;
  recommendation: string;
  model_version: string;
  processing_time_ms: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ── Quality ───────────────────────────────────────────────────
export type QualityStatus = 'good' | 'acceptable' | 'poor';

export interface QualityCheck {
  name: string;
  passed: boolean;
  score: number;    // 0–1
  message: string;
}

export interface QualityResult {
  overall_score: number;        // 0–100
  status: QualityStatus;
  checks: {
    brightness: QualityCheck;
    sharpness: QualityCheck;
    contrast: QualityCheck;
    noise: QualityCheck;
    artifact: QualityCheck;
    resolution: QualityCheck;
  };
  message: string;
  can_proceed: boolean;
}

// ── Progress Tracking ─────────────────────────────────────────
export interface ProgressImage {
  id: string;
  user_id: string;
  image_url: string;
  thumbnail_url?: string;
  notes?: string;
  screening_id?: string;        // linked screening if any
  body_location?: string;
  created_at: string;
  metadata: {
    width: number;
    height: number;
    file_size: number;
  };
}

export interface ProgressComparison {
  image_a: ProgressImage;
  image_b: ProgressImage;
  days_between: number;
  visual_notes: string[];       // non-medical visual observations
}

// ── History ───────────────────────────────────────────────────
export interface ScreeningHistoryItem {
  id: string;
  image_url: string;
  thumbnail_url?: string;
  label: ScreeningLabel;
  condition: ConditionType;
  confidence: number;
  severity: SeverityLevel;
  created_at: string;
}

export interface PaginatedHistory {
  items: ScreeningHistoryItem[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// ── Admin / Research ──────────────────────────────────────────
export interface AdminMetrics {
  total_screenings: number;
  total_users: number;
  screenings_today: number;
  screenings_this_week: number;
  average_confidence: number;
  accuracy_estimate: number;
  false_positive_rate: number;
  false_negative_rate: number;
  result_distribution: {
    label: string;
    count: number;
    percentage: number;
  }[];
  condition_distribution: {
    condition: ConditionType;
    count: number;
  }[];
  confidence_distribution: {
    range: string;
    count: number;
  }[];
  confusion_matrix: {
    true_positive: number;
    true_negative: number;
    false_positive: number;
    false_negative: number;
  };
  model_info: {
    version: string;
    architecture: string;
    training_date: string;
    dataset_size: number;
    input_size: string;
    auc_roc: number;
  };
  quality_stats: {
    avg_quality_score: number;
    rejected_for_quality: number;
  };
}

// ── API Response wrappers ─────────────────────────────────────
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

// ── Upload ────────────────────────────────────────────────────
export interface UploadResponse {
  image_id: string;
  image_url: string;
  message: string;
}

// ── Screening state machine ───────────────────────────────────
export type ScreeningState =
  | 'upload'
  | 'uploading'
  | 'quality'
  | 'analyzing'
  | 'results'
  | 'uncertain'
  | 'poor_quality'
  | 'error';

// ── Notification ──────────────────────────────────────────────
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

// ── Theme ─────────────────────────────────────────────────────
export type Theme = 'light' | 'dark' | 'system';
