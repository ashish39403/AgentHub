import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options?: SelectOption[];
  hint?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options = [], hint, children, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label htmlFor={selectId} className="text-xs font-medium text-[#111827] flex items-center justify-between">
            <span>{label}</span>
            {hint && <span className="text-[11px] font-normal text-[#6b7280]">{hint}</span>}
          </label>
        )}
        <div className="relative flex items-center w-full">
          <select
            id={selectId}
            ref={ref}
            className={cn(
              'w-full h-9 pl-3 pr-8 rounded-lg bg-white text-[#111827] text-sm border border-[#e5e7eb] appearance-none cursor-pointer transition-all',
              'focus:outline-none focus:border-[#0f766e] focus:ring-1 focus:ring-[#0f766e]',
              'disabled:opacity-50 disabled:bg-[#f9fafb] disabled:cursor-not-allowed',
              error && 'border-[#dc2626]',
              className
            )}
            {...props}
          >
            {options.length > 0
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <ChevronDown className="w-4 h-4 text-[#6b7280] absolute right-2.5 pointer-events-none" />
        </div>
        {error && <span className="text-xs text-[#dc2626]">{error}</span>}
      </div>
    );
  }
);

Select.displayName = 'Select';
