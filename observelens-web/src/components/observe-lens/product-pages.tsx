import {
  AppShell,
  FilterInput,
  PageHeader,
  SelectLike,
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
import { cn } from '@/lib/utils';
import {
  Activity,
  BellRing,
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
  FileSearch,
  FileText,
  Grid2X2,
  GitBranch,
  List,
  MessageCircle,
  MessageSquare,
  MoreVertical,
  Play,
  Plus,
  Search,
  Send,
  Server,
  Settings,
  ShieldCheck,
  Square,
  Zap,
} from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';

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
  createdAt: string;
  name: string;
  severity: 'Critical' | 'Warning' | 'Info';
  source: string;
  status: 'Acknowledged' | 'Investigating' | 'Open' | 'Resolved';
  updatedAt: string;
}

const incidents: IncidentRow[] = [
  {
    assignee: 'sre-team',
    createdAt: '2026-07-08 10:21:34',
    name: 'Kafka Consumer Lag 持续增长',
    severity: 'Critical',
    source: 'AlertManager',
    status: 'Investigating',
    updatedAt: '2m ago',
  },
  {
    assignee: 'lijing',
    createdAt: '2026-07-08 09:58:11',
    name: 'Broker CPU 使用率过高',
    severity: 'Warning',
    source: 'Grafana',
    status: 'Open',
    updatedAt: '23m ago',
  },
  {
    assignee: 'wangwei',
    createdAt: '2026-07-08 09:30:45',
    name: 'Pod CrashLoopBackOff',
    severity: 'Critical',
    source: 'AlertManager',
    status: 'Open',
    updatedAt: '51m ago',
  },
  {
    assignee: 'zhangsan',
    createdAt: '2026-07-08 08:12:07',
    name: 'Topic Unavailable',
    severity: 'Critical',
    source: 'AlertManager',
    status: 'Open',
    updatedAt: '2h ago',
  },
  {
    assignee: 'lijing',
    createdAt: '2026-07-08 07:45:22',
    name: 'Disk 使用率超过阈值',
    severity: 'Warning',
    source: 'Grafana',
    status: 'Acknowledged',
    updatedAt: '3h ago',
  },
  {
    assignee: 'sre-team',
    createdAt: '2026-07-08 07:20:18',
    name: 'API 错误率升高',
    severity: 'Warning',
    source: 'Webhook',
    status: 'Open',
    updatedAt: '3h ago',
  },
  {
    assignee: 'wangwei',
    createdAt: 'Yesterday 23:18',
    name: 'Database 连接数耗尽',
    severity: 'Critical',
    source: 'AlertManager',
    status: 'Resolved',
    updatedAt: 'Yesterday 23:45',
  },
  {
    assignee: 'zhangsan',
    createdAt: 'Yesterday 22:10',
    name: 'Redis 内存使用率过高',
    severity: 'Warning',
    source: 'Grafana',
    status: 'Resolved',
    updatedAt: 'Yesterday 22:35',
  },
  {
    assignee: 'lijing',
    createdAt: 'Yesterday 21:05',
    name: 'Service 响应时间过高',
    severity: 'Warning',
    source: 'Webhook',
    status: 'Resolved',
    updatedAt: 'Yesterday 21:20',
  },
  {
    assignee: 'sre-team',
    createdAt: 'Yesterday 20:15',
    name: 'Nginx 5xx 错误增多',
    severity: 'Critical',
    source: 'AlertManager',
    status: 'Resolved',
    updatedAt: 'Yesterday 20:40',
  },
];

const severityTone: Record<IncidentRow['severity'], StatusTone> = {
  Critical: 'red',
  Info: 'blue',
  Warning: 'amber',
};

const incidentStatusTone: Record<IncidentRow['status'], StatusTone> = {
  Acknowledged: 'violet',
  Investigating: 'blue',
  Open: 'blue',
  Resolved: 'emerald',
};

const severityDotClassNames: Record<IncidentRow['severity'], string> = {
  Critical: 'bg-red-500',
  Info: 'bg-blue-500',
  Warning: 'bg-amber-500',
};

const assigneeClassNames: Record<string, string> = {
  lijing: 'bg-lime-500',
  'sre-team': 'bg-violet-600',
  wangwei: 'bg-cyan-600',
  zhangsan: 'bg-orange-500',
};

const sourceClassNames: Record<string, string> = {
  AlertManager: 'bg-orange-500 text-white',
  Grafana: 'bg-orange-500 text-white',
  Webhook: 'bg-slate-100 text-slate-700',
};

const incidentColumns: DataColumn<IncidentRow>[] = [
  {
    className: 'w-[25%]',
    header: 'Title',
    render: (row) => (
      <div>
        <p className="font-semibold text-slate-950">{row.name}</p>
      </div>
    ),
  },
  {
    className: 'w-[12%]',
    header: 'Severity',
    render: (row) => (
      <StatusBadge tone={severityTone[row.severity]}>
        <span
          aria-hidden="true"
          className={cn(
            'mr-1.5 size-1.5 rounded-full',
            severityDotClassNames[row.severity],
          )}
        />
        {row.severity}
      </StatusBadge>
    ),
  },
  {
    className: 'w-[13%]',
    header: 'Status',
    render: (row) => (
      <StatusBadge tone={incidentStatusTone[row.status]}>
        {row.status}
      </StatusBadge>
    ),
  },
  {
    className: 'w-[13%]',
    header: 'Source',
    render: (row) => (
      <span className="inline-flex items-center gap-2">
        <span
          className={cn(
            'grid size-5 place-items-center rounded-full text-[10px] font-semibold',
            sourceClassNames[row.source],
          )}
        >
          !
        </span>
        {row.source}
      </span>
    ),
  },
  {
    className: 'w-[14%]',
    header: 'Start Time',
    render: (row) => row.createdAt,
  },
  {
    className: 'w-[11%]',
    header: 'Updated At',
    render: (row) => row.updatedAt,
  },
  {
    className: 'w-[13%]',
    header: 'Assignee',
    render: (row) => (
      <span className="inline-flex items-center gap-2">
        <span
          className={cn(
            'grid size-6 place-items-center rounded-full text-xs font-semibold text-white',
            assigneeClassNames[row.assignee] ?? 'bg-slate-500',
          )}
        >
          {row.assignee.slice(0, 1).toUpperCase()}
        </span>
        {row.assignee}
      </span>
    ),
  },
  {
    className: 'w-[12%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <LinkButton
          ariaLabel={`Open ${row.name} chat`}
          className="h-8 px-2.5"
          href="/"
        >
          <MessageCircle aria-hidden="true" size={15} />
          Ask AI
        </LinkButton>
        <ActionButton
          aria-label={`More actions for ${row.name}`}
          className="size-8 px-0 text-slate-500 hover:text-slate-900"
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

function IncidentPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 10 of 24 incidents</span>
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
  name: string;
  status: 'Enabled' | 'Disabled';
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

const integrations: IntegrationRow[] = [
  {
    createdAt: '2024-05-20 10:30',
    name: 'AlertManager (Production)',
    status: 'Enabled',
    type: 'AlertManager',
    url: 'https://observelens.company.com/webhook/alertmanager/abc123...',
  },
  {
    createdAt: '2024-05-18 14:22',
    name: 'Grafana Alerting',
    status: 'Enabled',
    type: 'Grafana',
    url: 'https://observelens.company.com/webhook/grafana/def456...',
  },
  {
    createdAt: '2024-05-15 09:11',
    name: 'Prometheus Alertmanager',
    status: 'Enabled',
    type: 'Prometheus',
    url: 'https://observelens.company.com/webhook/prometheus/ghi789...',
  },
  {
    createdAt: '2024-05-10 16:45',
    name: 'Datadog',
    status: 'Enabled',
    type: 'Datadog',
    url: 'https://observelens.company.com/webhook/datadog/jkl012...',
  },
  {
    createdAt: '2024-05-08 11:20',
    name: 'Zabbix',
    status: 'Disabled',
    type: 'Zabbix',
    url: 'https://observelens.company.com/webhook/zabbix/mno345...',
  },
  {
    createdAt: '2024-05-05 13:33',
    name: 'Nagios',
    status: 'Disabled',
    type: 'Nagios',
    url: 'https://observelens.company.com/webhook/nagios/pqr678...',
  },
  {
    createdAt: '2024-05-01 10:05',
    name: 'Webhook (Custom)',
    status: 'Enabled',
    type: 'Webhook',
    url: 'https://alerts.company.com/observelens/webhook/stu901...',
  },
  {
    createdAt: '2024-04-28 15:12',
    name: 'OpsGenie',
    status: 'Disabled',
    type: 'OpsGenie',
    url: 'https://observelens.company.com/webhook/opsgenie/vwx234...',
  },
];

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

function IntegrationStatusBadge({
  status,
}: {
  status: IntegrationRow['status'];
}): ReactNode {
  const isEnabled = status === 'Enabled';

  return (
    <span
      className={cn(
        'inline-flex h-6 items-center gap-1.5 rounded border px-2 text-xs font-medium',
        isEnabled
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
          : 'border-slate-200 bg-slate-50 text-slate-600',
      )}
    >
      <span
        className={cn(
          'size-1.5 rounded-full',
          isEnabled ? 'bg-emerald-500' : 'bg-slate-400',
        )}
      />
      {status}
    </span>
  );
}

const integrationColumns: DataColumn<IntegrationRow>[] = [
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
        <span className="block truncate text-sm text-slate-700">{row.url}</span>
        <ActionButton
          aria-label={`Copy ${row.name} webhook URL`}
          className="size-7 shrink-0 border-0 bg-transparent p-0 text-slate-500 shadow-none hover:bg-slate-100 hover:text-blue-600"
          message={`${row.name} webhook URL copied`}
          size="sm"
          variant="ghost"
        >
          <Copy aria-hidden="true" size={14} />
        </ActionButton>
      </span>
    ),
  },
  {
    className: 'w-[11%]',
    header: 'Status',
    render: (row) => <IntegrationStatusBadge status={row.status} />,
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
        <ActionButton
          aria-label={`Edit ${row.name}`}
          className="size-8 p-0 text-blue-600 hover:text-blue-700"
          message={`${row.name} editor opened`}
          size="sm"
          variant="ghost"
        >
          ✎
        </ActionButton>
        <ActionButton
          aria-label={`Test ${row.name} webhook`}
          className="size-8 p-0 text-blue-600 hover:text-blue-700"
          message={`${row.name} webhook test started`}
          size="sm"
          variant="ghost"
        >
          <Send aria-hidden="true" size={14} />
        </ActionButton>
        <ActionButton
          aria-label={`More actions for ${row.name}`}
          className="size-8 p-0 text-blue-600 hover:text-blue-700"
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

function LabeledFilterSelect({
  label,
  value,
}: {
  label: string;
  value: string;
}): ReactNode {
  return (
    <button
      className="inline-flex h-10 min-w-[206px] items-center justify-between rounded-md border border-slate-200 bg-white px-4 text-sm text-slate-800 shadow-sm transition hover:border-blue-200 hover:bg-blue-50"
      type="button"
    >
      <span className="font-medium text-slate-950">{label}</span>
      <span className="ml-6 flex items-center gap-5 text-slate-700">
        {value}
        <ChevronDown aria-hidden="true" size={15} />
      </span>
    </button>
  );
}

function IntegrationPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 8 of 8 integrations</span>
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

interface InspectionRow {
  createdAt: string;
  environment: 'Production' | 'Staging';
  id: string;
  lastRun: string;
  lastRunState?: 'Failed' | 'Running...' | 'Success';
  name: string;
  nextRun: string;
  scope: string;
  status: 'Completed' | 'Failed' | 'In Progress' | 'Scheduled';
  type:
    | 'Alert'
    | 'Connectivity'
    | 'Health'
    | 'Log'
    | 'Network'
    | 'Performance'
    | 'Resource'
    | 'Security';
}

const inspections: InspectionRow[] = [
  {
    createdAt: '2024-05-18 09:15:22',
    environment: 'Production',
    id: 'INS-20240520-001',
    lastRun: '2024-05-20 10:30:45',
    lastRunState: 'Success',
    name: 'Kubernetes Health Check',
    nextRun: '2024-05-21 10:30:00',
    scope: 'All Clusters (3)',
    status: 'Completed',
    type: 'Health',
  },
  {
    createdAt: '2024-05-19 14:22:10',
    environment: 'Production',
    id: 'INS-20240520-002',
    lastRun: '—',
    lastRunState: 'Running...',
    name: 'Database Connectivity',
    nextRun: '—',
    scope: 'Databases (12)',
    status: 'In Progress',
    type: 'Connectivity',
  },
  {
    createdAt: '2024-05-17 16:45:33',
    environment: 'Staging',
    id: 'INS-20240520-003',
    lastRun: '2024-05-20 09:15:30',
    lastRunState: 'Success',
    name: 'Cloud Resource Check',
    nextRun: '2024-05-21 09:00:00',
    scope: 'AWS Account',
    status: 'Completed',
    type: 'Resource',
  },
  {
    createdAt: '2024-05-16 11:05:18',
    environment: 'Production',
    id: 'INS-20240520-004',
    lastRun: '2024-05-20 08:45:12',
    lastRunState: 'Failed',
    name: 'Critical Alerts Review',
    nextRun: '2024-05-20 11:00:00',
    scope: 'All Services',
    status: 'Failed',
    type: 'Alert',
  },
  {
    createdAt: '2024-05-15 10:30:45',
    environment: 'Production',
    id: 'INS-20240520-005',
    lastRun: '—',
    name: 'Security Compliance Scan',
    nextRun: '2024-05-20 12:00:00',
    scope: 'All Resources',
    status: 'Scheduled',
    type: 'Security',
  },
  {
    createdAt: '2024-05-14 15:20:10',
    environment: 'Staging',
    id: 'INS-20240520-006',
    lastRun: '2024-05-19 23:10:05',
    lastRunState: 'Success',
    name: 'Log Pipeline Check',
    nextRun: '2024-05-20 23:00:00',
    scope: 'Logging Pipeline',
    status: 'Completed',
    type: 'Log',
  },
  {
    createdAt: '2024-05-13 13:10:22',
    environment: 'Production',
    id: 'INS-20240520-007',
    lastRun: '2024-05-19 22:05:45',
    lastRunState: 'Failed',
    name: 'Performance Baseline',
    nextRun: '2024-05-20 22:00:00',
    scope: 'Core Services (8)',
    status: 'Failed',
    type: 'Performance',
  },
  {
    createdAt: '2024-05-12 09:40:11',
    environment: 'Production',
    id: 'INS-20240520-008',
    lastRun: '—',
    name: 'Network Connectivity',
    nextRun: '2024-05-21 08:40:00',
    scope: 'VPC Networks (2)',
    status: 'Scheduled',
    type: 'Network',
  },
];

const inspectionTone: Record<InspectionRow['status'], StatusTone> = {
  Completed: 'emerald',
  Failed: 'red',
  'In Progress': 'blue',
  Scheduled: 'violet',
};

const inspectionTypeClassNames: Record<InspectionRow['type'], string> = {
  Alert: 'border-red-200 bg-red-50 text-red-700',
  Connectivity: 'border-amber-200 bg-amber-50 text-orange-700',
  Health: 'border-blue-200 bg-blue-50 text-blue-700',
  Log: 'border-blue-200 bg-blue-50 text-blue-700',
  Network: 'border-blue-200 bg-blue-50 text-blue-700',
  Performance: 'border-amber-200 bg-amber-50 text-orange-700',
  Resource: 'border-violet-200 bg-violet-50 text-violet-700',
  Security: 'border-cyan-200 bg-cyan-50 text-cyan-700',
};

const inspectionEnvironmentClassNames: Record<
  InspectionRow['environment'],
  string
> = {
  Production: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Staging: 'border-blue-200 bg-blue-50 text-blue-700',
};

const inspectionIconMap: Record<
  InspectionRow['type'],
  { className: string; icon: typeof Activity }
> = {
  Alert: { className: 'text-rose-500', icon: BellRing },
  Connectivity: { className: 'text-orange-500', icon: Database },
  Health: { className: 'text-blue-600', icon: Activity },
  Log: { className: 'text-blue-600', icon: FileText },
  Network: { className: 'text-blue-600', icon: GitBranch },
  Performance: { className: 'text-orange-500', icon: Zap },
  Resource: { className: 'text-violet-600', icon: Box },
  Security: { className: 'text-cyan-600', icon: ShieldCheck },
};

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

function InspectionStatusBadge({
  status,
}: {
  status: InspectionRow['status'];
}): ReactNode {
  return (
    <StatusBadge tone={inspectionTone[status]}>
      <span
        aria-hidden="true"
        className={cn(
          'mr-1.5 size-1.5 rounded-full',
          status === 'Completed' && 'bg-emerald-500',
          status === 'In Progress' && 'bg-blue-500',
          status === 'Failed' && 'bg-red-500',
          status === 'Scheduled' && 'bg-violet-500',
        )}
      />
      {status}
    </StatusBadge>
  );
}

const inspectionColumns: DataColumn<InspectionRow>[] = [
  {
    className: 'w-[17%]',
    header: 'Name ↕',
    render: (row) => {
      const Icon = inspectionIconMap[row.type].icon;

      return (
        <div className="flex items-center gap-3">
          <Icon
            aria-hidden="true"
            className={inspectionIconMap[row.type].className}
            size={22}
          />
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-950">{row.name}</p>
            <p className="mt-1 text-xs text-slate-600">{row.id}</p>
          </div>
        </div>
      );
    },
  },
  {
    className: 'w-[8%]',
    header: 'Type',
    render: (row) => (
      <InspectionTag className={inspectionTypeClassNames[row.type]}>
        {row.type}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[10%]',
    header: 'Environment ↕',
    render: (row) => (
      <InspectionTag
        className={inspectionEnvironmentClassNames[row.environment]}
      >
        {row.environment}
      </InspectionTag>
    ),
  },
  { className: 'w-[11%]', header: 'Scope', render: (row) => row.scope },
  {
    className: 'w-[10%]',
    header: 'Status ↕',
    render: (row) => <InspectionStatusBadge status={row.status} />,
  },
  {
    className: 'w-[12%]',
    header: 'Last Run ↕',
    render: (row) => (
      <div>
        <p>{row.lastRun}</p>
        {row.lastRunState ? (
          <p
            className={cn(
              'mt-1 text-xs',
              row.lastRunState === 'Success' && 'text-emerald-600',
              row.lastRunState === 'Failed' && 'text-red-600',
              row.lastRunState === 'Running...' && 'text-blue-600',
            )}
          >
            {row.lastRunState}
          </p>
        ) : null}
      </div>
    ),
  },
  { className: 'w-[12%]', header: 'Next Run ↕', render: (row) => row.nextRun },
  {
    className: 'w-[12%]',
    header: 'Created At ↕',
    render: (row) => row.createdAt,
  },
  {
    className: 'w-[8%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <ActionButton
          aria-label={`${row.status === 'In Progress' ? 'Stop' : 'Run'} ${row.name}`}
          className="size-8 p-0 text-blue-600 hover:text-blue-700"
          message={`${row.name} ${row.status === 'In Progress' ? 'stopped' : 'started'}`}
          size="sm"
          variant="ghost"
        >
          {row.status === 'In Progress' ? (
            <Square aria-hidden="true" size={13} />
          ) : (
            <Play aria-hidden="true" size={14} />
          )}
        </ActionButton>
        <LinkButton
          ariaLabel={`Open ${row.name} report`}
          className="size-8 border-slate-200 bg-slate-100 p-0 text-blue-600 hover:bg-slate-200 hover:text-blue-700"
          href="/chat/observations"
        >
          <FileText aria-hidden="true" size={14} />
        </LinkButton>
        <ActionButton
          aria-label={`More actions for ${row.name}`}
          className="size-8 p-0 text-blue-600 hover:text-blue-700"
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

const inspectionStats = [
  {
    delta: null,
    icon: Calendar,
    iconClassName: 'bg-blue-50 text-blue-600',
    label: 'Total Inspections',
    value: '48',
  },
  {
    delta: '↑ 12%',
    deltaClassName: 'text-emerald-600',
    icon: CheckCircle2,
    iconClassName: 'bg-emerald-50 text-emerald-600',
    label: 'Completed',
    value: '28',
  },
  {
    delta: null,
    icon: Clock,
    iconClassName: 'bg-amber-50 text-orange-500',
    label: 'In Progress',
    value: '6',
  },
  {
    delta: '↑ 33%',
    deltaClassName: 'text-red-600',
    icon: Square,
    iconClassName: 'bg-red-50 text-red-500',
    label: 'Failed',
    value: '8',
  },
  {
    delta: '↓ 25%',
    deltaClassName: 'text-emerald-600',
    icon: Clock,
    iconClassName: 'bg-violet-50 text-violet-600',
    label: 'Scheduled',
    value: '6',
  },
] as const;

function InspectionStatsGrid(): ReactNode {
  return (
    <div className="mb-3 grid grid-cols-5 gap-4">
      {inspectionStats.map((stat) => {
        const Icon = stat.icon;

        return (
          <section
            className="rounded-md border border-slate-200 bg-white p-4"
            key={stat.label}
          >
            <div className="flex items-center gap-4">
              <span
                className={cn(
                  'grid size-11 place-items-center rounded-full',
                  stat.iconClassName,
                )}
              >
                <Icon aria-hidden="true" size={22} />
              </span>
              <div>
                <p className="text-xs text-slate-500">{stat.label}</p>
                <div className="mt-1 flex items-end gap-3">
                  <span className="text-2xl font-semibold leading-none text-slate-950">
                    {stat.value}
                  </span>
                  {stat.delta ? (
                    <span
                      className={cn(
                        'pb-0.5 text-xs font-semibold',
                        stat.deltaClassName,
                      )}
                    >
                      {stat.delta}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-xs text-slate-500">vs last 7 days</p>
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}

function InspectionPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 8 of 48 inspections</span>
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
          aria-label="Previous inspection page"
          className="size-8 px-0"
          message="Previous page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        {[1, 2, 3, 4, 5].map((page) =>
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
          aria-label="Next inspection page"
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

interface EntityRow {
  environment: 'Production' | 'Staging';
  id: string;
  labels: string[];
  lastObserved: string;
  name: string;
  namespace: string;
  type:
    | 'Alert'
    | 'Cluster'
    | 'Database'
    | 'Function'
    | 'Host'
    | 'Pod'
    | 'Service'
    | 'Topic';
}

const entities: EntityRow[] = [
  {
    environment: 'Production',
    id: 'pod-5f7d6c8b7-2k9mz',
    labels: ['app: checkout', 'version: v2.1.0', '+3'],
    lastObserved: '2024-05-20 10:30:45',
    name: 'checkout-service',
    namespace: 'default',
    type: 'Pod',
  },
  {
    environment: 'Production',
    id: 'mysql-0',
    labels: ['app: orders', 'role: primary', '+2'],
    lastObserved: '2024-05-20 10:29:12',
    name: 'orders-db-primary',
    namespace: 'data',
    type: 'Database',
  },
  {
    environment: 'Production',
    id: 'svc-api-gateway',
    labels: ['app: gateway', 'tier: frontend', '+1'],
    lastObserved: '2024-05-20 10:28:33',
    name: 'api-gateway',
    namespace: 'default',
    type: 'Service',
  },
  {
    environment: 'Production',
    id: 'i-0abcd123ef4567890',
    labels: ['role: worker', 'az: ap-southeast-1a', '+1'],
    lastObserved: '2024-05-20 10:27:55',
    name: '10.10.2.15',
    namespace: '-',
    type: 'Host',
  },
  {
    environment: 'Production',
    id: 'topic-user-events',
    labels: ['env: prod', 'team: platform'],
    lastObserved: '2024-05-20 10:27:18',
    name: 'user-events',
    namespace: 'event-streaming',
    type: 'Topic',
  },
  {
    environment: 'Production',
    id: 'c-1a2b3c4d5e6f7g8h',
    labels: ['provider: aws', 'region: ap-southeast-1'],
    lastObserved: '2024-05-20 10:26:40',
    name: 'prod-cluster-01',
    namespace: '-',
    type: 'Cluster',
  },
  {
    environment: 'Production',
    id: 'alert-18293',
    labels: ['severity: critical', 'source: prometheus'],
    lastObserved: '2024-05-20 10:26:05',
    name: 'High CPU Usage',
    namespace: '-',
    type: 'Alert',
  },
  {
    environment: 'Staging',
    id: 'lambda-process-payment',
    labels: ['runtime: python3.11', 'team: payments'],
    lastObserved: '2024-05-20 10:25:31',
    name: 'process-payment',
    namespace: 'billing',
    type: 'Function',
  },
];

const entityTypeClassNames: Record<EntityRow['type'], string> = {
  Alert: 'border-red-200 bg-red-50 text-red-700',
  Cluster: 'border-cyan-200 bg-cyan-50 text-cyan-700',
  Database: 'border-violet-200 bg-violet-50 text-violet-700',
  Function: 'border-orange-200 bg-orange-50 text-orange-700',
  Host: 'border-orange-200 bg-orange-50 text-orange-700',
  Pod: 'border-blue-200 bg-blue-50 text-blue-700',
  Service: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Topic: 'border-pink-200 bg-pink-50 text-pink-700',
};

const entityEnvironmentClassNames: Record<EntityRow['environment'], string> = {
  Production: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Staging: 'border-blue-200 bg-blue-50 text-blue-700',
};

const entityIconMap: Record<
  EntityRow['type'],
  { className: string; icon: typeof Box }
> = {
  Alert: { className: 'text-pink-500', icon: BellRing },
  Cluster: { className: 'text-blue-600', icon: Box },
  Database: { className: 'text-orange-500', icon: Database },
  Function: { className: 'text-orange-500', icon: Zap },
  Host: { className: 'text-blue-600', icon: FileText },
  Pod: { className: 'text-blue-600', icon: Box },
  Service: { className: 'text-emerald-600', icon: GitBranch },
  Topic: { className: 'text-violet-600', icon: GitBranch },
};

const entityColumns: DataColumn<EntityRow>[] = [
  {
    className: 'w-[20%]',
    header: 'Name ↕',
    render: (row) => {
      const Icon = entityIconMap[row.type].icon;

      return (
        <div className="flex items-center gap-3">
          <Icon
            aria-hidden="true"
            className={entityIconMap[row.type].className}
            size={23}
          />
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
      <InspectionTag className={entityTypeClassNames[row.type]}>
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
    header: 'Environment',
    render: (row) => (
      <InspectionTag className={entityEnvironmentClassNames[row.environment]}>
        {row.environment}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[25%]',
    header: 'Labels / Tags',
    render: (row) => (
      <div className="flex flex-wrap gap-2">
        {row.labels.map((label) => (
          <span
            className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-700"
            key={label}
          >
            {label}
          </span>
        ))}
      </div>
    ),
  },
  {
    className: 'w-[15%]',
    header: 'Last Observed ↕',
    render: (row) => row.lastObserved,
  },
  {
    className: 'w-[7%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <LinkButton
          ariaLabel={`Open ${row.name} topology`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          href="/entity/topology"
        >
          <Eye aria-hidden="true" size={15} />
        </LinkButton>
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

function EntitySearchBar(): ReactNode {
  return (
    <section className="mb-3 rounded-md border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-4">
        <LabeledFilterSelect label="Entity Type" value="All Types" />
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
            type="search"
          />
        </label>
        <SearchButton />
      </div>
    </section>
  );
}

function EntityListToolbar(): ReactNode {
  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-700">
        <FileText aria-hidden="true" size={17} />
        <span>1,248 entities found</span>
      </div>
      <div className="flex items-center gap-3">
        <ActionButton message="Entity export started" size="sm" variant="ghost">
          <Download aria-hidden="true" size={15} />
          Export
        </ActionButton>
        <div className="flex overflow-hidden rounded-md border border-slate-200">
          <ActionButton
            aria-label="List view"
            className="rounded-none border-0 border-r border-slate-200"
            message="List view selected"
            size="sm"
            variant="ghost"
          >
            <List aria-hidden="true" size={15} />
          </ActionButton>
          <ActionButton
            aria-label="Grid view"
            className="rounded-none border-0"
            message="Grid view selected"
            size="sm"
            variant="ghost"
          >
            <Grid2X2 aria-hidden="true" size={15} />
          </ActionButton>
        </div>
        <ActionButton
          message="Column selector opened"
          size="sm"
          variant="outline"
        >
          <Settings aria-hidden="true" size={15} />
          Columns
        </ActionButton>
      </div>
    </div>
  );
}

function EntityPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 8 of 1,248 entities</span>
      <div className="flex items-center gap-3">
        <ActionButton
          className="h-8 gap-2 px-3 text-xs"
          message="Page size selector opened"
          size="sm"
          variant="outline"
        >
          20 / page
          <ChevronDown aria-hidden="true" size={14} />
        </ActionButton>
        <ActionButton
          aria-label="Previous entity page"
          className="size-8 px-0"
          message="Previous page selected"
          size="sm"
          variant="ghost"
        >
          <ChevronLeft aria-hidden="true" size={15} />
        </ActionButton>
        {[1, 2, 3].map((page) =>
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
        <span className="px-1 text-slate-400">...</span>
        <ActionButton
          className="size-8 px-0"
          message="Page 63 selected"
          size="sm"
          variant="ghost"
        >
          63
        </ActionButton>
        <ActionButton
          aria-label="Next entity page"
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

interface KnowledgeRow {
  author: string;
  category:
    | 'Best Practices'
    | 'FAQ'
    | 'Integrations'
    | 'References'
    | 'Research'
    | 'Templates';
  description: string;
  fileName: string;
  status: 'Archived' | 'Draft' | 'Published';
  size: string;
  type: 'Document' | 'Markdown' | 'PDF' | 'Spreadsheet';
  updatedAt: string;
}

const files: KnowledgeRow[] = [
  {
    author: 'sre-team',
    category: 'Best Practices',
    description: 'Comprehensive guide to incident management best practices.',
    fileName: 'Incident Management Best Practices.pdf',
    size: '2.4 MB',
    status: 'Published',
    type: 'PDF',
    updatedAt: '2024-05-20 10:30',
  },
  {
    author: 'wangwei',
    category: 'Templates',
    description: 'Template for creating on-call playbooks and procedures.',
    fileName: 'On-call Playbook Template.docx',
    size: '156 KB',
    status: 'Published',
    type: 'Document',
    updatedAt: '2024-05-18 14:22',
  },
  {
    author: 'lijing',
    category: 'References',
    description:
      'Reference guide for incident severity levels and definitions.',
    fileName: 'Severity Levels Reference.xlsx',
    size: '89 KB',
    status: 'Published',
    type: 'Spreadsheet',
    updatedAt: '2024-05-15 09:11',
  },
  {
    author: 'zhangsan',
    category: 'Best Practices',
    description: 'Step-by-step guide for conducting post-incident reviews.',
    fileName: 'Post-Incident Review Guide.md',
    size: '12 KB',
    status: 'Published',
    type: 'Markdown',
    updatedAt: '2024-05-10 16:45',
  },
  {
    author: 'sre-team',
    category: 'Templates',
    description: 'Pre-built templates for incident communications.',
    fileName: 'Communications Templates.pdf',
    size: '1.1 MB',
    status: 'Draft',
    type: 'PDF',
    updatedAt: '2024-05-08 11:20',
  },
  {
    author: 'lijing',
    category: 'Integrations',
    description: 'How to integrate external tools and services.',
    fileName: 'Integration Guide.md',
    size: '34 KB',
    status: 'Published',
    type: 'Markdown',
    updatedAt: '2024-05-05 13:33',
  },
  {
    author: 'wangwei',
    category: 'Research',
    description: 'Research on alert fatigue and mitigation strategies.',
    fileName: 'Alert Fatigue Study.pdf',
    size: '3.2 MB',
    status: 'Archived',
    type: 'PDF',
    updatedAt: '2024-05-01 10:05',
  },
  {
    author: 'sre-team',
    category: 'FAQ',
    description: 'Frequently asked questions about incident management.',
    fileName: 'FAQ - Incident Management.docx',
    size: '78 KB',
    status: 'Published',
    type: 'Document',
    updatedAt: '2024-04-28 15:12',
  },
];

const fileStatusTone: Record<KnowledgeRow['status'], StatusTone> = {
  Archived: 'slate',
  Draft: 'amber',
  Published: 'emerald',
};

const fileCategoryClassNames: Record<KnowledgeRow['category'], string> = {
  'Best Practices': 'border-violet-200 bg-violet-50 text-violet-700',
  FAQ: 'border-blue-200 bg-blue-50 text-blue-700',
  Integrations: 'border-blue-200 bg-blue-50 text-blue-700',
  References: 'border-blue-200 bg-blue-50 text-blue-700',
  Research: 'border-pink-200 bg-pink-50 text-pink-700',
  Templates: 'border-orange-200 bg-orange-50 text-orange-700',
};

const fileTypeClassNames: Record<KnowledgeRow['type'], string> = {
  Document: 'text-blue-600',
  Markdown: 'text-orange-500',
  PDF: 'text-red-600',
  Spreadsheet: 'text-emerald-600',
};

const authorClassNames: Record<string, string> = {
  lijing: 'bg-lime-600',
  'sre-team': 'bg-violet-700',
  wangwei: 'bg-blue-600',
  zhangsan: 'bg-orange-500',
};

const fileColumns: DataColumn<KnowledgeRow>[] = [
  {
    className: 'w-[30%]',
    header: 'Name',
    render: (row) => (
      <div className="flex items-center gap-3">
        <FileText
          aria-hidden="true"
          className={fileTypeClassNames[row.type]}
          size={22}
        />
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-950">
            {row.fileName}
          </p>
          <p className="mt-1 truncate text-xs text-slate-600">
            {row.description}
          </p>
        </div>
      </div>
    ),
  },
  {
    className: 'w-[12%]',
    header: 'Category',
    render: (row) => (
      <InspectionTag className={fileCategoryClassNames[row.category]}>
        {row.category}
      </InspectionTag>
    ),
  },
  {
    className: 'w-[11%]',
    header: 'Type',
    render: (row) => (
      <span className="inline-flex items-center gap-2">
        <FileText
          aria-hidden="true"
          className={fileTypeClassNames[row.type]}
          size={15}
        />
        {row.type}
      </span>
    ),
  },
  {
    className: 'w-[11%]',
    header: 'Status',
    render: (row) => (
      <StatusBadge tone={fileStatusTone[row.status]}>{row.status}</StatusBadge>
    ),
  },
  {
    className: 'w-[13%]',
    header: 'Updated At',
    render: (row) => row.updatedAt,
  },
  { className: 'w-[7%]', header: 'Size', render: (row) => row.size },
  {
    className: 'w-[11%]',
    header: 'Author',
    render: (row) => (
      <span className="inline-flex items-center gap-2">
        <span
          className={cn(
            'grid size-6 place-items-center rounded-full text-xs font-semibold text-white',
            authorClassNames[row.author] ?? 'bg-slate-500',
          )}
        >
          {row.author.slice(0, 1).toUpperCase()}
        </span>
        {row.author}
      </span>
    ),
  },
  {
    className: 'w-[8%]',
    header: 'Actions',
    render: (row) => (
      <div className="flex items-center gap-2">
        <ActionButton
          aria-label={`View ${row.fileName}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.fileName} opened`}
          size="sm"
          variant="ghost"
        >
          <Eye aria-hidden="true" size={15} />
        </ActionButton>
        <ActionButton
          aria-label={`Download ${row.fileName}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.fileName} download started`}
          size="sm"
          variant="ghost"
        >
          <Download aria-hidden="true" size={15} />
        </ActionButton>
        <ActionButton
          aria-label={`More actions for ${row.fileName}`}
          className="size-8 border-0 bg-transparent p-0 text-blue-600 shadow-none hover:bg-slate-100 hover:text-blue-700"
          message={`${row.fileName} actions opened`}
          size="sm"
          variant="ghost"
        >
          <MoreVertical aria-hidden="true" size={15} />
        </ActionButton>
      </div>
    ),
  },
];

function FilesPagination(): ReactNode {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600">
      <span>Showing 1 to 8 of 8 files</span>
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
          aria-label="Previous files page"
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
          aria-label="Next files page"
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

function SearchButton(): ReactNode {
  return <ActionButton message="Search executed">Search</ActionButton>;
}

export function IncidentsPage(): ReactNode {
  return (
    <AppShell activeItem="Incidents" activeSection="incidents">
      <PageHeader parentTitle="Incidents" title="Incidents" />
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
            <FilterInput placeholder="Search incidents..." />
            <SelectLike label="Severity" />
            <SelectLike label="Status" />
            <SelectLike label="Source" />
            <SelectLike label="Last 24 hours" />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <DataTable
            columns={incidentColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.name}
            rows={incidents}
          />
          <IncidentPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function IncidentIntegrationsPage(): ReactNode {
  return (
    <AppShell activeItem="Integrations" activeSection="incidents">
      <PageHeader
        actionsClassName="pr-4"
        actions={
          <ActionButton message="Add integration dialog opened">
            <Plus aria-hidden="true" size={15} />
            New Integrations
          </ActionButton>
        }
        description="Configure alert sources to receive incidents in ObserveLens via webhook."
        parentTitle="Incidents"
        title="Integrations"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput placeholder="Search integrations..." />
            <LabeledFilterSelect label="Type" value="All Types" />
            <LabeledFilterSelect label="Status" value="All Status" />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <DataTable
            columns={integrationColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.name}
            rows={integrations}
          />
          <IntegrationPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function InspectionsPage(): ReactNode {
  return (
    <AppShell activeItem="Inspections" activeSection="tasks">
      <PageHeader
        actions={
          <>
            <ActionButton
              message="Schedule inspection dialog opened"
              variant="outline"
            >
              <Calendar aria-hidden="true" size={15} />
              Schedule Inspection
            </ActionButton>
            <ActionButton message="New inspection dialog opened">
              <Plus aria-hidden="true" size={15} />
              New Inspection
            </ActionButton>
          </>
        }
        actionsClassName="pr-4"
        description="Manage and monitor inspection tasks across your environments."
        parentTitle="Tasks"
        title="Inspections"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <InspectionStatsGrid />
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput placeholder="Search inspections by name..." />
            <LabeledFilterSelect label="Status" value="All Statuses" />
            <LabeledFilterSelect label="Type" value="All Types" />
            <LabeledFilterSelect label="Environment" value="All Environments" />
            <LabeledFilterSelect label="Created At" value="Last 7 days" />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <DataTable
            columns={inspectionColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.id}
            rows={inspections}
          />
          <InspectionPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function EntitySearchPage(): ReactNode {
  return (
    <AppShell activeItem="Search" activeSection="entity">
      <PageHeader
        description="Search and discover entities across your infrastructure and observability data."
        parentTitle="Entity"
        title="Search"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <EntitySearchBar />
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <EntityListToolbar />
          <DataTable
            columns={entityColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.id}
            rows={entities}
          />
          <EntityPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function EntityTopologyPage(): ReactNode {
  const topologyNodes = [
    {
      className: 'left-[50%] top-[7%]',
      icon: GitBranch,
      label: 'user-frontend',
      subtitle: 'Service',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
    {
      className: 'left-[50%] top-[20%]',
      icon: GitBranch,
      label: 'api-gateway',
      subtitle: 'Service',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
    {
      className: 'left-[50%] top-[36%]',
      icon: Box,
      label: 'checkout-service',
      subtitle: 'Pod',
      tone: 'border-blue-500 bg-blue-50 text-blue-700 shadow-blue-100',
    },
    {
      className: 'left-[25%] top-[35%]',
      icon: GitBranch,
      label: 'payment-service',
      subtitle: 'Service',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
    {
      className: 'left-[25%] top-[51%]',
      icon: GitBranch,
      label: 'email-service',
      subtitle: 'Service',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
    {
      className: 'left-[72%] top-[27%]',
      icon: Database,
      label: 'redis-cache',
      subtitle: 'Redis',
      tone: 'border-violet-300 bg-violet-50 text-violet-700',
    },
    {
      className: 'left-[75%] top-[37%]',
      icon: Database,
      label: 'orders-db-primary',
      subtitle: 'Database (MySQL)',
      tone: 'border-orange-300 bg-orange-50 text-orange-600',
    },
    {
      className: 'left-[75%] top-[55%]',
      icon: Database,
      label: 'orders-db-replica',
      subtitle: 'Database (MySQL)',
      tone: 'border-orange-300 bg-orange-50 text-orange-600',
    },
    {
      className: 'left-[50%] top-[61%]',
      icon: MessageSquare,
      label: 'message-queue',
      subtitle: 'Kafka Topic',
      tone: 'border-violet-300 bg-violet-50 text-violet-700',
    },
    {
      className: 'left-[36%] top-[81%]',
      icon: GitBranch,
      label: 'inventory-service',
      subtitle: 'Consumer',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
    {
      className: 'left-[65%] top-[81%]',
      icon: GitBranch,
      label: 'notification-service',
      subtitle: 'Consumer',
      tone: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    },
  ];

  const legendItems = [
    ['bg-blue-600', 'Request'],
    ['border-violet-500 border-dashed', 'Cache'],
    ['bg-orange-500', 'Database'],
    ['border-orange-500 border-dashed', 'Replication'],
    ['border-violet-500 border-dashed', 'Message'],
    ['border-emerald-300 bg-emerald-50', 'Service'],
    ['border-orange-300 bg-orange-50', 'Database'],
    ['border-violet-300 bg-violet-50', 'Queue'],
    ['border-blue-300 bg-blue-50', 'External'],
  ];

  return (
    <AppShell activeItem="Topology" activeSection="entity">
      <PageHeader
        description="Visualize relationships and dependencies between entities in your infrastructure."
        parentTitle="Entity"
        title="Topology"
      />
      <div className="flex min-h-0 flex-1 flex-col overflow-auto px-6 pb-6">
        <section className="mb-3 rounded-md border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-4">
            <LabeledFilterSelect label="Environment" value="All Environments" />
            <LabeledFilterSelect label="Entity Type" value="All Types" />
            <label className="relative block min-w-0 flex-1">
              <span className="sr-only">Search topology entities</span>
              <input
                className="h-12 w-full rounded-md border border-slate-200 bg-white px-4 pr-12 text-sm text-slate-800 outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                placeholder="Search entity by name, ID, IP, or tag..."
                type="search"
              />
              <Search
                aria-hidden="true"
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-700"
                size={19}
              />
            </label>
            <SearchButton />
          </div>
        </section>
        <div className="grid min-h-[620px] grid-cols-[minmax(0,1fr)_480px] gap-3">
          <section className="relative overflow-hidden rounded-md border border-slate-200 bg-white">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,#e2e8f0_1px,transparent_0)] [background-size:18px_18px]" />
            <div className="absolute left-4 top-4 z-10 flex gap-2">
              {['⚙', '⛶', '+', '−', '⤢'].map((control) => (
                <ActionButton
                  aria-label={`Topology control ${control}`}
                  className="size-9 p-0"
                  key={control}
                  message={`Topology control ${control} selected`}
                  size="sm"
                  variant="ghost"
                >
                  {control}
                </ActionButton>
              ))}
            </div>
            <div className="absolute right-4 top-4 z-10">
              <LabeledFilterSelect label="Layout" value="Auto" />
            </div>
            <svg
              className="absolute inset-0 size-full"
              role="presentation"
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
            >
              <defs>
                <marker
                  id="arrow-blue"
                  markerHeight="6"
                  markerWidth="6"
                  orient="auto"
                  refX="5"
                  refY="3"
                >
                  <path d="M0,0 L6,3 L0,6 Z" fill="#2563eb" />
                </marker>
                <marker
                  id="arrow-purple"
                  markerHeight="6"
                  markerWidth="6"
                  orient="auto"
                  refX="5"
                  refY="3"
                >
                  <path d="M0,0 L6,3 L0,6 Z" fill="#7c3aed" />
                </marker>
                <marker
                  id="arrow-orange"
                  markerHeight="6"
                  markerWidth="6"
                  orient="auto"
                  refX="5"
                  refY="3"
                >
                  <path d="M0,0 L6,3 L0,6 Z" fill="#f97316" />
                </marker>
              </defs>
              <line
                stroke="#16a34a"
                strokeWidth="0.55"
                x1="50"
                x2="50"
                y1="12.5"
                y2="20"
              />
              <line
                stroke="#2563eb"
                strokeWidth="0.55"
                x1="50"
                x2="50"
                y1="25.5"
                y2="36"
              />
              <line
                markerEnd="url(#arrow-blue)"
                stroke="#2563eb"
                strokeWidth="0.55"
                x1="42.9"
                x2="33.4"
                y1="43"
                y2="43"
              />
              <line
                markerEnd="url(#arrow-blue)"
                stroke="#2563eb"
                strokeWidth="0.55"
                x1="57.1"
                x2="68.4"
                y1="43"
                y2="43"
              />
              <path
                d="M56.4 39.3 L67.8 32"
                markerEnd="url(#arrow-purple)"
                stroke="#7c3aed"
                strokeDasharray="1.6 1.2"
                strokeWidth="0.55"
                fill="none"
              />
              <path
                d="M43.8 39.8 L32.2 50"
                markerEnd="url(#arrow-purple)"
                stroke="#7c3aed"
                strokeDasharray="1.6 1.2"
                strokeWidth="0.55"
                fill="none"
              />
              <line
                stroke="#2563eb"
                strokeWidth="0.55"
                x1="50"
                x2="50"
                y1="46"
                y2="61"
              />
              <path
                d="M46.2 66 L39.1 78.6"
                markerEnd="url(#arrow-purple)"
                stroke="#7c3aed"
                strokeDasharray="1.6 1.2"
                strokeWidth="0.55"
                fill="none"
              />
              <path
                d="M53.8 66 L62.1 78.8"
                markerEnd="url(#arrow-purple)"
                stroke="#7c3aed"
                strokeDasharray="1.6 1.2"
                strokeWidth="0.55"
                fill="none"
              />
              <line
                markerEnd="url(#arrow-orange)"
                stroke="#f97316"
                strokeDasharray="1.8 1.3"
                strokeWidth="0.55"
                x1="75"
                x2="75"
                y1="44.8"
                y2="54"
              />
            </svg>
            {topologyNodes.map((node) => {
              const Icon = node.icon;

              return (
                <ActionButton
                  className={cn(
                    'absolute z-10 flex min-w-[154px] -translate-x-1/2 items-center gap-3 rounded-md border px-4 py-2 text-left text-sm shadow-sm',
                    node.tone,
                    node.className,
                  )}
                  key={node.label}
                  message={`${node.label} selected`}
                  variant="outline"
                >
                  <Icon aria-hidden="true" size={22} />
                  <span>
                    <span className="block font-semibold text-slate-950">
                      {node.label}
                    </span>
                    <span className="block text-xs font-medium text-slate-600">
                      {node.subtitle}
                    </span>
                  </span>
                </ActionButton>
              );
            })}
            <div className="absolute bottom-6 left-4 z-10 w-32 rounded-md border border-slate-200 bg-white p-3 text-xs shadow-sm">
              <div className="space-y-2">
                {legendItems.map(([tone, label]) => (
                  <div className="flex items-center gap-2" key={label}>
                    <span
                      className={cn(
                        'h-0.5 w-5 rounded border',
                        tone,
                        tone.startsWith('bg') && 'border-0',
                      )}
                    />
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="absolute bottom-6 right-6 z-10 h-28 w-40 rounded-md border border-slate-200 bg-white p-3 shadow-sm">
              <div className="relative size-full rounded border border-blue-300 bg-blue-50">
                <span className="absolute left-5 top-6 h-3 w-8 rounded border border-emerald-300 bg-emerald-100" />
                <span className="absolute left-14 top-12 h-3 w-8 rounded border border-violet-300 bg-violet-100" />
                <span className="absolute right-5 top-8 h-3 w-8 rounded border border-violet-300 bg-violet-100" />
                <span className="absolute bottom-3 left-8 h-3 w-8 rounded border border-emerald-300 bg-emerald-100" />
                <span className="absolute bottom-6 right-4 h-3 w-8 rounded border border-orange-300 bg-orange-100" />
              </div>
            </div>
          </section>
          <aside className="overflow-hidden rounded-md border border-slate-200 bg-white">
            <div className="flex items-start justify-between border-b border-slate-200 p-5">
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-full bg-blue-600 text-white">
                  <Box aria-hidden="true" size={20} />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold text-slate-950">
                      checkout-service
                    </h2>
                    <StatusBadge tone="emerald">Pod</StatusBadge>
                  </div>
                </div>
              </div>
              <button
                className="text-xl leading-none text-slate-500 hover:text-slate-900"
                type="button"
              >
                ×
              </button>
            </div>
            <div className="flex border-b border-slate-200 px-5">
              {['Overview', 'Relationships 7', 'Metrics', 'Alerts 2'].map(
                (tab, index) => (
                  <button
                    className={cn(
                      'h-11 px-3 text-sm font-medium',
                      index === 0
                        ? 'border-b-2 border-blue-600 text-blue-600'
                        : 'text-slate-600 hover:text-blue-600',
                    )}
                    key={tab}
                    type="button"
                  >
                    {tab}
                  </button>
                ),
              )}
            </div>
            <div className="space-y-5 p-5 text-sm">
              <dl className="grid grid-cols-[110px_1fr] gap-x-4 gap-y-4">
                <dt className="text-slate-500">Name</dt>
                <dd className="font-medium">checkout-service</dd>
                <dt className="text-slate-500">ID</dt>
                <dd>pod-5f7d6c8b7-2k9mz</dd>
                <dt className="text-slate-500">Namespace</dt>
                <dd>default</dd>
                <dt className="text-slate-500">Environment</dt>
                <dd>
                  <InspectionTag className="border-emerald-200 bg-emerald-50 text-emerald-700">
                    Production
                  </InspectionTag>
                </dd>
                <dt className="text-slate-500">Labels</dt>
                <dd className="flex flex-wrap gap-2">
                  {[
                    'app: checkout',
                    'version: v2.1.0',
                    'tier: backend',
                    '+3',
                  ].map((label) => (
                    <span
                      className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-700"
                      key={label}
                    >
                      {label}
                    </span>
                  ))}
                </dd>
                <dt className="text-slate-500">Created At</dt>
                <dd>2024-05-10 14:22:18</dd>
                <dt className="text-slate-500">Last Observed</dt>
                <dd className="flex items-center gap-2">
                  <Clock aria-hidden="true" size={15} />
                  2024-05-20 10:30:45
                </dd>
              </dl>
              <section className="border-t border-slate-200 pt-5">
                <h3 className="font-semibold text-slate-950">Description</h3>
                <p className="mt-3 leading-6 text-slate-700">
                  Checkout service handles order validation, pricing, and
                  payment processing.
                </p>
              </section>
              <section className="border-t border-slate-200 pt-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-slate-950">
                    Related Alerts
                  </h3>
                  <button className="text-sm text-blue-600" type="button">
                    View all
                  </button>
                </div>
                <div className="mt-4 space-y-4">
                  {[
                    ['bg-red-500', 'High Error Rate', 'Critical', '2m ago'],
                    ['bg-amber-500', 'High Latency', 'Warning', '15m ago'],
                  ].map(([dot, title, severity, time]) => (
                    <div className="flex items-start gap-3" key={title}>
                      <span className={cn('mt-1.5 size-2 rounded-full', dot)} />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-slate-950">{title}</p>
                        <p className="mt-1 text-xs text-slate-600">
                          checkout-service {title.toLowerCase()} is high
                        </p>
                      </div>
                      <div className="text-right">
                        <StatusBadge
                          tone={severity === 'Critical' ? 'red' : 'amber'}
                        >
                          {severity}
                        </StatusBadge>
                        <p className="mt-1 text-xs text-slate-500">{time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
              <section className="border-t border-slate-200 pt-5">
                <h3 className="font-semibold text-slate-950">Quick Actions</h3>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  <ActionButton
                    message="Metrics panel opened"
                    size="sm"
                    variant="outline"
                  >
                    <Activity aria-hidden="true" size={14} />
                    Metrics
                  </ActionButton>
                  <ActionButton
                    message="Logs panel opened"
                    size="sm"
                    variant="outline"
                  >
                    <FileSearch aria-hidden="true" size={14} />
                    Logs
                  </ActionButton>
                  <LinkButton className="h-8" href="/" tone="outline">
                    <Search aria-hidden="true" size={14} />
                    Query
                  </LinkButton>
                </div>
              </section>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

export function KnowledgeFilesPage(): ReactNode {
  return (
    <AppShell activeItem="Files" activeSection="knowledge">
      <PageHeader
        actions={
          <ActionButton message="Upload file dialog opened">
            <Plus aria-hidden="true" size={15} />
            Upload File
          </ActionButton>
        }
        actionsClassName="pr-4"
        description="Browse and manage knowledge base files and documents."
        parentTitle="Knowledge"
        title="Files"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput placeholder="Search files..." />
            <LabeledFilterSelect label="Category" value="All Categories" />
            <LabeledFilterSelect label="Type" value="All Types" />
            <LabeledFilterSelect label="Status" value="All Status" />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <DataTable
            columns={fileColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.fileName}
            rows={files}
          />
          <FilesPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function SettingsModelsPage(): ReactNode {
  return (
    <AppShell activeItem="Models" activeSection="settings">
      <PageHeader
        actions={
          <ActionButton message="Add model dialog opened">
            <Plus aria-hidden="true" size={15} />
            Add Model
          </ActionButton>
        }
        actionsClassName="pr-4"
        description="Manage and configure AI models used by ObserveLens."
        parentTitle="Settings"
        title="Models"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput placeholder="Search models by name or provider..." />
            <LabeledFilterSelect label="Provider" value="All Providers" />
            <LabeledFilterSelect label="Status" value="All Statuses" />
            <LabeledFilterSelect
              label="Capabilities"
              value="All Capabilities"
            />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <DataTable
            columns={modelColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => `${row.provider}-${row.model}`}
            rows={models}
          />
          <ModelsPagination />
        </section>
      </div>
    </AppShell>
  );
}

export function SettingsNotificationsPage(): ReactNode {
  return (
    <AppShell activeItem="Notifications" activeSection="settings">
      <PageHeader
        actions={
          <ActionButton message="Add webhook dialog opened">
            <Plus aria-hidden="true" size={15} />
            Add Webhook
          </ActionButton>
        }
        actionsClassName="pr-4"
        parentTitle="Settings"
        title="Notifications"
      />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-6">
        <Toolbar>
          <div className="flex flex-wrap gap-4">
            <FilterInput placeholder="Search notifications by name..." />
          </div>
          <SearchButton />
        </Toolbar>
        <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-5 py-5">
            <h2 className="text-lg font-semibold text-slate-950">
              Notification Webhooks
            </h2>
          </div>
          <DataTable
            columns={notificationColumns}
            containerClassName="rounded-none border-0"
            getRowKey={(row) => row.name}
            rows={notifications}
          />
        </section>
      </div>
    </AppShell>
  );
}

const observationTabs = [
  { icon: Activity, label: 'Metrics', value: 'API Gateway Error Rate' },
  { icon: FileSearch, label: 'Logs', value: '504 Timeout Burst' },
  { icon: GitBranch, label: 'Trace', value: 'user-service latency' },
  { icon: Box, label: 'Topology', value: 'api-gateway → user-service' },
];

export function ChatObservationsPage(): ReactNode {
  return (
    <AppShell activeItem="Observations" activeSection="chat">
      <PageHeader
        actions={
          <>
            <ActionButton message="Evidence export started" variant="outline">
              Export Evidence
            </ActionButton>
            <LinkButton href="/" tone="default">
              <Send aria-hidden="true" size={15} />
              Ask Follow-up
            </LinkButton>
          </>
        }
        description="Evidence panel linked to the active investigation step."
        parentTitle="Chat"
        title="Observations"
      />
      <div className="grid min-h-0 flex-1 grid-cols-[1fr_390px] gap-4 overflow-auto px-6 pb-6">
        <section className="rounded-md border border-slate-200 bg-white">
          <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
            <h2 className="text-sm font-semibold">Investigation Timeline</h2>
            <StatusBadge tone="blue">Step 4 Running</StatusBadge>
          </div>
          <div className="space-y-4 p-5">
            {[
              '建立调查计划',
              '查询服务指标',
              '分析错误日志',
              '验证依赖链路',
              '生成 RCA',
            ].map((step, index) => (
              <article className="flex gap-3" key={step}>
                <div
                  className={cn(
                    'grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold',
                    index < 3 && 'bg-emerald-500 text-white',
                    index === 3 && 'bg-blue-600 text-white',
                    index > 3 && 'bg-slate-100 text-slate-500',
                  )}
                >
                  {index < 3 ? '✓' : index + 1}
                </div>
                <div className="min-w-0 flex-1 rounded-md border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-950">{step}</h3>
                    <span className="text-xs text-slate-500">
                      10:{22 + index * 2}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {index === 3
                      ? '正在关联 Metrics、Logs 和 Trace 证据，验证 user-service 响应超时是否为主要根因。'
                      : '已完成证据查询，并将结果绑定到当前调查链路中。'}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>
        <aside className="rounded-md border border-slate-200 bg-white">
          <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
            <h2 className="text-sm font-semibold">Observation Evidence</h2>
            <ActionButton message="Observation evidence refreshed" size="sm">
              Refresh
            </ActionButton>
          </div>
          <div className="space-y-4 p-4">
            {observationTabs.map((tab) => {
              const Icon = tab.icon;

              return (
                <article
                  className="rounded-md border border-slate-200 p-4"
                  key={tab.label}
                >
                  <div className="flex items-center gap-3">
                    <div className="grid size-8 place-items-center rounded-md bg-blue-50 text-blue-700">
                      <Icon aria-hidden="true" size={16} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold">{tab.label}</h3>
                      <p className="text-xs text-slate-500">{tab.value}</p>
                    </div>
                  </div>
                  <div className="mt-4 h-24 rounded bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                    {tab.label === 'Metrics'
                      ? 'Error rate increased from 2.1% to 15.4%; p95 latency crossed 1.8s.'
                      : 'Evidence is linked to the active investigation step and can be verified before RCA confirmation.'}
                  </div>
                </article>
              );
            })}
            <section className="rounded-md border border-emerald-200 bg-emerald-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-emerald-800">
                <ShieldCheck aria-hidden="true" size={16} />
                Evidence Chain Verified
              </div>
              <p className="mt-2 text-xs leading-5 text-emerald-700">
                Metrics, logs, trace spans, and entity dependencies point to
                user-service timeout saturation.
              </p>
            </section>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
