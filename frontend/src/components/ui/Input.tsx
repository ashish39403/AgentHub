import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  mono?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, leftIcon, rightIcon, mono = false, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-[#111827] flex items-center justify-between">
            <span>{label}</span>
            {hint && <span className="text-[11px] font-normal text-[#6b7280]">{hint}</span>}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <div className="absolute left-2.5 flex items-center justify-center text-[#6b7280] pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={cn(
              'w-full h-9 rounded-lg bg-white text-[#111827] text-sm placeholder:text-[#9ca3af] border border-[#e5e7eb] transition-all',
              'focus:outline-none focus:border-[#0f766e] focus:ring-1 focus:ring-[#0f766e]',
              'disabled:opacity-50 disabled:bg-[#f9fafb] disabled:cursor-not-allowed',
              leftIcon ? 'pl-8' : 'pl-3',
              rightIcon ? 'pr-8' : 'pr-3',
              mono && 'font-mono text-[13px]',
              error && 'border-[#dc2626] focus:border-[#dc2626] focus:ring-[#dc2626]',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-2.5 flex items-center justify-center text-[#6b7280]">
              {rightIcon}
            </div>
          )}
        </div>
        {error && <span className="text-xs text-[#dc2626]">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
