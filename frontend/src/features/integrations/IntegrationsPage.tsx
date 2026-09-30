import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api-client';
import { Integration } from '../../types';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { formatRelativeTime } from '../../lib/utils';
import {
  Mail,
  Code,
  MessageSquare,
  CheckSquare,
  FileText,
  Webhook,
  CheckCircle2,
  AlertTriangle,
  Unlink,
  Link as LinkIcon,
  Search,
} from 'lucide-react';

export function IntegrationsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeModalInt, setActiveModalInt] = useState<Integration | null>(null);

  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations-list'],
    queryFn: () => api.getIntegrations(),
  });

  const connectMutation = useMutation({
    mutationFn: (provider: string) => api.connectIntegration(provider),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['integrations-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-action-items'] });
      if (updated.connect_url) {
        window.open(updated.connect_url, '_blank', 'noopener,noreferrer');
      }
      toast.success('Connection requested', updated.message || `${updated.name} connection started.`);
      setActiveModalInt(null);
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (provider: string) => api.disconnectIntegration(provider),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['integrations-list'] });
      toast.info('Integration disconnected', `${updated.name} revoked.`);
    },
  });

  const getProviderIcon = (provider: Integration['provider']) => {
    switch (provider) {
      case 'gmail':
        return <Mail className="w-5 h-5 text-red-500" />;
      case 'github':
        return <Code className="w-5 h-5 text-neutral-800" />;
      case 'slack':
        return <MessageSquare className="w-5 h-5 text-amber-500" />;
      case 'linear':
        return <CheckSquare className="w-5 h-5 text-indigo-500" />;
      case 'notion':
        return <FileText className="w-5 h-5 text-neutral-700" />;
      default:
        return <Webhook className="w-5 h-5 text-[#0f766e]" />;
    }
  };

  const filteredIntegrations = (integrations || []).filter(
    (i) =>
      i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-[1440px] mx-auto w-full space-y-6 lg:space-y-8 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-[#6b7280] font-mono text-[11px] uppercase tracking-wider">
            <span>Ecosystem</span>
            <span>/</span>
            <span>OAuth & API Connections</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-[#111827] tracking-tight">
            Integrations
          </h1>
          <p className="text-xs sm:text-sm text-[#4b5563]">
            Authorize external platforms, OAuth scopes, and webhook endpoints for agent tool execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search integrations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 pl-8 pr-3 bg-white text-xs text-[#111827] placeholder:text-[#9ca3af] rounded-lg border border-[#e5e7eb] shadow-2xs focus:outline-none focus:border-[#0f766e]"
            />
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        {isLoading ? (
          <div className="col-span-full p-8 text-center text-xs text-[#6b7280]">
            Loading integrations...
          </div>
        ) : (
          filteredIntegrations.map((item) => {
            const isConnected = item.status === 'connected';
            const isPending = item.status === 'pending';
            const isExpiring = item.status === 'expiring_soon' || item.status === 'error';

            return (
              <div
                key={item.id}
                className="p-5 rounded-xl bg-white border border-[#e5e7eb] shadow-2xs flex flex-col justify-between hover:border-[#0f766e]/40 transition-all group"
              >
                <div className="space-y-3">
                  {/* Card Header */}
                  <div className="flex items-start justify-between">
                    <div className="w-10 h-10 rounded-xl bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center shrink-0">
                      {getProviderIcon(item.provider)}
                    </div>
                    <Badge
                      status={
                        isConnected
                          ? 'active'
                          : isPending
                          ? 'warning'
                          : isExpiring
                          ? 'warning'
                          : 'queued'
                      }
                    >
                      {item.status === 'connected'
                        ? 'Connected'
                        : item.status === 'pending'
                        ? 'Pending'
                        : item.status === 'expiring_soon'
                        ? 'Expiring soon'
                        : item.status === 'error'
                        ? 'Degraded'
                        : 'Disconnected'}
                    </Badge>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-sm font-semibold text-[#111827]">
                      {item.name}
                    </h3>
                    <p className="text-xs text-[#4b5563] mt-1 leading-relaxed">
                      {item.description}
                    </p>
                  </div>

                  {/* Account / Token expiry status */}
                  {isConnected && (
                    <div className="p-2.5 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] text-[11px] font-mono space-y-1">
                      {item.account_email && (
                        <div className="flex items-center justify-between text-[#111827]">
                          <span className="text-[#6b7280]">Account:</span>
                          <span className="font-medium truncate max-w-[140px]">{item.account_email}</span>
                        </div>
                      )}
                      {item.expires_at && (
                        <div className="flex items-center justify-between text-[#6b7280]">
                          <span>Refreshed:</span>
                          <span>{formatRelativeTime(item.expires_at)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {isExpiring && (
                    <div className="p-2.5 rounded-lg bg-[#fffbeb] border border-[#fde68a] text-xs text-[#b45309] flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>Token expiring or rate-limited. Re-authenticate to restore full functionality.</span>
                    </div>
                  )}

                  {isPending && (
                    <div className="p-2.5 rounded-lg bg-[#f0fdfa] border border-[#99f6e4] text-xs text-[#0f766e] flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>{item.message || 'Connection requested. Complete OAuth before agents can use this provider.'}</span>
                    </div>
                  )}

                  {/* Permissions Scopes */}
                  <div className="pt-2">
                    <span className="text-[10px] uppercase font-semibold text-[#6b7280] block mb-1.5">
                      Authorized Scopes
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {(item.scopes || []).map((scope) => (
                        <span
                          key={scope}
                          className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#f3f4f6] text-[#4b5563] border border-[#e5e7eb]"
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer Action Button */}
                <div className="mt-5 pt-3 border-t border-[#f3f4f6] flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs text-[#6b7280]">
                    {isConnected ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#16a34a]" />
                    ) : null}
                    <span>{isConnected ? 'Syncing active' : 'Not authorized'}</span>
                  </div>

                  {isConnected ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => disconnectMutation.mutate(item.provider)}
                      className="h-8 shadow-2xs"
                    >
                      <Unlink className="w-3.5 h-3.5 text-[#dc2626]" />
                      <span className="text-[#dc2626]">Disconnect</span>
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setActiveModalInt(item)}
                      className="h-8 shadow-xs"
                    >
                      <LinkIcon className="w-3.5 h-3.5" />
                      <span>Connect</span>
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Connect Modal */}
      {activeModalInt && (
        <Modal
          isOpen={!!activeModalInt}
          onClose={() => setActiveModalInt(null)}
          title={`Connect ${activeModalInt.name}`}
          description={`Authenticate workspace credentials to grant your agents ${(activeModalInt.scopes || []).join(', ')} capabilities.`}
          footer={
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveModalInt(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => connectMutation.mutate(activeModalInt.provider)}
                disabled={connectMutation.isPending}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{connectMutation.isPending ? 'Starting...' : 'Start connection'}</span>
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div className="p-3.5 rounded-lg bg-[#f0fdfa] border border-[#99f6e4] flex items-center gap-3">
              {getProviderIcon(activeModalInt.provider)}
              <div className="text-xs text-[#0f766e]">
                <span className="font-semibold block">OAuth 2.0 PKCE Flow</span>
                <span>Composio owns OAuth token custody; AgentHub stores only connection status and IDs.</span>
              </div>
            </div>
            <p className="text-xs text-[#4b5563] leading-relaxed">
              {activeModalInt.message ||
                'The backend will create a provider connection request. Agents cannot use this integration until the account is connected.'}
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}
