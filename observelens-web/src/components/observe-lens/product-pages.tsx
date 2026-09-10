'use client';

import {
  AppShell,
  FilterInput,
  PageHeader,
} from '@/components/observe-lens/app-shell';
import {
  DataTable,
  type DataColumn,
} from '@/components/observe-lens/data-table';
import { ActionButton } from '@/components/observe-lens/interactive-controls';
import {
  StatusBadge,
  type StatusTone,
} from '@/components/observe-lens/status-badge';
import {
  createInspection,
  deleteInspection,
  disableInspection,
  enableInspection,
  executeInspection,
  inspectionQueryKeys,
  listInspections,
  listInspectionSchedules,
  listInspectionStatuses,
  type Inspection,
  type InspectionOption,
  type InspectionWriteRequest,
} from '@/lib/api/inspections';
import {
  conversationQueryKeys,
  listConversations,
  listMessages,
  messageQueryKeys,
  type AESPEvent,
  type Conversation,
  type Message,
} from '@/lib/api/conversations';
import {
  createIncidentIntegration,
  deleteIncidentIntegration,
  incidentQueryKeys,
  incidentIntegrationQueryKeys,
  listIncidentSeverities,
  listIncidentStatuses,
  listIncidentIntegrationStatuses,
  listIncidentIntegrationTypes,
  listIncidents,
  listIncidentIntegrations,
  openIncidentConversation,
  transitionIncident,
  updateIncident,
  type Incident,
  type IncidentIntegration,
  type UpdateIncidentRequest,
  type IncidentOption,
  updateIncidentIntegration,
} from '@/lib/api/incidents';
import {
  entityQueryKeys,
  getEntityTopology,
  listEntityTypes,
  searchEntities,
  type Entity,
  type EntityTopology,
} from '@/lib/api/entities';
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  knowledgeQueryKeys,
  listKnowledgeBases,
  listKnowledgeDocuments,
  searchKnowledge,
  updateKnowledgeBase,
  uploadKnowledgeDocument,
  type DocumentStatus,
  type DocumentType,
  type KnowledgeBase,
  type KnowledgeDocument,
  type RetrievalResult,
} from '@/lib/api/knowledge';
import {
  createModel,
  deleteModel,
  listModelProviders,
  listModelStatuses,
  listModels,
  settingsQueryKeys,
  updateModel,
  type ModelConfig,
  type ModelWriteRequest,
  type Option as SettingsOption,
  createNotification,
  deleteNotification,
  listNotificationTypes,
  listNotifications,
  notificationQueryKeys,
  updateNotification,
  type NotificationConfig,
  type NotificationWriteRequest,
} from '@/lib/api/settings';
import { ApiError, getApiBaseUrl } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  BellRing,
  BookOpen,
  Box,
  Calendar,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Clock,
  Copy,
  Database,
  Download,
  Eye,
  ExternalLink,
  FileCode,
  FileSearch,
  FileSpreadsheet,
  FileText,
  Folder,
  Funnel,
  Grid2X2,
  GitBranch,
  Info,
  List,
  MessageCircle,
  MessageSquare,
  MoreVertical,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  Server,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Square,
  Trash2,
  Upload,
  Zap,
  Globe,
  HardDriveUpload,
} from 'lucide-react';
import Link from 'next/link';
import { createPortal } from 'react-dom';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

function LinkButton({
  ariaLabel,
  children,
  className,
  href,
  tone = 'outline',
}: {
  ariaLabel?: string;
  children: ReactNode;
  className?: string;
  href: string;
  tone?: 'default' | 'outline';
}): ReactNode {
  return (
    <Link
      className={cn(
        'inline-flex h-8 items-center justify-center gap-2 rounded-lg px-2.5 text-xs font-semibold shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2',
        tone === 'default'
          ? 'bg-blue-600 text-white hover:bg-blue-700'
          : 'border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100',
        className,
      )}
      href={href}
      aria-label={ariaLabel}
    >
      {children}
    </Link>
  );
}

interface IncidentRow {
  assignee: string;
  conversationId: number | null;
  createdAt: string;
  description: string | null;
  id: number;
  incidentId: string;
  name: string;
  severity: string;
  source: string;
  status: string;
  updatedAt: string;
}

const severityTone: Record<IncidentRow['severity'], StatusTone> = {
  Critical: 'red',
  Error: 'amber',
  Warn: 'amber',
};

const incidentStatusTone: Record<IncidentRow['status'], StatusTone> = {
  Acknowledged: 'violet',
  Archived: 'slate',
  Closed: 'slate',
  Investigating: 'blue',
  Open: 'blue',
  Recovering: 'amber',
  Resolved: 'emerald',
};

const severityDotClassNames: Record<IncidentRow['severity'], string> = {
  Critical: 'bg-red-500',
  Error: 'bg-amber-500',
  Warn: 'bg-amber-500',
};

const assigneeClassNames: Record<string, string> = {
  lijing: 'bg-lime-500',
  'sre-team': 'bg-violet-600',
  wangwei: 'bg-cyan-600',
  zhangsan: 'bg-orange-500',
};

const sourceClassNames: Record<string, string> = {
  Alertmanager: 'bg-orange-500 text-white',
  AlertManager: 'bg-orange-500 text-white',
  Datadog: 'bg-violet-600 text-white',
  Grafana: 'bg-orange-500 text-white',
  Nagios: 'bg-slate-900 text-white',
  Opsgenie: 'bg-blue-600 text-white',
  Prometheus: 'bg-orange-500 text-white',
  Webhook: 'bg-slate-100 text-slate-700',
  Zabbix: 'bg-red-600 text-white',
};

const NEXT_STATUSES: Record<string, string[]> = {
  Open: ['Acknowledged', 'Investigating'],
  Acknowledged: ['Investigating'],
  Investigating: ['Recovering'],
  Recovering: ['Resolved'],
  Resolved: ['Closed'],
  Closed: [],
  Archived: [],
};

function IncidentStatusMenu({
  incident,
  isPending,
  onStatusChange,
}: {
  incident: IncidentRow;
  isPending: boolean;
  onStatusChange: (status: string, assignee?: string) => void;
}): ReactNode {
  const [isOpen, setIsOpen] = useState(false);
  const [assignee, setAssignee] = useState('');
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);
  const available = NEXT_STATUSES[incident.status] ?? [];

  const close = () => {
    setIsOpen(false);
    setPendingStatus(null);
    setAssignee('');
  };

  if (available.length === 0) {
    return (
      <ActionButton
        aria-label={`More actions for ${incident.name}`}
        className="size-8 px-0 text-slate-500 hover:text-slate-900"
        message={`${incident.name} actions opened`}
        size="sm"
        variant="ghost"
      >
        <MoreVertical aria-hidden="true" size={15} />
      </ActionButton>
    );
  }

  const handleSelect = (status: string) => {
    if (status === 'Acknowledged') {
      setPendingStatus(status);
      return;
    }
    close();
    onStatusChange(status);
  };

  const handleConfirm = () => {
    if (!assignee.trim()) return;
    close();
    onStatusChange('Acknowledged', assignee.trim());
  };

  return (
    <div className="relative">
      <ActionButton
        aria-label={`More actions for ${incident.name}`}
        className="size-8 px-0 text-slate-500 hover:text-slate-900"
        message={`${incident.name} actions opened`}
        size="sm"
        variant="ghost"
        onClick={() => setIsOpen((v) => !v)}
      >
        <MoreVertical aria-hidden="true" size={15} />
      </ActionButton>
      {isOpen ? (
        <>
          <div className="fixed inset-0 z-30" onClick={close} />
          <div className="absolute right-0 top-9 z-40 w-48 overflow-hidden rounded-md border border-slate-200 bg-white py-1 shadow-lg">
            <div className="flex items-center justify-between px-3 py-1.5">
              <span className="text-[11px] font-semibold uppercase text-slate-400">
                {pendingStatus === 'Acknowledged'
                  ? 'Assign to'
                  : 'Change status'}
              </span>
              <span className="text-[11px] font-medium text-slate-400">
                {incident.status}
              </span>
            </div>
            {pendingStatus === 'Acknowledged' ? (
              <div className="px-3 py-2">
                <input
                  autoFocus
                  className="w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  disabled={isPending}
                  onChange={(e) => setAssignee(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleConfirm();
                    if (e.key === 'Escape') close();
                  }}
                  placeholder="Enter assignee name"
                  type="text"
                  value={assignee}
                />
                <div className="mt-2 flex items-center gap-2">
                  <button
                    className="flex-1 rounded-md bg-blue-600 px-2 py-1.5 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
                    disabled={isPending || !assignee.trim()}
                    onClick={handleConfirm}
                    type="button"
                  >
                    Confirm
                  </button>
                  <button
                    className="rounded-md px-2 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
                    onClick={() => {
                      setPendingStatus(null);
                      setAssignee('');
                    }}
                    type="button"
                  >
                    Back
                  </button>
                </div>
              </div>
            ) : (
              available.map((status) => (
                <button
                  key={status}
                  className={cn(
                    'flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm transition',
                    isPending
                      ? 'text-slate-400'
                      : 'text-slate-700 hover:bg-blue-50 hover:text-blue-700',
                  )}
                  disabled={isPending}
                  onClick={() => handleSelect(status)}
                  type="button"
                >
                  <StatusBadge tone={incidentStatusTone[status] ?? 'slate'}>
                    {status}
                  </StatusBadge>
                  {status === 'Acknowledged' ? (
                    <span className="ml-auto text-[11px] text-slate-400">
                      assign
                    </span>
                  ) : null}
                </button>
              ))
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}

function getIncidentColumns({
  onOpenConversation,
  onStatusChange,
  openingIncidentId,
  statusChangingIncidentId,
}: {
  onOpenConversation: (row: IncidentRow) => void;
  onStatusChange: (row: IncidentRow, status: string, assignee?: string) => void;
  openingIncidentId: number | null;
  statusChangingIncidentId: number | null;
}): DataColumn<IncidentRow>[] {
  return [
    {
      className: 'w-[28%] truncate',
      header: 'Title',
      render: (row) => (
        <div className="truncate" title={`${row.name} (${row.incidentId})`}>
          <p className="truncate font-semibold text-slate-950">{row.name}</p>
          <p className="mt-1 truncate text-xs text-slate-500">
            {row.incidentId}
          </p>
        </div>
      ),
    },
    {
      className: 'w-[8%] truncate',
      header: 'Severity',
      render: (row) => (
        <span className="truncate" title={row.severity}>
          <StatusBadge tone={severityTone[row.severity] ?? 'slate'}>
            <span
              aria-hidden="true"
              className={cn(
                'mr-1.5 size-1.5 shrink-0 rounded-full',
                severityDotClassNames[row.severity] ?? 'bg-slate-400',
              )}
            />
            {row.severity}
          </StatusBadge>
        </span>
      ),
    },
    {
      className: 'w-[9%] truncate pr-2',
      header: 'Status',
      render: (row) => (
        <span className="truncate" title={row.status}>
          <StatusBadge tone={incidentStatusTone[row.status] ?? 'slate'}>
            {row.status}
          </StatusBadge>
        </span>
      ),
    },
    {
      className: 'w-[9%] truncate pl-2',
      header: 'Source',
      render: (row) => (
        <span
          className="inline-flex items-center gap-2 truncate"
          title={row.source}
        >
          <span
            className={cn(
              'grid size-5 shrink-0 place-items-center rounded-full text-[10px] font-semibold',
              sourceClassNames[row.source] ?? 'bg-slate-100 text-slate-700',
            )}
          >
            !
          </span>
          <span className="truncate">{row.source}</span>
        </span>
      ),
    },
    {
      className: 'w-[13%] truncate',
      header: 'Start Time',
      render: (row) => (
        <span className="truncate" title={row.createdAt}>
          {row.createdAt}
        </span>
      ),
    },
    {
      className: 'w-[11%] truncate pl-2',
      header: 'Updated At',
      render: (row) => (
        <span className="truncate" title={row.updatedAt}>
          {row.updatedAt}
        </span>
      ),
    },
    {
      className: 'w-[10%] truncate',
      header: 'Assignee',
      render: (row) => (
        <span
          className="inline-flex items-center gap-2 truncate"
          title={row.assignee}
        >
          <span
            className={cn(
              'grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold text-white',
              assigneeClassNames[row.assignee] ?? 'bg-slate-500',
            )}
          >
            {row.assignee.slice(0, 1).toUpperCase()}
          </span>
          <span className="truncate">{row.assignee}</span>
        </span>
      ),
    },
    {
      className: 'w-[12%]',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            aria-label={`Open ${row.name} chat`}
            className="inline-flex h-8 items-center justify-center gap-1.5 rounded-md bg-blue-600 px-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={openingIncidentId === row.id}
            onClick={() => onOpenConversation(row)}
            type="button"
          >
            <MessageCircle aria-hidden="true" size={15} />
            Ask AI
          </button>
          <IncidentStatusMenu
            incident={row}
            isPending={statusChangingIncidentId === row.id}
            onStatusChange={(status, assignee) =>
              onStatusChange(row, status, assignee)
            }
          />
        </div>
      ),
    },
  ];
}

function IncidentPagination({
  count,
  total,
}: {
  count: number;
  total: number;
}): ReactNode {
  const end = count === 0 ? 0 : count;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>
        Showing {count === 0 ? 0 : 1} to {end} of {total} incidents
      </span>
      <div className="flex items-center gap-2">
        <ActionButton
          aria-label="Previous incident page"
          className="size-8 px-0"
          message="Previous page selected"
          size="sm"
          variant="outline"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white">
          1
        </span>
        <ActionButton
          className="size-8 px-0"
          message="Page 2 selected"
          size="sm"
          variant="ghost"
        >
          2
        </ActionButton>
        <ActionButton
          className="size-8 px-0"
          message="Page 3 selected"
          size="sm"
          variant="ghost"
        >
          3
        </ActionButton>
        <ActionButton
          aria-label="Next incident page"
          className="size-8 px-0"
          message="Next page selected"
          size="sm"
          variant="outline"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </ActionButton>
        <ActionButton
          className="ml-2 h-8 gap-2 px-3 text-xs"
          message="Page size selector opened"
          size="sm"
          variant="outline"
        >
          10 / page
          <ChevronDown aria-hidden="true" size={14} />
        </ActionButton>
      </div>
    </div>
  );
}

interface IntegrationRow {
  createdAt: string;
  id: number;
  name: string;
  status: 'Enabled' | 'Disabled';
  token: string;
  tokenHint: string;
  type:
    | 'AlertManager'
    | 'Datadog'
    | 'Grafana'
    | 'Nagios'
    | 'OpsGenie'
    | 'Prometheus'
    | 'Webhook'
    | 'Zabbix';
  url: string;
}

const integrationLogoClassNames: Record<IntegrationRow['type'], string> = {
  AlertManager: 'rounded-full bg-orange-500 text-white',
  Datadog: 'rounded bg-violet-600 text-white',
  Grafana: 'rounded-full bg-orange-50 text-orange-600 ring-1 ring-orange-100',
  Nagios: 'rounded bg-white text-slate-950 ring-1 ring-slate-200',
  OpsGenie: 'rounded bg-blue-600 text-white',
  Prometheus: 'rounded-full bg-orange-500 text-white',
  Webhook: 'rounded bg-white text-slate-700 ring-1 ring-slate-200',
  Zabbix: 'rounded bg-red-600 text-white',
};

const integrationLogoText: Record<IntegrationRow['type'], string> = {
  AlertManager: '♟',
  Datadog: 'D',
  Grafana: 'G',
  Nagios: 'N',
  OpsGenie: '◆',
  Prometheus: '♟',
  Webhook: '⌘',
  Zabbix: 'Z',
};

const integrationTypeClassNames: Record<IntegrationRow['type'], string> = {
  AlertManager: 'border-blue-200 bg-blue-50 text-blue-700',
  Datadog: 'border-violet-200 bg-violet-50 text-violet-700',
  Grafana: 'border-blue-200 bg-blue-50 text-blue-700',
  Nagios: 'border-slate-200 bg-slate-50 text-slate-600',
  OpsGenie: 'border-blue-200 bg-blue-50 text-blue-700',
  Prometheus: 'border-blue-200 bg-blue-50 text-blue-700',
  Webhook: 'border-slate-200 bg-slate-50 text-slate-600',
  Zabbix: 'border-red-200 bg-red-50 text-red-700',
};

function IntegrationLogo({
  type,
}: {
  type: IntegrationRow['type'];
}): ReactNode {
  return (
    <span
      className={cn(
        'grid size-7 shrink-0 place-items-center text-sm font-black',
        integrationLogoClassNames[type],
      )}
    >
      {integrationLogoText[type]}
    </span>
  );
}

function IntegrationTypeBadge({
  type,
}: {
  type: IntegrationRow['type'];
}): ReactNode {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center rounded border px-2 text-xs font-medium',
        integrationTypeClassNames[type],
      )}
    >
      {type}
    </span>
  );
}

function IntegrationStatusSwitch({
  disabled,
  onToggle,
  status,
}: {
  disabled: boolean;
  onToggle: () => void;
  status: IntegrationRow['status'];
}): ReactNode {
  const isEnabled = status === 'Enabled';

  return (
    <button
      aria-pressed={isEnabled}
      className={cn(
        'inline-flex h-7 w-[82px] items-center rounded-full border p-0.5 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60',
        isEnabled
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
          : 'border-slate-200 bg-slate-100 text-slate-500',
      )}
      disabled={disabled}
      onClick={onToggle}
      type="button"
    >
      <span
        className={cn(
          'grid h-5 w-10 place-items-center rounded-full text-[10px] shadow-sm transition',
          isEnabled
            ? 'translate-x-[34px] bg-emerald-600 text-white'
            : 'translate-x-0 bg-white text-slate-500',
        )}
      >
        {isEnabled ? 'ON' : 'OFF'}
      </span>
    </button>
  );
}

function inferIntegrationType(name: string): IntegrationRow['type'] {
  const normalizedName = name.toLowerCase();

  if (normalizedName.includes('alertmanager')) {
    return 'AlertManager';
  }
  if (normalizedName.includes('datadog')) {
    return 'Datadog';
  }
  if (normalizedName.includes('grafana')) {
    return 'Grafana';
  }
  if (normalizedName.includes('nagios')) {
    return 'Nagios';
  }
  if (normalizedName.includes('opsgenie')) {
    return 'OpsGenie';
  }
  if (normalizedName.includes('prometheus')) {
    return 'Prometheus';
  }
  if (normalizedName.includes('zabbix')) {
    return 'Zabbix';
  }

  return 'Webhook';
}

function normalizeIntegrationStatus(status: string): IntegrationRow['status'] {
  return status.toUpperCase() === 'ENABLED' ? 'Enabled' : 'Disabled';
}

function normalizeIntegrationType(
  type?: string,
): IntegrationRow['type'] | null {
  const knownTypes: IntegrationRow['type'][] = [
    'Webhook',
    'AlertManager',
    'Grafana',
    'Prometheus',
    'Datadog',
    'Zabbix',
    'Nagios',
    'OpsGenie',
  ];

  const matchedType = knownTypes.find((knownType) => knownType === type);

  return matchedType ?? null;
}

function formatIntegrationDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date
    .toLocaleString('zh-CN', {
      day: '2-digit',
      hour: '2-digit',
      hour12: false,
      minute: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
    .replaceAll('/', '-');
}

function resolveWebhookUrl(webhookUrl: string): string {
  if (webhookUrl.startsWith('http://') || webhookUrl.startsWith('https://')) {
    return webhookUrl;
  }

  const apiBaseUrl = getApiBaseUrl();
  const apiOrigin = new URL(apiBaseUrl).origin;

  return new URL(webhookUrl, apiOrigin).toString();
}

function toIntegrationRow(integration: IncidentIntegration): IntegrationRow {
  return {
    createdAt: formatIntegrationDateTime(integration.created_at),
    id: integration.id,
    name: integration.name,
    status: normalizeIntegrationStatus(integration.status),
    token: integration.token || integration.token_hint,
    tokenHint: integration.token_hint,
    type:
      normalizeIntegrationType(integration.type) ??
      inferIntegrationType(integration.name),
    url: resolveWebhookUrl(integration.webhook_url),
  };
}

function formatIntegrationCreateError(error: unknown): string | undefined {
  if (error instanceof ApiError) {
    if (error.status === 409 || error.code === 'RESOURCE_CONFLICT') {
      return (
        error.message ||
        'Integration name already exists. Please use another name.'
      );
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return undefined;
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-9999px';
  textArea.style.top = '-9999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea);
}

function getIntegrationColumns({
  deletingIntegrationId,
  onCopyWebhookUrl,
  onDelete,
  onToggleStatus,
  onViewToken,
  updatingStatusIntegrationId,
}: {
  deletingIntegrationId: number | null;
  onCopyWebhookUrl: (row: IntegrationRow) => void;
  onDelete: (row: IntegrationRow) => void;
  onToggleStatus: (row: IntegrationRow) => void;
  onViewToken: (row: IntegrationRow) => void;
  updatingStatusIntegrationId: number | null;
}): DataColumn<IntegrationRow>[] {
  return [
    {
      className: 'w-[21%]',
      header: 'Name',
      render: (row) => (
        <span className="inline-flex items-center gap-3">
          <IntegrationLogo type={row.type} />
          <span className="font-semibold text-slate-950">{row.name}</span>
        </span>
      ),
    },
    {
      className: 'w-[11%]',
      header: 'Type',
      render: (row) => <IntegrationTypeBadge type={row.type} />,
    },
    {
      className: 'w-[32%]',
      header: 'Webhook URL',
      render: (row) => (
        <span className="flex min-w-0 items-center gap-2">
          <span className="block truncate text-sm text-slate-700">
            {row.url}
          </span>
          <button
            aria-label={`Copy ${row.name} webhook URL`}
            className="grid size-7 shrink-0 place-items-center rounded-md border-0 bg-transparent p-0 text-slate-500 shadow-none transition hover:bg-slate-100 hover:text-blue-600"
            onClick={() => onCopyWebhookUrl(row)}
            type="button"
          >
            <Copy aria-hidden="true" size={14} />
          </button>
        </span>
      ),
    },
    {
      className: 'w-[11%]',
      header: 'Status',
      render: (row) => (
        <IntegrationStatusSwitch
          disabled={updatingStatusIntegrationId === row.id}
          onToggle={() => onToggleStatus(row)}
          status={row.status}
        />
      ),
    },
    {
      className: 'w-[14%]',
      header: 'Created At',
      render: (row) => row.createdAt,
    },
    {
      className: 'w-[11%]',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            aria-label={`View ${row.name} token`}
            className="grid size-8 place-items-center rounded-md border border-blue-100 bg-blue-50 text-blue-600 shadow-sm transition hover:bg-blue-100 hover:text-blue-700"
            onClick={() => onViewToken(row)}
            type="button"
          >
            <Eye aria-hidden="true" size={15} />
          </button>
          <button
            aria-label={`Delete ${row.name}`}
            className="grid size-8 place-items-center rounded-md border border-red-100 bg-red-50 text-red-600 shadow-sm transition hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={deletingIntegrationId === row.id}
            onClick={() => onDelete(row)}
            type="button"
          >
            <Trash2 aria-hidden="true" size={15} />
          </button>
        </div>
      ),
    },
  ];
}

function LabeledFilterSelect({
  className,
  label,
  labelClassName,
  onChange,
  options = [],
  selectedValue = '',
  value,
}: {
  className?: string;
  label: string;
  labelClassName?: string;
  onChange?: (value: string) => void;
  options?: Array<{ label: string; value: string }>;
  selectedValue?: string;
  value: string;
}): ReactNode {
  const selectedOption = options.find(
    (option) => option.value === selectedValue,
  );
  const displayValue = selectedOption?.label ?? value;

  return (
    <label
      className={cn(
        'relative inline-flex h-10 min-w-[206px] cursor-pointer items-center rounded-md border border-slate-200 bg-white px-4 text-sm text-slate-800 shadow-sm transition focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 hover:border-blue-200 hover:bg-blue-50',
        className,
      )}
    >
      <span
        className={cn(
          'max-w-[76px] shrink-0 truncate font-medium text-slate-950',
          labelClassName,
        )}
      >
        {label}
      </span>
      <span className="min-w-0 flex-1 truncate pl-4 pr-6 text-right text-sm text-slate-700">
        {displayValue}
      </span>
      <select
        aria-label={label}
        className="absolute inset-0 h-full w-full cursor-pointer appearance-none opacity-0 outline-none"
        onChange={(event) => onChange?.(event.target.value)}
        value={selectedValue}
      >
        <option value="">{value}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-4 text-slate-500"
        size={15}
      />
    </label>
  );
}

function IntegrationTableState({
  children,
  tone = 'default',
}: {
  children: ReactNode;
  tone?: 'default' | 'danger';
}): ReactNode {
  return (
    <div
      className={cn(
        'flex min-h-[260px] items-center justify-center px-6 text-sm',
        tone === 'danger' ? 'text-red-600' : 'text-slate-500',
      )}
    >
      {children}
    </div>
  );
}

function IntegrationPagination({ count }: { count: number }): ReactNode {
  const firstItem = count > 0 ? 1 : 0;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>
        Showing {firstItem} to {count} of {count} integrations
      </span>
      <div className="flex items-center gap-3">
        <ActionButton
          className="h-8 gap-2 px-3 text-xs"
          message="Page size selector opened"
          size="sm"
          variant="outline"
        >
          10 / page
          <ChevronDown aria-hidden="true" size={14} />
        </ActionButton>
        <ActionButton
          aria-label="Previous integration page"
          className="size-8 px-0"
          message="Previous page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white">
          1
        </span>
        <ActionButton
          aria-label="Next integration page"
          className="size-8 px-0"
          message="Next page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    </div>
  );
}

const integrationFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Integration name is required.')
    .max(128, 'Integration name must be 128 characters or fewer.'),
  type: z.string().min(1, 'Integration type is required.'),
});

type IntegrationFormValues = z.infer<typeof integrationFormSchema>;

const fallbackIntegrationTypeOptions: IncidentOption[] = [
  { label: 'Webhook', value: 'Webhook' },
  { label: 'AlertManager', value: 'AlertManager' },
  { label: 'Grafana', value: 'Grafana' },
  { label: 'Prometheus', value: 'Prometheus' },
  { label: 'Datadog', value: 'Datadog' },
  { label: 'Zabbix', value: 'Zabbix' },
  { label: 'Nagios', value: 'Nagios' },
  { label: 'OpsGenie', value: 'OpsGenie' },
];

function RequiredLabel({ children }: { children: ReactNode }): ReactNode {
  return (
    <span className="text-sm font-medium text-slate-800">
      {children}
      <span aria-hidden="true" className="ml-0.5 text-red-500">
        *
      </span>
      <span className="sr-only">required</span>
    </span>
  );
}

function IntegrationFormDialog({
  errorMessage,
  isSubmitting,
  isOpen,
  onClose,
  onSubmit,
  typeOptions,
}: {
  errorMessage?: string;
  isSubmitting: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: IntegrationFormValues) => Promise<void>;
  typeOptions: IncidentOption[];
}): ReactNode {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<IntegrationFormValues>({
    defaultValues: {
      name: '',
      type: 'Webhook',
    },
    resolver: zodResolver(integrationFormSchema),
  });

  const closeDialog = () => {
    if (isSubmitting) {
      return;
    }
    reset();
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[520px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              New Integration
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Create a webhook integration for external alert sources.
            </p>
          </div>
          <button
            aria-label="Close integration dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>

        <form
          className="space-y-5 px-6 py-5"
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
        >
          <label className="block">
            <RequiredLabel>Integration Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.name ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="AlertManager Production"
              {...register('name')}
            />
            {errors.name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.name.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <RequiredLabel>Type</RequiredLabel>
            <select
              className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              {...register('type')}
            >
              {typeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-700">
            Webhook URL and masked token are generated by ObserveLens after the
            integration is created.
          </div>

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? 'Creating...' : 'Create Integration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function IntegrationTokenDialog({
  integration,
  onClose,
}: {
  integration: IntegrationRow | null;
  onClose: () => void;
}): ReactNode {
  if (!integration) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[460px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              Integration Token
            </h2>
            <p className="mt-1 text-sm text-slate-500">{integration.name}</p>
          </div>
          <button
            aria-label="Close token dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={onClose}
            type="button"
          >
            ×
          </button>
        </div>
        <div className="space-y-4 px-6 py-5">
          <div>
            <p className="text-sm font-medium text-slate-800">Token</p>
            <div className="mt-2 flex items-start gap-2 rounded-md border border-slate-200 bg-slate-50 p-3">
              <code className="min-w-0 flex-1 break-all font-mono text-sm leading-6 text-slate-800">
                {integration.token}
              </code>
              <button
                aria-label={`Copy ${integration.name} token`}
                className="inline-flex h-8 shrink-0 items-center justify-center gap-1 rounded-md bg-blue-600 px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
                onClick={() => {
                  void copyTextToClipboard(integration.token).catch(() => {
                    console.warn('Failed to copy integration token.');
                  });
                }}
                type="button"
              >
                <Copy aria-hidden="true" size={14} />
                Copy
              </button>
            </div>
          </div>
          <p className="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-700">
            This is the full plain token returned by ObserveLens. Copy and store
            it securely for webhook authentication.
          </p>
          <div className="flex justify-end border-t border-slate-200 pt-4">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
              onClick={onClose}
              type="button"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const fallbackEmbeddingModelOptions: IncidentOption[] = [
  { label: 'text-embedding-3-small', value: 'text-embedding-3-small' },
  { label: 'text-embedding-3-large', value: 'text-embedding-3-large' },
  { label: 'text-embedding-ada-002', value: 'text-embedding-ada-002' },
  { label: 'bge-large-zh-v1.5', value: 'bge-large-zh-v1.5' },
  { label: 'bge-m3', value: 'bge-m3' },
  { label: 'gte-large-zh', value: 'gte-large-zh' },
];

const knowledgeBaseFormSchema = z.object({
  description: z
    .string()
    .trim()
    .max(512, 'Description must be 512 characters or fewer.')
    .optional(),
  embedding_model: z.string().trim().min(1, 'Embedding model is required.'),
  name: z
    .string()
    .trim()
    .min(1, 'Knowledge base name is required.')
    .max(128, 'Knowledge base name must be 128 characters or fewer.'),
});

type KnowledgeBaseFormValues = z.infer<typeof knowledgeBaseFormSchema>;

function KnowledgeBaseFormDialog({
  errorMessage,
  isSubmitting,
  isOpen,
  onClose,
  onSubmit,
}: {
  errorMessage?: string;
  isSubmitting: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: KnowledgeBaseFormValues) => Promise<void>;
}): ReactNode {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<KnowledgeBaseFormValues>({
    defaultValues: {
      description: '',
      embedding_model: 'text-embedding-3-small',
      name: '',
    },
    resolver: zodResolver(knowledgeBaseFormSchema),
  });

  const closeDialog = () => {
    if (isSubmitting) {
      return;
    }
    reset();
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[520px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              New Knowledge Base
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Create a knowledge base to store and retrieve documents.
            </p>
          </div>
          <button
            aria-label="Close knowledge base dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>

        <form
          className="space-y-5 px-6 py-5"
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
        >
          <label className="block">
            <RequiredLabel>Knowledge Base Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.name ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="Production Runbooks"
              {...register('name')}
            />
            {errors.name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.name.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-800">
              Description
            </span>
            <textarea
              className={cn(
                'mt-2 min-h-[80px] w-full rounded-md border bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.description ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="Optional description for this knowledge base..."
              rows={3}
              {...register('description')}
            />
            {errors.description ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.description.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <RequiredLabel>Embedding Model</RequiredLabel>
            <select
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.embedding_model ? 'border-red-300' : 'border-slate-200',
              )}
              {...register('embedding_model')}
            >
              {fallbackEmbeddingModelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.embedding_model ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.embedding_model.message}
              </span>
            ) : null}
          </label>

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? 'Creating...' : 'Create Knowledge Base'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const inspectionFormSchema = z.object({
  description: z.string().trim().max(2000).optional(),
  enabled: z.boolean(),
  input_template: z
    .string()
    .trim()
    .min(1, 'Inspection prompt is required.')
    .max(4000, 'Inspection prompt must be 4000 characters or fewer.'),
  name: z
    .string()
    .trim()
    .min(1, 'Inspection name is required.')
    .max(128, 'Inspection name must be 128 characters or fewer.'),
  schedule: z.string().min(1, 'Schedule is required.'),
  scope: z
    .string()
    .trim()
    .min(1, 'Scope is required.')
    .max(128, 'Scope must be 128 characters or fewer.'),
});

type InspectionFormValues = z.infer<typeof inspectionFormSchema>;

function InspectionTag({
  children,
  className,
}: {
  children: ReactNode;
  className: string;
}): ReactNode {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center rounded border px-2 text-xs font-medium',
        className,
      )}
    >
      {children}
    </span>
  );
}

function InspectionTableState({
  children,
  tone = 'default',
}: {
  children: ReactNode;
  tone?: 'danger' | 'default';
}): ReactNode {
  return (
    <div
      className={cn(
        'flex min-h-[260px] items-center justify-center px-6 text-sm',
        tone === 'danger' ? 'text-red-600' : 'text-slate-500',
      )}
    >
      {children}
    </div>
  );
}

function inspectionStatusTone(status: Inspection['status']): StatusTone {
  switch (status) {
    case 'ENABLED':
      return 'emerald';
    case 'DISABLED':
      return 'slate';
    case 'RUNNING':
      return 'blue';
    case 'SUCCESS':
      return 'emerald';
    case 'FAILED':
      return 'red';
  }
}

function InspectionFormDialog({
  errorMessage,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
  scheduleOptions,
}: {
  errorMessage: string | null;
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (values: InspectionFormValues) => Promise<void>;
  scheduleOptions: InspectionOption[];
}): ReactNode {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<InspectionFormValues>({
    defaultValues: {
      description: '',
      enabled: true,
      input_template: 'Run a health inspection for {{scope}}.',
      name: '',
      schedule: '',
      scope: '',
    },
    resolver: zodResolver(inspectionFormSchema),
  });

  const closeDialog = (): void => {
    if (isSubmitting) return;
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[560px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              New Inspection
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Create a scheduled inspection using a real inspection prompt.
            </p>
          </div>
          <button
            aria-label="Close inspection dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            disabled={isSubmitting}
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>
        <form
          className="space-y-4 px-6 py-5"
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
        >
          <label className="block">
            <RequiredLabel>Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.name ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="Production Kubernetes health check"
              {...register('name')}
            />
            {errors.name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.name.message}
              </span>
            ) : null}
          </label>
          <label className="block">
            <RequiredLabel>Scope</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.scope ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="production cluster"
              {...register('scope')}
            />
            {errors.scope ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.scope.message}
              </span>
            ) : null}
          </label>
          <label className="block">
            <RequiredLabel>Schedule</RequiredLabel>
            <select
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.schedule ? 'border-red-300' : 'border-slate-200',
              )}
              disabled={scheduleOptions.length === 0}
              {...register('schedule')}
            >
              <option value="">
                {scheduleOptions.length === 0
                  ? 'Loading available schedules...'
                  : 'Select a schedule'}
              </option>
              {scheduleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.schedule ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.schedule.message}
              </span>
            ) : null}
          </label>
          <label className="block">
            <RequiredLabel>Inspection Prompt</RequiredLabel>
            <textarea
              className={cn(
                'mt-2 min-h-24 w-full rounded-md border bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.input_template ? 'border-red-300' : 'border-slate-200',
              )}
              {...register('input_template')}
            />
            {errors.input_template ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.input_template.message}
              </span>
            ) : null}
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-800">
              Description
            </span>
            <textarea
              className="mt-2 min-h-20 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              placeholder="Optional inspection purpose and operating context"
              {...register('description')}
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-800">
            <input
              className="size-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              type="checkbox"
              {...register('enabled')}
            />
            Enable after creation
          </label>
          {errorMessage ? (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </p>
          ) : null}
          <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
            <button
              className="h-10 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="h-10 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting || scheduleOptions.length === 0}
              type="submit"
            >
              {isSubmitting ? 'Creating...' : 'Create Inspection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function InspectionStatsGrid({
  enabled,
  loaded,
  total,
}: {
  enabled: number;
  loaded: number;
  total: number;
}): ReactNode {
  const stats = [
    { icon: Calendar, label: 'Total Inspections', value: total },
    { icon: CheckCircle2, label: 'Enabled', value: enabled },
    { icon: Clock, label: 'Disabled', value: Math.max(loaded - enabled, 0) },
    { icon: List, label: 'Loaded', value: loaded },
  ];

  return (
    <div className="mb-3 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <section
            className="rounded-md border border-slate-200 bg-white p-4"
            key={stat.label}
          >
            <div className="flex items-center gap-4">
              <span className="grid size-11 place-items-center rounded-full bg-blue-50 text-blue-600">
                <Icon aria-hidden="true" size={22} />
              </span>
              <div>
                <p className="text-xs text-slate-500">{stat.label}</p>
                <p className="mt-1 text-2xl font-semibold leading-none text-slate-950">
                  {stat.value}
                </p>
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}

function InspectionPagination({
  count,
  onPageChange,
  page,
  pageSize,
  total,
}: {
  count: number;
  onPageChange: (page: number) => void;
  page: number;
  pageSize: number;
  total: number;
}): ReactNode {
  const firstItem = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastItem = Math.min((page - 1) * pageSize + count, total);
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>
        Showing {firstItem} to {lastItem} of {total} inspections
      </span>
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-500">{pageSize} / page</span>
        <button
          aria-label="Previous inspection page"
          className="grid size-8 place-items-center rounded-md text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          type="button"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </button>
        <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white">
          {page}
        </span>
        <button
          aria-label="Next inspection page"
          className="grid size-8 place-items-center rounded-md text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          type="button"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </button>
      </div>
    </div>
  );
}

function InspectionTable({
  deletingId,
  executingId,
  onDelete,
  onExecute,
  onToggleEnabled,
  rows,
  togglingId,
}: {
  deletingId: number | null;
  executingId: number | null;
  onDelete: (inspection: Inspection) => void;
  onExecute: (inspection: Inspection) => void;
  onToggleEnabled: (inspection: Inspection) => void;
  rows: Inspection[];
  togglingId: number | null;
}): ReactNode {
  const columns: DataColumn<Inspection>[] = [
    {
      className: 'w-[22%]',
      header: 'Name',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-950">{row.name}</p>
          {row.description ? (
            <p className="mt-1 truncate text-xs text-slate-500">
              {row.description}
            </p>
          ) : null}
        </div>
      ),
    },
    { className: 'w-[18%]', header: 'Scope', render: (row) => row.scope },
    {
      className: 'w-[14%]',
      header: 'Schedule',
      render: (row) => row.schedule,
    },
    {
      className: 'w-[12%]',
      header: 'Status',
      render: (row) => (
        <StatusBadge tone={inspectionStatusTone(row.status)}>
          {row.status}
        </StatusBadge>
      ),
    },
    {
      className: 'w-[14%]',
      header: 'Last Run',
      render: (row) =>
        row.last_run_at ? formatIntegrationDateTime(row.last_run_at) : '—',
    },
    {
      className: 'w-[12%]',
      header: 'Created At',
      render: (row) => formatIntegrationDateTime(row.created_at),
    },
    {
      className: 'w-[8%]',
      header: 'Actions',
      render: (row) => {
        const isExecuting = executingId === row.id;
        const isToggling = togglingId === row.id;
        const isDeleting = deletingId === row.id;
        const isDisabled = isExecuting || isToggling || isDeleting;

        return (
          <div className="flex items-center gap-1">
            <button
              aria-label={`Run ${row.name}`}
              className="grid size-8 place-items-center rounded-md text-blue-600 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isDisabled}
              onClick={() => onExecute(row)}
              title="Run inspection"
              type="button"
            >
              <Play aria-hidden="true" size={14} />
            </button>
            <button
              aria-label={`${row.status === 'ENABLED' ? 'Disable' : 'Enable'} ${row.name}`}
              className="grid size-8 place-items-center rounded-md text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isDisabled}
              onClick={() => onToggleEnabled(row)}
              title={
                row.status === 'ENABLED'
                  ? 'Disable inspection'
                  : 'Enable inspection'
              }
              type="button"
            >
              {row.status === 'ENABLED' ? (
                <Square aria-hidden="true" size={13} />
              ) : (
                <CheckCircle2 aria-hidden="true" size={15} />
              )}
            </button>
            <button
              aria-label={`Delete ${row.name}`}
              className="grid size-8 place-items-center rounded-md text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isDisabled}
              onClick={() => onDelete(row)}
              title="Delete inspection"
              type="button"
            >
              <Trash2 aria-hidden="true" size={15} />
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <DataTable
      columns={columns}
      containerClassName="rounded-none border-0"
      getRowKey={(row) => String(row.id)}
      rows={rows}
    />
  );
}

const entityTypeClassNames: Record<string, string> = {
  alert: 'border-red-200 bg-red-50 text-red-700',
  cluster: 'border-cyan-200 bg-cyan-50 text-cyan-700',
  database: 'border-violet-200 bg-violet-50 text-violet-700',
  function: 'border-orange-200 bg-orange-50 text-orange-700',
  host: 'border-orange-200 bg-orange-50 text-orange-700',
  pod: 'border-blue-200 bg-blue-50 text-blue-700',
  service: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  topic: 'border-pink-200 bg-pink-50 text-pink-700',
};

function getEntityIcon(type: string): { className: string; icon: typeof Box } {
  switch (type.toLowerCase()) {
    case 'alert':
      return { className: 'text-pink-500', icon: BellRing };
    case 'database':
      return { className: 'text-orange-500', icon: Database };
    case 'function':
      return { className: 'text-orange-500', icon: Zap };
    case 'service':
      return { className: 'text-emerald-600', icon: GitBranch };
    case 'topic':
      return { className: 'text-violet-600', icon: GitBranch };
    default:
      return { className: 'text-blue-600', icon: Box };
  }
}

function formatEntityUpdatedAt(value: string | null): string {
  if (!value) return '-';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
    month: '2-digit',
    second: '2-digit',
    year: 'numeric',
  }).format(date);
}

const entityColumns: DataColumn<Entity>[] = [
  {
    className: 'w-[20%]',
    header: 'Name ↕',
    render: (row) => {
      const entityIcon = getEntityIcon(row.type);
      const Icon = entityIcon.icon;

      return (
        <div className="flex items-center gap-3">
          <Icon aria-hidden="true" className={entityIcon.className} size={23} />
          <div className="min-w-0">
            <p className="truncate font-semibold text-blue-600">{row.name}</p>
            <p className="mt-1 truncate text-xs text-slate-600">{row.id}</p>
          </div>
        </div>
      );
    },
  },
  {
    className: 'w-[11%]',
    header: 'Entity Type ↕',
    render: (row) => (
      <InspectionTag
        className={
          entityTypeClassNames[row.type.toLowerCase()] ??
          'border-slate-200 bg-slate-50 text-slate-700'
        }
      >
        {row.type}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[11%]',
    header: 'Namespace ↕',
    render: (row) => row.namespace,
  },
  {
    className: 'w-[11%]',
    header: 'Status',
    render: (row) => (
      <InspectionTag className="border-slate-200 bg-slate-50 text-slate-700">
        {row.status}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[25%]',
    header: 'Labels / Tags',
    render: (row) => (
      <div className="flex flex-wrap gap-2">
        {Object.entries(row.labels).map(([key, value]) => (
          <span
            className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-700"
            key={key}
          >
            {key}: {value}
          </span>
        ))}
      </div>
    ),
  },
  {
    className: 'w-[15%]',
    header: 'Updated At ↕',
    render: (row) => formatEntityUpdatedAt(row.updated_at),
  },
  {
    className: 'w-[7%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <LinkButton
          ariaLabel={`Open ${row.name} topology`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          href={`/entity/topology?entity_id=${encodeURIComponent(row.id)}`}
        >
          <Eye aria-hidden="true" size={15} />
        </LinkButton>
      </div>
    ),
  },
];

function EntitySearchBar({
  entityType,
  onEntityTypeChange,
  onQueryChange,
  onSearch,
  query,
  typeOptions,
}: {
  entityType: string;
  onEntityTypeChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  query: string;
  typeOptions: IncidentOption[];
}): ReactNode {
  return (
    <section className="mb-3 rounded-md border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-4">
        <LabeledFilterSelect
          className="min-w-[280px]"
          label="Entity Type"
          labelClassName="max-w-[100px]"
          onChange={onEntityTypeChange}
          options={typeOptions}
          selectedValue={entityType}
          value="All"
        />
        <label className="relative block min-w-0 flex-1">
          <span className="sr-only">Search entities</span>
          <Search
            aria-hidden="true"
            className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
            size={19}
          />
          <input
            className="h-12 w-full rounded-md border border-slate-200 bg-white pl-12 pr-4 text-sm text-slate-800 outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="Search by name, ID, IP, tag, or keyword..."
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') onSearch();
            }}
            type="search"
            value={query}
          />
        </label>
        <SearchButton onSearch={onSearch} />
      </div>
    </section>
  );
}

function EntityListToolbar({ total }: { total: number }): ReactNode {
  return (
    <div className="border-b border-slate-200 px-5 py-4">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-700">
        <FileText aria-hidden="true" size={17} />
        <span>{total.toLocaleString()} entities found</span>
      </div>
    </div>
  );
}

function EntityPagination({
  count,
  onPageChange,
  page,
  pageSize,
  total,
}: {
  count: number;
  onPageChange: (page: number) => void;
  page: number;
  pageSize: number;
  total: number;
}): ReactNode {
  const firstItem = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastItem = count === 0 ? 0 : firstItem + count - 1;
  const hasPreviousPage = page > 1;
  const hasNextPage = page * pageSize < total;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>
        Showing {firstItem} to {lastItem} of {total} entities
      </span>
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-500">{pageSize} / page</span>
        <ActionButton
          aria-label="Previous entity page"
          className="size-8 px-0"
          disabled={!hasPreviousPage}
          message={`Page ${page - 1} selected`}
          onClick={() => onPageChange(page - 1)}
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white">
          {page}
        </span>
        <ActionButton
          aria-label="Next entity page"
          className="size-8 px-0"
          disabled={!hasNextPage}
          message={`Page ${page + 1} selected`}
          onClick={() => onPageChange(page + 1)}
          size="sm"
          variant="ghost"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    </div>
  );
}

const documentStatusTone: Record<DocumentStatus, StatusTone> = {
  ARCHIVED: 'slate',
  FAILED: 'red',
  PENDING: 'amber',
  PROCESSING: 'blue',
  READY: 'emerald',
  REINDEXING: 'blue',
  UPLOADED: 'blue',
};

const documentTypeClassNames: Record<DocumentType, string> = {
  CASE: 'border-orange-200 bg-orange-50 text-orange-700',
  GUIDE: 'border-blue-200 bg-blue-50 text-blue-700',
  OTHER: 'border-slate-200 bg-slate-50 text-slate-700',
  REFERENCE: 'border-violet-200 bg-violet-50 text-violet-700',
  SOP: 'border-emerald-200 bg-emerald-50 text-emerald-700',
};

const documentTypeLabels: Record<DocumentType, string> = {
  CASE: 'Case',
  GUIDE: 'Guide',
  OTHER: 'Other',
  REFERENCE: 'Reference',
  SOP: 'SOP',
};

const authorPalette = [
  'bg-violet-700',
  'bg-blue-600',
  'bg-lime-600',
  'bg-orange-500',
  'bg-cyan-600',
];

function formatKnowledgeDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(value));
}

function formatDocumentStatus(status: DocumentStatus): string {
  const normalized = status.toLowerCase().replaceAll('_', ' ');
  return normalized.replace(/\b\w/g, (value) => value.toUpperCase());
}

function getDocumentDescription(document: KnowledgeDocument): string {
  const description = document.metadata?.description;
  if (typeof description === 'string' && description.trim()) {
    return description;
  }
  if (document.tags.length > 0) {
    return document.tags.join(', ');
  }
  return `${documentTypeLabels[document.document_type]} document`;
}

function getAuthorClassName(authorId: number): string {
  return (
    authorPalette[Math.abs(authorId) % authorPalette.length] ?? 'bg-slate-500'
  );
}

function formatDocumentSize(document: KnowledgeDocument): string {
  const sizeValue =
    document.metadata?.size_bytes ??
    document.metadata?.sizeBytes ??
    document.metadata?.file_size;

  if (typeof sizeValue !== 'number' || Number.isNaN(sizeValue)) {
    return '-';
  }

  if (sizeValue < 1024) {
    return `${sizeValue} B`;
  }

  if (sizeValue < 1024 * 1024) {
    return `${(sizeValue / 1024).toFixed(0)} KB`;
  }

  return `${(sizeValue / 1024 / 1024).toFixed(1)} MB`;
}

function inferDocumentType(fileName: string): DocumentType {
  const extension = fileName.split('.').pop()?.toLowerCase();

  if (extension === 'md' || extension === 'markdown') {
    return 'GUIDE';
  }

  if (extension === 'doc' || extension === 'docx' || extension === 'pdf') {
    return 'REFERENCE';
  }

  if (extension === 'xls' || extension === 'xlsx' || extension === 'csv') {
    return 'CASE';
  }

  return 'OTHER';
}

function getDocumentTypeIcon(documentType: DocumentType): typeof FileText {
  if (documentType === 'CASE') {
    return FileSpreadsheet;
  }

  if (documentType === 'GUIDE' || documentType === 'SOP') {
    return FileText;
  }

  if (documentType === 'REFERENCE') {
    return FileSearch;
  }

  return FileCode;
}

function buildDocumentContentUrl(documentId: string): string {
  return `${getApiBaseUrl()}/knowledge/documents/${documentId}/content`;
}

function FilesPagination({
  onPageChange,
  page,
  pageSize,
  total,
}: {
  onPageChange?: (page: number) => void;
  page: number;
  pageSize: number;
  total: number;
}): ReactNode {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const canGoPrevious = page > 1;
  const canGoNext = page < pageCount;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>
        Showing {start} to {end} of {total} files
      </span>
      <div className="flex items-center gap-3">
        <ActionButton
          className="h-8 gap-2 px-3 text-xs"
          message="Page size selector opened"
          size="sm"
          variant="outline"
        >
          {pageSize} / page
          <ChevronDown aria-hidden="true" size={14} />
        </ActionButton>
        <ActionButton
          aria-label="Previous files page"
          className="size-8 px-0"
          disabled={!canGoPrevious}
          message="Previous page selected"
          onClick={() => onPageChange?.(page - 1)}
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white">
          {page}
        </span>
        <ActionButton
          aria-label="Next files page"
          className="size-8 px-0"
          disabled={!canGoNext}
          message="Next page selected"
          onClick={() => onPageChange?.(page + 1)}
          size="sm"
          variant="ghost"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    </div>
  );
}

interface ModelRow {
  capabilities: string[];
  contextWindow: string;
  default?: boolean;
  lastUsed: string;
  model: string;
  provider: string;
  priority: number;
  requests: string;
  status: 'Disabled' | 'Enabled';
  tier: 'High' | 'Low' | 'Medium' | 'Premium';
  version: string;
}

const models: ModelRow[] = [
  {
    capabilities: ['Chat', 'Function Calling', 'Vision', '+2'],
    contextWindow: '128K',
    default: true,
    lastUsed: '2024-05-20 10:30:45',
    model: 'gpt-4o',
    provider: 'OpenAI',
    priority: 1,
    requests: '8,542',
    status: 'Enabled',
    tier: 'Premium',
    version: 'gpt-4o-2024-05-13',
  },
  {
    capabilities: ['Chat', 'Function Calling', '+1'],
    contextWindow: '200K',
    lastUsed: '2024-05-20 09:15:12',
    model: 'claude-3-5-sonnet',
    provider: 'Anthropic',
    priority: 2,
    requests: '5,621',
    status: 'Enabled',
    tier: 'Premium',
    version: 'claude-3-5-sonnet-20240620',
  },
  {
    capabilities: ['Chat', 'Vision', '+1'],
    contextWindow: '1M',
    lastUsed: '2024-05-19 16:45:33',
    model: 'gemini-1.5-pro',
    provider: 'Google',
    priority: 3,
    requests: '2,843',
    status: 'Enabled',
    tier: 'High',
    version: 'gemini-1.5-pro-001',
  },
  {
    capabilities: ['Chat'],
    contextWindow: '8K',
    lastUsed: '2024-05-18 14:22:10',
    model: 'llama-3-8b-instruct',
    provider: 'Meta',
    priority: 4,
    requests: '745',
    status: 'Enabled',
    tier: 'Medium',
    version: 'llama-3-8b-instruct',
  },
  {
    capabilities: ['Chat', 'Function Calling'],
    contextWindow: '16K',
    lastUsed: '2024-05-10 11:05:18',
    model: 'gpt-3.5-turbo',
    provider: 'OpenAI',
    priority: 5,
    requests: '—',
    status: 'Disabled',
    tier: 'Low',
    version: 'gpt-3.5-turbo-0125',
  },
  {
    capabilities: ['Chat'],
    contextWindow: '65K',
    lastUsed: '2024-05-08 08:30:01',
    model: 'mixtral-8x22b-instruct',
    provider: 'Mistral AI',
    priority: 6,
    requests: '—',
    status: 'Disabled',
    tier: 'Low',
    version: 'mixtral-8x22b-instruct-v0.1',
  },
  {
    capabilities: ['Chat', 'Function Calling'],
    contextWindow: '32K',
    lastUsed: '2024-05-05 13:10:22',
    model: 'deepseek-chat',
    provider: 'DeepSeek',
    priority: 7,
    requests: '—',
    status: 'Disabled',
    tier: 'Low',
    version: 'deepseek-chat',
  },
];

const providerLogoClassNames: Record<string, string> = {
  Anthropic: 'text-slate-950',
  DeepSeek: 'text-blue-600',
  Google: 'text-red-500',
  Meta: 'text-blue-600',
  'Mistral AI': 'text-orange-600',
  OpenAI: 'text-slate-950',
};

const providerLogoText: Record<string, string> = {
  Anthropic: 'AI',
  DeepSeek: '🐳',
  Google: 'G',
  Meta: '∞',
  'Mistral AI': 'M',
  OpenAI: '◎',
};

const modelTierTone: Record<ModelRow['tier'], string> = {
  High: 'border-blue-200 bg-blue-50 text-blue-700',
  Low: 'border-orange-200 bg-orange-50 text-orange-700',
  Medium: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Premium: 'border-violet-200 bg-violet-50 text-violet-700',
};

const modelColumns: DataColumn<ModelRow>[] = [
  {
    className: 'w-[16%]',
    header: 'Model Name ↕',
    render: (row) => (
      <div className="flex items-center gap-3">
        <span
          className={cn(
            'grid size-8 place-items-center text-xl font-black',
            providerLogoClassNames[row.provider],
          )}
        >
          {providerLogoText[row.provider]}
        </span>
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-950">
            {row.model}
            {row.default ? (
              <span className="ml-2 rounded border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700">
                Default
              </span>
            ) : null}
          </p>
          <p className="mt-1 truncate text-xs text-slate-600">{row.version}</p>
        </div>
      </div>
    ),
  },
  {
    className: 'w-[10%]',
    header: 'Provider ↕',
    render: (row) => (
      <span className="inline-flex items-center gap-2">
        <span
          className={cn(
            'text-lg font-black',
            providerLogoClassNames[row.provider],
          )}
        >
          {providerLogoText[row.provider]}
        </span>
        {row.provider}
      </span>
    ),
  },
  {
    className: 'w-[9%]',
    header: 'Status ↕',
    render: (row) => (
      <StatusBadge tone={row.status === 'Enabled' ? 'emerald' : 'red'}>
        {row.status}
      </StatusBadge>
    ),
  },
  {
    className: 'w-[19%]',
    header: 'Capabilities',
    render: (row) => (
      <div className="flex flex-wrap gap-2">
        {row.capabilities.map((capability) => (
          <span
            className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-700"
            key={capability}
          >
            {capability}
          </span>
        ))}
      </div>
    ),
  },
  {
    className: 'w-[8%]',
    header: 'Tier ↕',
    render: (row) => (
      <InspectionTag className={modelTierTone[row.tier]}>
        {row.tier}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[8%]',
    header: 'Priority ↕',
    render: (row) => (
      <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-blue-700">
        {row.priority}
      </span>
    ),
  },
  {
    className: 'w-[9%]',
    header: 'Context Window ↕',
    render: (row) => row.contextWindow,
  },
  {
    className: 'w-[10%]',
    header: 'Last Used ↕',
    render: (row) => row.lastUsed,
  },
  {
    className: 'w-[8%]',
    header: 'Requests (7d) ↕',
    render: (row) => row.requests,
  },
  {
    className: 'w-[5%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <ActionButton
          aria-label={`Edit ${row.model}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.model} editor opened`}
          size="sm"
          variant="ghost"
        >
          ✎
        </ActionButton>
        <ActionButton
          aria-label={`More actions for ${row.model}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.model} actions opened`}
          size="sm"
          variant="ghost"
        >
          <MoreVertical aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    ),
  },
];

function ModelsPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 7 of 12 models</span>
      <div className="flex items-center gap-3">
        <ActionButton
          className="h-8 gap-2 px-3 text-xs"
          message="Page size selector opened"
          size="sm"
          variant="outline"
        >
          10 / page
          <ChevronDown aria-hidden="true" size={14} />
        </ActionButton>
        <ActionButton
          aria-label="Previous models page"
          className="size-8 px-0"
          message="Previous page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        {[1, 2].map((page) =>
          page === 1 ? (
            <span
              className="grid size-8 place-items-center rounded-md bg-blue-600 text-xs font-semibold text-white"
              key={page}
            >
              {page}
            </span>
          ) : (
            <ActionButton
              className="size-8 px-0"
              key={page}
              message={`Page ${page} selected`}
              size="sm"
              variant="ghost"
            >
              {page}
            </ActionButton>
          ),
        )}
        <ActionButton
          aria-label="Next models page"
          className="size-8 px-0"
          message="Next page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronRight aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    </div>
  );
}

interface NotificationRow {
  description: string;
  lastUsed: string;
  name: string;
  status: 'Active' | 'Inactive';
  url: string;
}

const notifications: NotificationRow[] = [
  {
    description: 'Receives incident alerts',
    lastUsed: '2024-05-20 10:30:45',
    name: 'Incidents Webhook',
    status: 'Active',
    url: 'https://hooks.company.com/observe/incidents',
  },
  {
    description: 'Receives alert notifications',
    lastUsed: '2024-05-20 09:15:12',
    name: 'Alerts Webhook',
    status: 'Active',
    url: 'https://hooks.company.com/observe/alerts',
  },
  {
    description: 'Receives recovery events',
    lastUsed: '2024-05-19 16:45:33',
    name: 'Recovery Webhook',
    status: 'Active',
    url: 'https://hooks.company.com/observe/recovery',
  },
  {
    description: 'Receives custom system events',
    lastUsed: '2024-05-18 14:22:10',
    name: 'Custom Events Webhook',
    status: 'Active',
    url: 'https://hooks.company.com/observe/events',
  },
  {
    description: 'For testing and integration',
    lastUsed: '—',
    name: 'Test Webhook',
    status: 'Inactive',
    url: 'https://webhook.site/your-unique-url',
  },
];

const notificationColumns: DataColumn<NotificationRow>[] = [
  {
    className: 'w-[25%]',
    header: 'Name',
    render: (row) => (
      <div className="flex items-center gap-3">
        <GitBranch aria-hidden="true" className="text-pink-600" size={24} />
        <div>
          <p className="font-semibold text-slate-950">{row.name}</p>
          <p className="mt-1 text-sm text-slate-600">{row.description}</p>
        </div>
      </div>
    ),
  },
  {
    className: 'w-[36%]',
    header: 'Webhook URL',
    render: (row) => <span className="text-slate-700">{row.url}</span>,
  },
  {
    className: 'w-[14%]',
    header: 'Status',
    render: (row) => (
      <StatusBadge tone={row.status === 'Active' ? 'emerald' : 'slate'}>
        {row.status}
      </StatusBadge>
    ),
  },
  { className: 'w-[16%]', header: 'Last Used', render: (row) => row.lastUsed },
  {
    className: 'w-[9%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <ActionButton
          aria-label={`Edit ${row.name}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.name} notification editor opened`}
          size="sm"
          variant="ghost"
        >
          ✎
        </ActionButton>
        <ActionButton
          aria-label={`More actions for ${row.name}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.name} actions opened`}
          size="sm"
          variant="ghost"
        >
          <MoreVertical aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    ),
  },
];

function Toolbar({ children }: { children: ReactNode }): ReactNode {
  return (
    <section className="mb-3 rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {children}
      </div>
    </section>
  );
}

function SearchButton({
  message = 'Search executed',
  onSearch,
}: {
  message?: string;
  onSearch?: () => void;
} = {}): ReactNode {
  return (
    <ActionButton
      className="h-10 w-28 px-0"
      message={message}
      onClick={onSearch}
    >
      Search
    </ActionButton>
  );
}

function toIncidentRow(incident: Incident): IncidentRow {
  return {
    assignee: incident.external_metadata?.assignee ?? 'sre-team',
    conversationId: incident.conversation_id,
    createdAt: incident.started_at
      ? formatIntegrationDateTime(incident.started_at)
      : formatIntegrationDateTime(incident.created_at),
    description: incident.description,
    id: incident.id,
    incidentId: incident.incident_id,
    name: incident.name,
    severity: incident.severity,
    source: incident.source ?? 'Webhook',
    status: incident.status,
    updatedAt: formatIntegrationDateTime(incident.updated_at),
  };
}

export function IncidentsPage(): ReactNode {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [draftIncidentFilters, setDraftIncidentFilters] = useState({
    keyword: '',
    severity: '',
    source: '',
    status: '',
  });
  const [appliedIncidentFilters, setAppliedIncidentFilters] = useState({
    keyword: '',
    severity: '',
    source: '',
    status: '',
  });
  const incidentListParams = {
    keyword: appliedIncidentFilters.keyword,
    name: appliedIncidentFilters.keyword,
    page: 1,
    page_size: 20,
    severity: appliedIncidentFilters.severity,
    source: appliedIncidentFilters.source,
    status: appliedIncidentFilters.status,
  };
  const {
    data: incidentPage,
    error,
    isError,
    isFetching,
    isPending,
    refetch,
  } = useQuery({
    queryFn: () => listIncidents(incidentListParams),
    queryKey: incidentQueryKeys.list(incidentListParams),
  });
  const { data: incidentSeverityOptions = [] } = useQuery({
    queryFn: listIncidentSeverities,
    queryKey: incidentQueryKeys.severities(),
  });
  const { data: incidentStatusOptions = [] } = useQuery({
    queryFn: listIncidentStatuses,
    queryKey: incidentQueryKeys.statuses(),
  });
  const { data: incidentSourceIntegrations = [] } = useQuery({
    queryFn: () => listIncidentIntegrations(),
    queryKey: incidentIntegrationQueryKeys.list(),
  });
  const incidentSourceOptions = incidentSourceIntegrations.map(
    (integration) => ({
      label: integration.name,
      value: integration.name,
    }),
  );
  const openConversationMutation = useMutation({
    mutationFn: openIncidentConversation,
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({
        queryKey: incidentQueryKeys.all,
      });
      router.push(`/?conversationId=${response.conversation_id}`);
    },
  });
  const transitionIncidentMutation = useMutation({
    mutationFn: ({
      incidentId,
      status,
      assignee,
    }: {
      incidentId: number;
      status: string;
      assignee?: string;
    }) => transitionIncident(incidentId, { status, assignee }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: incidentQueryKeys.all,
      });
    },
  });
  const incidentRows = (incidentPage?.items ?? []).map(toIncidentRow);
  const incidentColumns = getIncidentColumns({
    onOpenConversation: (row) => openConversationMutation.mutate(row.id),
    onStatusChange: (row, status, assignee) =>
      transitionIncidentMutation.mutate({
        incidentId: row.id,
        status,
        assignee,
      }),
    openingIncidentId: openConversationMutation.isPending
      ? (openConversationMutation.variables ?? null)
      : null,
    statusChangingIncidentId: transitionIncidentMutation.isPending
      ? (transitionIncidentMutation.variables?.incidentId ?? null)
      : null,
  });

  return (
    <AppShell activeItem="Incidents" activeSection="incidents">
      <PageHeader
        description="Track active and archived incidents, review severity, source, owner, and AI investigation status."
        parentTitle="Incidents"
        title="Incidents"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <div className="mb-3 flex items-center gap-6 border-b border-slate-200">
          <button
            className="border-b-2 border-blue-600 px-5 py-2 text-sm font-semibold text-blue-600"
            type="button"
          >
            Active
          </button>
          <button
            className="px-5 py-2 text-sm font-medium text-slate-700 hover:text-blue-600"
            type="button"
          >
            Archived
          </button>
        </div>
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput
              onChange={(keyword) =>
                setDraftIncidentFilters((filters) => ({
                  ...filters,
                  keyword,
                }))
              }
              placeholder="Search incidents..."
              value={draftIncidentFilters.keyword}
            />
            <LabeledFilterSelect
              label="Severity"
              onChange={(severity) =>
                setDraftIncidentFilters((filters) => ({
                  ...filters,
                  severity,
                }))
              }
              options={incidentSeverityOptions}
              selectedValue={draftIncidentFilters.severity}
              value="All"
            />
            <LabeledFilterSelect
              label="Status"
              onChange={(status) =>
                setDraftIncidentFilters((filters) => ({
                  ...filters,
                  status,
                }))
              }
              options={incidentStatusOptions}
              selectedValue={draftIncidentFilters.status}
              value="All"
            />
            <LabeledFilterSelect
              label="Source"
              onChange={(source) =>
                setDraftIncidentFilters((filters) => ({
                  ...filters,
                  source,
                }))
              }
              options={incidentSourceOptions}
              selectedValue={draftIncidentFilters.source}
              value="All"
            />
          </div>
          <SearchButton
            message={
              isFetching
                ? 'Searching incidents...'
                : 'Incidents search completed'
            }
            onSearch={() => {
              const nextFilters = {
                keyword: draftIncidentFilters.keyword.trim(),
                name: draftIncidentFilters.keyword.trim(),
                severity: draftIncidentFilters.severity,
                source: draftIncidentFilters.source,
                status: draftIncidentFilters.status,
              };

              setAppliedIncidentFilters(nextFilters);
              if (
                nextFilters.keyword === appliedIncidentFilters.keyword &&
                nextFilters.severity === appliedIncidentFilters.severity &&
                nextFilters.source === appliedIncidentFilters.source &&
                nextFilters.status === appliedIncidentFilters.status
              ) {
                void refetch();
              }
            }}
          />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          {isPending ? (
            <IntegrationTableState>Loading incidents...</IntegrationTableState>
          ) : null}
          {isError ? (
            <IntegrationTableState tone="danger">
              {error.message || 'Failed to load incidents.'}
            </IntegrationTableState>
          ) : null}
          {!isPending && !isError && incidentRows.length === 0 ? (
            <IntegrationTableState>No incidents found.</IntegrationTableState>
          ) : null}
          {!isPending && !isError && incidentRows.length > 0 ? (
            <DataTable
              columns={incidentColumns}
              containerClassName="rounded-none border-0"
              getRowKey={(row) => String(row.id)}
              rows={incidentRows}
            />
          ) : null}
          <IncidentPagination
            count={incidentRows.length}
            total={incidentPage?.total ?? 0}
          />
        </section>
      </div>
    </AppShell>
  );
}

export function IncidentIntegrationsPage(): ReactNode {
  const queryClient = useQueryClient();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [draftIntegrationFilters, setDraftIntegrationFilters] = useState({
    name: '',
    status: '',
    type: '',
  });
  const [appliedIntegrationFilters, setAppliedIntegrationFilters] = useState({
    name: '',
    status: '',
    type: '',
  });
  const [viewingTokenIntegration, setViewingTokenIntegration] =
    useState<IntegrationRow | null>(null);
  const {
    data: integrationResponses = [],
    error,
    isError,
    isFetching,
    isPending,
    refetch,
  } = useQuery({
    queryFn: () => listIncidentIntegrations(appliedIntegrationFilters),
    queryKey: incidentIntegrationQueryKeys.list(appliedIntegrationFilters),
  });
  const { data: integrationTypeOptions = fallbackIntegrationTypeOptions } =
    useQuery({
      queryFn: listIncidentIntegrationTypes,
      queryKey: incidentIntegrationQueryKeys.types(),
    });
  const { data: integrationStatusOptions = [] } = useQuery({
    queryFn: listIncidentIntegrationStatuses,
    queryKey: incidentIntegrationQueryKeys.statuses(),
  });
  const createIntegrationMutation = useMutation({
    mutationFn: createIncidentIntegration,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: incidentIntegrationQueryKeys.list(),
      });
      setIsCreateDialogOpen(false);
    },
  });
  const deleteIntegrationMutation = useMutation({
    mutationFn: deleteIncidentIntegration,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: incidentIntegrationQueryKeys.list(),
      });
    },
  });
  const updateIntegrationMutation = useMutation({
    mutationFn: updateIncidentIntegration,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: incidentIntegrationQueryKeys.list(),
      });
    },
  });
  const integrationRows = integrationResponses.map(toIntegrationRow);
  const integrationColumns = getIntegrationColumns({
    deletingIntegrationId: deleteIntegrationMutation.isPending
      ? (deleteIntegrationMutation.variables ?? null)
      : null,
    onCopyWebhookUrl: (row) => {
      void copyTextToClipboard(row.url).catch(() => {
        console.warn('Failed to copy webhook URL.');
      });
    },
    onDelete: (row) => {
      if (
        window.confirm(
          `Delete integration "${row.name}"? This action cannot be undone.`,
        )
      ) {
        deleteIntegrationMutation.mutate(row.id);
      }
    },
    onToggleStatus: (row) => {
      updateIntegrationMutation.mutate({
        integrationId: row.id,
        request: {
          status: row.status === 'Enabled' ? 'DISABLED' : 'ENABLED',
        },
      });
    },
    onViewToken: setViewingTokenIntegration,
    updatingStatusIntegrationId: updateIntegrationMutation.isPending
      ? (updateIntegrationMutation.variables?.integrationId ?? null)
      : null,
  });
  const createError = formatIntegrationCreateError(
    createIntegrationMutation.error,
  );

  return (
    <AppShell activeItem="Integrations" activeSection="incidents">
      <PageHeader
        actionsClassName="pr-[17px]"
        actions={
          <button
            className="inline-flex h-10 w-28 items-center justify-center rounded-md bg-blue-600 px-0 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2"
            onClick={() => setIsCreateDialogOpen(true)}
            type="button"
          >
            New
          </button>
        }
        description="Configure alert sources to receive incidents in ObserveLens via webhook."
        parentTitle="Incidents"
        title="Integrations"
      />
      <IntegrationFormDialog
        errorMessage={createError}
        isOpen={isCreateDialogOpen}
        isSubmitting={createIntegrationMutation.isPending}
        onClose={() => {
          createIntegrationMutation.reset();
          setIsCreateDialogOpen(false);
        }}
        onSubmit={async (values) => {
          await createIntegrationMutation.mutateAsync({
            name: values.name,
            type: values.type,
          });
        }}
        typeOptions={integrationTypeOptions}
      />
      <IntegrationTokenDialog
        integration={viewingTokenIntegration}
        onClose={() => setViewingTokenIntegration(null)}
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput
              onChange={(name) =>
                setDraftIntegrationFilters((filters) => ({
                  ...filters,
                  name,
                }))
              }
              placeholder="Search integrations..."
              value={draftIntegrationFilters.name}
            />
            <LabeledFilterSelect
              label="Type"
              onChange={(type) =>
                setDraftIntegrationFilters((filters) => ({
                  ...filters,
                  type,
                }))
              }
              options={integrationTypeOptions}
              selectedValue={draftIntegrationFilters.type}
              value="All"
            />
            <LabeledFilterSelect
              label="Status"
              onChange={(status) =>
                setDraftIntegrationFilters((filters) => ({
                  ...filters,
                  status,
                }))
              }
              options={integrationStatusOptions}
              selectedValue={draftIntegrationFilters.status}
              value="All"
            />
          </div>
          <SearchButton
            message={
              isFetching
                ? 'Searching integrations...'
                : 'Integrations search completed'
            }
            onSearch={() => {
              const nextFilters = {
                name: draftIntegrationFilters.name.trim(),
                status: draftIntegrationFilters.status,
                type: draftIntegrationFilters.type,
              };

              setAppliedIntegrationFilters(nextFilters);
              if (
                nextFilters.name === appliedIntegrationFilters.name &&
                nextFilters.status === appliedIntegrationFilters.status &&
                nextFilters.type === appliedIntegrationFilters.type
              ) {
                void refetch();
              }
            }}
          />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          {isPending ? (
            <IntegrationTableState>
              Loading incident integrations...
            </IntegrationTableState>
          ) : null}
          {isError ? (
            <IntegrationTableState tone="danger">
              {error.message || 'Failed to load incident integrations.'}
            </IntegrationTableState>
          ) : null}
          {!isPending && !isError && integrationRows.length === 0 ? (
            <IntegrationTableState>
              No incident integrations found.
            </IntegrationTableState>
          ) : null}
          {!isPending && !isError && integrationRows.length > 0 ? (
            <DataTable
              columns={integrationColumns}
              containerClassName="rounded-none border-0"
              getRowKey={(row) => String(row.id)}
              rows={integrationRows}
            />
          ) : null}
          <IntegrationPagination count={integrationRows.length} />
        </section>
      </div>
    </AppShell>
  );
}

export function InspectionsPage(): ReactNode {
  const [draftName, setDraftName] = useState('');
  const [draftStatus, setDraftStatus] = useState('');
  const [filters, setFilters] = useState({ name: '', status: '' });
  const [page, setPage] = useState(1);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const pageSize = 20;

  const inspectionsQuery = useQuery({
    queryFn: () => listInspections({ page, page_size: pageSize }),
    queryKey: inspectionQueryKeys.list({ page, page_size: pageSize }),
  });
  const statusOptionsQuery = useQuery({
    queryFn: listInspectionStatuses,
    queryKey: inspectionQueryKeys.statuses(),
  });
  const scheduleOptionsQuery = useQuery({
    queryFn: listInspectionSchedules,
    queryKey: inspectionQueryKeys.schedules(),
  });

  const invalidateInspections = async (): Promise<void> => {
    await queryClient.invalidateQueries({ queryKey: inspectionQueryKeys.all });
  };
  const createMutation = useMutation({
    mutationFn: createInspection,
    onSuccess: async () => {
      await invalidateInspections();
      setActionError(null);
      setActionMessage('Inspection created.');
      setIsCreateDialogOpen(false);
    },
  });
  const executeMutation = useMutation({
    mutationFn: executeInspection,
    onSuccess: async (result) => {
      await invalidateInspections();
      setActionError(null);
      setActionMessage(`Inspection execution started (run #${result.run_id}).`);
    },
  });
  const enableMutation = useMutation({
    mutationFn: enableInspection,
    onSuccess: invalidateInspections,
  });
  const disableMutation = useMutation({
    mutationFn: disableInspection,
    onSuccess: invalidateInspections,
  });
  const deleteMutation = useMutation({
    mutationFn: deleteInspection,
    onSuccess: async () => {
      await invalidateInspections();
      setActionError(null);
      setActionMessage('Inspection deleted.');
    },
  });

  const inspectionPage = inspectionsQuery.data;
  const inspectionRows = useMemo(() => {
    const normalizedName = filters.name.toLocaleLowerCase();
    return (inspectionPage?.items ?? []).filter((inspection) => {
      const matchesName =
        !normalizedName ||
        inspection.name.toLocaleLowerCase().includes(normalizedName);
      const matchesStatus =
        !filters.status || inspection.status === filters.status;
      return matchesName && matchesStatus;
    });
  }, [filters.name, filters.status, inspectionPage?.items]);
  const enabledCount = (inspectionPage?.items ?? []).filter(
    (inspection) => inspection.status === 'ENABLED',
  ).length;

  const setMutationError = (error: unknown): void => {
    setActionMessage(null);
    setActionError(
      error instanceof Error ? error.message : 'The inspection request failed.',
    );
  };
  const applyFilters = (): void => {
    setFilters({ name: draftName.trim(), status: draftStatus });
    setPage(1);
  };
  const handleCreate = async (values: InspectionFormValues): Promise<void> => {
    try {
      const request: InspectionWriteRequest = {
        description: values.description?.trim() || null,
        enabled: values.enabled,
        input_template: values.input_template,
        name: values.name,
        schedule: values.schedule,
        scope: values.scope,
      };
      await createMutation.mutateAsync(request);
    } catch (error) {
      setMutationError(error);
      throw error;
    }
  };
  const handleExecute = (inspection: Inspection): void => {
    void executeMutation.mutateAsync(inspection.id).catch(setMutationError);
  };
  const handleToggleEnabled = (inspection: Inspection): void => {
    const mutation =
      inspection.status === 'ENABLED' ? disableMutation : enableMutation;
    void mutation.mutateAsync(inspection.id).catch(setMutationError);
  };
  const handleDelete = (inspection: Inspection): void => {
    if (!window.confirm(`Delete inspection "${inspection.name}"?`)) return;
    void deleteMutation.mutateAsync(inspection.id).catch(setMutationError);
  };

  return (
    <AppShell activeItem="Inspections" activeSection="tasks">
      <PageHeader
        actions={
          <>
            <button
              className="inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 text-xs font-semibold text-blue-700 shadow-sm transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={inspectionsQuery.isFetching}
              onClick={() => {
                void inspectionsQuery.refetch();
              }}
              type="button"
            >
              <RefreshCw aria-hidden="true" size={15} />
              Refresh
            </button>
            <button
              className="inline-flex h-9 items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700"
              onClick={() => {
                setActionError(null);
                setIsCreateDialogOpen(true);
              }}
              type="button"
            >
              <Plus aria-hidden="true" size={15} />
              New Inspection
            </button>
          </>
        }
        actionsClassName="pr-4"
        description="Manage scheduled inspection tasks with live service data."
        parentTitle="Tasks"
        title="Inspections"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <InspectionStatsGrid
          enabled={enabledCount}
          loaded={inspectionPage?.items.length ?? 0}
          total={inspectionPage?.total ?? 0}
        />
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput
              onChange={setDraftName}
              placeholder="Search loaded inspections by name..."
              value={draftName}
            />
            <LabeledFilterSelect
              label="Status"
              onChange={setDraftStatus}
              options={statusOptionsQuery.data ?? []}
              selectedValue={draftStatus}
              value="All"
            />
          </div>
          <button
            className="h-10 w-28 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={inspectionsQuery.isFetching}
            onClick={applyFilters}
            type="button"
          >
            Search
          </button>
        </Toolbar>
        {actionMessage ? (
          <p className="mb-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {actionMessage}
          </p>
        ) : null}
        {actionError ? (
          <p className="mb-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {actionError}
          </p>
        ) : null}
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          {inspectionsQuery.isPending ? (
            <InspectionTableState>Loading inspections...</InspectionTableState>
          ) : null}
          {inspectionsQuery.isError ? (
            <InspectionTableState tone="danger">
              {inspectionsQuery.error.message || 'Failed to load inspections.'}
            </InspectionTableState>
          ) : null}
          {!inspectionsQuery.isPending &&
          !inspectionsQuery.isError &&
          inspectionRows.length === 0 ? (
            <InspectionTableState>No inspections found.</InspectionTableState>
          ) : null}
          {!inspectionsQuery.isPending &&
          !inspectionsQuery.isError &&
          inspectionRows.length > 0 ? (
            <InspectionTable
              deletingId={
                deleteMutation.isPending ? deleteMutation.variables : null
              }
              executingId={
                executeMutation.isPending ? executeMutation.variables : null
              }
              onDelete={handleDelete}
              onExecute={handleExecute}
              onToggleEnabled={handleToggleEnabled}
              rows={inspectionRows}
              togglingId={
                enableMutation.isPending
                  ? enableMutation.variables
                  : disableMutation.isPending
                    ? disableMutation.variables
                    : null
              }
            />
          ) : null}
          <InspectionPagination
            count={inspectionRows.length}
            onPageChange={setPage}
            page={page}
            pageSize={pageSize}
            total={inspectionPage?.total ?? 0}
          />
        </section>
      </div>
      <InspectionFormDialog
        errorMessage={actionError}
        isOpen={isCreateDialogOpen}
        isSubmitting={createMutation.isPending}
        onClose={() => setIsCreateDialogOpen(false)}
        onSubmit={handleCreate}
        scheduleOptions={scheduleOptionsQuery.data ?? []}
      />
    </AppShell>
  );
}

export function EntitySearchPage(): ReactNode {
  const [draftQuery, setDraftQuery] = useState('');
  const [draftEntityType, setDraftEntityType] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({
    query: '',
    type: '',
  });
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const entityTypesQuery = useQuery({
    queryFn: listEntityTypes,
    queryKey: entityQueryKeys.types(),
  });
  const entitiesQuery = useQuery({
    queryFn: () =>
      searchEntities({
        ...appliedFilters,
        page,
        page_size: pageSize,
      }),
    queryKey: entityQueryKeys.search({
      ...appliedFilters,
      page,
      page_size: pageSize,
    }),
  });
  const entityPage = entitiesQuery.data;
  const typeOptions = entityTypesQuery.data ?? [];

  const handleSearch = (): void => {
    const nextFilters = {
      query: draftQuery.trim(),
      type: draftEntityType,
    };

    setPage(1);
    setAppliedFilters(nextFilters);
    if (
      nextFilters.query === appliedFilters.query &&
      nextFilters.type === appliedFilters.type
    ) {
      void entitiesQuery.refetch();
    }
  };

  return (
    <AppShell activeItem="Search" activeSection="entity">
      <PageHeader
        description="Search and discover entities across your infrastructure and observability data."
        parentTitle="Entity"
        title="Search"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <EntitySearchBar
          entityType={draftEntityType}
          onEntityTypeChange={setDraftEntityType}
          onQueryChange={setDraftQuery}
          onSearch={handleSearch}
          query={draftQuery}
          typeOptions={typeOptions}
        />
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <EntityListToolbar total={entityPage?.total ?? 0} />
          {entitiesQuery.isPending ? (
            <IntegrationTableState>Loading entities...</IntegrationTableState>
          ) : null}
          {entitiesQuery.isError ? (
            <IntegrationTableState tone="danger">
              {entitiesQuery.error.message || 'Failed to load entities.'}
            </IntegrationTableState>
          ) : null}
          {!entitiesQuery.isPending &&
          !entitiesQuery.isError &&
          (entityPage?.items.length ?? 0) === 0 ? (
            <IntegrationTableState>No entities found.</IntegrationTableState>
          ) : null}
          {!entitiesQuery.isPending &&
          !entitiesQuery.isError &&
          (entityPage?.items.length ?? 0) > 0 ? (
            <DataTable
              columns={entityColumns}
              containerClassName="rounded-none border-0"
              getRowKey={(row) => row.id}
              rows={entityPage?.items ?? []}
            />
          ) : null}
          <EntityPagination
            count={entityPage?.items.length ?? 0}
            onPageChange={setPage}
            page={entityPage?.page ?? page}
            pageSize={entityPage?.page_size ?? pageSize}
            total={entityPage?.total ?? 0}
          />
        </section>
      </div>
    </AppShell>
  );
}

export function EntityTopologyPage(): ReactNode {
  const hasAppliedUrlEntity = useRef(false);
  const [draftQuery, setDraftQuery] = useState('');
  const [draftType, setDraftType] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ query: '', type: '' });
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [direction, setDirection] = useState<
    'both' | 'downstream' | 'upstream'
  >('both');
  const [depth, setDepth] = useState(3);

  const entityTypesQuery = useQuery({
    queryFn: listEntityTypes,
    queryKey: entityQueryKeys.types(),
  });
  const candidateEntitiesQuery = useQuery({
    queryFn: () =>
      searchEntities({
        page: 1,
        page_size: 50,
        query: appliedFilters.query,
        type: appliedFilters.type,
      }),
    queryKey: entityQueryKeys.search({
      page: 1,
      page_size: 50,
      query: appliedFilters.query,
      type: appliedFilters.type,
    }),
  });
  const topologyQuery = useQuery({
    enabled: selectedEntityId !== null,
    queryFn: () =>
      getEntityTopology(selectedEntityId as string, { depth, direction }),
    queryKey: entityQueryKeys.topology(selectedEntityId ?? '', {
      depth,
      direction,
    }),
  });

  useEffect(() => {
    const entityIdFromUrl = new URLSearchParams(window.location.search).get(
      'entity_id',
    );

    if (!hasAppliedUrlEntity.current && entityIdFromUrl) {
      setSelectedEntityId(entityIdFromUrl);
      setSelectedNodeId(entityIdFromUrl);
      hasAppliedUrlEntity.current = true;
    }
  }, []);

  const topology: EntityTopology | undefined = topologyQuery.data;
  const nodePositions = useMemo(() => {
    const nodes = topology?.nodes ?? [];
    const columns = Math.max(Math.ceil(Math.sqrt(nodes.length)), 1);
    const rows = Math.max(Math.ceil(nodes.length / columns), 1);

    return new Map(
      nodes.map((node, index) => {
        const column = index % columns;
        const row = Math.floor(index / columns);
        const x = columns === 1 ? 50 : 10 + (column * 80) / (columns - 1);
        const y = rows === 1 ? 50 : 12 + (row * 76) / (rows - 1);
        return [node.id, { x, y }];
      }),
    );
  }, [topology?.nodes]);
  const selectedNode =
    topology?.nodes.find((node) => node.id === selectedNodeId) ??
    topology?.nodes.find((node) => node.id === topology.root_entity_id) ??
    null;
  const selectedNodeRelationships = (topology?.edges ?? []).filter(
    (edge) =>
      edge.source_entity_id === selectedNode?.id ||
      edge.target_entity_id === selectedNode?.id,
  );

  const applyFilters = (): void => {
    setAppliedFilters({ query: draftQuery.trim(), type: draftType });
    setSelectedEntityId(null);
    setSelectedNodeId(null);
  };
  const selectRootEntity = (entity: Entity): void => {
    setSelectedEntityId(entity.id);
    setSelectedNodeId(entity.id);
  };

  return (
    <AppShell activeItem="Topology" activeSection="entity">
      <PageHeader
        description="Explore live dependency relationships returned by the Observability Data Catalog."
        parentTitle="Entity"
        title="Topology"
      />
      <div className="flex min-h-0 flex-1 flex-col overflow-auto px-6 pb-6">
        <section className="mb-3 rounded-md border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center gap-4">
            <LabeledFilterSelect
              label="Entity Type"
              onChange={setDraftType}
              options={entityTypesQuery.data ?? []}
              selectedValue={draftType}
              value="All"
            />
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Search topology entities</span>
              <input
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-4 pr-12 text-sm text-slate-800 outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                onChange={(event) => setDraftQuery(event.target.value)}
                placeholder="Search entity by name, ID, namespace, or label..."
                type="search"
                value={draftQuery}
              />
              <Search
                aria-hidden="true"
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-700"
                size={19}
              />
            </label>
            <button
              className="h-10 rounded-md bg-blue-600 px-5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={candidateEntitiesQuery.isFetching}
              onClick={applyFilters}
              type="button"
            >
              Search
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {candidateEntitiesQuery.isPending ? (
              <span className="text-sm text-slate-500">
                Loading entities...
              </span>
            ) : null}
            {candidateEntitiesQuery.isError ? (
              <span className="text-sm text-red-600">
                {candidateEntitiesQuery.error.message ||
                  'Failed to load entities.'}
              </span>
            ) : null}
            {!candidateEntitiesQuery.isPending &&
            !candidateEntitiesQuery.isError &&
            (candidateEntitiesQuery.data?.items.length ?? 0) === 0 ? (
              <span className="text-sm text-slate-500">
                No matching entities.
              </span>
            ) : null}
            {(candidateEntitiesQuery.data?.items ?? []).map((entity) => (
              <button
                className={cn(
                  'rounded-md border px-3 py-2 text-left text-xs transition',
                  selectedEntityId === entity.id
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-blue-200 hover:bg-blue-50',
                )}
                key={entity.id}
                onClick={() => selectRootEntity(entity)}
                type="button"
              >
                <span className="block font-semibold">{entity.name}</span>
                <span className="mt-0.5 block text-slate-500">
                  {entity.type} · {entity.namespace || '—'}
                </span>
              </button>
            ))}
          </div>
        </section>
        <div className="grid min-h-[620px] grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_380px]">
          <section className="relative min-h-[620px] overflow-auto rounded-md border border-slate-200 bg-white">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,#e2e8f0_1px,transparent_0)] [background-size:18px_18px]" />
            <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur">
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <GitBranch
                  aria-hidden="true"
                  className="text-blue-600"
                  size={17}
                />
                <span>{topology?.nodes.length ?? 0} nodes</span>
                <span className="text-slate-300">•</span>
                <span>{topology?.edges.length ?? 0} relationships</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <LabeledFilterSelect
                  className="h-8 min-w-[150px] text-xs"
                  label="Direction"
                  onChange={(value) =>
                    setDirection(value as 'both' | 'downstream' | 'upstream')
                  }
                  options={[
                    { label: 'Both directions', value: 'both' },
                    { label: 'Upstream', value: 'upstream' },
                    { label: 'Downstream', value: 'downstream' },
                  ]}
                  selectedValue={direction}
                  value="Direction"
                />
                <LabeledFilterSelect
                  className="h-8 min-w-[112px] text-xs"
                  label="Depth"
                  onChange={(value) => setDepth(Number(value))}
                  options={[
                    { label: '1 hop', value: '1' },
                    { label: '2 hops', value: '2' },
                    { label: '3 hops', value: '3' },
                  ]}
                  selectedValue={String(depth)}
                  value="Depth"
                />
              </div>
            </div>
            {!selectedEntityId ? (
              <div className="relative z-10 flex min-h-[560px] items-center justify-center px-6 text-center text-sm text-slate-500">
                Choose a real entity above to load its topology.
              </div>
            ) : null}
            {topologyQuery.isPending ? (
              <div className="relative z-10 flex min-h-[560px] items-center justify-center text-sm text-slate-500">
                Loading topology from the catalog...
              </div>
            ) : null}
            {topologyQuery.isError ? (
              <div className="relative z-10 flex min-h-[560px] items-center justify-center px-6 text-center text-sm text-red-600">
                {topologyQuery.error.message || 'Failed to load topology.'}
              </div>
            ) : null}
            {topology && !topologyQuery.isPending && !topologyQuery.isError ? (
              <div className="relative z-10 min-h-[560px] min-w-[760px]">
                <svg
                  aria-hidden="true"
                  className="absolute inset-0 size-full overflow-visible"
                  preserveAspectRatio="none"
                  viewBox="0 0 100 100"
                >
                  <defs>
                    <marker
                      id="topology-arrow"
                      markerHeight="4"
                      markerWidth="4"
                      orient="auto"
                      refX="3.5"
                      refY="2"
                    >
                      <path d="M0,0 L4,2 L0,4 z" fill="#94a3b8" />
                    </marker>
                  </defs>
                  {topology.edges.map((edge) => {
                    const source = nodePositions.get(edge.source_entity_id);
                    const target = nodePositions.get(edge.target_entity_id);
                    if (!source || !target) return null;
                    return (
                      <line
                        key={edge.id}
                        markerEnd="url(#topology-arrow)"
                        stroke="#94a3b8"
                        strokeWidth="0.35"
                        x1={source.x}
                        x2={target.x}
                        y1={source.y}
                        y2={target.y}
                      />
                    );
                  })}
                </svg>
                {topology.nodes.map((node) => {
                  const position = nodePositions.get(node.id);
                  if (!position) return null;
                  const isRoot = node.id === topology.root_entity_id;
                  const isSelected = node.id === selectedNode?.id;
                  return (
                    <button
                      className={cn(
                        'absolute z-10 w-40 -translate-x-1/2 -translate-y-1/2 rounded-md border bg-white px-3 py-2 text-left shadow-sm transition hover:border-blue-300 hover:shadow-md',
                        isRoot && 'border-blue-500 ring-2 ring-blue-100',
                        isSelected &&
                          !isRoot &&
                          'border-violet-400 ring-2 ring-violet-100',
                      )}
                      key={node.id}
                      onClick={() => setSelectedNodeId(node.id)}
                      style={{ left: `${position.x}%`, top: `${position.y}%` }}
                      type="button"
                    >
                      <span className="flex items-center gap-2">
                        <Box
                          aria-hidden="true"
                          className="shrink-0 text-blue-600"
                          size={16}
                        />
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-semibold text-slate-950">
                            {node.name}
                          </span>
                          <span className="block truncate text-xs text-slate-500">
                            {node.type}
                          </span>
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            ) : null}
          </section>
          <aside className="overflow-hidden rounded-md border border-slate-200 bg-white">
            {!selectedNode ? (
              <div className="flex min-h-[240px] min-h-full items-center justify-center px-6 text-center text-sm text-slate-500">
                Select a topology node to view its live entity details.
              </div>
            ) : (
              <div className="space-y-5 p-5 text-sm">
                <div className="flex items-start justify-between gap-3 border-b border-slate-200 pb-5">
                  <div className="min-w-0">
                    <p className="truncate text-lg font-semibold text-slate-950">
                      {selectedNode.name}
                    </p>
                    <p className="mt-1 break-all text-xs text-slate-500">
                      {selectedNode.id}
                    </p>
                  </div>
                  <StatusBadge tone="blue">{selectedNode.type}</StatusBadge>
                </div>
                <dl className="grid grid-cols-[100px_1fr] gap-x-3 gap-y-4">
                  <dt className="text-slate-500">Namespace</dt>
                  <dd className="break-words text-slate-800">
                    {selectedNode.namespace || '—'}
                  </dd>
                  <dt className="text-slate-500">Status</dt>
                  <dd className="text-slate-800">{selectedNode.status}</dd>
                  <dt className="text-slate-500">Last Observed</dt>
                  <dd className="text-slate-800">
                    {selectedNode.updated_at
                      ? formatIntegrationDateTime(selectedNode.updated_at)
                      : '—'}
                  </dd>
                </dl>
                <section className="border-t border-slate-200 pt-5">
                  <h3 className="font-semibold text-slate-950">
                    Relationships ({selectedNodeRelationships.length})
                  </h3>
                  {selectedNodeRelationships.length === 0 ? (
                    <p className="mt-3 text-sm text-slate-500">
                      No relationships returned for this entity.
                    </p>
                  ) : (
                    <ul className="mt-3 space-y-2">
                      {selectedNodeRelationships.map((edge) => (
                        <li
                          className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700"
                          key={edge.id}
                        >
                          <span className="font-medium">{edge.type}</span>
                          <span className="mx-1 text-slate-400">·</span>
                          {edge.source_entity_id === selectedNode.id
                            ? `to ${edge.target_entity_id}`
                            : `from ${edge.source_entity_id}`}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
                <section className="border-t border-slate-200 pt-5">
                  <h3 className="font-semibold text-slate-950">Labels</h3>
                  {Object.keys(selectedNode.labels).length === 0 ? (
                    <p className="mt-3 text-sm text-slate-500">
                      No labels returned.
                    </p>
                  ) : (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {Object.entries(selectedNode.labels).map(
                        ([key, value]) => (
                          <span
                            className="max-w-full break-all rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700"
                            key={key}
                          >
                            {key}: {value}
                          </span>
                        ),
                      )}
                    </div>
                  )}
                </section>
              </div>
            )}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

type UploadType = 'local' | 'url';

function UploadTypeDialog({
  isOpen,
  onClose,
  onSelect,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (type: UploadType) => void;
}): ReactNode {
  if (!isOpen) {
    return null;
  }

  const options: {
    description: string;
    icon: typeof HardDriveUpload;
    label: string;
    type: UploadType;
  }[] = [
    {
      description: 'Upload a file from your computer.',
      icon: HardDriveUpload,
      label: 'Upload Local File',
      type: 'local',
    },
    {
      description: 'Import a document from a web URL.',
      icon: Globe,
      label: 'Upload Web URL',
      type: 'url',
    },
  ];

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[440px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              Upload File
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Choose how you want to add a document.
            </p>
          </div>
          <button
            aria-label="Close upload type dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={onClose}
            type="button"
          >
            ×
          </button>
        </div>
        <div className="space-y-3 p-6">
          {options.map((option) => {
            const Icon = option.icon;
            return (
              <button
                className="flex w-full items-center gap-4 rounded-md border border-slate-200 bg-white px-4 py-4 text-left transition hover:border-blue-300 hover:bg-blue-50"
                key={option.type}
                onClick={() => onSelect(option.type)}
                type="button"
              >
                <span className="grid size-10 shrink-0 place-items-center rounded-md bg-indigo-50 text-blue-700">
                  <Icon aria-hidden="true" size={20} />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-slate-950">
                    {option.label}
                  </span>
                  <span className="mt-0.5 block text-xs text-slate-500">
                    {option.description}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function UploadFileDialog({
  errorMessage,
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
  uploadType,
}: {
  errorMessage?: string;
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (values: {
    file?: File | null;
    name?: string;
    url?: string;
  }) => void;
  uploadType: UploadType;
}): ReactNode {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const closeDialog = () => {
    if (isSubmitting) {
      return;
    }
    setName('');
    setUrl('');
    setFile(null);
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  const isLocal = uploadType === 'local';
  const title = isLocal ? 'Upload Local File' : 'Upload Web URL';
  const canSubmit = isLocal ? file !== null : url.trim() !== '';

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[520px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
            <p className="mt-1 text-sm text-slate-500">
              {isLocal
                ? 'Select a file from your computer to upload.'
                : 'Enter a web URL to import a document.'}
            </p>
          </div>
          <button
            aria-label="Close upload dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
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
            if (!canSubmit) {
              return;
            }
            onSubmit({
              file,
              name: name.trim() || undefined,
              url: url.trim() || undefined,
            });
          }}
        >
          {isLocal ? (
            <div className="block">
              <span className="text-sm font-medium text-slate-800">File</span>
              <button
                className="mt-2 flex w-full items-center gap-3 rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-left transition hover:border-blue-400 hover:bg-blue-50"
                onClick={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.onchange = () => {
                    if (input.files?.[0]) {
                      setFile(input.files[0]);
                    }
                  };
                  input.click();
                }}
                type="button"
              >
                <span className="grid size-9 shrink-0 place-items-center rounded-md bg-white text-slate-400 shadow-sm">
                  <Upload aria-hidden="true" size={17} />
                </span>
                <span className="min-w-0 flex-1">
                  {file ? (
                    <>
                      <span className="block truncate text-sm font-medium text-slate-950">
                        {file.name}
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-500">
                        Click to replace
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="block text-sm font-medium text-slate-600">
                        Click to browse or drag a file here
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-400">
                        Supports common document formats
                      </span>
                    </>
                  )}
                </span>
              </button>
            </div>
          ) : (
            <label className="block">
              <span className="text-sm font-medium text-slate-800">
                Web URL
              </span>
              <input
                className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/document.pdf"
                type="url"
                value={url}
              />
            </label>
          )}

          <label className="block">
            <span className="text-sm font-medium text-slate-800">
              Document Name (optional)
            </span>
            <input
              className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              onChange={(event) => setName(event.target.value)}
              placeholder={isLocal ? (file?.name ?? 'Untitled') : 'Untitled'}
              type="text"
              value={name}
            />
          </label>

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting || !canSubmit}
              type="submit"
            >
              {isSubmitting ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function KnowledgeFilesPage(): ReactNode {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [baseKeyword, setBaseKeyword] = useState('');
  const [documentKeyword, setDocumentKeyword] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [documentStatus, setDocumentStatus] = useState('');
  const [documentPage, setDocumentPage] = useState(1);
  const [openKnowledgeBaseMenuId, setOpenKnowledgeBaseMenuId] = useState<
    string | null
  >(null);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<
    string | null
  >(null);
  const [isCreateBaseDialogOpen, setIsCreateBaseDialogOpen] = useState(false);
  const [knowledgeBaseMenuPosition, setKnowledgeBaseMenuPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);
  const [isUploadTypeDialogOpen, setIsUploadTypeDialogOpen] = useState(false);
  const [uploadType, setUploadType] = useState<UploadType>('local');
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);

  const baseQueryParams = {
    keyword: baseKeyword,
    page: 1,
    page_size: 50,
  };
  const documentQueryParams = {
    document_type: (documentType || undefined) as DocumentType | undefined,
    keyword: documentKeyword,
    page: documentPage,
    page_size: 10,
    status: (documentStatus || undefined) as DocumentStatus | undefined,
  };
  const knowledgeBasesQuery = useQuery({
    queryFn: () => listKnowledgeBases(baseQueryParams),
    queryKey: knowledgeQueryKeys.bases(baseQueryParams),
  });
  const knowledgeBases = useMemo(
    () => knowledgeBasesQuery.data?.items ?? [],
    [knowledgeBasesQuery.data?.items],
  );
  const selectedKnowledgeBase =
    knowledgeBases.find((item) => item.id === selectedKnowledgeBaseId) ?? null;
  const documentsQuery = useQuery({
    enabled: selectedKnowledgeBaseId !== null,
    queryFn: () =>
      listKnowledgeDocuments(
        selectedKnowledgeBaseId ?? '',
        documentQueryParams,
      ),
    queryKey: knowledgeQueryKeys.documents(
      selectedKnowledgeBaseId,
      documentQueryParams,
    ),
  });
  const createBaseMutation = useMutation({
    mutationFn: createKnowledgeBase,
    onSuccess: async (knowledgeBase) => {
      await queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
      setSelectedKnowledgeBaseId(knowledgeBase.id);
      setIsCreateBaseDialogOpen(false);
    },
  });
  const uploadDocumentMutation = useMutation({
    mutationFn: ({
      file,
      knowledgeBaseId,
    }: {
      file: File;
      knowledgeBaseId: string;
    }) =>
      uploadKnowledgeDocument(knowledgeBaseId, {
        document_type: inferDocumentType(file.name),
        file,
        metadata: {
          size_bytes: file.size,
        },
        name: file.name,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
    },
  });
  const updateBaseMutation = useMutation({
    mutationFn: ({
      knowledgeBase,
      status,
      name,
      description,
    }: {
      description?: string | null;
      knowledgeBase: KnowledgeBase;
      name?: string;
      status?: KnowledgeBase['status'];
    }) =>
      updateKnowledgeBase(knowledgeBase.id, {
        description,
        name,
        status,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
    },
  });
  const deleteBaseMutation = useMutation({
    mutationFn: deleteKnowledgeBase,
    onSuccess: async (_result, knowledgeBaseId) => {
      if (selectedKnowledgeBaseId === knowledgeBaseId) {
        setSelectedKnowledgeBaseId(null);
      }
      setOpenKnowledgeBaseMenuId(null);
      await queryClient.invalidateQueries({
        queryKey: knowledgeQueryKeys.all,
      });
    },
  });
  const documents = documentsQuery.data?.items ?? [];
  const documentTotal = documentsQuery.data?.total ?? 0;
  const queryError =
    knowledgeBasesQuery.error instanceof ApiError
      ? knowledgeBasesQuery.error.message
      : documentsQuery.error instanceof ApiError
        ? documentsQuery.error.message
        : 'Knowledge data could not be loaded.';
  const mutationError =
    createBaseMutation.error instanceof ApiError
      ? createBaseMutation.error.message
      : uploadDocumentMutation.error instanceof ApiError
        ? uploadDocumentMutation.error.message
        : updateBaseMutation.error instanceof ApiError
          ? updateBaseMutation.error.message
          : deleteBaseMutation.error instanceof ApiError
            ? deleteBaseMutation.error.message
            : null;
  const documentColumns: DataColumn<KnowledgeDocument>[] = [
    {
      className: 'w-[28%]',
      header: 'Name',
      render: (document) => {
        const DocumentIcon = getDocumentTypeIcon(document.document_type);

        return (
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={cn(
                'grid size-8 shrink-0 place-items-center rounded-md border',
                documentTypeClassNames[document.document_type],
              )}
            >
              <DocumentIcon aria-hidden="true" size={15} />
            </span>
            <div className="min-w-0">
              <p className="truncate font-semibold text-slate-950">
                {document.name}
              </p>
              <p className="mt-1 truncate text-xs text-slate-500">
                {getDocumentDescription(document)}
              </p>
            </div>
          </div>
        );
      },
    },
    {
      className: 'w-[10%]',
      header: 'Category',
      render: (document) => (
        <span className="inline-flex max-w-full rounded bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
          <span className="truncate">
            {document.tags[0] ?? documentTypeLabels[document.document_type]}
          </span>
        </span>
      ),
    },
    {
      className: 'w-[8%]',
      header: 'Status',
      render: (document) => (
        <StatusBadge tone={documentStatusTone[document.status]}>
          {formatDocumentStatus(document.status)}
        </StatusBadge>
      ),
    },
    {
      className: 'w-[13%]',
      header: 'Updated At',
      render: (document) => formatKnowledgeDate(document.updated_at),
    },
    {
      className: 'w-[8%]',
      header: 'Size',
      render: (document) => formatDocumentSize(document),
    },
    {
      className: 'w-[10%]',
      header: 'Author',
      render: (document) => (
        <div className="flex min-w-0 items-center gap-2">
          <span
            className={cn(
              'grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold text-white',
              getAuthorClassName(document.created_by),
            )}
          >
            {String(document.created_by).slice(-1)}
          </span>
          <span className="truncate text-xs text-slate-600">
            user-{document.created_by}
          </span>
        </div>
      ),
    },
    {
      className: 'w-[15%]',
      header: 'Actions',
      render: (document) => (
        <div className="flex items-center gap-1">
          <ActionButton
            aria-label={`View ${document.name}`}
            className="size-8 px-0 text-slate-500 hover:text-blue-600"
            message={`${document.name} opened`}
            size="sm"
            variant="ghost"
          >
            <Eye aria-hidden="true" size={14} />
          </ActionButton>
          <a
            aria-label={`Download ${document.name}`}
            className="grid size-8 place-items-center rounded-lg border border-slate-200 bg-slate-100 text-slate-500 shadow-sm transition hover:bg-slate-200 hover:text-blue-600"
            href={buildDocumentContentUrl(document.id)}
          >
            <Download aria-hidden="true" size={14} />
          </a>
          <ActionButton
            aria-label={`More actions for ${document.name}`}
            className="size-8 px-0 text-slate-500 hover:text-blue-600"
            message={`${document.name} actions opened`}
            size="sm"
            variant="ghost"
          >
            <MoreVertical aria-hidden="true" size={14} />
          </ActionButton>
        </div>
      ),
    },
  ];

  useEffect(() => {
    if (knowledgeBases.length === 0) {
      setSelectedKnowledgeBaseId(null);
      return;
    }

    if (!knowledgeBases.some((item) => item.id === selectedKnowledgeBaseId)) {
      setSelectedKnowledgeBaseId(knowledgeBases[0]?.id ?? null);
    }
  }, [knowledgeBases, selectedKnowledgeBaseId]);

  function handleCreateKnowledgeBase(): void {
    setIsCreateBaseDialogOpen(true);
  }

  async function handleSubmitKnowledgeBase(
    values: KnowledgeBaseFormValues,
  ): Promise<void> {
    await createBaseMutation.mutateAsync({
      description: values.description?.trim() || undefined,
      embedding_model: values.embedding_model,
      name: values.name,
    });
  }

  function handleUploadFile(file: File | undefined): void {
    if (!file || !selectedKnowledgeBaseId) {
      return;
    }

    uploadDocumentMutation.mutate({
      file,
      knowledgeBaseId: selectedKnowledgeBaseId,
    });
  }

  function handleToggleKnowledgeBase(knowledgeBase: KnowledgeBase): void {
    updateBaseMutation.mutate({
      knowledgeBase,
      status: knowledgeBase.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE',
    });
  }

  function handleEditKnowledgeBase(knowledgeBase: KnowledgeBase): void {
    const name = window.prompt('Knowledge base name', knowledgeBase.name);
    const trimmedName = name?.trim();

    if (!trimmedName || trimmedName === knowledgeBase.name) {
      setOpenKnowledgeBaseMenuId(null);
      setKnowledgeBaseMenuPosition(null);
      return;
    }

    updateBaseMutation.mutate({
      knowledgeBase,
      name: trimmedName,
    });
    setOpenKnowledgeBaseMenuId(null);
    setKnowledgeBaseMenuPosition(null);
  }

  function handleDeleteKnowledgeBase(knowledgeBase: KnowledgeBase): void {
    if (!window.confirm(`Delete knowledge base "${knowledgeBase.name}"?`)) {
      setOpenKnowledgeBaseMenuId(null);
      setKnowledgeBaseMenuPosition(null);
      return;
    }

    deleteBaseMutation.mutate(knowledgeBase.id);
  }

  return (
    <AppShell activeItem="Knowledge Bases" activeSection="knowledge">
      <PageHeader
        description="Browse and manage knowledge bases and their files."
        parentTitle="Knowledge"
        title="Knowledge Bases"
      />
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(320px,390px)_1fr] gap-4 overflow-auto px-6 pb-6">
        <aside className="rounded-md border border-slate-200 bg-white">
          <div className="flex items-center gap-3 border-b border-slate-200 p-4">
            <FilterInput
              onChange={setBaseKeyword}
              placeholder="Search knowledge bases..."
              value={baseKeyword}
            />
            <ActionButton
              className="h-10 shrink-0"
              disabled={createBaseMutation.isPending}
              message="Knowledge base creation started"
              onClick={handleCreateKnowledgeBase}
            >
              New
            </ActionButton>
          </div>
          <div
            className={cn(
              knowledgeBases.length > 1
                ? 'max-h-[calc(100vh-292px)] overflow-y-auto'
                : 'overflow-visible',
            )}
          >
            {knowledgeBasesQuery.isLoading ? (
              <IntegrationTableState>
                Loading knowledge bases...
              </IntegrationTableState>
            ) : knowledgeBasesQuery.isError ? (
              <IntegrationTableState tone="danger">
                {queryError}
              </IntegrationTableState>
            ) : knowledgeBases.length === 0 ? (
              <IntegrationTableState>
                No knowledge bases found.
              </IntegrationTableState>
            ) : (
              <div className="divide-y divide-slate-100">
                {knowledgeBases.map((knowledgeBase) => {
                  const isSelected =
                    knowledgeBase.id === selectedKnowledgeBaseId;
                  const isActive = knowledgeBase.status === 'ACTIVE';
                  const isChangingStatus =
                    updateBaseMutation.isPending &&
                    updateBaseMutation.variables?.knowledgeBase.id ===
                      knowledgeBase.id;
                  const isDeleting =
                    deleteBaseMutation.isPending &&
                    deleteBaseMutation.variables === knowledgeBase.id;

                  return (
                    <div
                      className={cn(
                        'flex w-full items-center gap-2.5 px-3 py-3 text-left transition hover:bg-blue-50',
                        isSelected && 'bg-blue-50',
                      )}
                      key={knowledgeBase.id}
                    >
                      <button
                        className="flex min-w-0 flex-1 items-center gap-2.5 text-left"
                        onClick={() => {
                          setSelectedKnowledgeBaseId(knowledgeBase.id);
                          setDocumentPage(1);
                        }}
                        type="button"
                      >
                        <span className="grid size-8 shrink-0 place-items-center rounded-md bg-indigo-50 text-blue-700">
                          <Folder
                            aria-hidden="true"
                            className="fill-blue-700"
                            size={18}
                            strokeWidth={1.8}
                          />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-semibold text-slate-950">
                            {knowledgeBase.name}
                          </span>
                          <span className="mt-1 block truncate text-xs text-slate-500">
                            {knowledgeBase.description ?? 'Knowledge base'}
                          </span>
                        </span>
                      </button>
                      <button
                        aria-label={
                          isActive
                            ? `Disable ${knowledgeBase.name}`
                            : `Enable ${knowledgeBase.name}`
                        }
                        aria-pressed={isActive}
                        className={cn(
                          'relative h-5 w-9 shrink-0 rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
                          isActive ? 'bg-indigo-500' : 'bg-slate-300',
                        )}
                        disabled={isChangingStatus || isDeleting}
                        onClick={() => handleToggleKnowledgeBase(knowledgeBase)}
                        title={isActive ? 'Disable' : 'Enable'}
                        type="button"
                      >
                        <span
                          className={cn(
                            'absolute top-0.5 grid size-4 rounded-full bg-white shadow-sm transition',
                            isActive ? 'left-[18px]' : 'left-0.5',
                          )}
                        />
                      </button>
                      <div className="relative shrink-0">
                        <button
                          aria-expanded={
                            openKnowledgeBaseMenuId === knowledgeBase.id
                          }
                          aria-label={`More actions for ${knowledgeBase.name}`}
                          className="grid size-7 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                          onClick={(event) => {
                            const rect =
                              event.currentTarget.getBoundingClientRect();
                            setKnowledgeBaseMenuPosition({
                              right: window.innerWidth - rect.right,
                              top: rect.bottom + 4,
                            });
                            setOpenKnowledgeBaseMenuId((currentId) =>
                              currentId === knowledgeBase.id
                                ? null
                                : knowledgeBase.id,
                            );
                          }}
                          type="button"
                        >
                          <MoreVertical aria-hidden="true" size={16} />
                        </button>
                        {openKnowledgeBaseMenuId === knowledgeBase.id &&
                        knowledgeBaseMenuPosition
                          ? createPortal(
                              <>
                                <div
                                  className="fixed inset-0 z-50"
                                  onClick={() => {
                                    setOpenKnowledgeBaseMenuId(null);
                                    setKnowledgeBaseMenuPosition(null);
                                  }}
                                />
                                <div
                                  className="fixed z-[60] w-32 overflow-hidden rounded-md border border-slate-200 bg-white py-1 shadow-lg shadow-slate-200"
                                  style={{
                                    top: `${knowledgeBaseMenuPosition.top}px`,
                                    right: `${knowledgeBaseMenuPosition.right}px`,
                                  }}
                                >
                                  <button
                                    className="block h-9 w-full px-3 text-left text-sm text-slate-700 hover:bg-blue-50 hover:text-blue-700"
                                    onClick={() =>
                                      handleEditKnowledgeBase(knowledgeBase)
                                    }
                                    type="button"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    className="block h-9 w-full px-3 text-left text-sm text-red-600 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                                    disabled={isDeleting}
                                    onClick={() =>
                                      handleDeleteKnowledgeBase(knowledgeBase)
                                    }
                                    type="button"
                                  >
                                    Delete
                                  </button>
                                </div>
                              </>,
                              document.body,
                            )
                          : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        <section className="min-w-0 overflow-hidden rounded-md border border-slate-200 bg-white">
          {selectedKnowledgeBase ? (
            <>
              <div className="border-b border-slate-200 px-5 pt-5">
                <div className="mb-4 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="mb-4 flex items-center gap-2 text-xs text-slate-500">
                      <span>Knowledge Bases</span>
                      <ChevronRight aria-hidden="true" size={13} />
                      <span className="truncate font-medium text-slate-700">
                        Files
                      </span>
                    </div>
                    <div className="flex min-w-0 items-center gap-4">
                      <span className="grid size-11 shrink-0 place-items-center rounded-md bg-indigo-50 text-blue-700">
                        <Folder
                          aria-hidden="true"
                          className="fill-blue-700"
                          size={21}
                          strokeWidth={1.8}
                        />
                      </span>
                      <div className="min-w-0">
                        <h2 className="truncate text-2xl font-semibold text-slate-950">
                          {selectedKnowledgeBase.name}
                        </h2>
                        <p className="mt-1 truncate text-sm text-slate-600">
                          {selectedKnowledgeBase.description ??
                            'Knowledge base files and documents.'}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <input
                      className="hidden"
                      onChange={(event) => {
                        handleUploadFile(event.target.files?.[0]);
                        event.currentTarget.value = '';
                      }}
                      ref={fileInputRef}
                      type="file"
                    />
                    <ActionButton
                      className="h-10 gap-2"
                      disabled={uploadDocumentMutation.isPending}
                      message="Upload file dialog opened"
                      onClick={() => setIsUploadTypeDialogOpen(true)}
                    >
                      <Upload aria-hidden="true" size={15} />
                      Upload File
                    </ActionButton>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <Toolbar>
                  <div className="flex flex-wrap gap-4">
                    <FilterInput
                      onChange={(keyword) => {
                        setDocumentKeyword(keyword);
                        setDocumentPage(1);
                      }}
                      placeholder="Search files..."
                      value={documentKeyword}
                    />
                    <LabeledFilterSelect
                      label="Category"
                      onChange={(value) => {
                        setDocumentType(value);
                        setDocumentPage(1);
                      }}
                      options={[
                        { label: 'Guide', value: 'GUIDE' },
                        { label: 'SOP', value: 'SOP' },
                        { label: 'Case', value: 'CASE' },
                        { label: 'Reference', value: 'REFERENCE' },
                        { label: 'Other', value: 'OTHER' },
                      ]}
                      selectedValue={documentType}
                      value="All"
                    />
                    <LabeledFilterSelect
                      label="Status"
                      onChange={(value) => {
                        setDocumentStatus(value);
                        setDocumentPage(1);
                      }}
                      options={[
                        { label: 'Uploaded', value: 'UPLOADED' },
                        { label: 'Pending', value: 'PENDING' },
                        { label: 'Processing', value: 'PROCESSING' },
                        { label: 'Ready', value: 'READY' },
                        { label: 'Failed', value: 'FAILED' },
                        { label: 'Archived', value: 'ARCHIVED' },
                      ]}
                      selectedValue={documentStatus}
                      value="All"
                    />
                  </div>
                  <ActionButton
                    className="h-10 w-28 px-0"
                    message="Knowledge documents search executed"
                    onClick={() => documentsQuery.refetch()}
                  >
                    Search
                  </ActionButton>
                </Toolbar>
                {mutationError ? (
                  <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {mutationError}
                  </div>
                ) : null}
                <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
                  {documentsQuery.isLoading ? (
                    <IntegrationTableState>
                      Loading files...
                    </IntegrationTableState>
                  ) : documentsQuery.isError ? (
                    <IntegrationTableState tone="danger">
                      {queryError}
                    </IntegrationTableState>
                  ) : documents.length === 0 ? (
                    <IntegrationTableState>
                      No files found.
                    </IntegrationTableState>
                  ) : (
                    <DataTable
                      columns={documentColumns}
                      containerClassName="rounded-none border-0"
                      getRowKey={(document) => document.id}
                      rows={documents}
                    />
                  )}
                  <FilesPagination
                    onPageChange={setDocumentPage}
                    page={documentPage}
                    pageSize={documentQueryParams.page_size}
                    total={documentTotal}
                  />
                </div>
              </div>
            </>
          ) : (
            <IntegrationTableState>
              Select or create a knowledge base to manage files.
            </IntegrationTableState>
          )}
        </section>
      </div>
      <UploadTypeDialog
        isOpen={isUploadTypeDialogOpen}
        onClose={() => setIsUploadTypeDialogOpen(false)}
        onSelect={(type) => {
          setUploadType(type);
          setIsUploadTypeDialogOpen(false);
          setIsUploadDialogOpen(true);
        }}
      />
      <UploadFileDialog
        isOpen={isUploadDialogOpen}
        isSubmitting={uploadDocumentMutation.isPending}
        onClose={() => setIsUploadDialogOpen(false)}
        onSubmit={(values) => {
          if (uploadType === 'local') {
            if (values.file) {
              handleUploadFile(values.file);
            }
            setIsUploadDialogOpen(false);
          } else {
            // Web URL upload - for now just close, no backend integration
            setIsUploadDialogOpen(false);
          }
        }}
        uploadType={uploadType}
      />
      <KnowledgeBaseFormDialog
        errorMessage={
          createBaseMutation.error instanceof ApiError
            ? createBaseMutation.error.message
            : undefined
        }
        isOpen={isCreateBaseDialogOpen}
        isSubmitting={createBaseMutation.isPending}
        onClose={() => {
          createBaseMutation.reset();
          setIsCreateBaseDialogOpen(false);
        }}
        onSubmit={handleSubmitKnowledgeBase}
      />
    </AppShell>
  );
}

function formatScore(score: number): string {
  return score.toFixed(2);
}

function getSearchResultCategory(result: RetrievalResult): string {
  return result.metadata.tags[0] ?? result.citation.section ?? 'Knowledge';
}

export function KnowledgeTestPage(): ReactNode {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'hybrid' | 'keyword'>('hybrid');
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const knowledgeBasesQuery = useQuery({
    queryFn: () =>
      listKnowledgeBases({
        page: 1,
        page_size: 100,
        status: 'ACTIVE',
      }),
    queryKey: knowledgeQueryKeys.bases({
      page: 1,
      page_size: 100,
      status: 'ACTIVE',
    }),
  });
  const knowledgeBases = useMemo(
    () => knowledgeBasesQuery.data?.items ?? [],
    [knowledgeBasesQuery.data?.items],
  );
  const selectedKnowledgeBase =
    knowledgeBases.find((item) => item.id === selectedKnowledgeBaseId) ??
    knowledgeBases[0] ??
    null;
  const searchMutation = useMutation({
    mutationFn: () =>
      searchKnowledge({
        include_trace: true,
        knowledge_base_ids: selectedKnowledgeBase
          ? [selectedKnowledgeBase.id]
          : undefined,
        query: query.trim(),
        rerank: searchMode === 'hybrid',
        top_k: 8,
      }),
  });
  const searchResponse = searchMutation.data;
  const results = searchResponse?.results ?? [];
  const averageScore =
    results.length === 0
      ? 0
      : results.reduce((total, result) => total + result.score, 0) /
        results.length;
  const searchError =
    searchMutation.error instanceof ApiError
      ? searchMutation.error.message
      : 'Knowledge search could not be completed.';

  useEffect(() => {
    if (!selectedKnowledgeBaseId && knowledgeBases[0]) {
      setSelectedKnowledgeBaseId(knowledgeBases[0].id);
    }
  }, [knowledgeBases, selectedKnowledgeBaseId]);

  function handleSearch(): void {
    if (!query.trim()) {
      return;
    }

    searchMutation.mutate();
  }

  function handleClear(): void {
    setQuery('');
    searchMutation.reset();
  }

  return (
    <AppShell activeItem="Test" activeSection="knowledge">
      <PageHeader
        actions={
          <>
            <label className="relative inline-flex h-10 min-w-[280px] items-center gap-3 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 shadow-sm">
              <span className="grid size-7 shrink-0 place-items-center rounded-md bg-violet-50 text-violet-700">
                <BookOpen aria-hidden="true" size={16} />
              </span>
              <select
                aria-label="Knowledge base"
                className="min-w-0 flex-1 cursor-pointer appearance-none bg-transparent pr-7 font-semibold outline-none"
                onChange={(event) =>
                  setSelectedKnowledgeBaseId(event.target.value)
                }
                value={selectedKnowledgeBase?.id ?? ''}
              >
                {knowledgeBases.map((knowledgeBase) => (
                  <option key={knowledgeBase.id} value={knowledgeBase.id}>
                    {knowledgeBase.name}
                  </option>
                ))}
              </select>
              <ChevronDown
                aria-hidden="true"
                className="pointer-events-none absolute right-3 text-slate-500"
                size={15}
              />
            </label>
            <LinkButton className="h-10 px-4" href="/knowledge/files">
              View Files
              <ExternalLink aria-hidden="true" size={14} />
            </LinkButton>
          </>
        }
        actionsClassName="pr-4"
        description="Test knowledge base retrieval and evaluate search results."
        parentTitle="Knowledge"
        title="Test"
      />
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(360px,430px)_1fr] gap-4 overflow-auto px-6 pb-6">
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-sm font-semibold text-slate-950">
              1. Enter your query
            </h2>
          </div>
          <div className="space-y-5 p-5">
            <label className="block">
              <span className="sr-only">Search query</span>
              <textarea
                className="h-36 w-full resize-none rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                maxLength={2000}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Ask a question or enter keywords..."
                value={query}
              />
              <span className="mt-1 block text-right text-xs text-slate-500">
                {query.length} / 2000
              </span>
            </label>

            <div>
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                Search Mode
                <Info aria-hidden="true" size={14} />
              </div>
              <div className="inline-flex overflow-hidden rounded-md border border-slate-200 bg-white">
                {[
                  ['hybrid', 'Hybrid (Vector + Keyword)'],
                  ['keyword', 'Keyword Only'],
                ].map(([value, label]) => (
                  <button
                    className={cn(
                      'h-10 px-4 text-sm font-medium transition',
                      searchMode === value
                        ? 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-500'
                        : 'text-slate-700 hover:bg-slate-50',
                    )}
                    key={value}
                    onClick={() => setSearchMode(value as 'hybrid' | 'keyword')}
                    type="button"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <button
              className="flex h-12 w-full items-center justify-between rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
              type="button"
            >
              <span className="inline-flex items-center gap-2">
                <Funnel aria-hidden="true" size={16} />
                Filters (Optional)
              </span>
              <ChevronDown aria-hidden="true" size={16} />
            </button>
            <button
              className="flex h-12 w-full items-center justify-between rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
              type="button"
            >
              <span className="inline-flex items-center gap-2">
                <SlidersHorizontal aria-hidden="true" size={16} />
                Advanced Options
              </span>
              <ChevronDown aria-hidden="true" size={16} />
            </button>

            <div className="grid grid-cols-2 gap-3">
              <ActionButton
                className="h-11 gap-2"
                disabled={!query.trim() || searchMutation.isPending}
                message="Knowledge search submitted"
                onClick={handleSearch}
              >
                <Search aria-hidden="true" size={16} />
                Search
              </ActionButton>
              <ActionButton
                className="h-11 gap-2"
                message="Knowledge search cleared"
                onClick={handleClear}
                variant="outline"
              >
                <RotateCcw aria-hidden="true" size={16} />
                Clear
              </ActionButton>
            </div>

            <div className="rounded-md border border-blue-100 bg-blue-50 px-4 py-3">
              <div className="flex items-center justify-between text-sm font-semibold text-blue-800">
                <span className="inline-flex items-center gap-2">
                  <Info aria-hidden="true" size={15} />
                  Tips
                </span>
                <button
                  aria-label="Dismiss tips"
                  className="text-slate-500 hover:text-slate-800"
                  type="button"
                >
                  ×
                </button>
              </div>
              <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-600">
                <li>Use natural language questions for better results</li>
                <li>
                  Be specific about the incident type, component, or error
                </li>
                <li>Add filters to narrow down results</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="min-w-0 overflow-hidden rounded-md border border-slate-200 bg-white">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-950">
                2. Search Results
              </h2>
              <Info aria-hidden="true" className="text-slate-500" size={14} />
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-slate-600">View</span>
              <div className="inline-flex overflow-hidden rounded-md border border-slate-200">
                <button
                  aria-label="List view"
                  className={cn(
                    'grid size-9 place-items-center',
                    viewMode === 'list'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-500',
                  )}
                  onClick={() => setViewMode('list')}
                  type="button"
                >
                  <List aria-hidden="true" size={16} />
                </button>
                <button
                  aria-label="Grid view"
                  className={cn(
                    'grid size-9 place-items-center border-l border-slate-200',
                    viewMode === 'grid'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-500',
                  )}
                  onClick={() => setViewMode('grid')}
                  type="button"
                >
                  <Grid2X2 aria-hidden="true" size={16} />
                </button>
              </div>
              <span className="text-slate-600">Sort by</span>
              <LabeledFilterSelect label="" value="Relevance" />
            </div>
          </div>
          <div className="space-y-4 p-4">
            <div className="grid grid-cols-4 gap-3">
              {[
                [String(results.length), 'Results'],
                [
                  searchResponse?.trace
                    ? `${(searchResponse.trace.latency_ms / 1000).toFixed(2)} s`
                    : '0.00 s',
                  'Search Time',
                ],
                [formatScore(averageScore), 'Avg. Score'],
                [searchMode === 'hybrid' ? 'Hybrid' : 'Keyword', 'Search Mode'],
              ].map(([value, label]) => (
                <div
                  className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3"
                  key={label}
                >
                  <p className="text-lg font-semibold text-blue-600">{value}</p>
                  <p className="mt-1 text-xs text-slate-500">{label}</p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              <span>
                Showing results from{' '}
                <span className="font-semibold">
                  {selectedKnowledgeBase?.name ?? 'All'}
                </span>{' '}
                knowledge base
              </span>
              <span>Query rewritten</span>
            </div>

            {searchMutation.isPending ? (
              <IntegrationTableState>
                Searching knowledge...
              </IntegrationTableState>
            ) : searchMutation.isError ? (
              <IntegrationTableState tone="danger">
                {searchError}
              </IntegrationTableState>
            ) : results.length === 0 ? (
              <IntegrationTableState>
                Enter a query and run search to preview retrieval results.
              </IntegrationTableState>
            ) : (
              <div className="space-y-3">
                {results.map((result, index) => {
                  const DocumentIcon = getDocumentTypeIcon(
                    result.metadata.document_type ?? 'OTHER',
                  );

                  return (
                    <article
                      className="grid grid-cols-[36px_58px_1fr_auto] items-start gap-3 rounded-md border border-slate-200 bg-white px-3 py-3"
                      key={result.chunk_id}
                    >
                      <span className="grid size-8 place-items-center rounded-md bg-slate-100 text-sm font-semibold text-slate-700">
                        {index + 1}
                      </span>
                      <span className="rounded-md bg-emerald-100 px-2 py-1 text-center text-xs font-semibold text-emerald-700">
                        {formatScore(result.score)}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-3">
                          <DocumentIcon
                            aria-hidden="true"
                            className="shrink-0 text-blue-600"
                            size={17}
                          />
                          <h3 className="truncate text-sm font-semibold text-slate-950">
                            {result.citation.document_name}
                          </h3>
                        </div>
                        <p className="mt-1 truncate text-xs text-slate-500">
                          {getSearchResultCategory(result)} ·{' '}
                          {result.metadata.document_type
                            ? documentTypeLabels[result.metadata.document_type]
                            : 'Document'}{' '}
                          · Updated {result.citation.document_version}
                        </p>
                        <p className="mt-2 line-clamp-2 text-sm leading-5 text-slate-700">
                          {result.citation.snippet ?? result.content}
                        </p>
                      </div>
                      <div className="flex min-w-[100px] flex-col items-end gap-6">
                        <span className="rounded bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                          {getSearchResultCategory(result)}
                        </span>
                        <a
                          className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-700"
                          href={result.citation.source_url}
                        >
                          View
                          <ExternalLink aria-hidden="true" size={13} />
                        </a>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

const modelFormSchema = z.object({
  credential_ref: z.string().trim().optional(),
  endpoint: z.string().trim().optional(),
  model_name: z
    .string()
    .trim()
    .min(1, 'Model name is required.')
    .max(128, 'Model name must be 128 characters or fewer.'),
  name: z
    .string()
    .trim()
    .min(1, 'Name is required.')
    .max(128, 'Name must be 128 characters or fewer.'),
  provider: z.string().trim().min(1, 'Provider is required.'),
});

type ModelFormValues = z.infer<typeof modelFormSchema>;

function ModelFormDialog({
  errorMessage,
  initialValues,
  isEditMode = false,
  isSubmitting,
  isOpen,
  onClose,
  onSubmit,
  providerOptions,
}: {
  errorMessage?: string;
  initialValues?: ModelFormValues | null;
  isEditMode?: boolean;
  isSubmitting: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: ModelFormValues) => Promise<void>;
  providerOptions: SettingsOption[];
}): ReactNode {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<ModelFormValues>({
    defaultValues: initialValues ?? {
      credential_ref: '',
      endpoint: '',
      model_name: '',
      name: '',
      provider: 'OPENAI',
    },
    resolver: zodResolver(modelFormSchema),
  });

  useEffect(() => {
    if (initialValues) {
      reset(initialValues);
    }
  }, [initialValues, reset]);

  const closeDialog = () => {
    if (isSubmitting) {
      return;
    }
    reset();
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[520px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              {isEditMode ? 'Edit Model' : 'New Model'}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {isEditMode
                ? 'Update AI model configuration.'
                : 'Configure a new AI model for ObserveLens.'}
            </p>
          </div>
          <button
            aria-label="Close model dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>

        <form
          className="space-y-5 px-6 py-5"
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
        >
          <label className="block">
            <RequiredLabel>Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.name ? 'border-red-300' : 'border-slate-200',
                isEditMode && 'cursor-not-allowed bg-slate-50 text-slate-500',
              )}
              placeholder="Production GPT-4o"
              readOnly={isEditMode}
              {...register('name')}
            />
            {errors.name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.name.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <RequiredLabel>Provider</RequiredLabel>
            <select
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.provider ? 'border-red-300' : 'border-slate-200',
              )}
              {...register('provider')}
            >
              {providerOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.provider ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.provider.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <RequiredLabel>Model Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.model_name ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="gpt-4o-2024-05-13"
              {...register('model_name')}
            />
            {errors.model_name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.model_name.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-800">Endpoint</span>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.endpoint ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="https://api.openai.com/v1"
              {...register('endpoint')}
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-800">API Key</span>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.credential_ref ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="secret/openai-api-key"
              {...register('credential_ref')}
            />
          </label>

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? isEditMode
                  ? 'Saving...'
                  : 'Creating...'
                : isEditMode
                  ? 'Save Changes'
                  : 'Create Model'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function SettingsModelsPage(): ReactNode {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [isCreateModelDialogOpen, setIsCreateModelDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);

  const queryParams = { page, page_size: 20 };
  const modelsQuery = useQuery({
    queryFn: () => listModels(queryParams),
    queryKey: settingsQueryKeys.models(queryParams),
  });
  const { data: providerOptions = [] } = useQuery({
    queryFn: listModelProviders,
    queryKey: [...settingsQueryKeys.all, 'providers'],
  });
  const { data: statusOptions = [] } = useQuery({
    queryFn: listModelStatuses,
    queryKey: [...settingsQueryKeys.all, 'statuses'],
  });

  const deleteModelMutation = useMutation({
    mutationFn: deleteModel,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: settingsQueryKeys.all,
      });
    },
  });
  const createModelMutation = useMutation({
    mutationFn: createModel,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: settingsQueryKeys.all,
      });
      setIsCreateModelDialogOpen(false);
    },
  });
  const updateModelMutation = useMutation({
    mutationFn: ({ id, request }: { id: number; request: ModelWriteRequest }) =>
      updateModel(id, request),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: settingsQueryKeys.all,
      });
      setEditingModel(null);
    },
  });

  const allModels = modelsQuery.data?.items ?? [];
  const total = modelsQuery.data?.total ?? 0;
  const pageSize = modelsQuery.data?.page_size ?? 20;

  // Client-side filtering for keyword, provider, status since the API
  // does not yet support these as query params
  const filteredModels = useMemo(
    () =>
      allModels.filter((model) => {
        if (
          keyword &&
          !model.name.toLowerCase().includes(keyword.toLowerCase()) &&
          !model.provider.toLowerCase().includes(keyword.toLowerCase())
        ) {
          return false;
        }
        if (providerFilter && model.provider !== providerFilter) {
          return false;
        }
        if (statusFilter && model.status !== statusFilter) {
          return false;
        }
        return true;
      }),
    [allModels, keyword, providerFilter, statusFilter],
  );

  const queryError =
    modelsQuery.error instanceof ApiError
      ? modelsQuery.error.message
      : deleteModelMutation.error instanceof ApiError
        ? deleteModelMutation.error.message
        : 'Models could not be loaded.';

  function handleDeleteModel(model: ModelConfig): void {
    if (!window.confirm(`Delete model "${model.name}"?`)) {
      return;
    }
    deleteModelMutation.mutate(model.id);
  }

  function handleToggleModelStatus(model: ModelConfig): void {
    updateModelMutation.mutate({
      id: model.id,
      request: {
        name: model.name,
        provider: model.provider,
        model_name: model.model_name,
        endpoint: model.endpoint,
        credential_ref: model.credential,
        status: model.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE',
      },
    });
  }

  const modelColumns: DataColumn<ModelConfig>[] = [
    {
      className: 'w-[18%]',
      header: 'Model Name',
      render: (model) => (
        <div className="flex items-center gap-3">
          <span
            className={cn(
              'grid size-8 place-items-center text-lg font-black',
              providerLogoClassNames[model.provider] ?? 'text-slate-950',
            )}
          >
            {providerLogoText[model.provider] ?? model.provider[0]}
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-950">
              {model.name}
              {model.is_default ? (
                <span className="ml-2 rounded border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700">
                  Default
                </span>
              ) : null}
            </p>
            <p className="mt-1 truncate text-xs text-slate-600">
              {model.model_name}
            </p>
          </div>
        </div>
      ),
    },
    {
      className: 'w-[10%]',
      header: 'Provider',
      render: (model) => (
        <span className="inline-flex items-center gap-2">
          <span
            className={cn(
              'text-lg font-black',
              providerLogoClassNames[model.provider] ?? 'text-slate-950',
            )}
          >
            {providerLogoText[model.provider] ?? model.provider[0]}
          </span>
          {model.provider}
        </span>
      ),
    },
    {
      className: 'w-[18%]',
      header: 'Endpoint',
      render: (model) => (
        <span className="truncate text-xs text-slate-600">
          {model.endpoint ?? '—'}
        </span>
      ),
    },
    {
      className: 'w-[14%]',
      header: 'API Key',
      render: (model) => {
        const key = model.credential;
        const masked =
          key && key.length > 12
            ? `${key.slice(0, 6)}***${key.slice(-6)}`
            : (key ?? '—');
        return (
          <span className="truncate font-mono text-xs text-slate-600">
            {masked}
          </span>
        );
      },
    },
    {
      className: 'w-[8%]',
      header: 'Status',
      render: (model) => {
        const isActive = model.status === 'ACTIVE';
        const isToggling =
          updateModelMutation.isPending &&
          updateModelMutation.variables?.id === model.id;
        return (
          <button
            aria-label={
              isActive ? `Disable ${model.name}` : `Enable ${model.name}`
            }
            aria-pressed={isActive}
            className={cn(
              'relative h-5 w-9 shrink-0 rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
              isActive ? 'bg-indigo-500' : 'bg-slate-300',
            )}
            disabled={isToggling}
            onClick={() => handleToggleModelStatus(model)}
            title={isActive ? 'Disable' : 'Enable'}
            type="button"
          >
            <span
              className={cn(
                'absolute top-0.5 grid size-4 rounded-full bg-white shadow-sm transition',
                isActive ? 'left-[18px]' : 'left-0.5',
              )}
            />
          </button>
        );
      },
    },
    {
      className: 'w-[10%]',
      header: 'Author',
      render: (model) => (
        <div className="flex min-w-0 items-center gap-2">
          <span
            className={cn(
              'grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold text-white',
              getAuthorClassName(model.created_by),
            )}
          >
            {String(model.created_by).slice(-1)}
          </span>
          <span className="truncate text-xs text-slate-600">
            user-{model.created_by}
          </span>
        </div>
      ),
    },
    {
      className: 'w-[12%]',
      header: 'Updated At',
      render: (model) => formatKnowledgeDate(model.updated_at),
    },
    {
      className: 'w-[10%]',
      header: 'Actions',
      render: (model) => (
        <div className="flex items-center gap-2">
          <ActionButton
            aria-label={`Edit ${model.name}`}
            className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
            message={`${model.name} editor opened`}
            onClick={() => setEditingModel(model)}
            size="sm"
            variant="ghost"
          >
            ✎
          </ActionButton>
          <ActionButton
            aria-label={`Delete ${model.name}`}
            className="size-8 border-0 bg-transparent p-0 text-red-600 shadow-none hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={
              deleteModelMutation.isPending &&
              deleteModelMutation.variables === model.id
            }
            message={`${model.name} deleted`}
            onClick={() => handleDeleteModel(model)}
            size="sm"
            variant="ghost"
          >
            <Trash2 aria-hidden="true" size={15} />
          </ActionButton>
        </div>
      ),
    },
  ];

  return (
    <AppShell activeItem="Models" activeSection="settings">
      <PageHeader
        actions={
          <button
            className="inline-flex h-10 w-28 items-center justify-center rounded-md bg-blue-600 px-0 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2"
            onClick={() => setIsCreateModelDialogOpen(true)}
            type="button"
          >
            New
          </button>
        }
        actionsClassName="pr-4"
        description="Manage and configure AI models used by ObserveLens."
        parentTitle="Settings"
        title="Models"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput
              onChange={setKeyword}
              placeholder="Search models by name or provider..."
              value={keyword}
            />
            <LabeledFilterSelect
              label="Provider"
              onChange={setProviderFilter}
              options={providerOptions}
              selectedValue={providerFilter}
              value="All"
            />
            <LabeledFilterSelect
              label="Status"
              onChange={setStatusFilter}
              options={statusOptions}
              selectedValue={statusFilter}
              value="All"
            />
          </div>
          <ActionButton
            className="h-10 w-28 px-0"
            message="Models search executed"
            onClick={() => modelsQuery.refetch()}
          >
            Search
          </ActionButton>
        </Toolbar>
        {queryError && modelsQuery.isError ? (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {queryError}
          </div>
        ) : null}
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          {modelsQuery.isLoading ? (
            <IntegrationTableState>Loading models...</IntegrationTableState>
          ) : modelsQuery.isError ? (
            <IntegrationTableState tone="danger">
              {queryError}
            </IntegrationTableState>
          ) : filteredModels.length === 0 ? (
            <IntegrationTableState>No models found.</IntegrationTableState>
          ) : (
            <DataTable
              columns={modelColumns}
              containerClassName="rounded-none border-0"
              getRowKey={(model) => String(model.id)}
              rows={filteredModels}
            />
          )}
          <FilesPagination
            onPageChange={setPage}
            page={page}
            pageSize={pageSize}
            total={total}
          />
        </section>
      </div>
      <ModelFormDialog
        errorMessage={
          createModelMutation.error instanceof ApiError
            ? createModelMutation.error.message
            : undefined
        }
        isOpen={isCreateModelDialogOpen}
        isSubmitting={createModelMutation.isPending}
        onClose={() => {
          createModelMutation.reset();
          setIsCreateModelDialogOpen(false);
        }}
        onSubmit={async (values) => {
          await createModelMutation.mutateAsync({
            credential_ref: values.credential_ref?.trim() || null,
            endpoint: values.endpoint?.trim() || null,
            model_name: values.model_name,
            name: values.name,
            provider: values.provider,
          });
        }}
        providerOptions={providerOptions}
      />
      <ModelFormDialog
        errorMessage={
          updateModelMutation.error instanceof ApiError
            ? updateModelMutation.error.message
            : undefined
        }
        initialValues={
          editingModel
            ? {
                credential_ref: editingModel.credential ?? '',
                endpoint: editingModel.endpoint ?? '',
                model_name: editingModel.model_name,
                name: editingModel.name,
                provider: editingModel.provider,
              }
            : null
        }
        isEditMode
        isOpen={editingModel !== null}
        isSubmitting={updateModelMutation.isPending}
        onClose={() => {
          updateModelMutation.reset();
          setEditingModel(null);
        }}
        onSubmit={async (values) => {
          if (!editingModel) {
            return;
          }
          await updateModelMutation.mutateAsync({
            id: editingModel.id,
            request: {
              credential_ref: values.credential_ref?.trim() || null,
              endpoint: values.endpoint?.trim() || null,
              model_name: values.model_name,
              name: values.name,
              provider: values.provider,
            },
          });
        }}
        providerOptions={providerOptions}
      />
    </AppShell>
  );
}

const notificationFormSchema = z.object({
  channel_type: z.string().trim().min(1, 'Type is required.'),
  credential_ref: z.string().trim().optional(),
  name: z
    .string()
    .trim()
    .min(1, 'Name is required.')
    .max(128, 'Name must be 128 characters or fewer.'),
  target: z.string().trim().min(1, 'Target is required.'),
});

type NotificationFormValues = z.infer<typeof notificationFormSchema>;

function NotificationFormDialog({
  errorMessage,
  initialValues,
  isEditMode = false,
  isSubmitting,
  isOpen,
  onClose,
  onSubmit,
  typeOptions,
}: {
  errorMessage?: string;
  initialValues?: NotificationFormValues | null;
  isEditMode?: boolean;
  isSubmitting: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: NotificationFormValues) => Promise<void>;
  typeOptions: SettingsOption[];
}): ReactNode {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<NotificationFormValues>({
    defaultValues: initialValues ?? {
      channel_type: 'WEBHOOK',
      credential_ref: '',
      name: '',
      target: '',
    },
    resolver: zodResolver(notificationFormSchema),
  });

  useEffect(() => {
    if (initialValues) {
      reset(initialValues);
    }
  }, [initialValues, reset]);

  const closeDialog = () => {
    if (isSubmitting) {
      return;
    }
    reset();
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4"
      role="dialog"
    >
      <div className="w-full max-w-[520px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              {isEditMode ? 'Edit Notification' : 'New Notification'}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {isEditMode
                ? 'Update notification webhook configuration.'
                : 'Configure a notification webhook for alerts and updates.'}
            </p>
          </div>
          <button
            aria-label="Close notification dialog"
            className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            onClick={closeDialog}
            type="button"
          >
            ×
          </button>
        </div>

        <form
          className="space-y-5 px-6 py-5"
          onSubmit={(event) => {
            void handleSubmit(onSubmit)(event);
          }}
        >
          <label className="block">
            <RequiredLabel>Name</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.name ? 'border-red-300' : 'border-slate-200',
                isEditMode && 'cursor-not-allowed bg-slate-50 text-slate-500',
              )}
              placeholder="Incidents Webhook"
              readOnly={isEditMode}
              {...register('name')}
            />
            {errors.name ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.name.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <RequiredLabel>Type</RequiredLabel>
            <select
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.channel_type ? 'border-red-300' : 'border-slate-200',
              )}
              {...register('channel_type')}
            >
              {typeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <RequiredLabel>Target URL</RequiredLabel>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.target ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="https://hooks.company.com/observe/incidents"
              {...register('target')}
            />
            {errors.target ? (
              <span className="mt-1 block text-xs text-red-600">
                {errors.target.message}
              </span>
            ) : null}
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-800">Token</span>
            <input
              className={cn(
                'mt-2 h-10 w-full rounded-md border bg-white px-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100',
                errors.credential_ref ? 'border-red-300' : 'border-slate-200',
              )}
              placeholder="secret/webhook-token"
              {...register('credential_ref')}
            />
          </label>

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              onClick={closeDialog}
              type="button"
            >
              Cancel
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? isEditMode
                  ? 'Saving...'
                  : 'Creating...'
                : isEditMode
                  ? 'Save Changes'
                  : 'Create Notification'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function SettingsNotificationsPage(): ReactNode {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [draftKeyword, setDraftKeyword] = useState('');
  const [appliedKeyword, setAppliedKeyword] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingNotification, setEditingNotification] =
    useState<NotificationConfig | null>(null);

  const queryParams = { page, page_size: 20 };
  const notificationsQuery = useQuery({
    queryFn: () => listNotifications(queryParams),
    queryKey: notificationQueryKeys.list(queryParams),
  });
  const { data: notificationTypeOptions = [] } = useQuery({
    queryFn: listNotificationTypes,
    queryKey: [...notificationQueryKeys.all, 'types'],
  });

  const deleteNotificationMutation = useMutation({
    mutationFn: deleteNotification,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.all,
      });
    },
  });
  const updateNotificationMutation = useMutation({
    mutationFn: ({
      id,
      request,
    }: {
      id: number;
      request: NotificationWriteRequest;
    }) => updateNotification(id, request),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.all,
      });
      setEditingNotification(null);
    },
  });
  const createNotificationMutation = useMutation({
    mutationFn: createNotification,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: notificationQueryKeys.all,
      });
      setIsCreateDialogOpen(false);
    },
  });

  const allNotifications = notificationsQuery.data?.items ?? [];
  const total = notificationsQuery.data?.total ?? 0;
  const pageSize = notificationsQuery.data?.page_size ?? 20;

  const filteredNotifications = useMemo(
    () =>
      allNotifications.filter((notification) => {
        if (
          appliedKeyword &&
          !notification.name
            .toLowerCase()
            .includes(appliedKeyword.toLowerCase())
        ) {
          return false;
        }
        return true;
      }),
    [allNotifications, appliedKeyword],
  );

  const queryError =
    notificationsQuery.error instanceof ApiError
      ? notificationsQuery.error.message
      : deleteNotificationMutation.error instanceof ApiError
        ? deleteNotificationMutation.error.message
        : updateNotificationMutation.error instanceof ApiError
          ? updateNotificationMutation.error.message
          : 'Notifications could not be loaded.';

  function handleDeleteNotification(notification: NotificationConfig): void {
    if (!window.confirm(`Delete notification "${notification.name}"?`)) {
      return;
    }
    deleteNotificationMutation.mutate(notification.id);
  }

  function handleToggleNotificationStatus(
    notification: NotificationConfig,
  ): void {
    updateNotificationMutation.mutate({
      id: notification.id,
      request: {
        name: notification.name,
        channel_type: notification.type,
        target: notification.target,
        status: notification.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE',
      },
    });
  }

  const notificationColumns: DataColumn<NotificationConfig>[] = [
    {
      className: 'w-[25%]',
      header: 'Name',
      render: (notification) => (
        <div className="flex items-center gap-3">
          <span className="grid size-8 shrink-0 place-items-center rounded-md bg-pink-50 text-pink-600">
            <BellRing aria-hidden="true" size={16} />
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-950">
              {notification.name}
            </p>
            <p className="mt-1 truncate text-xs text-slate-500">
              {notification.type}
            </p>
          </div>
        </div>
      ),
    },
    {
      className: 'w-[28%]',
      header: 'Target',
      render: (notification) => (
        <span className="truncate text-xs text-slate-600">
          {notification.target}
        </span>
      ),
    },
    {
      className: 'w-[14%]',
      header: 'Token',
      render: (notification) => {
        const token = notification.credential;
        const masked =
          token && token.length > 12
            ? `${token.slice(0, 6)}***${token.slice(-6)}`
            : (token ?? '—');
        return (
          <span className="truncate font-mono text-xs text-slate-600">
            {masked}
          </span>
        );
      },
    },
    {
      className: 'w-[8%]',
      header: 'Status',
      render: (notification) => {
        const isActive = notification.status === 'ACTIVE';
        const isToggling =
          updateNotificationMutation.isPending &&
          updateNotificationMutation.variables?.id === notification.id;
        return (
          <button
            aria-label={
              isActive
                ? `Disable ${notification.name}`
                : `Enable ${notification.name}`
            }
            aria-pressed={isActive}
            className={cn(
              'relative h-5 w-9 shrink-0 rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
              isActive ? 'bg-indigo-500' : 'bg-slate-300',
            )}
            disabled={isToggling}
            onClick={() => handleToggleNotificationStatus(notification)}
            title={isActive ? 'Disable' : 'Enable'}
            type="button"
          >
            <span
              className={cn(
                'absolute top-0.5 grid size-4 rounded-full bg-white shadow-sm transition',
                isActive ? 'left-[18px]' : 'left-0.5',
              )}
            />
          </button>
        );
      },
    },
    {
      className: 'w-[15%]',
      header: 'Updated At',
      render: (notification) => formatKnowledgeDate(notification.updated_at),
    },
    {
      className: 'w-[15%]',
      header: 'Actions',
      render: (notification) => (
        <div className="flex items-center gap-2">
          <ActionButton
            aria-label={`Edit ${notification.name}`}
            className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
            message={`${notification.name} editor opened`}
            onClick={() => setEditingNotification(notification)}
            size="sm"
            variant="ghost"
          >
            ✎
          </ActionButton>
          <ActionButton
            aria-label={`Delete ${notification.name}`}
            className="size-8 border-0 bg-transparent p-0 text-red-600 shadow-none hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={
              deleteNotificationMutation.isPending &&
              deleteNotificationMutation.variables === notification.id
            }
            message={`${notification.name} deleted`}
            onClick={() => handleDeleteNotification(notification)}
            size="sm"
            variant="ghost"
          >
            <Trash2 aria-hidden="true" size={15} />
          </ActionButton>
        </div>
      ),
    },
  ];

  return (
    <AppShell activeItem="Notifications" activeSection="settings">
      <PageHeader
        actions={
          <button
            className="inline-flex h-10 w-28 items-center justify-center rounded-md bg-blue-600 px-0 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2"
            onClick={() => setIsCreateDialogOpen(true)}
            type="button"
          >
            New
          </button>
        }
        actionsClassName="pr-4"
        description="Manage notification webhooks and delivery channels for alerts, updates, and incident workflows."
        parentTitle="Settings"
        title="Notifications"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput
              onChange={setDraftKeyword}
              placeholder="Search notifications by name..."
              value={draftKeyword}
            />
          </div>
          <ActionButton
            className="h-10 w-28 px-0"
            message="Notifications search executed"
            onClick={() => setAppliedKeyword(draftKeyword.trim())}
          >
            Search
          </ActionButton>
        </Toolbar>
        {queryError && notificationsQuery.isError ? (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {queryError}
          </div>
        ) : null}
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          {notificationsQuery.isLoading ? (
            <IntegrationTableState>
              Loading notifications...
            </IntegrationTableState>
          ) : notificationsQuery.isError ? (
            <IntegrationTableState tone="danger">
              {queryError}
            </IntegrationTableState>
          ) : filteredNotifications.length === 0 ? (
            <IntegrationTableState>
              No notifications found.
            </IntegrationTableState>
          ) : (
            <DataTable
              columns={notificationColumns}
              containerClassName="rounded-none border-0"
              getRowKey={(notification) => String(notification.id)}
              rows={filteredNotifications}
            />
          )}
          <FilesPagination
            onPageChange={setPage}
            page={page}
            pageSize={pageSize}
            total={total}
          />
        </section>
      </div>
      <NotificationFormDialog
        errorMessage={
          createNotificationMutation.error instanceof ApiError
            ? createNotificationMutation.error.message
            : undefined
        }
        isOpen={isCreateDialogOpen}
        isSubmitting={createNotificationMutation.isPending}
        onClose={() => {
          createNotificationMutation.reset();
          setIsCreateDialogOpen(false);
        }}
        onSubmit={async (values) => {
          await createNotificationMutation.mutateAsync({
            channel_type: values.channel_type,
            credential_ref: values.credential_ref?.trim() || null,
            name: values.name,
            target: values.target,
          });
        }}
        typeOptions={notificationTypeOptions}
      />
      <NotificationFormDialog
        errorMessage={
          updateNotificationMutation.error instanceof ApiError
            ? updateNotificationMutation.error.message
            : undefined
        }
        initialValues={
          editingNotification
            ? {
                channel_type: editingNotification.type,
                credential_ref: editingNotification.credential ?? '',
                name: editingNotification.name,
                target: editingNotification.target,
              }
            : null
        }
        isEditMode
        isOpen={editingNotification !== null}
        isSubmitting={updateNotificationMutation.isPending}
        onClose={() => {
          updateNotificationMutation.reset();
          setEditingNotification(null);
        }}
        onSubmit={async (values) => {
          if (!editingNotification) {
            return;
          }
          await updateNotificationMutation.mutateAsync({
            id: editingNotification.id,
            request: {
              channel_type: values.channel_type,
              credential_ref: values.credential_ref?.trim() || null,
              name: values.name,
              target: values.target,
            },
          });
        }}
        typeOptions={notificationTypeOptions}
      />
    </AppShell>
  );
}

const observationTabs = [
  { icon: Activity, label: 'Metrics', value: 'API Gateway Error Rate' },
  { icon: FileSearch, label: 'Logs', value: '504 Timeout Burst' },
  { icon: GitBranch, label: 'Trace', value: 'user-service latency' },
  { icon: Box, label: 'Topology', value: 'api-gateway → user-service' },
];

function getObservationEventContent(event: AESPEvent): string {
  const content = event.data.content;

  if (typeof content === 'string' && content.trim()) {
    return content;
  }

  const summary = event.data.summary;

  if (typeof summary === 'string' && summary.trim()) {
    return summary;
  }

  return JSON.stringify(event.data);
}

function ObservationMessage({ message }: { message: Message }): ReactNode {
  const isUser = message.role.toUpperCase() === 'USER';

  return (
    <article className="flex gap-3">
      <span
        className={cn(
          'grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold',
          isUser ? 'bg-blue-600 text-white' : 'bg-emerald-500 text-white',
        )}
      >
        {isUser ? 'U' : 'A'}
      </span>
      <div className="min-w-0 flex-1 rounded-md border border-slate-200 p-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold text-slate-950">
            {isUser ? 'User request' : 'Agent observation'}
          </h3>
          <span className="shrink-0 text-xs text-slate-500">
            {formatIntegrationDateTime(message.created_at)}
          </span>
        </div>
        <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">
          {message.content}
        </p>
      </div>
    </article>
  );
}

export function ChatObservationsPage(): ReactNode {
  const [selectedConversationId, setSelectedConversationId] = useState<
    number | null
  >(null);
  const conversationsQuery = useQuery({
    queryFn: () => listConversations({ page: 1, page_size: 100 }),
    queryKey: conversationQueryKeys.list({ page: 1, page_size: 100 }),
  });

  useEffect(() => {
    if (
      selectedConversationId === null &&
      conversationsQuery.data?.items.length
    ) {
      setSelectedConversationId(conversationsQuery.data.items[0].id);
    }
  }, [conversationsQuery.data?.items, selectedConversationId]);

  const messagesQuery = useQuery({
    enabled: selectedConversationId !== null,
    queryFn: () =>
      listMessages(selectedConversationId as number, {
        page: 1,
        page_size: 100,
      }),
    queryKey: messageQueryKeys.list(selectedConversationId ?? 0, {
      page: 1,
      page_size: 100,
    }),
  });
  const selectedConversation =
    conversationsQuery.data?.items.find(
      (conversation) => conversation.id === selectedConversationId,
    ) ?? null;
  const messages = messagesQuery.data?.items ?? [];
  const evidenceEvents = messages.flatMap(
    (message) => message.metadata?.events ?? [],
  );

  return (
    <AppShell activeItem="Observations" activeSection="chat">
      <PageHeader
        actions={
          <LinkButton href="/" tone="default">
            <Send aria-hidden="true" size={15} />
            Ask Follow-up
          </LinkButton>
        }
        description="Review messages and streamed evidence from a real investigation conversation."
        parentTitle="Chat"
        title="Observations"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <section className="mb-4 rounded-md border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="min-w-[280px] flex-1">
              <span className="sr-only">Conversation</span>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                disabled={
                  conversationsQuery.isPending || conversationsQuery.isError
                }
                onChange={(event) =>
                  setSelectedConversationId(Number(event.target.value))
                }
                value={selectedConversationId ?? ''}
              >
                <option value="">Select a conversation</option>
                {(conversationsQuery.data?.items ?? []).map(
                  (conversation: Conversation) => (
                    <option key={conversation.id} value={conversation.id}>
                      {conversation.title || `Conversation #${conversation.id}`}
                    </option>
                  ),
                )}
              </select>
            </label>
            <button
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={
                messagesQuery.isFetching || selectedConversationId === null
              }
              onClick={() => {
                void messagesQuery.refetch();
              }}
              type="button"
            >
              <RefreshCw aria-hidden="true" size={15} />
              Refresh
            </button>
          </div>
          {conversationsQuery.isError ? (
            <p className="mt-3 text-sm text-red-600">
              {conversationsQuery.error.message ||
                'Failed to load conversations.'}
            </p>
          ) : null}
        </section>
        <div className="grid min-h-0 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_390px]">
          <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
            <div className="flex min-h-12 items-center justify-between gap-3 border-b border-slate-200 px-4">
              <div>
                <h2 className="text-sm font-semibold">
                  Investigation Timeline
                </h2>
                {selectedConversation ? (
                  <p className="mt-0.5 text-xs text-slate-500">
                    {selectedConversation.title ||
                      `Conversation #${selectedConversation.id}`}
                  </p>
                ) : null}
              </div>
              {selectedConversation ? (
                <StatusBadge tone="blue">
                  {selectedConversation.status}
                </StatusBadge>
              ) : null}
            </div>
            {selectedConversationId === null ? (
              <div className="flex min-h-[360px] items-center justify-center px-6 text-center text-sm text-slate-500">
                Select a conversation to load its investigation timeline.
              </div>
            ) : null}
            {messagesQuery.isPending ? (
              <div className="flex min-h-[360px] items-center justify-center text-sm text-slate-500">
                Loading conversation messages...
              </div>
            ) : null}
            {messagesQuery.isError ? (
              <div className="flex min-h-[360px] items-center justify-center px-6 text-center text-sm text-red-600">
                {messagesQuery.error.message || 'Failed to load messages.'}
              </div>
            ) : null}
            {!messagesQuery.isPending &&
            !messagesQuery.isError &&
            selectedConversationId !== null &&
            messages.length === 0 ? (
              <div className="flex min-h-[360px] items-center justify-center px-6 text-center text-sm text-slate-500">
                This conversation has no messages yet.
              </div>
            ) : null}
            {!messagesQuery.isPending &&
            !messagesQuery.isError &&
            messages.length > 0 ? (
              <div className="space-y-4 p-5">
                {messages.map((message) => (
                  <ObservationMessage key={message.id} message={message} />
                ))}
              </div>
            ) : null}
          </section>
          <aside className="overflow-hidden rounded-md border border-slate-200 bg-white">
            <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
              <h2 className="text-sm font-semibold">Observation Evidence</h2>
              <span className="text-xs text-slate-500">
                {evidenceEvents.length} events
              </span>
            </div>
            {selectedConversationId === null ? (
              <div className="flex min-h-[240px] items-center justify-center px-6 text-center text-sm text-slate-500">
                Evidence will appear after you select a conversation.
              </div>
            ) : null}
            {selectedConversationId !== null && evidenceEvents.length === 0 ? (
              <div className="flex min-h-[240px] items-center justify-center px-6 text-center text-sm text-slate-500">
                No AESP evidence events were returned for this conversation.
              </div>
            ) : null}
            {evidenceEvents.length > 0 ? (
              <div className="space-y-3 p-4">
                {evidenceEvents.map((event) => (
                  <article
                    className="rounded-md border border-slate-200 p-3"
                    key={`${event.run_id}:${event.sequence}:${event.id}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <StatusBadge tone="violet">{event.type}</StatusBadge>
                      <span className="text-xs text-slate-500">
                        {formatIntegrationDateTime(event.timestamp)}
                      </span>
                    </div>
                    <p className="mt-3 max-h-44 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
                      {getObservationEventContent(event)}
                    </p>
                  </article>
                ))}
              </div>
            ) : null}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
