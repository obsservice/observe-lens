'use client';

import { AppShell } from '@/components/observe-lens/app-shell';
import { StatusBadge } from '@/components/observe-lens/status-badge';
import { Button } from '@/components/ui/button';
import {
  conversationQueryKeys,
  createConversation,
  listConversations,
  listMessages,
  messageQueryKeys,
  streamConversationMessage,
  updateConversation,
  type AESPEvent,
  type Conversation,
  type Message,
} from '@/lib/api/conversations';
import { ApiError } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Archive,
  Check,
  Clock,
  ChevronDown,
  ChevronUp,
  Download,
  Edit3,
  Info,
  Loader2,
  MessageSquarePlus,
  MoreHorizontal,
  Paperclip,
  Search,
  Send,
  Share2,
  RotateCcw,
} from 'lucide-react';
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

const conversationListParams = { page: 1, page_size: 100 };

function formatConversationDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
    month: '2-digit',
  });
}

function conversationStatusTone(status: string): 'emerald' | 'slate' {
  return status.toUpperCase() === 'ACTIVE' ? 'emerald' : 'slate';
}

function formatMessageTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('zh-CN', {
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
  });
}

function isUserMessage(role: string): boolean {
  return role.toUpperCase() === 'USER';
}

function ChatMessageBubble({ message }: { message: Message }): ReactNode {
  const fromUser = isUserMessage(message.role);

  return (
    <div
      className={cn(
        'flex items-start gap-3',
        fromUser ? 'justify-end' : 'justify-start',
      )}
    >
      <div
        className={cn(
          'max-w-[680px] rounded-lg px-4 py-3 text-sm leading-6',
          fromUser
            ? 'bg-blue-600 text-white'
            : 'border border-slate-200 bg-white text-slate-800',
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <p
          className={cn(
            'mt-1.5 text-xs',
            fromUser ? 'text-blue-100' : 'text-slate-400',
          )}
        >
          {formatMessageTime(message.created_at)}
        </p>
      </div>
      {fromUser ? (
        <div className="grid size-9 shrink-0 place-items-center rounded-full bg-slate-700 text-sm font-semibold text-white">
          U
        </div>
      ) : null}
    </div>
  );
}

interface InvestigationStep {
  stepId: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  summary?: string;
}

interface InvestigationObservation {
  id: string;
  title: string;
  observationType: string;
  summary?: string;
  content?: Record<string, unknown>;
}

interface InvestigationFinding {
  id: string;
  title: string;
  category?: string;
  analysis?: string;
}

interface InvestigationState {
  analysis: string | null;
  steps: InvestigationStep[];
  observations: InvestigationObservation[];
  findings: InvestigationFinding[];
  output: string;
  error: string | null;
}

const emptyInvestigation: InvestigationState = {
  analysis: null,
  steps: [],
  observations: [],
  findings: [],
  output: '',
  error: null,
};

function applyEventToInvestigation(
  prev: InvestigationState,
  event: AESPEvent,
): InvestigationState {
  const data = event.data;
  const next: InvestigationState = { ...prev };

  switch (event.type) {
    case 'analysis.generated': {
      const content = data['content'];
      if (typeof content === 'string') next.analysis = content;
      break;
    }
    case 'plan.generated': {
      const steps = data['steps'];
      if (Array.isArray(steps)) {
        next.steps = steps.map((step) => {
          const s = step as Record<string, unknown>;
          return {
            stepId: String(s['step_id'] ?? s['id'] ?? ''),
            title: String(s['title'] ?? ''),
            status: 'pending' as const,
          };
        });
      }
      break;
    }
    case 'step.started': {
      const stepId = String(data['step_id'] ?? '');
      const title = String(data['title'] ?? '');
      next.steps = prev.steps.map((s) =>
        s.stepId === stepId
          ? { ...s, title: title || s.title, status: 'running' }
          : s,
      );
      if (!next.steps.some((s) => s.stepId === stepId)) {
        next.steps = [
          ...prev.steps,
          { stepId, title, status: 'running' as const },
        ];
      }
      break;
    }
    case 'step.completed': {
      const stepId = String(data['step_id'] ?? '');
      const summary = data['summary'];
      next.steps = prev.steps.map((s) =>
        s.stepId === stepId
          ? {
              ...s,
              status: 'completed' as const,
              summary: typeof summary === 'string' ? summary : s.summary,
            }
          : s,
      );
      break;
    }
    case 'step.failed': {
      const stepId = String(data['step_id'] ?? '');
      next.steps = prev.steps.map((s) =>
        s.stepId === stepId ? { ...s, status: 'failed' as const } : s,
      );
      break;
    }
    case 'observation.generated': {
      const id = String(data['id'] ?? '');
      if (!prev.observations.some((o) => o.id === id)) {
        next.observations = [
          ...prev.observations,
          {
            id,
            title: String(data['title'] ?? ''),
            observationType: String(data['observation_type'] ?? ''),
            summary:
              typeof data['summary'] === 'string' ? data['summary'] : undefined,
            content:
              data['content'] && typeof data['content'] === 'object'
                ? (data['content'] as Record<string, unknown>)
                : undefined,
          },
        ];
      }
      break;
    }
    case 'finding.generated': {
      const id = String(data['id'] ?? '');
      if (!prev.findings.some((f) => f.id === id)) {
        next.findings = [
          ...prev.findings,
          {
            id,
            title: String(data['title'] ?? ''),
            category:
              typeof data['category'] === 'string'
                ? data['category']
                : undefined,
            analysis:
              typeof data['analysis'] === 'string'
                ? data['analysis']
                : undefined,
          },
        ];
      }
      break;
    }
    case 'output.progress': {
      const delta = data['content'];
      if (typeof delta === 'string') next.output = prev.output + delta;
      break;
    }
    case 'output.completed': {
      const content = data['content'];
      if (typeof content === 'string') next.output = content;
      break;
    }
    case 'run.failed': {
      const message = data['message'];
      if (typeof message === 'string') next.error = message;
      break;
    }
  }

  return next;
}

function restoreInvestigation(events: AESPEvent[]): InvestigationState {
  return events.reduce(applyEventToInvestigation, emptyInvestigation);
}

function stepStatusTone(
  status: InvestigationStep['status'],
): 'blue' | 'emerald' | 'red' | 'slate' {
  switch (status) {
    case 'running':
      return 'blue';
    case 'completed':
      return 'emerald';
    case 'failed':
      return 'red';
    default:
      return 'slate';
  }
}

function stepStatusLabel(status: InvestigationStep['status']): string {
  switch (status) {
    case 'running':
      return '运行中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    default:
      return '待开始';
  }
}

function findingCategoryTone(
  category?: string,
): 'amber' | 'red' | 'blue' | 'slate' {
  switch (category) {
    case 'issue':
      return 'red';
    case 'risk':
      return 'amber';
    case 'anomaly':
      return 'blue';
    default:
      return 'slate';
  }
}

function ObservationContent({
  content,
  type,
}: {
  content: Record<string, unknown>;
  type: string;
}): ReactNode {
  if (type === 'table' && Array.isArray(content['columns']) && Array.isArray(content['rows'])) {
    const columns = content['columns'] as unknown[];
    const rows = content['rows'] as unknown[][];

    return (
      <div className="mt-3 overflow-hidden rounded border border-slate-200">
        <table className="w-full text-left text-[11px]">
          <thead className="bg-slate-50 text-slate-500"><tr>{columns.map((column) => <th className="px-2 py-1.5 font-medium" key={String(column)}>{String(column)}</th>)}</tr></thead>
          <tbody className="divide-y divide-slate-100">{rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td className="px-2 py-1.5 text-slate-700" key={cellIndex}>{String(cell)}</td>)}</tr>)}</tbody>
        </table>
      </div>
    );
  }

  if (type === 'log' && Array.isArray(content['lines'])) {
    return <pre className="mt-3 overflow-x-auto rounded bg-slate-950 px-3 py-2 text-[11px] leading-5 text-slate-200">{(content['lines'] as unknown[]).map(String).join('\n')}</pre>;
  }

  if (type === 'chart' && Array.isArray(content['x_axis']) && Array.isArray(content['series'])) {
    const series = content['series'] as Array<Record<string, unknown>>;
    return (
      <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-3">
        <div className="flex h-16 items-end gap-1">
          {(content['x_axis'] as unknown[]).map((_, index) => {
            const value = Number((series[0]?.['values'] as unknown[] | undefined)?.[index] ?? 0);
            return <div className="flex-1 rounded-t bg-blue-400" key={index} style={{ height: `${Math.max(10, Math.min(100, value))}%` }} />;
          })}
        </div>
        <div className="mt-2 flex justify-between text-[10px] text-slate-400">{(content['x_axis'] as unknown[]).map((label) => <span key={String(label)}>{String(label)}</span>)}</div>
      </div>
    );
  }

  return null;
}

function InvestigationPanel({
  investigation,
  isStreaming,
}: {
  investigation: InvestigationState;
  isStreaming: boolean;
}): ReactNode {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const hasContent =
    investigation.analysis !== null ||
    investigation.steps.length > 0 ||
    investigation.observations.length > 0 ||
    investigation.findings.length > 0 ||
    investigation.output !== '' ||
    investigation.error !== null;

  if (!hasContent && !isStreaming) {
    return null;
  }

  return (
    <div className="flex items-start">
      <div className="min-w-0 flex-1 space-y-3">
        {investigation.analysis ? (
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-100">
            <div className="flex h-11 items-center gap-2 px-4">
              <Info className="text-blue-600" size={16} />
              <h3 className="text-sm font-semibold text-slate-900">
                Info 分析信息
              </h3>
              <ChevronDown className="ml-auto text-slate-500" size={15} />
            </div>
            <p className="border-t border-slate-100 px-4 py-3 text-sm leading-6 text-slate-700">
              {investigation.analysis}
            </p>
          </section>
        ) : null}

        {investigation.steps.length > 0 ? (
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-100">
            <div className="flex h-11 items-center gap-2 px-4">
              <span className="grid size-5 place-items-center rounded border border-slate-400 text-[11px] text-slate-600">⌕</span>
              <h3 className="text-sm font-semibold text-slate-900">
                Investigation 调查过程
              </h3>
              <ChevronUp className="ml-auto text-slate-500" size={15} />
            </div>
            <div className="border-t border-slate-200 px-3 py-3">
              <p className="mb-3 px-1 text-xs font-semibold text-slate-700">执行计划</p>
              <div className="mb-3 flex items-center gap-1 overflow-x-auto px-1 pb-1">
                {investigation.steps.map((step, index) => (
                  <div className="flex min-w-[120px] flex-1 items-center gap-1" key={`plan-${step.stepId || index}`}>
                    <span className={cn(
                      'grid size-5 shrink-0 place-items-center rounded-full border text-[11px] font-semibold',
                      step.status === 'completed' ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-blue-300 text-blue-600',
                    )}>{index + 1}</span>
                    <span className="truncate text-xs text-slate-600">{step.title}</span>
                    {index < investigation.steps.length - 1 ? <span className="mx-1 h-px flex-1 bg-slate-300" /> : null}
                  </div>
                ))}
              </div>
            <div className="divide-y divide-slate-200 rounded-md border border-slate-200">
              {investigation.steps.map((step, index) => (
                <button
                  className="grid w-full grid-cols-[1fr_auto] items-center gap-4 px-3 py-2.5 text-left transition hover:bg-slate-50"
                  key={step.stepId || index}
                  onClick={() => {
                    const stepKey = step.stepId || String(index);
                    setExpandedSteps((current) => {
                      const next = new Set(current);
                      if (next.has(stepKey)) {
                        next.delete(stepKey);
                      } else {
                        next.add(stepKey);
                      }
                      return next;
                    });
                  }}
                  type="button"
                >
                  <div className="flex min-w-0 items-start gap-3">
                    <span
                      className={cn(
                        'mt-0.5 grid size-5 shrink-0 place-items-center rounded-full text-xs font-semibold text-white',
                        step.status === 'completed' && 'bg-emerald-500',
                        step.status === 'running' && 'bg-blue-600',
                        step.status === 'failed' && 'bg-red-500',
                        step.status === 'pending' &&
                          'bg-slate-300 text-slate-600',
                      )}
                    >
                      {step.status === 'completed'
                        ? '✓'
                        : step.status === 'failed'
                          ? '✕'
                          : index + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-slate-900">
                        步骤 {index + 1}
                        <span className="ml-3">{step.title}</span>
                      </p>
                      {step.summary ? (
                        <p className="mt-1 truncate text-xs text-slate-600">
                          {step.summary}
                        </p>
                      ) : null}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge tone={stepStatusTone(step.status)}>{stepStatusLabel(step.status)}</StatusBadge>
                    {expandedSteps.has(step.stepId || String(index)) ? (
                      <ChevronUp className="text-slate-400" size={14} />
                    ) : (
                      <ChevronDown className="text-slate-400" size={14} />
                    )}
                  </div>
                  {expandedSteps.has(step.stepId || String(index)) ? (
                    <div className="col-span-2 ml-8 border-t border-slate-100 pt-2 text-xs leading-5 text-slate-600">
                      {step.summary || (step.status === 'pending' ? '等待上一步完成' : '暂无详细信息')}
                    </div>
                  ) : null}
                </button>
              ))}
            </div>
            </div>
          </section>
        ) : null}

        {investigation.observations.length > 0 ? (
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-100">
            <div className="flex h-11 items-center gap-2 px-4">
              <span className="text-blue-600">◈</span>
              <h3 className="text-sm font-semibold text-slate-900">
                Entity 相关实体（{investigation.observations.length}）
              </h3>
              <ChevronUp className="ml-auto text-slate-500" size={15} />
            </div>
            <div className="divide-y divide-slate-100 border-t border-slate-100">
              {investigation.observations.map((obs) => (
                <div className="px-4 py-3" key={obs.id}>
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-slate-900">
                      {obs.title}
                    </p>
                    <StatusBadge tone="violet">
                      {obs.observationType}
                    </StatusBadge>
                  </div>
                  {obs.summary ? (
                    <p className="mt-1 text-xs text-slate-600">{obs.summary}</p>
                  ) : null}
                  {obs.content ? <ObservationContent content={obs.content} type={obs.observationType} /> : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {investigation.findings.length > 0 ? (
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-100">
            <div className="flex h-10 items-center px-4">
              <h3 className="text-sm font-semibold text-slate-900">
                Finding 发现（{investigation.findings.length}）
              </h3>
            </div>
            <div className="divide-y divide-slate-100 border-t border-slate-100">
              {investigation.findings.map((finding) => (
                <div className="px-4 py-3" key={finding.id}>
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-slate-900">
                      {finding.title}
                    </p>
                    {finding.category ? (
                      <StatusBadge tone={findingCategoryTone(finding.category)}>
                        {finding.category}
                      </StatusBadge>
                    ) : null}
                  </div>
                  {finding.analysis ? (
                    <p className="mt-1 text-xs leading-5 text-slate-600">
                      {finding.analysis}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {investigation.output ? (
          <section className="rounded-lg border border-slate-200 bg-white shadow-sm shadow-slate-100">
            <div className="flex h-11 items-center gap-2 px-4">
              <span className="text-slate-700">▤</span>
              <h3 className="text-sm font-semibold text-slate-900">
                RCA 根因分析报告
              </h3>
              <ChevronUp className="ml-auto text-slate-500" size={15} />
            </div>
            <div className="border-t border-slate-100 px-4 py-3">
              <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">
                {investigation.output}
              </p>
              {isStreaming ? (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-violet-400 align-middle" />
              ) : null}
            </div>
          </section>
        ) : null}

        {investigation.error ? (
          <section className="rounded-md border border-red-200 bg-red-50 px-4 py-3">
            <p className="text-sm font-medium text-red-700">
              {investigation.error}
            </p>
          </section>
        ) : null}

        {isStreaming &&
        !investigation.analysis &&
        investigation.steps.length === 0 ? (
          <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
            <Loader2 aria-hidden="true" className="animate-spin" size={14} />
            Thinking…
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ChatMessageList({
  investigation,
  isStreaming,
  isLoading,
  messages,
}: {
  investigation: InvestigationState;
  isStreaming: boolean;
  isLoading: boolean;
  messages: Message[];
}): ReactNode {
  const scrollRef = useRef<HTMLDivElement>(null);
  const visibleMessages = useMemo(() => {
    if (!investigation.output) {
      return messages;
    }

    const latestAssistantIndex = messages.findLastIndex(
      (message) => !isUserMessage(message.role),
    );

    if (latestAssistantIndex === -1) {
      return messages;
    }

    return messages.filter((_, index) => index !== latestAssistantIndex);
  }, [investigation.output, messages]);

  useEffect(() => {
    const element = scrollRef.current;

    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages, investigation, isStreaming]);

  return (
    <div
      className="min-h-0 flex-1 overflow-y-auto px-6 pb-32 pt-7"
      ref={scrollRef}
    >
      <div className="mx-auto w-full max-w-[1080px] space-y-4">
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Clock aria-hidden="true" className="animate-pulse" size={14} />
            Loading messages…
          </div>
        ) : visibleMessages.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center">
            <p className="text-sm font-medium text-slate-600">
              No messages yet
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Send a message below to start the investigation.
            </p>
          </div>
        ) : (
          visibleMessages.map((message) => (
            <ChatMessageBubble key={message.id} message={message} />
          ))
        )}
        {isStreaming ||
        investigation.analysis ||
        investigation.steps.length > 0 ||
        investigation.observations.length > 0 ||
        investigation.findings.length > 0 ||
        investigation.output ||
        investigation.error ? (
          <InvestigationPanel
            investigation={investigation}
            isStreaming={isStreaming}
          />
        ) : null}
      </div>
    </div>
  );
}

function ChatMessageInput({
  conversationId,
  isStreaming,
  onSent,
  onStreamEvent,
  onStreamStart,
  onStreamEnd,
}: {
  conversationId: number;
  isStreaming: boolean;
  onSent: () => void;
  onStreamEvent: (event: AESPEvent) => void;
  onStreamStart: () => void;
  onStreamEnd: () => void;
}): ReactNode {
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = content.trim();

    if (!trimmed || isStreaming) {
      return;
    }

    setContent('');
    setError(null);
    onStreamStart();

    const controller = new AbortController();
    abortRef.current = controller;

    void streamConversationMessage(
      conversationId,
      trimmed,
      {
        onComplete: () => {
          abortRef.current = null;
          onStreamEnd();
          onSent();
        },
        onError: (err) => {
          abortRef.current = null;
          onStreamEnd();
          setError(err.message);
        },
        onEvent: onStreamEvent,
      },
      controller.signal,
    );
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    onStreamEnd();
  };

  useEffect(() => {
    const textarea = textareaRef.current;

    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }
  }, [content]);

  return (
    <div className="absolute bottom-4 left-0 right-0 px-6">
      <form
        className="mx-auto w-full max-w-[1080px] rounded-lg border border-blue-500 bg-white p-3 shadow-lg shadow-slate-200/60"
        onSubmit={handleSubmit}
      >
        <textarea
          className="max-h-40 w-full resize-none border-0 text-sm text-slate-800 outline-none placeholder:text-slate-400"
          onChange={(event) => setContent(event.target.value)}
          placeholder="Ask anything about your observability data..."
          ref={textareaRef}
          rows={1}
          value={content}
        />
        {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
        <div className="flex items-center justify-between">
          <button className="inline-flex h-8 items-center gap-1 rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-700 hover:bg-slate-50" type="button">
            <Paperclip size={14} /> Attach <ChevronDown size={13} />
          </button>
          <div className="flex items-center">
          {isStreaming ? (
            <button
              className="mr-2 rounded-md border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
              onClick={handleCancel}
              type="button"
            >
              Stop
            </button>
          ) : null}
          <Button
            aria-label="Send message"
            className="size-9 px-0"
            disabled={!content.trim() || isStreaming}
            type="submit"
          >
            <Send aria-hidden="true" size={16} />
          </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function ChatSessionList({
  conversations,
  isCollapsed,
  isLoading,
  onCreate,
  onSelect,
  onToggle,
  search,
  selectedConversationId,
  setSearch,
}: {
  conversations: Conversation[];
  isCollapsed: boolean;
  isLoading: boolean;
  onCreate: () => void;
  onSelect: (conversationId: number) => void;
  onToggle: () => void;
  search: string;
  selectedConversationId: number | null;
  setSearch: (value: string) => void;
}): ReactNode {
  if (isCollapsed) {
    return null;
  }

  return (
    <aside className="w-[346px] shrink-0 border-r border-slate-200 bg-white">
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-6">
        <h1 className="text-lg font-semibold tracking-normal text-slate-950">
          Sessions
        </h1>
        <button
          aria-label="Collapse sessions"
          className="grid size-8 place-items-center rounded-md text-xl font-light text-slate-400 transition hover:bg-slate-50 hover:text-slate-700"
          onClick={onToggle}
          type="button"
        >
          ‹
        </button>
      </div>
      <div className="mt-4 flex gap-3 px-6">
        <label className="relative flex-1">
          <span className="sr-only">Search sessions</span>
          <input
            className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 pr-10 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search sessions..."
            type="search"
            value={search}
          />
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-700" size={17} />
        </label>
        <Button
          aria-label="New session"
          className="size-10 rounded-md border-blue-500 bg-white px-0 text-xl text-blue-600 hover:bg-blue-50"
          disabled={isLoading}
          onClick={onCreate}
          variant="outline"
        >
          +
        </Button>
      </div>

      <div className="mt-5 space-y-1 px-5">
        {isLoading ? (
          <p className="px-2.5 py-3 text-sm text-slate-500">
            Loading sessions…
          </p>
        ) : conversations.length === 0 ? (
          <p className="px-2.5 py-3 text-sm text-slate-500">
            No sessions found.
          </p>
        ) : (
          conversations.map((conversation) => {
            const isActive = conversation.id === selectedConversationId;

            return (
              <button
                className={cn(
                  'flex w-full gap-3 rounded-lg px-2.5 py-3.5 text-left transition',
                  isActive
                    ? 'bg-blue-50/80 shadow-sm shadow-blue-100'
                    : 'hover:bg-slate-50',
                )}
                key={conversation.id}
                onClick={() => onSelect(conversation.id)}
                type="button"
              >
                <div className={cn(
                  'grid size-9 shrink-0 place-items-center rounded-md text-white',
                  isActive ? 'bg-emerald-500' : 'bg-violet-100 text-violet-600',
                )}>
                  <MessageSquarePlus aria-hidden="true" size={17} />
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="truncate text-sm font-semibold text-slate-950">
                    {conversation.title}
                  </h2>
                  <div className="mt-1 flex items-center justify-between whitespace-nowrap text-xs text-slate-500">
                    <span>{conversation.status.toUpperCase() === 'ACTIVE' ? '进行中' : '已归档'}</span>
                    <span>{formatConversationDate(conversation.updated_at)}</span>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  return 'Unable to load sessions. Please try again.';
}

function NewSessionDialog({
  error,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
}: {
  error: unknown;
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (title: string) => void;
}): ReactNode {
  const [title, setTitle] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const closeDialog = (): void => {
    if (isSubmitting) {
      return;
    }

    setTitle('');
    setValidationError(null);
    onClose();
  };

  useEffect(() => {
    if (!isOpen) {
      setTitle('');
      setValidationError(null);
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[480px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              New session
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Give this investigation conversation a descriptive title.
            </p>
          </div>
          <button
            aria-label="Close new session dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            disabled={isSubmitting}
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>
        <form
          className="space-y-5 px-6 py-5"
          onSubmit={(event) => {
            event.preventDefault();
            const nextTitle = title.trim();

            if (!nextTitle) {
              setValidationError('Session title is required.');
              return;
            }

            if (nextTitle.length > 256) {
              setValidationError(
                'Session title must be 256 characters or fewer.',
              );
              return;
            }

            setValidationError(null);
            onSubmit(nextTitle);
          }}
        >
          <label className="block" htmlFor="new-session-title">
            <span className="text-sm font-medium text-slate-800">
              Session title
            </span>
            <input
              autoFocus
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                validationError ? 'border-red-300' : 'border-slate-200',
              )}
              disabled={isSubmitting}
              id="new-session-title"
              maxLength={256}
              onChange={(event) => {
                setTitle(event.target.value);
                setValidationError(null);
              }}
              placeholder="e.g. API error-rate investigation"
              value={title}
            />
            {validationError ? (
              <span className="mt-1 block text-xs text-red-600">
                {validationError}
              </span>
            ) : null}
          </label>
          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {getErrorMessage(error)}
            </p>
          ) : null}
          <div className="flex justify-end gap-3">
            <Button
              disabled={isSubmitting}
              onClick={closeDialog}
              variant="ghost"
            >
              Cancel
            </Button>
            <Button disabled={isSubmitting} type="submit">
              {isSubmitting ? 'Creating…' : 'Create session'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function HomePage(): ReactNode {
  const queryClient = useQueryClient();
  const [isSessionsCollapsed, setIsSessionsCollapsed] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedConversationId, setSelectedConversationId] = useState<
    number | null
  >(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isNewSessionDialogOpen, setIsNewSessionDialogOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [messageRefreshKey, setMessageRefreshKey] = useState(0);
  const [isStreaming, setIsStreaming] = useState(false);
  const [investigation, setInvestigation] =
    useState<InvestigationState>(emptyInvestigation);

  const streamAbortRef = useRef<AbortController | null>(null);

  const conversationsQuery = useQuery({
    queryFn: () => listConversations(conversationListParams),
    queryKey: conversationQueryKeys.list(conversationListParams),
  });

  const conversationItems = conversationsQuery.data?.items;
  const conversations = useMemo(
    () => conversationItems ?? [],
    [conversationItems],
  );
  const filteredConversations = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase();

    if (!normalizedSearch) {
      return conversations;
    }

    return conversations.filter((conversation) =>
      conversation.title.toLocaleLowerCase().includes(normalizedSearch),
    );
  }, [conversations, search]);

  useEffect(() => {
    if (
      selectedConversationId !== null &&
      conversations.some(
        (conversation) => conversation.id === selectedConversationId,
      )
    ) {
      return;
    }

    setSelectedConversationId(conversations[0]?.id ?? null);
  }, [conversations, selectedConversationId]);

  const selectedConversation =
    conversations.find(
      (conversation) => conversation.id === selectedConversationId,
    ) ?? null;

  useEffect(() => {
    setTitle(selectedConversation?.title ?? '');
    setIsEditingTitle(false);
  }, [selectedConversation?.id, selectedConversation?.title]);

  const messagesQuery = useQuery({
    enabled: selectedConversationId !== null,
    queryFn: () => listMessages(selectedConversationId!, { page_size: 100 }),
    queryKey: messageQueryKeys.list(selectedConversationId ?? 0, {
      page_size: 100,
    }),
  });
  const currentMessages = useMemo(
    () =>
      (messagesQuery.data?.items ?? []).filter(
        (message) => message.conversation_id === selectedConversationId,
      ),
    [messagesQuery.data?.items, selectedConversationId],
  );

  useEffect(() => {
    const assistantMessage = [...currentMessages]
      .reverse()
      .find((message) => !isUserMessage(message.role));
    const events = assistantMessage?.metadata?.events;

    setInvestigation(events?.length ? restoreInvestigation(events) : emptyInvestigation);
  }, [currentMessages, selectedConversationId]);

  useEffect(() => {
    void messagesQuery.refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConversationId, messageRefreshKey]);

  const invalidateConversations = async (): Promise<void> => {
    await queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.all,
    });
  };

  const refreshMessages = (): void => {
    setMessageRefreshKey((value) => value + 1);
  };

  const handleStreamStart = (): void => {
    setIsStreaming(true);
    setInvestigation(emptyInvestigation);
  };

  const handleStreamEnd = (): void => {
    setIsStreaming(false);
  };

  const handleStreamEvent = (event: AESPEvent): void => {
    setInvestigation((prev) => applyEventToInvestigation(prev, event));
  };

  useEffect(() => {
    const abortRef = streamAbortRef;

    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const createMutation = useMutation({
    mutationFn: (conversationTitle: string) =>
      createConversation({ title: conversationTitle }),
    onSuccess: async (conversation) => {
      setSelectedConversationId(conversation.id);
      setIsNewSessionDialogOpen(false);
      await invalidateConversations();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      conversationId,
      title: nextTitle,
      status,
    }: {
      conversationId: number;
      title?: string;
      status?: string;
    }) => updateConversation(conversationId, { status, title: nextTitle }),
    onSuccess: async () => {
      setIsEditingTitle(false);
      await invalidateConversations();
    },
  });

  const saveTitle = (): void => {
    const nextTitle = title.trim();

    if (
      !selectedConversation ||
      !nextTitle ||
      nextTitle === selectedConversation.title
    ) {
      setIsEditingTitle(false);
      setTitle(selectedConversation?.title ?? '');
      return;
    }

    updateMutation.mutate({
      conversationId: selectedConversation.id,
      title: nextTitle,
    });
  };

  const error =
    conversationsQuery.error ?? messagesQuery.error ?? updateMutation.error;

  const openNewSessionDialog = (): void => {
    createMutation.reset();
    setIsNewSessionDialogOpen(true);
  };

  const closeNewSessionDialog = (): void => {
    createMutation.reset();
    setIsNewSessionDialogOpen(false);
  };

  return (
    <AppShell activeItem="Sessions" activeSection="chat">
      <NewSessionDialog
        error={createMutation.error}
        isOpen={isNewSessionDialogOpen}
        isSubmitting={createMutation.isPending}
        onClose={closeNewSessionDialog}
        onSubmit={(conversationTitle) => {
          createMutation.mutate(conversationTitle);
        }}
      />
      <div className="flex min-h-0 flex-1">
        <ChatSessionList
          conversations={filteredConversations}
          isCollapsed={isSessionsCollapsed}
          isLoading={conversationsQuery.isLoading}
          onCreate={openNewSessionDialog}
          onSelect={setSelectedConversationId}
          onToggle={() => setIsSessionsCollapsed((value) => !value)}
          search={search}
          selectedConversationId={selectedConversationId}
          setSearch={setSearch}
        />
        <section className="relative flex min-w-0 flex-1 flex-col border-x border-slate-200 bg-white">
          <div className="flex min-h-[76px] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
            <div className="flex min-w-0 items-center gap-3">
              {isSessionsCollapsed ? (
                <button
                  aria-label="Expand sessions"
                  className="grid size-8 shrink-0 place-items-center rounded-md border border-blue-200 bg-blue-50 text-sm font-semibold text-blue-700 shadow-sm transition hover:bg-blue-100"
                  onClick={() => setIsSessionsCollapsed(false)}
                  type="button"
                >
                  ›
                </button>
              ) : null}
              {selectedConversation ? (
                isEditingTitle ? (
                  <input
                    autoFocus
                    className="h-8 min-w-0 max-w-md rounded border border-blue-300 px-2 text-lg font-semibold text-slate-950 outline-none ring-2 ring-blue-100"
                    disabled={updateMutation.isPending}
                    onChange={(event) => setTitle(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        saveTitle();
                      }
                      if (event.key === 'Escape') {
                        setIsEditingTitle(false);
                        setTitle(selectedConversation.title);
                      }
                    }}
                    value={title}
                  />
                ) : (
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h2 className="truncate text-lg font-semibold text-slate-950">
                        {selectedConversation.title}
                      </h2>
                      <button aria-label="Rename session" className="text-slate-700 hover:text-blue-600" onClick={() => setIsEditingTitle(true)} type="button"><Edit3 size={14} /></button>
                      <span className="text-amber-400">★</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">创建于 {formatConversationDate(selectedConversation.created_at)}</p>
                  </div>
                )
              ) : (
                <h2 className="text-lg font-semibold text-slate-950">
                  Sessions
                </h2>
              )}
              {selectedConversation ? (
                <StatusBadge
                  tone={conversationStatusTone(selectedConversation.status)}
                >
                  {selectedConversation.status}
                </StatusBadge>
              ) : null}
            </div>
            {selectedConversation ? (
              <div className="flex shrink-0 items-center gap-2">
                <Button size="sm" variant="ghost"><Share2 size={14} />Share</Button>
                <Button size="sm" variant="ghost"><Download size={14} />Export</Button>
                <Button aria-label="More session actions" size="sm" variant="ghost"><MoreHorizontal size={16} /></Button>
                {isEditingTitle ? (
                  <Button
                    aria-label="Save session title"
                    disabled={updateMutation.isPending}
                    onClick={saveTitle}
                    size="sm"
                  >
                    <Check aria-hidden="true" size={15} />
                    Save
                  </Button>
                ) : (
                  <Button
                    aria-label="Edit session title"
                    onClick={() => setIsEditingTitle(true)}
                    size="sm"
                    variant="ghost"
                  >
                    <Edit3 aria-hidden="true" size={15} />
                    Rename
                  </Button>
                )}
                <Button
                  disabled={updateMutation.isPending}
                  onClick={() =>
                    updateMutation.mutate({
                      conversationId: selectedConversation.id,
                      status:
                        selectedConversation.status.toUpperCase() === 'ACTIVE'
                          ? 'ARCHIVED'
                          : 'ACTIVE',
                    })
                  }
                  size="sm"
                  variant="outline"
                >
                  {selectedConversation.status.toUpperCase() === 'ACTIVE' ? (
                    <Archive aria-hidden="true" size={15} />
                  ) : (
                    <RotateCcw aria-hidden="true" size={15} />
                  )}
                  {selectedConversation.status.toUpperCase() === 'ACTIVE'
                    ? 'Archive'
                    : 'Restore'}
                </Button>
              </div>
            ) : null}
          </div>

          {selectedConversation ? (
            <>
              <ChatMessageList
                isLoading={messagesQuery.isLoading}
                messages={currentMessages}
                investigation={investigation}
                isStreaming={isStreaming}
              />
              <ChatMessageInput
                conversationId={selectedConversation.id}
                isStreaming={isStreaming}
                onSent={refreshMessages}
                onStreamEvent={handleStreamEvent}
                onStreamStart={handleStreamStart}
                onStreamEnd={handleStreamEnd}
              />
            </>
          ) : conversationsQuery.isLoading ? (
            <div className="flex min-h-0 flex-1 items-center justify-center">
              <p className="text-sm text-slate-500">Loading sessions…</p>
            </div>
          ) : error ? (
            <div className="flex min-h-0 flex-1 items-center justify-center">
              <div className="max-w-md text-center">
                <p className="text-sm font-medium text-red-700">
                  {getErrorMessage(error)}
                </p>
                <Button
                  className="mt-4"
                  onClick={() => void conversationsQuery.refetch()}
                  variant="outline"
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex min-h-0 flex-1 items-center justify-center">
              <div className="max-w-md text-center">
                <p className="text-lg font-semibold text-slate-900">
                  No conversation selected
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  Create a session to start an investigation conversation.
                </p>
                <Button
                  className="mt-5"
                  disabled={createMutation.isPending}
                  onClick={openNewSessionDialog}
                >
                  <MessageSquarePlus aria-hidden="true" size={16} />
                  New session
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
