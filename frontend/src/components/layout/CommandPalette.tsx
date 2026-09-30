import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api-client';
import { Search, Cpu, Clock, Play, ArrowRight } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onQuickRun: () => void;
}

export function CommandPalette({ isOpen, onClose, onQuickRun }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { data: allAgents = [] } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
    enabled: isOpen,
  });
  const { data: allRoutines = [] } = useQuery({
    queryKey: ['routines-list'],
    queryFn: () => api.getRoutines(),
    enabled: isOpen,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const agents = allAgents.filter((a) =>
    a.name.toLowerCase().includes(query.toLowerCase()) || a.objective.toLowerCase().includes(query.toLowerCase())
  );

  const routines = allRoutines.filter((r) =>
    r.name.toLowerCase().includes(query.toLowerCase()) || r.prompt.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} maxWidth="xl">
      <div className="-m-5">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#e5e7eb] bg-[#f9fafb]">
          <Search className="w-4 h-4 text-[#6b7280]" />
          <input
            autoFocus
            type="text"
            placeholder="Type a command, agent, or routine name..."
            className="w-full bg-transparent text-sm text-[#111827] placeholder:text-[#9ca3af] focus:outline-none"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-[#e5e7eb] text-[#6b7280]">
            ESC
          </kbd>
        </div>

        <div className="p-3 max-h-[60vh] overflow-y-auto space-y-4 bg-white">
          {/* Quick Actions */}
          <div>
            <div className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
              Quick Actions
            </div>
            <div className="space-y-0.5">
              <button
                onClick={() => {
                  onClose();
                  onQuickRun();
                }}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs hover:bg-[#f3f4f6] text-[#111827] transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Play className="w-3.5 h-3.5 text-[#0f766e]" />
                  <span className="font-medium">Trigger Quick Run</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#9ca3af]" />
              </button>

              <button
                onClick={() => {
                  onClose();
                  navigate('/agents/new');
                }}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs hover:bg-[#f3f4f6] text-[#111827] transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Cpu className="w-3.5 h-3.5 text-[#0f766e]" />
                  <span className="font-medium">Create New Agent</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#9ca3af]" />
              </button>
            </div>
          </div>

          {/* Agents */}
          {agents.length > 0 && (
            <div>
              <div className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                Agents
              </div>
              <div className="space-y-0.5">
                {agents.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => {
                      onClose();
                      navigate(`/agents/${a.id}/chat`);
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs hover:bg-[#f3f4f6] text-[#111827] transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Cpu className="w-3.5 h-3.5 text-[#6b7280] shrink-0" />
                      <div className="truncate">
                        <span className="font-medium">{a.name}</span>
                        <span className="text-[11px] text-[#6b7280] ml-2 font-mono">{a.version}</span>
                      </div>
                    </div>
                    <span className="text-[11px] text-[#0f766e] shrink-0 font-medium">
                      Open Chat
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Routines */}
          {routines.length > 0 && (
            <div>
              <div className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                Routines
              </div>
              <div className="space-y-0.5">
                {routines.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => {
                      onClose();
                      navigate('/routines');
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs hover:bg-[#f3f4f6] text-[#111827] transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Clock className="w-3.5 h-3.5 text-[#6b7280] shrink-0" />
                      <span className="font-medium truncate">{r.name}</span>
                    </div>
                    <span className="font-mono text-[11px] text-[#6b7280] shrink-0">
                      {r.schedule}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
