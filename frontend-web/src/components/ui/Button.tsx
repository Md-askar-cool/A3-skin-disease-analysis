// ============================================================
// SafeSkin AI – Button Component
// Variants: primary | secondary | outline | ghost | danger
// Sizes: sm | md | lg
// ============================================================
import React from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const variantStyles: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: [
    'bg-gradient-to-r from-primary-500 to-primary-600',
    'text-white shadow-md hover:shadow-lg hover:shadow-primary-500/25',
    'hover:from-primary-600 hover:to-primary-700',
    'active:from-primary-700 active:to-primary-800',
    'disabled:from-primary-300 disabled:to-primary-300',
    'border border-primary-500/20',
  ].join(' '),

  secondary: [
    'bg-gradient-to-r from-secondary-500 to-secondary-600',
    'text-white shadow-md hover:shadow-lg hover:shadow-secondary-500/25',
    'hover:from-secondary-600 hover:to-secondary-700',
    'active:from-secondary-700 active:to-secondary-800',
    'disabled:from-secondary-300 disabled:to-secondary-300',
    'border border-secondary-500/20',
  ].join(' '),

  outline: [
    'bg-white/80 backdrop-blur-sm',
    'text-primary-600 border-2 border-primary-500',
    'hover:bg-primary-50 hover:border-primary-600',
    'active:bg-primary-100',
    'disabled:border-primary-200 disabled:text-primary-300',
  ].join(' '),

  ghost: [
    'bg-transparent text-slate-600',
    'hover:bg-slate-100 hover:text-slate-800',
    'active:bg-slate-200',
    'disabled:text-slate-300',
  ].join(' '),

  danger: [
    'bg-gradient-to-r from-danger-500 to-danger-600',
    'text-white shadow-md hover:shadow-lg hover:shadow-danger-500/25',
    'hover:from-danger-600 hover:to-danger-700',
    'active:from-danger-700 active:to-danger-800',
    'disabled:from-danger-300 disabled:to-danger-300',
    'border border-danger-500/20',
  ].join(' '),

  success: [
    'bg-gradient-to-r from-success-500 to-success-600',
    'text-white shadow-md hover:shadow-lg hover:shadow-success-500/25',
    'hover:from-success-600 hover:to-success-700',
    'disabled:from-success-300 disabled:to-success-300',
  ].join(' '),
};

const sizeStyles: Record<NonNullable<ButtonProps['size']>, string> = {
  xs: 'px-2.5 py-1 text-xs rounded-lg gap-1',
  sm: 'px-3.5 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-xl gap-2',
  xl: 'px-8 py-4 text-lg rounded-2xl gap-2.5',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      iconRight,
      fullWidth = false,
      className,
      disabled,
      children,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={clsx(
          // Base
          'inline-flex items-center justify-center font-semibold',
          'transition-all duration-200 ease-in-out',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
          'select-none cursor-pointer',
          'disabled:cursor-not-allowed disabled:opacity-60',
          // Variant
          variantStyles[variant],
          // Size
          sizeStyles[size],
          // Full width
          fullWidth && 'w-full',
          className,
        )}
        {...props}
      >
        {/* Left icon / loading spinner */}
        {loading ? (
          <Loader2 className="animate-spin shrink-0" size={size === 'xl' ? 22 : size === 'lg' ? 20 : 16} />
        ) : icon ? (
          <span className="shrink-0">{icon}</span>
        ) : null}

        {/* Label */}
        <span>{children}</span>

        {/* Right icon */}
        {!loading && iconRight && <span className="shrink-0">{iconRight}</span>}
      </button>
    );
  },
);

Button.displayName = 'Button';
export default Button;
