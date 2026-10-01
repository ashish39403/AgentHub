import React, { useState } from 'react';
import { useAuth } from '../../lib/auth-context';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Switch } from '../../components/ui/Switch';
import { useToast } from '../../components/ui/Toast';
import { Sun, Check, UserRound, ShieldCheck } from 'lucide-react';

export function SettingsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [telemetryEnabled, setTelemetryEnabled] = useState(true);

  const handleSave = () => {
    toast.success('Settings updated', 'Workspace preferences persisted.');
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-[#78716c] font-mono text-[11px] uppercase tracking-wider">
          <span>Account</span>
          <span>/</span>
          <span>Preferences</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold text-[#1e1b19] tracking-tight">
          Settings
        </h1>
        <p className="text-xs sm:text-sm text-[#57534e]">
          Manage your profile display, interface preferences, and safe runtime visibility.
        </p>
      </div>

      <div className="space-y-6">
        <div className="p-5 rounded-xl bg-white border border-[#e7e5e4] shadow-xs space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[#faf2ee]">
            <img
              src={user?.avatar_url || `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(user?.name || 'User')}`}
              alt={user?.name || 'Profile'}
              className="w-12 h-12 rounded-full object-cover border border-[#e7e5e4]"
              referrerPolicy="no-referrer"
            />
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-[#1e1b19] truncate">
                {user?.name || 'Signed in user'}
              </h2>
              <p className="text-xs text-[#78716c] truncate">
                {user?.email || 'No email available'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Name" disabled value={user?.name || ''} />
            <Input label="Email" disabled value={user?.email || ''} />
          </div>

          <div className="rounded-xl border border-[#e7e5e4] bg-[#f9fafb] p-3 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-white border border-[#e7e5e4] text-[#0f766e] flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-semibold text-[#1e1b19] block">Account Security</span>
              <p className="text-xs text-[#57534e] mt-0.5">
                Secrets, API keys, and backend gateway details stay server-side. They are not exposed in user settings.
              </p>
            </div>
          </div>
        </div>

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

        <div className="p-5 rounded-xl bg-white border border-[#e7e5e4] shadow-xs space-y-4">
          <h2 className="text-sm font-semibold text-[#1e1b19] pb-2 border-b border-[#faf2ee]">
            Runtime Visibility
          </h2>

          <Switch
            label="Enable live telemetry streaming"
            description="Shows live tool progress and response streaming inside chat views."
            checked={telemetryEnabled}
            onCheckedChange={setTelemetryEnabled}
          />

          <div className="rounded-xl border border-[#e7e5e4] bg-white p-3 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#f0fdfa] border border-[#99f6e4] text-[#0f766e] flex items-center justify-center shrink-0">
              <UserRound className="w-4 h-4" />
            </div>
            <p className="text-xs text-[#57534e]">
              Workspace IDs, deployment names, and API gateway URLs are intentionally hidden from normal user settings.
            </p>
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
