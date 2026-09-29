import React from 'react';
import { Cpu } from 'lucide-react';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen w-full bg-white flex flex-col justify-between p-4 sm:p-6 lg:p-8">
      {/* Top Header */}
      <div className="flex items-center justify-between max-w-5xl mx-auto w-full">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#0f766e] text-white flex items-center justify-center font-bold text-base shadow-xs">
            <Cpu className="w-4 h-4" />
          </div>
          <span className="text-base font-semibold text-[#111827] tracking-tight">
            AgentHub
          </span>
        </div>
      </div>

      {/* Center Auth Card */}
      <div className="w-full max-w-md mx-auto my-auto py-8">
        <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-md p-6 sm:p-8">
          {children}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-[#6b7280] py-4">
        <span>AgentHub Autonomous Orchestration Console • Production Ready</span>
      </div>
    </div>
  );
}
