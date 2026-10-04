import React, { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { useToast } from '../../components/ui/Toast';
import { api } from '../../lib/api-client';
import { Loader2, Play, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { AgentCreateInput } from '../../types';

interface QuickRunModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface StarterAgentTemplate {
  id: string;
  name: string;
  description: string;
  prompt: string;
  agent: AgentCreateInput;
}

export function QuickRunModal({ isOpen, onClose }: QuickRunModalProps) {
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [selectedStarterId, setSelectedStarterId] = useState(starterAgentTemplates[0].id);
  const [prompt, setPrompt] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: agents = [] } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
    enabled: isOpen,
  });

  useEffect(() => {
    const selectedAgentExists = agents.some((agent) => agent.id === selectedAgentId);
    if ((!selectedAgentId || !selectedAgentExists) && agents.length > 0) {
      setSelectedAgentId(agents[0].id);
    }
    if (selectedAgentId && !selectedAgentExists && agents.length === 0) {
      setSelectedAgentId('');
    }
  }, [agents, selectedAgentId]);

  const handleRun = async () => {
    const selectedStarter = starterAgentTemplates.find((template) => template.id === selectedStarterId) || starterAgentTemplates[0];

    if (!selectedAgentId && !selectedStarter) {
      toast.error('Agent required', 'Select an agent or starter template to execute.');
      return;
    }

    setIsRunning(true);
    try {
      const targetAgent = selectedAgentId
        ? agents.find((agent) => agent.id === selectedAgentId)
        : await api.createAgent(selectedStarter.agent);

      if (!targetAgent) {
        throw new Error('No target agent available for quick run.');
      }

      const executionPrompt =
        prompt.trim() ||
        (selectedAgentId ? `Run your default objective now: ${targetAgent.objective}` : selectedStarter.prompt);
      const conv = await api.createConversation(targetAgent.id, executionPrompt.slice(0, 42) || 'Quick Run Session');
      await api.sendMessage(conv.id, executionPrompt);

      queryClient.invalidateQueries({ queryKey: ['agents-list'] });
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', targetAgent.id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-action-items'] });
      toast.success(
        selectedAgentId ? 'Execution complete' : 'Starter agent created',
        `${targetAgent.name} is ready with a new quick-run chat.`
      );
      onClose();
      navigate(`/agents/${targetAgent.id}/chat?conv=${conv.id}`);
    } catch (error) {
      toast.error('Execution failed', error instanceof Error ? error.message : 'Could not dispatch quick run.');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#f0fdfa] text-[#0f766e] flex items-center justify-center border border-[#99f6e4]">
            <Play className="w-3.5 h-3.5 fill-current" />
          </div>
          <span className="font-semibold text-[#111827]">Quick Run Agent</span>
        </div>
      }
      description="Immediately execute an autonomous agent with a custom one-off prompt or default instructions."
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            isLoading={isRunning}
            onClick={handleRun}
            disabled={isRunning}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Execution</span>
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {isRunning && (
          <div className="rounded-lg border border-[#99f6e4] bg-[#f0fdfa] p-3 flex items-start gap-3 text-xs text-[#0f766e]">
            <Loader2 className="w-4 h-4 animate-spin shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-[#115e59]">Agent is running</div>
              <p className="mt-0.5 leading-relaxed">
                Creating the session and waiting for the LLM response. This can take a few seconds.
              </p>
            </div>
          </div>
        )}

        {agents.length === 0 ? (
          <div className="space-y-2">
            <div className="text-xs font-medium text-[#111827]">Starter Agents</div>
            <div className="grid grid-cols-1 gap-2">
              {starterAgentTemplates.map((template) => {
                const isSelected = selectedStarterId === template.id;

                return (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => {
                      setSelectedStarterId(template.id);
                      setPrompt(template.prompt);
                    }}
                    className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                      isSelected
                        ? 'border-[#0f766e] bg-[#f0fdfa] text-[#111827]'
                        : 'border-[#e5e7eb] bg-white text-[#4b5563] hover:border-[#0f766e]'
                    }`}
                  >
                    <div className="text-xs font-semibold">{template.name}</div>
                    <div className="mt-1 text-[11px] leading-relaxed">{template.description}</div>
                  </button>
                );
              })}
            </div>
            <div className="rounded-lg border border-[#ccfbf1] bg-[#f0fdfa] p-3 text-xs text-[#0f766e]">
              Launching will create the selected starter agent, open a new chat, and run the prompt immediately.
            </div>
          </div>
        ) : (
          <Select
            label="Target Agent"
            hint={`${agents.length} available`}
            value={selectedAgentId}
            onChange={(e) => setSelectedAgentId(e.target.value)}
            options={agents.map((a) => ({
              value: a.id,
              label: `${a.name} (${a.tools.length} tools)`,
            }))}
          />
        )}

        <Textarea
          label="Execution Prompt Override (Optional)"
          hint="Leave empty to use agent default instructions"
          placeholder="e.g. Scrape AI engineering internships from the past 24 hours and format as markdown..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
        />

        <div className="space-y-2">
          <span className="text-xs font-medium text-[#111827]">Examples</span>
          <div className="grid grid-cols-1 gap-2">
            {quickRunExamples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setPrompt(example)}
                className="rounded-lg border border-[#e5e7eb] bg-white px-3 py-2 text-left text-xs text-[#4b5563] hover:border-[#0f766e] hover:text-[#111827] transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}

const quickRunExamples = [
  'Find today\'s latest AI engineering internship opportunities and summarize the top 5.',
  'Search for remote software engineering internships posted this week and rank them by relevance.',
  'Draft a professional LinkedIn message asking a recruiter about internship openings.',
];

const starterAgentTemplates: StarterAgentTemplate[] = [
  {
    id: 'research-agent',
    name: 'Research Agent',
    description: 'Searches live web results and summarizes useful opportunities or news.',
    prompt: 'Find today\'s latest AI engineering internship opportunities and summarize the top 5 with source links.',
    agent: {
      name: 'Research Agent',
      objective: 'Research current web information and summarize the most relevant findings for the user.',
      instructions:
        'You are a careful research agent. Use web_search for current information, compare results, avoid unsupported claims, and answer with concise headings and source-aware summaries.',
      model: 'google/gemini-2.5-flash',
      temperature: 0.2,
      tools: ['web_search', 'summarize_text', 'save_memory', 'datetime'],
      version: 'v1.0',
      status: 'active',
    },
  },
  {
    id: 'drafting-agent',
    name: 'Drafting Agent',
    description: 'Creates polished messages, outreach notes, and application drafts.',
    prompt: 'Draft a professional LinkedIn message asking a recruiter about software engineering internship openings.',
    agent: {
      name: 'Drafting Agent',
      objective: 'Draft professional messages and rewrite user text clearly without sending anything automatically.',
      instructions:
        'You are a professional drafting agent. Use draft_message when the user asks for outreach, email, LinkedIn, or reminder drafts. Never send messages automatically.',
      model: 'google/gemini-2.5-flash',
      temperature: 0.35,
      tools: ['draft_message', 'summarize_text', 'save_memory'],
      version: 'v1.0',
      status: 'active',
    },
  },
  {
    id: 'productivity-agent',
    name: 'Productivity Agent',
    description: 'Summarizes tasks, remembers notes, and helps plan next actions.',
    prompt: 'Summarize my current internship preparation tasks into a clear priority list for today.',
    agent: {
      name: 'Productivity Agent',
      objective: 'Help the user organize tasks, summarize notes, and save useful memory for future sessions.',
      instructions:
        'You are a productivity agent. Summarize clearly, use datetime for time-sensitive planning, and use memory tools when the user asks to save or recall information.',
      model: 'google/gemini-2.5-flash',
      temperature: 0.25,
      tools: ['datetime', 'summarize_text', 'save_memory', 'get_memory'],
      version: 'v1.0',
      status: 'active',
    },
  },
];
