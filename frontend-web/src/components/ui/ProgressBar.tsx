// ============================================================
// SafeSkin AI – ProgressBar Component
// Animated horizontal progress bar for quality & confidence
// ============================================================
import React, { useEffect, useRef } from 'react';
import { clsx } from 'clsx';

export interface ProgressBarProps {
  value: number;            // 0–100
  max?: number;
  label?: string;
  showValue?: boolean;
  valueFormat?: 'percent' | 'fraction' | 'raw';
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'auto';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  animated?: boolean;       // Animate fill on mount
  striped?: boolean;
  className?: string;
}

const sizeMap = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
};

/**
 * Returns a fill color based on the value (for 'auto' color).
 * 0–40: danger, 41–70: warning, 71–100: success
 */
function getAutoColor(value: number): string {
  if (value >= 71) return 'from-success-400 to-success-500';
  if (value >= 41) return 'from-warning-400 to-warning-500';
  return 'from-danger-400 to-danger-500';
}

const colorMap: Record<string, string> = {
  primary: 'from-primary-400 to-primary-600',
  success: 'from-success-400 to-success-500',
  warning: 'from-warning-400 to-warning-500',
  danger: 'from-danger-400 to-danger-500',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showValue = false,
  valueFormat = 'percent',
  color = 'auto',
  size = 'md',
  animated = true,
  striped = false,
  className,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const fillRef = useRef<HTMLDivElement>(null);

  // Animate fill width on mount
  useEffect(() => {
    if (!animated || !fillRef.current) return;
    fillRef.current.style.width = '0%';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (fillRef.current) {
          fillRef.current.style.width = `${percentage}%`;
        }
      });
    });
  }, [percentage, animated]);

  const fillColor = color === 'auto' ? getAutoColor(percentage) : colorMap[color];

  const displayValue = (() => {
    switch (valueFormat) {
      case 'fraction': return `${value}/${max}`;
      case 'raw': return String(value);
      default: return `${Math.round(percentage)}%`;
    }
  })();

  return (
    <div className={clsx('w-full', className)}>
      {/* Header: label + optional value */}
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              {displayValue}
            </span>
          )}
        </div>
      )}

      {/* Track */}
      <div
        className={clsx(
          'w-full rounded-full overflow-hidden',
          'bg-slate-100 dark:bg-slate-800',
          sizeMap[size],
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        {/* Fill */}
        <div
          ref={fillRef}
          style={animated ? { width: '0%', transition: 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)' } : { width: `${percentage}%` }}
          className={clsx(
            'h-full rounded-full bg-gradient-to-r',
            fillColor,
            striped && [
              'relative overflow-hidden',
              'after:absolute after:inset-0',
              'after:bg-[length:1rem_1rem]',
              'after:bg-gradient-to-r after:from-white/20 after:to-transparent',
            ],
          )}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
