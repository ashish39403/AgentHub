import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiError, api, streamMessageHelper } from '../../lib/api-client';
import { Conversation, Message, ToolCallPayload } from '../../types';
import { Button } from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import { formatRelativeTime } from '../../lib/utils';
import {
  Terminal,
  Search,
  Plus,
  Trash2,
  Sliders,
  Send,
  Paperclip,
  AtSign,
  ChevronDown,
  ChevronUp,
  Layers,
  CheckCircle2,
  Loader2,
  Square,
  Sparkles,
  X,
  Bot,
} from 'lucide-react';

const hasApiStatus = (error: unknown, status: number) =>
  error instanceof ApiError || (typeof error === 'object' && error !== null && 'status' in error)
    ? (error as { status?: number }).status === status
    : false;

export function AgentChatPage() {
  const { id: agentId } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const convParam = searchParams.get('conv');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [activeConvId, setActiveConvId] = useState<string | null>(convParam);
  const [searchChats, setSearchChats] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingTools, setStreamingTools] = useState<ToolCallPayload[]>([]);
  const [showTelemetry, setShowTelemetry] = useState(true);
  const [collapsedTools, setCollapsedTools] = useState<Record<string, boolean>>({});
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Queries
  const { data: agent } = useQuery({
    queryKey: ['agent-chat-detail', agentId],
    queryFn: () => (agentId ? api.getAgent(agentId) : null),
  });

  const { data: conversations } = useQuery({
    queryKey: ['agent-conversations', agentId],
    queryFn: () => (agentId ? api.getConversations(agentId) : []),
  });

  // Set initial active conversation if not set
  useEffect(() => {
    if (!activeConvId && conversations && conversations.length > 0) {
      setActiveConvId(conversations[0].id);
    }
  }, [conversations, activeConvId]);

  const removeConversationLocally = useCallback((conversationId: string) => {
    const existing =
      queryClient.getQueryData<Conversation[]>(['agent-conversations', agentId]) ||
      conversations ||
      [];
    const remaining = existing.filter((conversation) => conversation.id !== conversationId);

    queryClient.setQueryData(['agent-conversations', agentId], remaining);
    queryClient.removeQueries({ queryKey: ['conversation-messages', conversationId] });

    if (activeConvId === conversationId) {
      setActiveConvId(remaining[0]?.id ?? null);
    }

    return remaining;
  }, [activeConvId, agentId, conversations, queryClient]);

  const {
    data: currentConversation,
    error: conversationError,
    refetch: refetchConversation,
  } = useQuery({
    queryKey: ['conversation-messages', activeConvId],
    queryFn: () => (activeConvId ? api.getConversation(activeConvId) : null),
    enabled: !!activeConvId,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 1;
    },
  });

  useEffect(() => {
    if (hasApiStatus(conversationError, 404) && activeConvId) {
      removeConversationLocally(activeConvId);
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] });
    }
  }, [conversationError, activeConvId, agentId, queryClient, removeConversationLocally]);

  const messages = currentConversation?.messages || [];
  const chatItems = buildChatItems(messages);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, streamingTools]);

  // Create new conversation mutation
  const createConvMutation = useMutation({
    mutationFn: () => api.createConversation(agentId!, 'New Exploration Session'),
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] });
      setActiveConvId(newConv.id);
      toast.success('Session started', 'New conversation workspace created.');
    },
  });

  const deleteConvMutation = useMutation({
    mutationFn: async (conversationId: string) => {
      try {
        await api.deleteConversation(conversationId);
      } catch (error) {
        if (hasApiStatus(error, 404)) return;
        throw error;
      }
    },
    onMutate: async (deletedConversationId) => {
      await queryClient.cancelQueries({ queryKey: ['agent-conversations', agentId] });
      await queryClient.cancelQueries({ queryKey: ['conversation-messages', deletedConversationId] });

      const previousConversations =
        queryClient.getQueryData<Conversation[]>(['agent-conversations', agentId]) ||
        conversations ||
        [];
      const previousActiveConversationId = activeConvId;

      removeConversationLocally(deletedConversationId);

      return { previousConversations, previousActiveConversationId };
    },
    onSuccess: (_, deletedConversationId) => {
      removeConversationLocally(deletedConversationId);
      toast.success('Conversation cleared', 'The current conversation was deleted.');
    },
    onError: (error, deletedConversationId, context) => {
      if (hasApiStatus(error, 404)) {
        removeConversationLocally(deletedConversationId);
        toast.info('Conversation was already removed.');
        return;
      }

      if (context?.previousConversations) {
        queryClient.setQueryData(['agent-conversations', agentId], context.previousConversations);
      }
      if (context?.previousActiveConversationId) {
        setActiveConvId(context.previousActiveConversationId);
      }

      toast.error('Delete failed', 'Could not delete this conversation.');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] });
    },
  });

  const handleSend = async () => {
    if (!inputMessage.trim() || isStreaming || !agentId) return;

    const userText = inputMessage;
    setInputMessage('');
    setIsStreaming(true);
    setStreamingContent('');
    setStreamingTools([]);

    const abortCtrl = new AbortController();
    abortControllerRef.current = abortCtrl;

    let conversationId = activeConvId;
    if (!conversationId) {
      try {
        const newConversation = await api.createConversation(agentId, userText.slice(0, 60) || 'New Exploration Session');
        conversationId = newConversation.id;
        setActiveConvId(newConversation.id);
        queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] });
      } catch (err) {
        setIsStreaming(false);
        toast.error('Session error', err instanceof Error ? err.message : 'Could not start a conversation.');
        return;
      }
    }

    await streamMessageHelper({
      conversationId,
      content: userText,
      signal: abortCtrl.signal,
      onToken: (token) => {
        setStreamingContent((prev) => prev + token);
      },
      onToolCall: (toolCall) => {
        setStreamingTools((prev) => {
          const idx = prev.findIndex((t) => t.id === toolCall.id);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = toolCall;
            return updated;
          }
          return [...prev, toolCall];
        });
      },
      onComplete: () => {
        setIsStreaming(false);
        setStreamingContent('');
        setStreamingTools([]);
        refetchConversation();
        queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] });
      },
      onError: (err) => {
        setIsStreaming(false);
        toast.error('Streaming error', err.message);
      },
    });
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      toast.info('Streaming stopped');
    }
  };

  const toggleToolCollapse = (toolId: string) => {
    setCollapsedTools((prev) => ({
      ...prev,
      [toolId]: !prev[toolId],
    }));
  };

  const filteredConvs = (conversations || []).filter((c) =>
    c.title.toLowerCase().includes(searchChats.toLowerCase())
  );

  return (
    <div className="flex flex-col w-full h-[calc(100vh-3.5rem)] overflow-hidden bg-white">
      <div className="flex flex-1 w-full overflow-hidden border-t border-[#e5e7eb]">
        {/* LEFT PANEL: Conversation History */}
        <div className="w-64 shrink-0 hidden md:flex flex-col bg-[#f9fafb] border-r border-[#e5e7eb] select-none">
          <div className="p-3 pb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#111827] tracking-tight">
              Conversations
            </span>
            <button
              onClick={() => createConvMutation.mutate()}
              className="flex items-center gap-1 px-2 py-1 rounded-md bg-white hover:bg-[#f3f4f6] text-[#111827] text-xs font-medium border border-[#e5e7eb] shadow-2xs transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New</span>
            </button>
          </div>

          <div className="px-3 pb-2">
            <div className="relative flex items-center">
              <Search className="w-3.5 h-3.5 text-[#6b7280] absolute left-2" />
              <input
                type="text"
                placeholder="Filter chats..."
                value={searchChats}
                onChange={(e) => setSearchChats(e.target.value)}
                className="w-full h-7 pl-7 pr-2 rounded-md bg-white text-xs text-[#111827] placeholder:text-[#9ca3af] border border-[#e5e7eb] focus:outline-none focus:border-[#0f766e]"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-2 space-y-1">
            {filteredConvs.map((conv) => {
              const isActive = conv.id === activeConvId;

              return (
                <div
                  key={conv.id}
                  onClick={() => setActiveConvId(conv.id)}
                  className={`group p-2.5 rounded-lg border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-white border-[#0f766e] shadow-xs'
                      : 'border-transparent hover:bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-xs font-semibold truncate max-w-[130px] ${
                        isActive ? 'text-[#0f766e]' : 'text-[#111827]'
                      }`}
                    >
                      {agent?.name || 'Agent'}
                    </span>
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        if (!isStreaming) {
                          deleteConvMutation.mutate(conv.id);
                        }
                      }}
                      disabled={isStreaming || deleteConvMutation.isPending}
                      className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-[#6b7280] hover:text-[#dc2626] hover:bg-[#fee2e2] disabled:opacity-40 transition-all cursor-pointer"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <p className="text-xs font-medium text-[#111827] truncate">
                    {conv.title}
                  </p>
                  <p className="font-mono text-[10px] text-[#6b7280] truncate mt-0.5">
                    Updated {formatRelativeTime(conv.updated_at)}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="p-3 border-t border-[#e5e7eb] bg-[#f9fafb] flex items-center justify-between text-[10px] font-mono text-[#6b7280]">
            <span className="uppercase tracking-wider">Storage usage</span>
            <span className="text-[#111827]">14 / 50 chats</span>
          </div>
        </div>

        {/* CENTER PANEL: Chat Stream & Composer */}
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          {/* Top Action Bar */}
          <div className="h-13 px-4 py-2 border-b border-[#e5e7eb] flex items-center justify-between bg-white/95 backdrop-blur-xs z-10">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-7 h-7 rounded-md bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4] flex items-center justify-center font-bold text-sm shrink-0">
                <Terminal className="w-4 h-4" />
              </div>

              <div className="flex items-center gap-2 min-w-0">
                <span className="text-sm font-semibold text-[#111827] truncate">
                  {agent?.name || 'Agent Worker'}
                </span>

                {/* Routine Status Chip */}
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#f0fdfa] border border-[#99f6e4] text-[#0f766e] text-[11px] font-medium shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#0f766e] animate-pulse" />
                  <span>Executing routine</span>
                </span>
              </div>

              <div className="hidden lg:flex items-center ml-1 px-2 py-0.5 rounded bg-[#f9fafb] border border-[#e5e7eb] text-[#6b7280] font-mono text-[10px]">
                {agent?.model || 'claude-3-5-sonnet-20241022'}
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  if (activeConvId && !isStreaming) {
                    deleteConvMutation.mutate(activeConvId);
                  }
                }}
                disabled={!activeConvId || isStreaming || deleteConvMutation.isPending}
                className="p-1.5 rounded text-[#6b7280] hover:text-[#111827] hover:bg-[#f3f4f6] transition-colors cursor-pointer"
                title="Clear conversation"
              >
                <Trash2 className="w-4 h-4" />
              </button>

              <button
                onClick={() => navigate(`/agents/${agentId}/edit`)}
                className="p-1.5 rounded text-[#6b7280] hover:text-[#111827] hover:bg-[#f3f4f6] transition-colors cursor-pointer"
                title="Agent settings"
              >
                <Sliders className="w-4 h-4" />
              </button>

              <button
                onClick={() => setShowTelemetry(!showTelemetry)}
                className="lg:hidden p-1.5 rounded text-[#6b7280] hover:text-[#111827] hover:bg-[#f3f4f6] transition-colors cursor-pointer"
                title="Toggle Telemetry"
              >
                <Layers className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Message Stream Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 bg-white">
            {chatItems.map(({ message: msg, tools }) => {
              const isUser = msg.role === 'user';

              if (isUser) {
                return (
                  <div key={msg.id} className="flex items-start justify-end gap-3">
                    <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 bg-[#f3f4f6] border border-[#e5e7eb] text-[#111827] shadow-2xs">
                      <p className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap select-text">
                        {msg.content}
                      </p>
                      <div className="mt-1.5 flex items-center justify-end gap-1.5 font-mono text-[10px] text-[#6b7280]">
                        <span>{formatRelativeTime(msg.created_at)}</span>
                        <CheckCircle2 className="w-3 h-3 text-[#16a34a]" />
                      </div>
                    </div>
                  </div>
                );
              }

              // Assistant message
              return (
                <div key={msg.id} className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-md bg-[#0f766e] text-white flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                    <Bot className="w-4 h-4" />
                  </div>

                  <div className="flex-1 min-w-0 space-y-3 max-w-3xl">
                    {/* Thinking indicator */}
                    {tools.length > 0 && (
                      <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#f9fafb] border border-[#e5e7eb] text-[#4b5563] font-mono text-[11px]">
                        <Sparkles className="w-3.5 h-3.5 text-[#0f766e]" />
                        <span>Sources checked</span>
                        <span className="text-[#6b7280]">•</span>
                        <span className="text-[#6b7280]">{tools.length} tool{tools.length === 1 ? '' : 's'} used</span>
                      </div>
                    )}

                    {/* Tool Call Cards */}
                    {tools.length > 0 && (
                      <div className="space-y-2">
                        {tools.map((tool) => {
                          const isCollapsed = collapsedTools[tool.id] ?? true;

                          return (
                            <div
                              key={tool.id}
                              className="rounded-lg bg-white border border-[#e5e7eb] overflow-hidden"
                            >
                              <div
                                onClick={() => toggleToolCollapse(tool.id)}
                                className="px-3 py-2 flex items-center justify-between text-[#111827] cursor-pointer select-none"
                              >
                                <div className="flex items-center gap-2 text-xs">
                                  <span className="font-semibold text-[#0f766e]">
                                    {formatToolName(tool.tool_name)}
                                  </span>
                                  <span className="text-[#6b7280]">
                                    {formatToolSummary(tool.output)}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#f0fdf4] text-[#15803d] border border-[#bbf7d0]">
                                    Succeeded
                                  </span>
                                  {isCollapsed ? (
                                    <ChevronDown className="w-4 h-4 text-[#6b7280]" />
                                  ) : (
                                    <ChevronUp className="w-4 h-4 text-[#6b7280]" />
                                  )}
                                </div>
                              </div>

                              {!isCollapsed && (
                                <div className="px-3 pb-2.5 pt-1.5 border-t border-[#e5e7eb] bg-[#f9fafb] text-[11px] text-[#4b5563] space-y-1.5">
                                  <div>
                                    <span className="text-[#0f766e] font-medium">Query: </span>
                                    {formatToolInput(tool.input)}
                                  </div>
                                  {tool.output && (
                                    <div>
                                      <span className="text-[#16a34a] font-medium">Result: </span>
                                      {formatToolOutput(tool.output)}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Markdown Output Body */}
                    <div className="rounded-xl bg-[#f9fafb] p-4 border border-[#e5e7eb] text-xs sm:text-sm text-[#111827] leading-relaxed whitespace-pre-wrap">
                      <MarkdownMessage content={msg.content} />
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Live Streaming Assistant Message */}
            {isStreaming && (
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-md bg-[#0f766e] text-white flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0 space-y-3 max-w-3xl">
                  {/* Thinking Bar */}
                  <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#f9fafb] border border-[#e5e7eb] text-[#4b5563] font-mono text-[11px]">
                    <Loader2 className="w-3.5 h-3.5 text-[#0f766e] animate-spin" />
                    <span>Thinking & dispatching tool calls...</span>
                  </div>

                  {/* Streaming Tools */}
                  {streamingTools.length > 0 && (
                    <div className="space-y-2">
                      {streamingTools.map((tool) => (
                        <div
                          key={tool.id}
                          className="rounded-lg bg-[#f9fafb] border border-[#e5e7eb] overflow-hidden"
                        >
                          <div className="px-3 py-2 flex items-center justify-between text-[#111827]">
                            <div className="flex items-center gap-2 font-mono text-xs">
                              <span className="text-[#6b7280]">tool:</span>
                              <span className="font-semibold text-[#0f766e]">
                                {tool.tool_name}
                              </span>
                            </div>
                            <span
                              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                                tool.status === 'running'
                                  ? 'bg-[#f0fdfa] text-[#0f766e] border border-[#99f6e4]'
                                  : 'bg-[#f0fdf4] text-[#15803d] border border-[#bbf7d0]'
                              }`}
                            >
                              {tool.status === 'running' && <span className="w-1.5 h-1.5 rounded-full bg-[#0f766e] animate-ping" />}
                              {tool.status === 'running' ? 'Running' : 'Succeeded'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Streaming Content */}
                  {streamingContent && (
                    <div className="rounded-xl bg-[#f9fafb] p-4 border border-[#e5e7eb] text-xs sm:text-sm text-[#111827] leading-relaxed">
                      <MarkdownMessage content={streamingContent} />
                      <span className="inline-block w-2 h-4 ml-1 bg-[#0f766e] align-middle animate-pulse" />
                    </div>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Composer Bar */}
          <div className="p-4 pt-0 bg-white">
            <div className="max-w-3xl mx-auto rounded-xl border border-[#e5e7eb] bg-white shadow-2xs focus-within:border-[#0f766e] transition-all">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={`Message ${agent?.name || 'Agent'} or type / for tools...`}
                rows={2}
                className="w-full px-3.5 py-3 bg-transparent text-xs sm:text-sm text-[#111827] placeholder:text-[#9ca3af] resize-none focus:outline-none"
              />

              <div className="px-3 pb-2.5 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setInputMessage((prev) => prev + ' /internship_research ')}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#f3f4f6] hover:bg-[#e5e7eb] text-[#6b7280] hover:text-[#111827] font-mono text-[11px] transition-colors border border-[#e5e7eb] cursor-pointer"
                  >
                    <AtSign className="w-3 h-3" />
                    <span>tools</span>
                  </button>

                  <button
                    onClick={() => toast.info('File attachment attached to runtime memory')}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#f3f4f6] hover:bg-[#e5e7eb] text-[#6b7280] hover:text-[#111827] font-mono text-[11px] transition-colors border border-[#e5e7eb] cursor-pointer"
                  >
                    <Paperclip className="w-3 h-3" />
                    <span>Attach</span>
                  </button>

                  <span className="text-[#e5e7eb] mx-1">|</span>

                  <div className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded text-[#4b5563] font-mono text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#16a34a]" />
                    <span>{agent?.model || 'Claude 3.5 Sonnet'}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-[#6b7280] hidden sm:inline">
                    ⌘ + Enter
                  </span>

                  {isStreaming ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleStop}
                      className="h-8 px-3"
                    >
                      <Square className="w-3.5 h-3.5 fill-current" />
                      <span>Stop</span>
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSend}
                      disabled={!inputMessage.trim()}
                      className="h-8 w-8 p-0"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Agent Telemetry & Live Stream */}
        {showTelemetry && (
          <div className="w-72 shrink-0 hidden xl:flex flex-col bg-[#f9fafb] border-l border-[#e5e7eb] select-none">
            <div className="h-13 px-4 py-2 border-b border-[#e5e7eb] flex items-center justify-between bg-white">
              <span className="text-xs font-semibold text-[#111827]">
                Agent Telemetry
              </span>
              <button
                onClick={() => setShowTelemetry(false)}
                className="p-1 rounded text-[#6b7280] hover:text-[#111827] cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-5">
              {/* Objective Section */}
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280] block mb-1.5">
                  Active Objective
                </span>
                <div className="p-2.5 rounded-lg bg-white border border-[#e5e7eb] text-xs text-[#111827] leading-relaxed shadow-2xs">
                  "{agent?.objective || 'Find AI internships and draft weekly digest'}"
                </div>
              </div>

              {/* Context Window Gauge */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280]">
                    Context Window
                  </span>
                  <span className="font-mono text-[11px] text-[#0f766e] font-medium">
                    3.2%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-[#e5e7eb] rounded-full overflow-hidden">
                  <div className="h-full bg-[#0f766e] rounded-full w-[3.2%]" />
                </div>
                <div className="flex justify-between mt-1 font-mono text-[10px] text-[#6b7280]">
                  <span>4,120 tokens</span>
                  <span>128k max</span>
                </div>
              </div>

              {/* Tools in Execution Scope */}
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280] block mb-2">
                  Tools in Execution Scope
                </span>
                <div className="flex flex-wrap gap-1">
                  {(agent?.tools || ['internship_research', 'gmail_read', 'save_report', 'draft_message']).map(
                    (tool) => (
                      <span
                        key={tool}
                        className="font-mono text-[10px] px-2 py-0.5 rounded bg-white border border-[#e5e7eb] text-[#111827] shadow-2xs"
                      >
                        {tool}
                      </span>
                    )
                  )}
                </div>
              </div>

              {/* Execution Stream Live Logs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6b7280]">
                    Execution Stream
                  </span>
                  <span className="font-mono text-[10px] text-[#16a34a] flex items-center gap-1 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#16a34a]" />
                    LIVE
                  </span>
                </div>
                <div className="space-y-1.5 font-mono text-[10px] bg-white p-2.5 rounded-lg border border-[#e5e7eb] shadow-2xs">
                  <div className="flex items-start gap-2">
                    <span className="text-[#6b7280]">09:14:02</span>
                    <span className="text-[#4b5563] truncate">Task dispatched</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-[#6b7280]">09:14:04</span>
                    <span className="text-[#0f766e] truncate">Calling Lever/GH scrapers</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-[#6b7280]">09:14:06</span>
                    <span className="text-[#4b5563] truncate">14 nodes hydrated</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-[#6b7280]">09:14:07</span>
                    <span className="text-[#4b5563] truncate">6 passed filters</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-[#6b7280]">09:14:08</span>
                    <span className="text-[#0d9488] font-medium animate-pulse truncate">
                      Drafting digest payload
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Footer */}
            <div className="p-3 border-t border-[#e5e7eb] bg-[#f9fafb] flex items-center justify-between font-mono text-[10px] text-[#6b7280]">
              <span>Latency: 284ms</span>
              <span>Cost: ~$0.014</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function buildChatItems(messages: Message[]): { message: Message; tools: ToolCallPayload[] }[] {
  const items: { message: Message; tools: ToolCallPayload[] }[] = [];
  let pendingTools: ToolCallPayload[] = [];

  for (const message of messages) {
    if (message.role === 'tool') {
      const toolCalls = message.tool_calls || [];
      const parsedOutput = parseToolOutput(message.content);
      pendingTools.push(
        ...toolCalls.map((tool) => ({
          ...tool,
          output: parsedOutput,
          status: 'succeeded' as const,
        }))
      );
      continue;
    }

    if (message.role === 'assistant') {
      items.push({ message, tools: [...pendingTools, ...(message.tool_calls || [])] });
      pendingTools = [];
      continue;
    }

    items.push({ message, tools: [] });
  }

  if (pendingTools.length > 0) {
    const lastAssistant = [...items].reverse().find((item) => item.message.role === 'assistant');
    if (lastAssistant) {
      lastAssistant.tools.push(...pendingTools);
    }
  }

  return items;
}

function parseToolOutput(content: string): Record<string, unknown> | string {
  try {
    const parsed = JSON.parse(content);
    return typeof parsed === 'object' && parsed !== null ? parsed : content;
  } catch {
    return content;
  }
}

function formatToolOutput(output: Record<string, unknown> | string): string {
  if (typeof output === 'string') {
    return output.length > 320 ? `${output.slice(0, 320)}...` : output;
  }

  const status = typeof output.status === 'string' ? output.status : 'completed';
  const provider = typeof output.primary_provider === 'string' ? ` via ${output.primary_provider}` : '';
  const tavily = output.tavily_used === true ? ' + Tavily fallback' : '';
  const headline = typeof output.headline === 'string' ? ` - ${output.headline}` : '';
  return `${status}${provider}${tavily}${headline}`;
}

function formatToolName(name: string): string {
  return name
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatToolInput(input: Record<string, unknown>): string {
  const query = input.query;
  if (typeof query === 'string' && query.trim()) {
    return query;
  }
  const purpose = input.purpose;
  if (typeof purpose === 'string' && purpose.trim()) {
    return purpose;
  }
  return 'Tool input prepared by the agent.';
}

function formatToolSummary(output: Record<string, unknown> | string | undefined): string {
  if (!output) return 'completed';
  if (typeof output === 'string') return 'completed';
  if (typeof output.primary_provider === 'string') return `via ${output.primary_provider}`;
  if (typeof output.status === 'string') return output.status;
  return 'completed';
}

function MarkdownMessage({ content }: { content: string }) {
  const lines = content.split('\n');

  return (
    <div className="space-y-2">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={index} className="h-1" />;
        }

        if (/^\*\*[^*]+\*\*$/.test(trimmed)) {
          return (
            <div key={index} className="pt-1 text-sm font-semibold text-[#111827]">
              {trimmed.slice(2, -2)}
            </div>
          );
        }

        if (/^\d+\.\s+/.test(trimmed)) {
          return (
            <div key={index} className="flex gap-2">
              <span className="text-[#6b7280]">{trimmed.match(/^\d+\./)?.[0]}</span>
              <span>{renderInlineMarkdown(trimmed.replace(/^\d+\.\s+/, ''))}</span>
            </div>
          );
        }

        if (trimmed.startsWith('- ')) {
          return (
            <div key={index} className="flex gap-2">
              <span className="text-[#0f766e]">-</span>
              <span>{renderInlineMarkdown(trimmed.slice(2))}</span>
            </div>
          );
        }

        return <p key={index}>{renderInlineMarkdown(line)}</p>;
      })}
    </div>
  );
}

function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-[#111827]">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={index} className="px-1 py-0.5 rounded bg-white border border-[#e5e7eb] font-mono text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}
