// ============================================================
// SafeSkin AI – ResultCard Component
// Individual result card with animated entrance
// ============================================================
import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

export interface ResultCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  colorScheme?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral' | 'secondary';
  delay?: number;          // animation stagger delay
  size?: 'normal' | 'large';
  badge?: React.ReactNode;
  className?: string;
}

const colorSchemeMap = {
  primary: {
    header: 'bg-gradient-to-r from-primary-500 to-primary-600',
    icon: 'bg-primary-100 text-primary-600',
    border: 'border-primary-100',
    accent: 'bg-primary-50',
  },
  secondary: {
    header: 'bg-gradient-to-r from-secondary-500 to-secondary-600',
    icon: 'bg-secondary-100 text-secondary-600',
    border: 'border-secondary-100',
    accent: 'bg-secondary-50',
  },
  success: {
    header: 'bg-gradient-to-r from-success-500 to-success-600',
    icon: 'bg-success-100 text-success-600',
    border: 'border-success-100',
    accent: 'bg-success-50',
  },
  warning: {
    header: 'bg-gradient-to-r from-warning-500 to-warning-600',
    icon: 'bg-warning-100 text-warning-600',
    border: 'border-warning-100',
    accent: 'bg-warning-50',
  },
  danger: {
    header: 'bg-gradient-to-r from-danger-500 to-danger-600',
    icon: 'bg-danger-100 text-danger-600',
    border: 'border-danger-100',
    accent: 'bg-danger-50',
  },
  neutral: {
    header: 'bg-gradient-to-r from-slate-500 to-slate-600',
    icon: 'bg-slate-100 text-slate-600',
    border: 'border-slate-100',
    accent: 'bg-slate-50',
  },
};

export const ResultCard: React.FC<ResultCardProps> = ({
  title,
  icon,
  children,
  colorScheme = 'primary',
  delay = 0,
  size = 'normal',
  badge,
  className,
}) => {
  const colors = colorSchemeMap[colorScheme];

  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay,
        duration: 0.5,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={clsx(
        'rounded-2xl border overflow-hidden shadow-card',
        'bg-white dark:bg-slate-900',
        colors.border,
        size === 'large' && 'col-span-full md:col-span-2',
        className,
      )}
    >
      {/* Colored header bar */}
      <div className={clsx('px-5 py-3.5 flex items-center justify-between', colors.header)}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center text-white">
            {icon}
          </div>
          <h3 className="text-sm font-semibold text-white">{title}</h3>
        </div>
        {badge && <div>{badge}</div>}
      </div>

      {/* Body */}
      <div className="p-5">{children}</div>
    </motion.div>
  );
};

export default ResultCard;
