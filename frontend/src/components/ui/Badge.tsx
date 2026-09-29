import React from 'react';
import { cn } from '../../lib/utils';
import { StatusType } from '../../types';

export interface BadgeProps {
  status?: StatusType | 'warning' | 'info';
  children?: React.ReactNode;
  showDot?: boolean;
  className?: string;
  variant?: 'solid' | 'subtle' | 'outline';
}

export function Badge({ status = 'queued', children, showDot = true, className }: BadgeProps) {
  const statusStyles: Record<string, { bg: string; text: string; border: string; dot: string; ping?: boolean }> = {
    succeeded: {
      bg: 'bg-[#f0fdf4]',
      text: 'text-[#15803d]',
      border: 'border-[#bbf7d0]',
      dot: 'bg-[#16a34a]',
    },
    running: {
      bg: 'bg-[#f0fdfa]',
      text: 'text-[#0f766e]',
      border: 'border-[#99f6e4]',
      dot: 'bg-[#0f766e]',
      ping: true,
    },
    failed: {
      bg: 'bg-[#fef2f2]',
      text: 'text-[#dc2626]',
      border: 'border-[#fecaca]',
      dot: 'bg-[#dc2626]',
    },
    queued: {
      bg: 'bg-[#f9fafb]',
      text: 'text-[#6b7280]',
      border: 'border-[#e5e7eb]',
      dot: 'bg-[#9ca3af]',
    },
    active: {
      bg: 'bg-[#f0fdfa]',
      text: 'text-[#0f766e]',
      border: 'border-[#99f6e4]',
      dot: 'bg-[#0f766e]',
    },
    paused: {
      bg: 'bg-[#f9fafb]',
      text: 'text-[#6b7280]',
      border: 'border-[#e5e7eb]',
      dot: 'bg-[#9ca3af]',
    },
    draft: {
      bg: 'bg-[#f9fafb]',
      text: 'text-[#6b7280]',
      border: 'border-[#e5e7eb]',
      dot: 'bg-[#9ca3af]',
    },
    warning: {
      bg: 'bg-[#fffbeb]',
      text: 'text-[#b45309]',
      border: 'border-[#fde68a]',
      dot: 'bg-[#d97706]',
    },
    info: {
      bg: 'bg-[#f9fafb]',
      text: 'text-[#111827]',
      border: 'border-[#e5e7eb]',
      dot: 'bg-[#0f766e]',
    },
  };

  const current = statusStyles[status] || statusStyles.queued;
  const displayText = children || status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border select-none whitespace-nowrap',
        current.bg,
        current.text,
        current.border,
        className
      )}
    >
      {showDot && (
        <span className="relative flex h-1.5 w-1.5">
          {current.ping && (
            <span
              className={cn(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                current.dot
              )}
            />
          )}
          <span className={cn('relative inline-flex rounded-full h-1.5 w-1.5', current.dot)} />
        </span>
      )}
      <span>{displayText}</span>
    </span>
  );
}
