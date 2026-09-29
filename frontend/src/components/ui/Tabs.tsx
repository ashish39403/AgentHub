import React from 'react';
import { cn } from '../../lib/utils';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
  variant?: 'segmented' | 'underline';
}

export function Tabs({ tabs, activeTab, onChange, className, variant = 'segmented' }: TabsProps) {
  if (variant === 'underline') {
    return (
      <div className={cn('flex items-center gap-6 border-b border-[#e5e7eb]', className)}>
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={cn(
                'flex items-center gap-2 pb-2.5 text-xs font-medium transition-colors border-b-2 -mb-px cursor-pointer',
                isActive
                  ? 'text-[#0f766e] border-[#0f766e]'
                  : 'text-[#4b5563] border-transparent hover:text-[#111827]'
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {typeof tab.count === 'number' && (
                <span className="px-1.5 py-0.2 rounded-full bg-[#f3f4f6] text-[10px] font-mono">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn('flex items-center p-0.5 rounded-lg bg-[#f3f4f6] border border-[#e5e7eb] gap-0.5', className)}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer whitespace-nowrap',
              isActive
                ? 'bg-white text-[#111827] shadow-2xs'
                : 'text-[#4b5563] hover:text-[#111827]'
            )}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {typeof tab.count === 'number' && (
              <span className="px-1.5 py-0.2 rounded-full bg-[#e5e7eb] text-[10px] font-mono">
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
