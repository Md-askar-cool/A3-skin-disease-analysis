// ============================================================
// SafeSkin AI – QualityReport Component
// Animated quality score ring + check items
// ============================================================
import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle, RefreshCw, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';
import type { QualityResult, QualityCheck } from '@/types';
import Button from '@/components/ui/Button';

interface QualityReportProps {
  result: QualityResult;
  onProceed?: () => void;
  onRetry?: () => void;
  compact?: boolean;
}

// ── Score Ring (SVG circular progress) ───────────────────────
const ScoreRing: React.FC<{ score: number; status: QualityResult['status'] }> = ({
  score,
  status,
}) => {
  const circumference = 2 * Math.PI * 50; // r=50
  const offset = circumference - (score / 100) * circumference;
  const circleRef = useRef<SVGCircleElement>(null);

  const strokeColor =
    status === 'good' ? '#10B981' : status === 'acceptable' ? '#F59E0B' : '#EF4444';

  useEffect(() => {
    if (!circleRef.current) return;
    circleRef.current.style.strokeDashoffset = String(circumference);
    // Animate to target after paint
    const raf = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (circleRef.current) {
          circleRef.current.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)';
          circleRef.current.style.strokeDashoffset = String(offset);
        }
      });
    });
    return () => cancelAnimationFrame(raf);
  }, [circumference, offset]);

  return (
    <div className="relative w-36 h-36">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        {/* Track */}
        <circle cx="60" cy="60" r="50" fill="none" stroke="#e2e8f0" strokeWidth="10" />
        {/* Fill */}
        <circle
          ref={circleRef}
          cx="60"
          cy="60"
          r="50"
          fill="none"
          stroke={strokeColor}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-slate-800">{score}</span>
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          Quality
        </span>
      </div>
    </div>
  );
};

// ── Single check item ─────────────────────────────────────────
const CheckItem: React.FC<{ check: QualityCheck; label: string; index: number }> = ({
  check,
  label,
  index,
}) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.08 + 0.3 }}
    className="flex items-center gap-3"
  >
    {/* Icon */}
    {check.passed ? (
      <CheckCircle size={18} className="text-success-500 shrink-0" />
    ) : (
      <AlertTriangle size={18} className="text-warning-500 shrink-0" />
    )}
    {/* Label + score bar */}
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className={clsx(
          'text-xs font-semibold',
          check.passed ? 'text-success-600' : 'text-warning-600',
        )}>
          {Math.round(check.score * 100)}%
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${check.score * 100}%` }}
          transition={{ delay: index * 0.08 + 0.5, duration: 0.8, ease: 'easeOut' }}
          className={clsx(
            'h-full rounded-full',
            check.passed ? 'bg-success-400' : 'bg-warning-400',
          )}
        />
      </div>
    </div>
  </motion.div>
);

export const QualityReport: React.FC<QualityReportProps> = ({
  result,
  onProceed,
  onRetry,
  compact = false,
}) => {
  const { overall_score, status, checks, message, can_proceed } = result;

  // If compact is true, render a minimal version
  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <ScoreRing score={overall_score} status={status} />
        <div>
          <h4 className="font-medium text-slate-900">Image Quality: {overall_score}/100</h4>
          <p className="text-sm text-slate-500">{message}</p>
        </div>
      </div>
    );
  }

  const statusConfig = {
    good: {
      icon: <CheckCircle size={20} className="text-success-600" />,
      label: 'Excellent Quality',
      bg: 'bg-success-50 border-success-200',
      text: 'text-success-700',
      badgeBg: 'bg-success-100 text-success-700',
    },
    acceptable: {
      icon: <AlertTriangle size={20} className="text-warning-600" />,
      label: 'Acceptable Quality',
      bg: 'bg-warning-50 border-warning-200',
      text: 'text-warning-700',
      badgeBg: 'bg-warning-100 text-warning-700',
    },
    poor: {
      icon: <XCircle size={20} className="text-danger-600" />,
      label: 'Poor Quality',
      bg: 'bg-danger-50 border-danger-200',
      text: 'text-danger-700',
      badgeBg: 'bg-danger-100 text-danger-700',
    },
  }[status];

  const checkLabels: Partial<Record<keyof typeof checks, string>> = {
    brightness: 'Brightness',
    sharpness: 'Sharpness',
    contrast: 'Contrast',
    noise: 'Noise Level',
    artifact: 'Artifact Free',
    resolution: 'Resolution',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* ── Header: status banner ──────────────────────────────── */}
      <div className={clsx(
        'flex items-center gap-3 p-4 rounded-xl border',
        statusConfig.bg,
      )}>
        {statusConfig.icon}
        <div>
          <p className={clsx('font-semibold', statusConfig.text)}>{statusConfig.label}</p>
          <p className={clsx('text-sm mt-0.5', statusConfig.text, 'opacity-80')}>{message}</p>
        </div>
        <span className={clsx('ml-auto text-xs font-bold px-2.5 py-1 rounded-full', statusConfig.badgeBg)}>
          Score: {overall_score}/100
        </span>
      </div>

      {/* ── Score ring + checks ────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center gap-8">
        {/* Score ring */}
        <div className="flex flex-col items-center gap-2 shrink-0">
          <ScoreRing score={overall_score} status={status} />
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            Overall Score
          </p>
        </div>

        {/* Individual checks */}
        <div className="flex-1 w-full space-y-3">
          <p className="text-sm font-semibold text-slate-600 mb-3">Quality Metrics</p>
          {Object.entries(checks).map(([key, check], i) => (
            <CheckItem
              key={key}
              check={check as QualityCheck}
              label={checkLabels[key as keyof typeof checks] ?? key}
              index={i}
            />
          ))}
        </div>
      </div>

      {/* ── Actions ──────────────────────────────────────────────────────── */}
      {(onRetry || (can_proceed && onProceed)) && (
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          {onRetry && (
            <Button
              variant="ghost"
              icon={<RefreshCw size={16} />}
              onClick={onRetry}
              className="flex-1"
            >
              Upload Different Image
            </Button>
          )}

          {can_proceed && onProceed && (
            <Button
              variant="primary"
              size="lg"
              iconRight={<ArrowRight size={18} />}
              onClick={onProceed}
              className="flex-1"
            >
              {status === 'acceptable' ? 'Proceed Anyway' : 'Continue to Analysis'}
            </Button>
          )}
        </div>
      )}

      {/* Poor quality note */}
      {!can_proceed && (
        <p className="text-xs text-center text-slate-500 bg-slate-50 rounded-xl p-3">
          Image quality is too low for reliable AI analysis. Please retake the photo with better
          lighting and focus, ensuring the lesion is clearly visible.
        </p>
      )}
    </motion.div>
  );
};

export default QualityReport;
