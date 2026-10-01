import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '../../lib/utils';
import { useAuth } from '../../lib/auth-context';
import { api } from '../../lib/api-client';
import {
  LayoutGrid,
  Cpu,
  Clock,
  Puzzle,
  Sliders,
  Plus,
  ChevronsUpDown,
  LogOut,
} from 'lucide-react';

interface SidebarProps {
  onNewAgentClick?: () => void;
  onCloseMobile?: () => void;
}

export function Sidebar({ onNewAgentClick, onCloseMobile }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profileMenuOpen, setProfileMenuOpen] = React.useState(false);
  const { data: recentAgents = [] } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
  });

  const mainNav = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutGrid },
    { name: 'Agents', path: '/agents', icon: Cpu },
    { name: 'Routines', path: '/routines', icon: Clock },
    { name: 'Integrations', path: '/integrations', icon: Puzzle },
    { name: 'Settings', path: '/settings', icon: Sliders },
  ];

  return (
    <aside className="h-full w-64 bg-white border-r border-[#e5e7eb] flex flex-col justify-between select-none">
      <div className="flex flex-col flex-1 overflow-y-auto">
        {/* Workspace Brand Lockup */}
        <div className="h-14 px-4 border-b border-[#e5e7eb] flex items-center justify-between">
          <div
            className="flex items-center gap-2.5 min-w-0 cursor-pointer"
            onClick={() => {
              navigate('/dashboard');
              onCloseMobile?.();
            }}
          >
            <div className="w-8 h-8 rounded-lg bg-[#0f766e] text-white flex items-center justify-center font-bold text-base shadow-xs">
              <Cpu className="w-4 h-4" />
            </div>
            <span className="text-base font-semibold text-[#111827] tracking-tight truncate">
              AgentHub
            </span>
          </div>
        </div>

        {/* Platform Nav */}
        <div className="px-3 pt-4">
          <div className="px-2 pb-1.5">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Platform
            </span>
          </div>
          <nav className="flex flex-col gap-0.5">
            {mainNav.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors',
                    isActive
                      ? 'bg-[#f3f4f6] text-[#111827] font-semibold'
                      : 'text-[#4b5563] hover:bg-[#f9fafb] hover:text-[#111827]'
                  )
                }
              >
                <item.icon className="w-4 h-4 shrink-0 text-[#6b7280]" />
                <span>{item.name}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Recent Agents Section */}
        <div className="px-3 pt-6">
          <div className="px-2 pb-1.5 flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-[#6b7280]">
              Recent Agents
            </span>
            <button
              onClick={() => {
                onNewAgentClick ? onNewAgentClick() : navigate('/agents/new');
                onCloseMobile?.();
              }}
              className="text-[#6b7280] hover:text-[#111827] p-0.5 rounded transition-colors"
              title="Create new agent"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex flex-col gap-0.5">
            {recentAgents.slice(0, 4).map((agent) => (
              <button
                key={agent.id}
                onClick={() => {
                  navigate(`/agents/${agent.id}/chat`);
                  onCloseMobile?.();
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-[#4b5563] hover:bg-[#f9fafb] hover:text-[#111827] transition-colors group text-left"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#16a34a] shrink-0" />
                <span className="truncate flex-1 font-medium">{agent.name}</span>
                <span className="font-mono text-[11px] text-[#9ca3af] group-hover:text-[#4b5563]">
                  {agent.status}
                </span>
              </button>
            ))}
            {recentAgents.length === 0 && (
              <div className="px-2.5 py-1.5 text-xs text-[#6b7280]">No agents yet</div>
            )}
          </div>
        </div>
      </div>

      {/* User Profile & Footer Area */}
      <div className="p-3 border-t border-[#e5e7eb] relative">
        {profileMenuOpen && (
          <div className="absolute bottom-full left-3 right-3 mb-2 p-1.5 rounded-lg bg-white border border-[#e5e7eb] shadow-lg flex flex-col gap-1 z-50">
            <button
              onClick={() => {
                navigate('/settings');
                setProfileMenuOpen(false);
                onCloseMobile?.();
              }}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded text-xs text-[#4b5563] hover:bg-[#f9fafb] text-left transition-colors"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Workspace Settings</span>
            </button>
            <div className="h-px bg-[#e5e7eb] my-0.5" />
            <button
              onClick={() => {
                logout();
                setProfileMenuOpen(false);
              }}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded text-xs text-[#dc2626] hover:bg-[#fee2e2] text-left transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign out</span>
            </button>
          </div>
        )}

        <div
          onClick={() => setProfileMenuOpen(!profileMenuOpen)}
          className="flex items-center justify-between p-1.5 rounded-lg hover:bg-[#f9fafb] transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="relative shrink-0">
              <img
                src={user?.avatar_url || `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(user?.name || 'User')}`}
                alt={user?.name || 'User Profile'}
                className="w-8 h-8 rounded-full object-cover border border-[#e5e7eb]"
                referrerPolicy="no-referrer"
              />
              <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-[#16a34a] ring-1 ring-white" />
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-[#111827] truncate leading-tight">
                {user?.name || 'Signed in user'}
              </span>
              <span className="text-[11px] font-mono text-[#6b7280] truncate leading-tight">
                {user?.email || 'No email'}
              </span>
            </div>
          </div>
          <ChevronsUpDown className="w-4 h-4 text-[#6b7280] shrink-0" />
        </div>
      </div>
    </aside>
  );
}
