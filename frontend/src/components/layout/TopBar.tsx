import React from 'react';
import { Button } from '../ui/Button';
import { Search, Play, Menu } from 'lucide-react';

interface TopBarProps {
  onQuickRunClick: () => void;
  onSearchClick: () => void;
  onMobileMenuToggle: () => void;
}

export function TopBar({ onQuickRunClick, onSearchClick, onMobileMenuToggle }: TopBarProps) {
  return (
    <header className="fixed top-0 left-0 lg:left-64 right-0 h-14 bg-white/95 backdrop-blur-md border-b border-[#e5e7eb] z-30 px-4 lg:px-6 flex items-center justify-between">
      {/* Left side: Mobile Toggle + Breadcrumbs + Search input */}
      <div className="flex items-center gap-3 md:gap-4">
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-1.5 rounded-lg text-[#4b5563] hover:bg-[#f3f4f6]"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-1.5 text-[#6b7280] font-mono text-[11px]">
          <span className="text-[#111827] text-xs font-semibold">AgentHub</span>
          <span>/</span>
          <span className="px-1.5 py-0.5 rounded bg-[#f3f4f6] border border-[#e5e7eb] text-[#111827]">
            v1.4.2
          </span>
        </div>

        {/* Global Search Bar */}
        <button
          onClick={onSearchClick}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-[#f9fafb] hover:bg-[#f3f4f6] border border-[#e5e7eb] text-[#6b7280] hover:text-[#111827] transition-colors text-xs cursor-pointer"
        >
          <Search className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden md:inline">Search runs, agents, logs...</span>
          <span className="md:hidden">Search...</span>
          <kbd className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-[#e5e7eb] text-[#6b7280] ml-1 shadow-2xs">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right side: Docs and Quick Run */}
      <div className="flex items-center gap-2 sm:gap-3">
        <a
          href="#docs"
          onClick={(e) => {
            e.preventDefault();
          }}
          className="text-xs font-medium text-[#6b7280] hover:text-[#111827] px-2 py-1 rounded transition-colors hidden sm:inline"
        >
          Docs
        </a>

        <Button
          variant="primary"
          size="sm"
          onClick={onQuickRunClick}
          className="h-8 shadow-xs"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Quick Run</span>
        </Button>
      </div>
    </header>
  );
}
