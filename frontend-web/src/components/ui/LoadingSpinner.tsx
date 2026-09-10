// ============================================================
// SafeSkin AI – LoadingSpinner Component
// Animated spinner with optional label text
// ============================================================
import React from 'react';
import { clsx } from 'clsx';

export interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'white' | 'slate';
  text?: string;
  fullPage?: boolean;
  className?: string;
}

const sizeMap = {
  xs: { spinner: 'w-4 h-4 border-2', text: 'text-xs' },
  sm: { spinner: 'w-6 h-6 border-2', text: 'text-sm' },
  md: { spinner: 'w-8 h-8 border-[3px]', text: 'text-sm' },
  lg: { spinner: 'w-12 h-12 border-4', text: 'text-base' },
  xl: { spinner: 'w-16 h-16 border-4', text: 'text-lg' },
};

const colorMap = {
  primary: 'border-primary-200 border-t-primary-600',
  secondary: 'border-secondary-200 border-t-secondary-600',
  white: 'border-white/30 border-t-white',
  slate: 'border-slate-200 border-t-slate-600',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'primary',
  text,
  fullPage = false,
  className,
}) => {
  const { spinner: spinnerSize, text: textSize } = sizeMap[size];

  const content = (
    <div
      className={clsx(
        'flex flex-col items-center justify-center gap-3',
        className,
      )}
    >
      {/* Spinner ring */}
      <div className="relative">
        <div
          className={clsx(
            'rounded-full animate-spin',
            spinnerSize,
            colorMap[color],
          )}
        />
        {/* Glow effect for primary */}
        {color === 'primary' && (
          <div
            className={clsx(
              'absolute inset-0 rounded-full opacity-30 animate-ping',
              'border border-primary-400',
            )}
          />
        )}
      </div>

      {/* Optional text */}
      {text && (
        <p
          className={clsx(
            'font-medium animate-pulse',
            textSize,
            color === 'white' ? 'text-white/80' : 'text-slate-500',
          )}
        >
          {text}
        </p>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
};

export default LoadingSpinner;
