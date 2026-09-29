import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'surface';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'secondary', size = 'md', isLoading = false, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0f766e]/40 focus-visible:ring-offset-1 disabled:opacity-50 disabled:pointer-events-none cursor-pointer select-none active:translate-y-[0.5px]';

    const variants = {
      primary: 'bg-[#0f766e] hover:bg-[#115e59] text-white shadow-xs',
      secondary: 'bg-[#f3f4f6] hover:bg-[#e5e7eb] text-[#111827] border border-[#e5e7eb] shadow-2xs',
      surface: 'bg-white hover:bg-[#f9fafb] text-[#111827] border border-[#e5e7eb] shadow-2xs',
      outline: 'bg-white border border-[#e5e7eb] text-[#111827] hover:bg-[#f9fafb]',
      ghost: 'bg-transparent hover:bg-[#f3f4f6] text-[#4b5563] hover:text-[#111827]',
      destructive: 'bg-[#dc2626] hover:bg-[#b91c1c] text-white shadow-xs',
    };

    const sizes = {
      sm: 'h-8 px-2.5 text-xs gap-1.5',
      md: 'h-9 px-3.5 text-sm gap-2',
      lg: 'h-10 px-4 text-sm gap-2',
      icon: 'h-8 w-8 p-0 text-sm',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
