// ============================================================
// SafeSkin AI – Badge Component
// Colored badges for results, severity, confidence
// ============================================================
import React from 'react';
import { clsx } from 'clsx';

export type BadgeVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'neutral'
  | 'info';

export type BadgeSize = 'xs' | 'sm' | 'md' | 'lg';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;          // Show a colored dot before text
  pill?: boolean;         // Fully rounded vs slightly rounded
  outline?: boolean;      // Outlined style
  icon?: React.ReactNode;
  className?: string;
}

const variantMap: Record<BadgeVariant, { solid: string; outline: string; dot: string }> = {
  primary: {
    solid: 'bg-primary-100 text-primary-700 border-primary-200',
    outline: 'border-2 border-primary-400 text-primary-600 bg-transparent',
    dot: 'bg-primary-500',
  },
  secondary: {
    solid: 'bg-secondary-100 text-secondary-700 border-secondary-200',
    outline: 'border-2 border-secondary-400 text-secondary-600 bg-transparent',
    dot: 'bg-secondary-500',
  },
  success: {
    solid: 'bg-success-50 text-success-700 border-success-200',
    outline: 'border-2 border-success-400 text-success-600 bg-transparent',
    dot: 'bg-success-500',
  },
  warning: {
    solid: 'bg-warning-50 text-warning-700 border-warning-200',
    outline: 'border-2 border-warning-400 text-warning-600 bg-transparent',
    dot: 'bg-warning-500',
  },
  danger: {
    solid: 'bg-danger-50 text-danger-700 border-danger-200',
    outline: 'border-2 border-danger-400 text-danger-600 bg-transparent',
    dot: 'bg-danger-500',
  },
  neutral: {
    solid: 'bg-slate-100 text-slate-600 border-slate-200',
    outline: 'border-2 border-slate-300 text-slate-500 bg-transparent',
    dot: 'bg-slate-400',
  },
  info: {
    solid: 'bg-blue-50 text-blue-700 border-blue-200',
    outline: 'border-2 border-blue-400 text-blue-600 bg-transparent',
    dot: 'bg-blue-500',
  },
};

const sizeMap: Record<BadgeSize, string> = {
  xs: 'text-2xs px-1.5 py-0.5 gap-1',
  sm: 'text-xs px-2 py-0.5 gap-1',
  md: 'text-xs px-2.5 py-1 gap-1.5',
  lg: 'text-sm px-3 py-1 gap-1.5',
};

const dotSizeMap: Record<BadgeSize, string> = {
  xs: 'w-1 h-1',
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2 h-2',
};

/**
 * Helper to get the right badge variant based on screening result
 */
export function getLabelVariant(label: string): BadgeVariant {
  switch (label) {
    case 'benign': return 'success';
    case 'malignant': return 'danger';
    case 'uncertain': return 'warning';
    default: return 'neutral';
  }
}

/**
 * Helper to get badge variant for severity level
 */
export function getSeverityVariant(severity: string): BadgeVariant {
  switch (severity) {
    case 'low': return 'success';
    case 'moderate': return 'warning';
    case 'high': return 'danger';
    case 'very_high': return 'danger';
    default: return 'neutral';
  }
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  pill = true,
  outline = false,
  icon,
  className,
}) => {
  const styles = variantMap[variant];

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium border',
        outline ? styles.outline : styles.solid,
        sizeMap[size],
        pill ? 'rounded-full' : 'rounded-md',
        className,
      )}
    >
      {/* Colored dot */}
      {dot && (
        <span
          className={clsx(
            'rounded-full shrink-0',
            dotSizeMap[size],
            styles.dot,
          )}
        />
      )}
      {/* Icon */}
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </span>
  );
};

export default Badge;
