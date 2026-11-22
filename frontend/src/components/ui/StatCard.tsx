import React from 'react';

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: string;
  className?: string;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  sublabel,
  className = '',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`card p-5 flex items-start gap-4 ${
        onClick ? 'cursor-pointer hover:border-slate-300 hover:shadow-md transition-all' : ''
      } ${className}`}
    >
      <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-700 flex-shrink-0">
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-2xl font-bold tracking-tight text-slate-900 truncate">
          {value}
        </div>
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-0.5">
          {label}
        </div>
        {sublabel && (
          <div className="text-xs text-slate-400 mt-1 truncate">
            {sublabel}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
