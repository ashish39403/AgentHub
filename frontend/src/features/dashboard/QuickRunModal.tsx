import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { useToast } from '../../components/ui/Toast';
import { api } from '../../lib/api-client';
import { Play, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface QuickRunModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function QuickRunModal({ isOpen, onClose }: QuickRunModalProps) {
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();
  const { data: agents = [] } = useQuery({
    queryKey: ['agents-list'],
    queryFn: () => api.getAgents(),
    enabled: isOpen,
  });

  useEffect(() => {
    if (!selectedAgentId && agents.length > 0) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgentId]);

  const handleRun = async () => {
    if (!selectedAgentId) {
      toast.error('Agent required', 'Please select an agent to execute.');
      return;
    }

    setIsRunning(true);
    try {
      const conv = await api.createConversation(selectedAgentId, prompt ? prompt.slice(0, 30) : 'Quick Run Session');
      if (prompt) {
        await api.sendMessage(conv.id, prompt);
      }
      toast.success('Execution started', 'Dispatched run across worker runtime.');
      onClose();
      navigate(`/agents/${selectedAgentId}/chat?conv=${conv.id}`);
    } catch {
      toast.error('Execution failed', 'Could not dispatch quick run.');
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
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Execution</span>
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Select
          label="Target Autonomous Agent"
          value={selectedAgentId}
          onChange={(e) => setSelectedAgentId(e.target.value)}
          options={agents.map((a) => ({
            value: a.id,
            label: `${a.name} (${a.tools.length} tools attached)`,
          }))}
        />

        <Textarea
          label="Execution Prompt Override (Optional)"
          hint="Leave empty to use agent default instructions"
          placeholder="e.g. Scrape AI engineering internships from the past 24 hours and format as markdown..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
        />
      </div>
    </Modal>
  );
}
