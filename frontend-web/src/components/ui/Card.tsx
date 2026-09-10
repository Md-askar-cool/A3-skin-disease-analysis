// ============================================================
// SafeSkin AI – Card Component
// Glass morphism styled card with optional header & hover
// ============================================================
import React from 'react';
import { clsx } from 'clsx';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  hover?: boolean;
  glass?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  border?: boolean;
  gradient?: boolean;
}

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
  xl: 'p-10',
};

export const Card: React.FC<CardProps> = ({
  children,
  className,
  header,
  footer,
  hover = false,
  glass = false,
  padding = 'md',
  border = true,
  gradient = false,
}) => {
  return (
    <div
      className={clsx(
        'rounded-2xl',
        // Background
        glass
          ? 'bg-white/70 backdrop-blur-md dark:bg-slate-900/70'
          : 'bg-white dark:bg-slate-900',
        // Border
        border && 'border border-slate-100 dark:border-slate-800',
        // Shadow
        'shadow-card',
        // Hover
        hover && [
          'transition-all duration-300 ease-out',
          'hover:-translate-y-1 hover:shadow-card-hover',
          'cursor-pointer',
        ],
        // Gradient background
        gradient && 'bg-gradient-to-br from-white to-primary-50/30',
        className,
      )}
    >
      {/* Header */}
      {header && (
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          {header}
        </div>
      )}

      {/* Body */}
      <div className={paddingStyles[padding]}>{children}</div>

      {/* Footer */}
      {footer && (
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
