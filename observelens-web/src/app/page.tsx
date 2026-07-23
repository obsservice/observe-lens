'use client';

import { AppShell } from '@/components/observe-lens/app-shell';
import { ActionButton } from '@/components/observe-lens/interactive-controls';
import { StatusBadge } from '@/components/observe-lens/status-badge';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';
import { useState } from 'react';

const sessions = [
  {
    title: 'API 服务错误率升高排查',
    description: '分析 api-gateway 服务错误率升高的原因',
    time: '10:30 AM',
    icon: '</>',
    accent: 'bg-emerald-500',
    active: true,
    favorite: true,
  },
  {
    title: '数据库连接数异常',
    description: 'PostgreSQL 连接数持续增长到上限',
    time: '09:18 AM',
    icon: 'DB',
    accent: 'bg-violet-500',
    active: false,
    favorite: false,
  },
  {
    title: 'Kubernetes 节点资源告警',
    description: '节点 CPU 使用率超过 90% 告警分析',
    time: 'Yesterday',
    icon: 'K8',
    accent: 'bg-blue-600',
    active: false,
    favorite: true,
  },
  {
    title: '订单系统响应慢',
    description: '订单创建接口响应时间突增排查',
    time: 'May 19',
    icon: '🛒',
    accent: 'bg-orange-50 text-orange-500',
    active: false,
    favorite: false,
  },
];

const investigationRows = [
  [
    '检查系统概况',
    '查看整体指标趋势，确认错误率在 10:00 开始显著上升。',
    '已完成',
  ],
  [
    '检查应用指标',
    'api-gateway 错误率从 2% 上升到 15%+，5xx 占比 82%。',
    '已完成',
  ],
  [
    '检查日志错误',
    '大量出现 user-service 调用超时错误，状态码 504。',
    '已完成',
  ],
  ['检查依赖服务', '正在分析 user-service 指标和端点健康状态。', '运行中'],
  ['根因定位', '等待上一步完成。', '待开始'],
];

const entityCards = [
  ['Service', 'api-gateway'],
  ['Service', 'user-service'],
  ['Namespace', 'prod'],
  ['Pod', 'api-gateway-7f9c9d8'],
  ['Deployment', 'api-gateway'],
];

function ChatSessionList({
  isCollapsed,
  onToggle,
}: {
  isCollapsed: boolean;
  onToggle: () => void;
}): ReactNode {
  if (isCollapsed) {
    return null;
  }

  return (
    <aside className="w-[346px] shrink-0 border-r border-slate-200 bg-white">
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-3">
        <h1 className="text-lg font-semibold tracking-normal text-slate-950">
          Sessions
        </h1>
        <button
          aria-label="Collapse sessions"
          className="grid size-8 place-items-center rounded-md border border-slate-200 bg-slate-100 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-200"
          onClick={onToggle}
          type="button"
        >
          ‹
        </button>
      </div>
      <div className="mt-4 flex gap-3 px-3">
        <label className="relative flex-1">
          <span className="sr-only">Search sessions</span>
          <input
            className="h-10 w-full rounded-md border border-slate-200 bg-white px-4 pr-10 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="Search sessions..."
            type="search"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-lg text-slate-800">
            ⌕
          </span>
        </label>
        <ActionButton
          aria-label="New session"
          className="size-10 px-0 text-xl"
          message="New investigation session created"
          variant="outline"
        >
          +
        </ActionButton>
      </div>

      <div className="mt-5 space-y-3 px-3">
        {sessions.map((session) => (
          <article
            className={cn(
              'flex gap-3 rounded-md px-2.5 py-3 transition',
              session.active
                ? 'bg-blue-50/70 shadow-sm shadow-blue-100'
                : 'hover:bg-slate-50',
            )}
            key={session.title}
          >
            <div
              className={cn(
                'grid size-9 shrink-0 place-items-center rounded-md text-xs font-bold text-white',
                session.accent,
              )}
            >
              {session.icon}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="truncate text-sm font-semibold text-slate-950">
                {session.title}
              </h2>
              <div className="mt-1 flex items-center gap-2 whitespace-nowrap text-xs text-slate-500">
                <span>{session.time}</span>
                <span className="text-slate-300">•</span>
                <span
                  className={cn(
                    'inline-flex items-center',
                    session.favorite ? 'text-amber-500' : 'text-slate-500',
                  )}
                  title={session.favorite ? 'Favorited' : 'Not favorited'}
                >
                  <span aria-hidden="true">{session.favorite ? '★' : '☆'}</span>
                </span>
                {session.active ? (
                  <>
                    <span className="text-slate-300">•</span>
                    <span className="text-blue-600">Active</span>
                  </>
                ) : null}
              </div>
            </div>
          </article>
        ))}
      </div>
    </aside>
  );
}

export default function HomePage(): ReactNode {
  const [isSessionsCollapsed, setIsSessionsCollapsed] = useState(false);

  return (
    <AppShell activeItem="Sessions" activeSection="chat">
      <div className="flex min-h-0 flex-1">
        <ChatSessionList
          isCollapsed={isSessionsCollapsed}
          onToggle={() => setIsSessionsCollapsed((value) => !value)}
        />
        <section className="relative flex min-w-0 flex-1 flex-col bg-white">
          <div className="flex h-12 shrink-0 items-center justify-between border-b border-slate-200 px-6">
            <div>
              <div className="flex items-center gap-3">
                {isSessionsCollapsed ? (
                  <button
                    aria-label="Expand sessions"
                    className="grid size-8 place-items-center rounded-md border border-blue-200 bg-blue-50 text-sm font-semibold text-blue-700 shadow-sm transition hover:bg-blue-100"
                    onClick={() => setIsSessionsCollapsed(false)}
                    type="button"
                  >
                    ›
                  </button>
                ) : null}
                <h2 className="text-lg font-semibold text-slate-950">
                  API 服务错误率升高排查
                </h2>
                <ActionButton
                  className="text-sm text-slate-700"
                  message="Session title editor opened"
                  title="Edit title"
                  variant="ghost"
                >
                  ✎
                </ActionButton>
                <ActionButton
                  className="text-sm text-amber-400"
                  message="Session pinned"
                  title="Pin session"
                  variant="ghost"
                >
                  ★
                </ActionButton>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ActionButton message="Share dialog opened" variant="outline">
                Share
              </ActionButton>
              <ActionButton message="Export task started" variant="outline">
                Export
              </ActionButton>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-auto px-6 pb-32 pt-7">
            <div className="mx-auto w-full max-w-[950px]">
              <div className="ml-auto flex max-w-[700px] items-start justify-end gap-4">
                <div className="rounded-md bg-blue-50 px-4 py-3 text-sm text-slate-800">
                  api-gateway 服务错误率从 2% 飙升到 15%
                  以上，帮我分析下可能的原因。
                </div>
                <div className="grid size-9 shrink-0 place-items-center rounded-full bg-violet-600 text-sm font-semibold text-white">
                  S
                </div>
              </div>
              <p className="mt-1 text-right text-xs text-slate-400">10:30 AM</p>

              <div className="mt-4 space-y-3">
                <section className="rounded-md border border-slate-200 bg-white">
                  <div className="flex h-10 items-center justify-between px-4">
                    <h3 className="text-sm font-semibold text-slate-900">
                      Info 分析信息
                    </h3>
                    <ActionButton
                      message="Analysis info collapsed"
                      variant="ghost"
                    >
                      ⌄
                    </ActionButton>
                  </div>
                  <p className="border-t border-slate-100 px-4 py-3 text-sm leading-6 text-slate-700">
                    api-gateway 服务的错误率在 10:00 左右从 2% 快速上升到 15%
                    以上，持续时间约 23
                    分钟。通过指标、日志和链路追踪分析，初步定位到后端
                    <span className="mx-1 rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
                      user-service
                    </span>
                    响应超时导致。
                  </p>
                </section>

                <section className="rounded-md border border-slate-200 bg-white">
                  <div className="flex h-10 items-center justify-between px-4">
                    <h3 className="text-sm font-semibold text-slate-900">
                      Entity 相关实体（5）
                    </h3>
                  </div>
                  <div className="grid grid-cols-5 gap-3 border-t border-slate-100 px-4 py-3">
                    {entityCards.map(([label, value]) => (
                      <div
                        className="rounded border border-slate-200 bg-white px-3 py-2"
                        key={`${label}-${value}`}
                      >
                        <p className="text-[11px] text-slate-500">{label}</p>
                        <p className="mt-1 truncate text-xs font-medium text-slate-700">
                          {value}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-md border border-slate-200 bg-white">
                  <div className="flex h-11 items-center justify-between px-4">
                    <h3 className="text-sm font-semibold text-slate-900">
                      Investigation 调查过程
                    </h3>
                  </div>
                  <div className="divide-y divide-slate-200 border-t border-slate-200">
                    {investigationRows.map(([title, body, state], index) => (
                      <div
                        className="grid grid-cols-[1fr_92px] items-center gap-4 px-4 py-3"
                        key={title}
                      >
                        <div className="flex min-w-0 items-start gap-3">
                          <span
                            className={cn(
                              'mt-0.5 grid size-5 shrink-0 place-items-center rounded-full text-xs font-semibold text-white',
                              state === '已完成' && 'bg-emerald-500',
                              state === '运行中' && 'bg-blue-600',
                              state === '待开始' &&
                                'bg-slate-300 text-slate-600',
                            )}
                          >
                            {state === '已完成' ? '✓' : index + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-semibold text-slate-900">
                              步骤 {index + 1}
                              <span className="ml-3">{title}</span>
                            </p>
                            <p className="mt-1 truncate text-xs text-slate-600">
                              {body}
                            </p>
                          </div>
                        </div>
                        <StatusBadge
                          tone={
                            state === '运行中'
                              ? 'blue'
                              : state === '已完成'
                                ? 'emerald'
                                : 'slate'
                          }
                        >
                          {state}
                        </StatusBadge>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 left-0 right-[17px] px-6">
            <div className="mx-auto w-full max-w-[950px]">
              <form className="w-full rounded-md border border-blue-400 bg-white p-3 shadow-lg shadow-blue-100">
                <label className="sr-only" htmlFor="message">
                  Ask anything about your observability data
                </label>
                <textarea
                  className="h-10 w-full resize-none border-0 text-sm text-slate-800 outline-none placeholder:text-slate-500"
                  id="message"
                  placeholder="Ask anything about your observability data..."
                />
                <div className="flex items-center justify-end">
                  <ActionButton
                    aria-label="Send message"
                    className="size-9 px-0 text-lg"
                    message="Message sent to ObserveLens"
                  >
                    ▷
                  </ActionButton>
                </div>
              </form>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
