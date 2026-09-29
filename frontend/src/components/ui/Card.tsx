import React from 'react';
import { cn } from '../../lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  variant?: 'default' | 'muted' | 'flat';
}

export function Card({
  className,
  children,
  header,
  footer,
  variant = 'default',
  ...props
}: CardProps) {
  const bgStyles = {
    default: 'bg-white border-[#e5e7eb] shadow-2xs',
    muted: 'bg-[#f9fafb] border-[#e5e7eb]',
    flat: 'bg-transparent border-[#e5e7eb]',
  };

  return (
    <div
      className={cn(
        'rounded-xl border transition-all overflow-hidden flex flex-col',
        bgStyles[variant],
        className
      )}
      {...props}
    >
      {header && (
        <div className="px-4 py-3.5 border-b border-[#e5e7eb] flex items-center justify-between">
          {header}
        </div>
      )}
      <div className="p-4 flex-1">{children}</div>
      {footer && (
        <div className="px-4 py-3 bg-[#f9fafb] border-t border-[#e5e7eb] flex items-center justify-between">
          {footer}
        </div>
      )}
    </div>
  );
}
