import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  mono?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, mono = false, id, rows = 3, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-[#111827] flex items-center justify-between">
            <span>{label}</span>
            {hint && <span className="text-[11px] font-normal text-[#6b7280]">{hint}</span>}
          </label>
        )}
        <textarea
          id={inputId}
          ref={ref}
          rows={rows}
          className={cn(
            'w-full rounded-lg bg-white text-[#111827] text-sm placeholder:text-[#9ca3af] border border-[#e5e7eb] p-3 transition-all',
            'focus:outline-none focus:border-[#0f766e] focus:ring-1 focus:ring-[#0f766e]',
            'disabled:opacity-50 disabled:bg-[#f9fafb] disabled:cursor-not-allowed resize-y',
            mono && 'font-mono text-xs leading-relaxed',
            error && 'border-[#dc2626] focus:border-[#dc2626] focus:ring-[#dc2626]',
            className
          )}
          {...props}
        />
        {error && <span className="text-xs text-[#dc2626]">{error}</span>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
