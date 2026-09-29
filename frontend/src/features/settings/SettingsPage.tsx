import React, { useState } from 'react';
import { useAuth } from '../../lib/auth-context';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Switch } from '../../components/ui/Switch';
import { useToast } from '../../components/ui/Toast';
import { mockDb } from '../../lib/api-client';
import { Sun, RotateCcw, Check, Sparkles } from 'lucide-react';

export function SettingsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [workspaceName, setWorkspaceName] = useState('Workspace Prod (US East)');
  const [apiBaseUrl, setApiBaseUrl] = useState(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
  const [telemetryEnabled, setTelemetryEnabled] = useState(true);

  const handleSave = () => {
    toast.success('Settings updated', 'Workspace preferences persisted.');
  };

  const handleResetMockData = () => {
    if (confirm('Reset mock workspace to initial baseline data?')) {
      mockDb.reset();
      toast.success('Workspace reset', 'All agents, runs, and chats restored to defaults.');
      setTimeout(() => window.location.reload(), 300);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-[#78716c] font-mono text-[11px] uppercase tracking-wider">
          <span>Configuration</span>
          <span>/</span>
          <span>System Settings</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold text-[#1e1b19] tracking-tight">
          Workspace Settings
        </h1>
        <p className="text-xs sm:text-sm text-[#57534e]">
          Manage workspace identity, theme preferences, API proxy endpoints, and execution quotas.
        </p>
      </div>

      <div className="space-y-6">
        {/* Appearance Card */}
        <div className="p-5 rounded-xl bg-white border border-[#e7e5e4] shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#faf2ee]">
            <div>
              <h2 className="text-sm font-semibold text-[#1e1b19]">
                Appearance & Interface Theme
              </h2>
              <p className="text-xs text-[#78716c] mt-0.5">
                Clean, high-contrast light workspace theme is active.
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#e6fffa] text-[#0f766e] border border-[#99f6e4]">
              <Check className="w-3.5 h-3.5" />
              White Theme Active
            </span>
          </div>

          <div className="p-4 rounded-xl border border-[#0f766e] bg-[#f0fdf4]/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-white border border-[#e7e5e4] text-[#0f766e] flex items-center justify-center shadow-xs">
                <Sun className="w-5 h-5" />
              </div>
              <div>
                <span className="text-sm font-medium text-[#1e1b19] block">
                  Pure White Theme (Stitch Design Specification)
                </span>
                <span className="text-xs text-[#57534e]">
                  Calibrated warm canvas (#fff8f5), crisp hairline borders, and emerald accents.
                </span>
              </div>
            </div>
            <span className="text-xs font-mono font-medium text-[#0f766e] bg-white px-2 py-1 rounded border border-[#99f6e4]">
              DEFAULT
            </span>
          </div>
        </div>

        {/* Workspace Identity */}
        <div className="p-5 rounded-xl bg-white border border-[#e7e5e4] shadow-xs space-y-4">
          <h2 className="text-sm font-semibold text-[#1e1b19] pb-2 border-b border-[#faf2ee]">
            Workspace Identity & API Gateway
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Workspace Name"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
            />

            <Input
              label="Operator Email"
              disabled
              value={user?.email || 'elena@agenthub.dev'}
              hint="Managed via master SSO"
            />
          </div>

          <Input
            label="FastAPI Backend Gateway URL"
            hint="Default: http://localhost:8000"
            mono
            value={apiBaseUrl}
            onChange={(e) => setApiBaseUrl(e.target.value)}
          />

          <Switch
            label="Enable live telemetry streaming"
            description="Streams token-by-token logs and tool call telemetry to the right rail inspector."
            checked={telemetryEnabled}
            onCheckedChange={setTelemetryEnabled}
          />
        </div>

        {/* Data & Mock Store Management */}
        <div className="p-5 rounded-xl bg-white border border-[#e7e5e4] shadow-xs space-y-4">
          <h2 className="text-sm font-semibold text-[#1e1b19] pb-2 border-b border-[#faf2ee]">
            Local Sandbox & Data Store
          </h2>

          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-[#1e1b19] block">
                Reset Mock State
              </span>
              <span className="text-xs text-[#57534e]">
                Restores sample agents "Internship Scout", "Inbox Summarizer", routines and tool run histories.
              </span>
            </div>

            <Button
              variant="surface"
              size="sm"
              onClick={handleResetMockData}
              className="shadow-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset to Defaults</span>
            </Button>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-end">
          <Button variant="primary" size="md" onClick={handleSave}>
            Save Preferences
          </Button>
        </div>
      </div>
    </div>
  );
}
