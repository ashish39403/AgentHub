import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { QuickRunModal } from '../../features/dashboard/QuickRunModal';
import { CommandPalette } from './CommandPalette';
import { X } from 'lucide-react';

export function AppShell() {
  const [quickRunOpen, setQuickRunOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white text-[#111827] flex">
      {/* Desktop Fixed Sidebar */}
      <div className="hidden lg:block fixed left-0 top-0 bottom-0 z-40 w-64">
        <Sidebar onNewAgentClick={() => setQuickRunOpen(true)} />
      </div>

      {/* Mobile Drawer Backdrop & Sidebar */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs animate-in fade-in"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative w-72 max-w-[80vw] h-full bg-white shadow-2xl z-10 flex flex-col">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 right-3 p-1.5 rounded-lg text-[#6b7280] hover:text-[#111827]"
              aria-label="Close navigation drawer"
            >
              <X className="w-5 h-5" />
            </button>
            <Sidebar
              onNewAgentClick={() => {
                setMobileMenuOpen(false);
                setQuickRunOpen(true);
              }}
              onCloseMobile={() => setMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <TopBar
          onQuickRunClick={() => setQuickRunOpen(true)}
          onSearchClick={() => setSearchOpen(true)}
          onMobileMenuToggle={() => setMobileMenuOpen(true)}
        />

        <main className="flex-1 pt-14 w-full min-h-[calc(100vh-3.5rem)] bg-white overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* Global Modals */}
      <QuickRunModal isOpen={quickRunOpen} onClose={() => setQuickRunOpen(false)} />
      <CommandPalette
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onQuickRun={() => setQuickRunOpen(true)}
      />
    </div>
  );
}
