import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'sky' | 'teal' | 'navy' | 'amber' | 'emerald' | 'rose' | 'purple';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
}) => {
  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200/60',
    sky: 'bg-sky-50 text-sky-700 border border-sky-200/80',
    teal: 'bg-teal-50 text-teal-700 border border-teal-200/80',
    navy: 'bg-slate-900 text-slate-100 border border-slate-800',
    amber: 'bg-amber-50 text-amber-700 border border-amber-200/80',
    emerald: 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
    rose: 'bg-rose-50 text-rose-700 border border-rose-200/80',
    purple: 'bg-purple-50 text-purple-700 border border-purple-200/80',
  };

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-0.5 font-medium',
    md: 'text-xs px-3 py-1 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};

export default Badge;
